import dataclasses
import tkinter
import rotary_encoder
import pydantic


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



def on_clockwise_turn(number: int):
    def _on_clockwise_turn():
        print(f"CW {number}")
    return _on_clockwise_turn


def on_counter_clockwise_turn(number: int):
    def _on_counter_clockwise_turn():
        print(f"CCW {number}")
    return _on_counter_clockwise_turn


def on_button_down(number: int):
    def _on_button_down():
        print(f"PRESS {number}")
    return _on_button_down


def on_button_up(number: int):
    def _on_button_up():
        print(f"RELEASE {number}")
    return _on_button_up


def main():
    window = tkinter.Tk()
    window.attributes("-fullscreen", True)


    with rotary_encoder.connect(
        clk_pin=0,
        dt_pin=5,
        sw_pin=6,
        on_clockwise_turn=on_clockwise_turn(0),
        on_counter_clockwise_turn=on_counter_clockwise_turn(0),
        on_button_down=on_button_down(0),
        on_button_up=on_button_up(0),
    ), rotary_encoder.connect(
        clk_pin=13,
        dt_pin=19,
        sw_pin=26,
        on_clockwise_turn=on_clockwise_turn(1),
        on_counter_clockwise_turn=on_counter_clockwise_turn(1),
        on_button_down=on_button_down(1),
        on_button_up=on_button_up(1),
    ), rotary_encoder.connect(
        clk_pin=21,
        dt_pin=20,
        sw_pin=16,
        on_clockwise_turn=on_clockwise_turn(2),
        on_counter_clockwise_turn=on_counter_clockwise_turn(2),
        on_button_down=on_button_down(2),
        on_button_up=on_button_up(2),
    ):
        window.mainloop()


if __name__ == "__main__":
    # main()
    pass
