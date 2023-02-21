import dataclasses
import pydantic
import requests
import tkinter


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
            response = session.send(request, timeout=1)
        except requests.ConnectionError as e:
            raise ConnectionError() from e
    if response.status_code >= 400:
        raise ConnectionError()
    return response


@dataclasses.dataclass
class Machine:
    def __init__(self, url: str = "192.167.2.223:8080"):
        self.x = tkinter.DoubleVar()
        self.y = tkinter.DoubleVar()
        self.z = tkinter.DoubleVar()

    def update_status():
        try:

