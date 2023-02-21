from __future__ import annotations

import dataclasses
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
    jog_feed_rate: float = pydantic.Field(alias="jogFeedRate")
    jog_step_size_xy: float = pydantic.Field(alias="jogStepSizeXy")
    jog_step_size_y: float = pydantic.Field(alias="jogStepSizeY")
    preferred_units: str = pydantic.Field(alias="preferredUnits")


class MachineCoords(pydantic.BaseModel):
    units: str
    x: float
    y: float
    z: float


class MachineStatus(pydantic.BaseModel):
    state: str
    machine_coord: MachineCoords = pydantic.Field(alias="machineCoord")
    work_coord: MachineCoords = pydantic.Field(alias="workCoord")
    spindle_speed: float = pydantic.Field(alias="spindleSpeed")


def send_request(request: requests.Request) -> requests.Response:
    with requests.Session() as session:
        try:
            print("send1")
            response = session.send(request.prepare(), timeout=(3.05, 1))
            print("send2")
        except requests.ConnectionError as e:
            raise ConnectionError() from e
    if response.status_code >= 400:
        raise ConnectionError()
    return response



class LoopingThread(threading.Thread):
    def __init__(self, name: str) -> None:
        self.stop_flag = threading.Event()
        super().__init__(name=name, daemon=True)
    
    def loop(self) -> None:
        return NotImplemented

    def run(self) -> None:
        print(self.getName())
        while not self.stop_flag.is_set():
            self.loop()
    
    def stop(self) -> None:
        self.stop_flag.set()


class UGSClient(LoopingThread):
    def __init__(self) -> None:
        self._queue = collections.deque()
        super().__init__("ugs-client")

    def loop():
        pass


class StatusThread(LoopingThread):
    def __init__(self, machine: Machine) -> None:
        self.machine = machine
        super().__init__("machine-status-thread")
    
    def loop(self) -> None:
        self.machine.update_status()
        time.sleep(0.2)


@dataclasses.dataclass
class Machine:
    def __init__(self, url: str = "http://192.167.2.223:8080/"):
        self.url = url
        self.status_error = tkinter.BooleanVar()

        self.machine_x = tkinter.DoubleVar()
        self.machine_y = tkinter.DoubleVar()
        self.machine_z = tkinter.DoubleVar()

        self.work_x = tkinter.DoubleVar()
        self.work_y = tkinter.DoubleVar()
        self.work_z = tkinter.DoubleVar()

        self.status_tread = StatusThread(self)
        self.status_tread.start()

    def update_status(self):
        print("foo")
        try:
            print("bar")
            response = send_request(
                requests.Request("GET", self.url + "api/v1/status/getStatus")
            )
        except ConnectionError:
            print("buzz")
            self.status_error.set(True)
            return
        print("machine_status")
        self.status_error.set(False)
        machine_status = MachineStatus(**response.json())

        self.machine_x.set(machine_status.machine_coord.x)
        self.machine_y.set(machine_status.machine_coord.y)
        self.machine_z.set(machine_status.machine_coord.z)

        self.work_x.set(machine_status.work_coord.x)
        self.work_y.set(machine_status.work_coord.y)
        self.work_z.set(machine_status.work_coord.z)

