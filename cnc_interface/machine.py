from __future__ import annotations
from contextlib import contextmanager

import dataclasses
from typing import Callable, Generic, Iterator, TypeVar
import pydantic
import requests
import threading
import time

import rotary_encoder


class ConnectionError(Exception):
    pass


class MachineSettings(pydantic.BaseModel):
    jog_feed_rate: float = pydantic.Field(alias="jogFeedRate", default=0)
    jog_step_size_xy: float = pydantic.Field(alias="jogStepSizeXY", default=0)
    jog_step_size_z: float = pydantic.Field(alias="jogStepSizeZ", default=0)
    preferred_units: str = pydantic.Field(alias="preferredUnits", default="MM")


class MachineCoords(pydantic.BaseModel):
    units: str = "MM"
    x: float = 0
    y: float = 0
    z: float = 0


class SpindleSettings(pydantic.BaseModel):
    speed: float = 0
    is_on: bool = False


class MachineStatus(pydantic.BaseModel):
    state: str = "UNKNOWN"
    machine_coord: MachineCoords = pydantic.Field(alias="machineCoord", default_factory=MachineCoords)
    work_coord: MachineCoords = pydantic.Field(alias="workCoord", default_factory=MachineCoords)
    spindle_speed: float = pydantic.Field(alias="spindleSpeed", default=0)


class Machine(pydantic.BaseModel):
    is_connected: bool = False
    machine_status: MachineStatus = pydantic.Field(default_factory=MachineStatus)
    machine_settings: MachineSettings = pydantic.Field(default_factory=MachineSettings)
    spindle_settings: SpindleSettings = pydantic.Field(default_factory=SpindleSettings)


class _UpdateThread(threading.Thread):
    def __init__(self, value: SelfUpdatingValue):
        self._stop_flag = threading.Event()
        self._value = value
        name = "updater-for-" + repr(value)
        super().__init__(name=name, daemon=True)

    def run(self) -> None:
        while not self._stop_flag.is_set():
            self._value.update()
    
    def stop(self) -> None:
        self._stop_flag.set()
        self.join()


_T = TypeVar("_T", bound=pydantic.BaseModel)


@dataclasses.dataclass
class SelfUpdatingValue(Generic[_T]):
    _value: _T
    _fetch_new_value: Callable[[], _T]
    _lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self._update_thread = _UpdateThread(self)

    def update(self) -> None:
        new_value = self._fetch_new_value()
        with self._lock:
            self._value = new_value

    def value(self) -> _T:
        with self._lock:
            return self._value.copy(deep=True)

    @contextmanager
    def enabled(self) -> Iterator[None]:
        self._update_thread.start()
        try:
            yield
        finally:
            self._update_thread.stop()


@dataclasses.dataclass
class UGSClient:
    ip_address: str
    has_connection: bool = False

    def _send_request(self, request: requests.Request) -> requests.Response:
        with requests.Session() as session:
            try:
                response = session.send(request.prepare(), timeout=(1, 1))
            except requests.ConnectionError as e:
                self.has_connection = False
                raise ConnectionError() from e
        if response.status_code >= 400:
            self.has_connection = False
            raise ConnectionError()
        return response

    def get_machine_status(self) -> MachineStatus:
        try:
            response = self._send_request(
                requests.Request("GET", f"http://{self.ip_address}:8080/api/v1/status/getStatus")
            )
        except ConnectionError:
            return MachineStatus()
        return MachineStatus(**response.json())
    
    def get_machine_settings(self) -> MachineSettings:
        try:
            response = self._send_request(
                requests.Request("GET", f"http://{self.ip_address}:8080/api/v1/settings/getSettings")
            )
        except ConnectionError:
            return MachineSettings()
        return MachineSettings(**response.json())
    
    def post_machine_settings(self, machine_settings: MachineSettings) -> None:
        try:
            self._send_request(
                requests.Request(
                    "POST", 
                    f"http://{self.ip_address}:8080/api/v1/settings/setSettings",
                    json=machine_settings.dict(by_alias=True)
                )
            )
        except ConnectionError:
            return
    
    def post_spindle_settings(self, spindle_settings: SpindleSettings) -> None:
        json = {
            "commands": f"S{spindle_settings.speed} {'M03' if spindle_settings.is_on else 'M05'}"
        }
        try:
            self._send_request(
                requests.Request(
                    "POST", 
                    f"http://{self.ip_address}:8080/api/v1/machine/sendGcode",
                    json=json
                )
            )
        except ConnectionError:
            return
    
    def jog(self, x: int, y: int, z: int) -> None:
        try:
            self._send_request(
                requests.Request(
                    "GET", 
                    f"http://{self.ip_address}:8080/api/v1/machine/jog", 
                    params={
                        "x": x,
                        "y": y,
                        "z": z,
                    })
            )
        except ConnectionError:
            return
        


@dataclasses.dataclass
class DigitalReadout:
    ugs_client: UGSClient
    controls: Controls
    has_connection: bool = False

    def __post_init__(self) -> None:
        self.machine = SelfUpdatingValue(Machine(), self._fetch_machine)

    def _fetch_machine(self) -> Machine:
        machine_status = self.ugs_client.get_machine_status()
        machine_settings = self.ugs_client.get_machine_settings()

        return Machine(
            is_connected=self.ugs_client.has_connection,
            machine_status=machine_status,
            machine_settings=machine_settings,
            spindle_settings=self.controls.get_spindle_settings(),
        )

    @contextmanager
    def syncing(self) -> Iterator[None]:
        with self.machine.enabled():
            yield


@dataclasses.dataclass(frozen=True)
class Dial:
    clk_pin: int
    dt_pin: int
    sw_pin: int


