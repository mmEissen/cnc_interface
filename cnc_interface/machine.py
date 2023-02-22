from __future__ import annotations
from contextlib import contextmanager

import dataclasses
from typing import Callable, Generic, Iterator, TypeVar
import pydantic
import requests
import tkinter
import threading
import collections
import time
import traceback


class ConnectionError(Exception):
    pass


class MachineSettings(pydantic.BaseModel):
    jog_feed_rate: float = pydantic.Field(alias="jogFeedRate", default=0)
    jog_step_size_xy: float = pydantic.Field(alias="jogStepSizeXy", default=0)
    jog_step_size_y: float = pydantic.Field(alias="jogStepSizeY", default=0)
    preferred_units: str = pydantic.Field(alias="preferredUnits", default=0)


class MachineCoords(pydantic.BaseModel):
    units: str = "MM"
    x: float = 0
    y: float = 0
    z: float = 0


class MachineStatus(pydantic.BaseModel):
    state: str = "UNKNOWN"
    machine_coord: MachineCoords = pydantic.Field(alias="machineCoord", default_factory=MachineCoords)
    work_coord: MachineCoords = pydantic.Field(alias="workCoord", default_factory=MachineCoords)
    spindle_speed: float = pydantic.Field(alias="spindleSpeed", default=0)


def send_request(request: requests.Request) -> requests.Response:
    with requests.Session() as session:
        try:
            response = session.send(request.prepare(), timeout=(1, 1))
        except requests.ConnectionError as e:
            raise ConnectionError() from e
    if response.status_code >= 400:
        raise ConnectionError()
    return response


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
class Machine:
    url: str = "http://192.168.2.223:8080/"
    has_connection: bool = False

    def __post_init__(self) -> None:
        self.machine_status = SelfUpdatingValue(MachineStatus(), self._fetch_machine_status)

    def _fetch_machine_status(self) -> MachineStatus:
        try:
            response = send_request(
                requests.Request("GET", self.url + "api/v1/status/getStatus")
            )
        except ConnectionError:
            self.has_connection = False
            return MachineStatus()
        
        self.has_connection = True
        return MachineStatus(**response.json())
    
    @contextmanager
    def syncing(self) -> Iterator[None]:
        with self.machine_status.enabled():
            yield