def increase(number: float, min_value: float, max_value: float, factor: float = 1.05) -> float:
    number = max(min(number, max_value), min_value)
    number = (number - min_value) * factor + min_value
    return max(min(number, max_value), min_value)


def decrease(number: float, min_value: float, max_value: float, factor: float = 1.05) -> float:
    number = max(min(number, max_value), min_value)
    number = (number - min_value) / factor + min_value
    return max(min(number, max_value), min_value)


SHORT_PRESS_SECONDS = 0.5

@dataclasses.dataclass
class Controls:
    ugs_client: UGSClient

    x_dial: Dial
    y_dial: Dial
    z_dial: Dial

    max_feedrate: float = 1000
    fine_feedrate: float = 50
    step_size_multiplier: float = 1 / 1000

    max_spindle_speed: float = 10_000
    min_spindle_speed: float = 100
    
    _spindle_settings: SpindleSettings = dataclasses.field(default_factory=SpindleSettings)

    _is_x_pressed: bool = False
    _is_y_pressed: bool = False
    _is_z_pressed: bool = False

    _when_x_down: float = 0
    _when_y_down: float = 0
    _when_z_down: float = 0

    def __post_init__(self) -> None:
        self._feedrate = self.max_feedrate
        self._spindle_settings.speed = self.max_spindle_speed
        self._post_settings()
        self._post_spindle()

    def get_spindle_settings(self) -> SpindleSettings:
        return self._spindle_settings.copy(deep=True)

    def do_nothing(self) -> None:
        pass

    def step_size(self) -> float:
        return self.step_size_multiplier * self._feedrate
    
    def toggle_feedrate(self) -> None:
        if self._feedrate == self.fine_feedrate:
            self._feedrate = self.max_feedrate
        else:
            self._feedrate = self.fine_feedrate
        self._post_settings()

    def _post_settings(self) -> None:
        self.ugs_client.post_machine_settings(
            MachineSettings(
                jogFeedRate=self._feedrate,
                jogStepSizeXY=self.step_size(),
                jogStepSizeZ=self.step_size(),
            )
        )
    
    def _post_spindle(self) -> None:
        self.ugs_client.post_spindle_settings(self.get_spindle_settings())

    def on_x_cw(self) -> None:
        if self._is_x_pressed:
            pass
        else:
            self._when_x_down = 0
            self.ugs_client.jog(1, 0, 0)
 
    def on_y_cw(self) -> None:
        if self._is_y_pressed:
            pass
        else:
            self._when_y_down = 0
            self.ugs_client.jog(0, 1, 0)

    def on_z_cw(self) -> None:
        if self._is_z_pressed:
            self._spindle_settings.speed = increase(
                self._spindle_settings.speed,
                self.min_spindle_speed,
                self.max_spindle_speed,
            )
            self._post_spindle()
        else:
            self._when_y_down = 0
            self.ugs_client.jog(0, 0, 1)

    def on_x_ccw(self) -> None:
        if self._is_x_pressed:
            pass
        else:
            self._when_x_down = 0
            self.ugs_client.jog(-1, 0, 0)
 
    def on_y_ccw(self) -> None:
        if self._is_y_pressed:
            pass
        else:
            self._when_y_down = 0
            self.ugs_client.jog(0, -1, 0)

    def on_z_ccw(self) -> None:
        if self._is_z_pressed:
            self._spindle_settings.speed = decrease(
                self._spindle_settings.speed,
                self.min_spindle_speed,
                self.max_spindle_speed,
            )
            self._post_spindle()
        else:
            self._when_z_down = 0
            self.ugs_client.jog(0, 0, -1)

    def on_x_down(self) -> None:
        self._is_x_pressed = True
        self._when_x_down = time.time()

    def on_y_down(self) -> None:
        self._is_y_pressed = True
        self._when_y_down = time.time()
    
    def on_z_down(self) -> None:
        self._is_z_pressed = True
        self._when_z_down = time.time()

    def on_x_up(self) -> None:
        self._is_x_pressed = False
        if time.time() - self._when_x_down > SHORT_PRESS_SECONDS:
            return
        self.toggle_feedrate()

    def on_y_up(self) -> None:
        self._is_y_pressed = False
        if time.time() - self._when_y_down > SHORT_PRESS_SECONDS:
            return
    
    def on_z_up(self) -> None:
        self._is_z_pressed = False
        if time.time() - self._when_z_down > SHORT_PRESS_SECONDS:
            return
        self._spindle_settings.is_on = not self._spindle_settings.is_on
        self._post_spindle()

    @contextmanager
    def connected(self) -> Iterator[None]:
        with rotary_encoder.connect(
            clk_pin=self.x_dial.clk_pin,
            dt_pin=self.x_dial.dt_pin,
            sw_pin=self.x_dial.sw_pin,
            on_clockwise_turn=self.on_x_cw,
            on_counter_clockwise_turn=self.on_x_ccw,
            on_button_down=self.on_x_down,
            on_button_up=self.on_x_up,
        ), rotary_encoder.connect(
            clk_pin=self.y_dial.clk_pin,
            dt_pin=self.y_dial.dt_pin,
            sw_pin=self.y_dial.sw_pin,
            on_clockwise_turn=self.on_y_cw,
            on_counter_clockwise_turn=self.on_y_ccw,
            on_button_down=self.on_y_down,
            on_button_up=self.on_y_up,
        ), rotary_encoder.connect(
            clk_pin=self.z_dial.clk_pin,
            dt_pin=self.z_dial.dt_pin,
            sw_pin=self.z_dial.sw_pin,
            on_clockwise_turn=self.on_z_cw,
            on_counter_clockwise_turn=self.on_z_ccw,
            on_button_down=self.on_z_down,
            on_button_up=self.on_z_up,
        ):
            yield
