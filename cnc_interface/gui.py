import tkinter
from cnc_interface import machine


UPDATE_DELAY = 100


def launch_window(cnc: machine.DigitalReadout) -> None:
    mono_font = ("Courier", 17)

    root = tkinter.Tk()

    root.attributes("-fullscreen", True)

    status_bar_frame = tkinter.Frame(root)

    label_connection = tkinter.Label(status_bar_frame, font=mono_font)
    label_connection.grid(row=0, column=0)

    status_bar_frame.pack()

    second_row_frame = tkinter.Frame(root)

    settings_frame = tkinter.Frame(second_row_frame)

    coords_frame = tkinter.Frame(settings_frame)

    tkinter.Label(coords_frame, text="X:", font=mono_font).grid(sticky="E", row=1, column=0)
    tkinter.Label(coords_frame, text="Y:", font=mono_font).grid(sticky="E", row=2, column=0)
    tkinter.Label(coords_frame, text="Z:", font=mono_font).grid(sticky="E", row=3, column=0)

    tkinter.Label(coords_frame, text="Machine", font=mono_font).grid(sticky="E", row=0, column=1)
    label_machine_x = tkinter.Label(coords_frame, font=mono_font)
    label_machine_y = tkinter.Label(coords_frame, font=mono_font)
    label_machine_z = tkinter.Label(coords_frame, font=mono_font)
    label_machine_x.grid(sticky="E", row=1, column=1)
    label_machine_y.grid(sticky="E", row=2, column=1)
    label_machine_z.grid(sticky="E", row=3, column=1)

    tkinter.Label(coords_frame, text="Work", font=mono_font).grid(sticky="E", row=0, column=2)
    label_work_x = tkinter.Label(coords_frame, font=mono_font)
    label_work_y = tkinter.Label(coords_frame, font=mono_font)
    label_work_z = tkinter.Label(coords_frame, font=mono_font)
    label_work_x.grid(sticky="E", row=1, column=2)
    label_work_y.grid(sticky="E", row=2, column=2)
    label_work_z.grid(sticky="E", row=3, column=2)

    coords_frame.grid(row=0, column=0)

    spindle_frame = tkinter.Frame(settings_frame)

    tkinter.Label(spindle_frame, text="Spindle:", font=mono_font).grid(sticky="E", row=1, column=0)
    label_spindle_status = tkinter.Label(spindle_frame, font=mono_font)
    label_spindle_status.grid(row=1, column=1)

    tkinter.Label(spindle_frame, text="Speed:", font=mono_font).grid(sticky="E", row=2, column=0)
    label_spindle_speed = tkinter.Label(spindle_frame, font=mono_font)
    label_spindle_speed.grid(sticky="E", row=2, column=1)

    tkinter.Label(spindle_frame, text="Feed Rate:", font=mono_font).grid(sticky="E", row=3, column=0)
    label_feed_rate = tkinter.Label(spindle_frame, font=mono_font)
    label_feed_rate.grid(sticky="E", row=3, column=1)

    tkinter.Label(spindle_frame, text="Step:", font=mono_font).grid(sticky="E", row=4, column=0)
    label_step_size = tkinter.Label(spindle_frame, font=mono_font)
    label_step_size.grid(sticky="E", row=4, column=1)

    spindle_frame.grid(row=1, column=0)

    settings_frame.grid(row=0, column=0)

    buttons_frame = tkinter.Frame(second_row_frame)

    button_reset_zero = tkinter.Button(buttons_frame, text="RESET\nZERO", font=mono_font, width=7, height=4)
    button_reset_zero.pack()

    button_goto_zero = tkinter.Button(buttons_frame, text="GO TO\nZERO", font=mono_font, width=7, height=4)
    button_goto_zero.pack()

    buttons_frame.grid(row=0, column=1)


    second_row_frame.pack()




    def sync_model():
        machine = cnc.machine.value()

        label_connection.config(text="CONNECTED" if machine.is_connected else "DISCONNECTED")

        machine_status = machine.machine_status
        label_machine_x.config(text=f"{machine_status.machine_coord.x: > 9.3f}")
        label_machine_y.config(text=f"{machine_status.machine_coord.y: > 9.3f}")
        label_machine_z.config(text=f"{machine_status.machine_coord.z: > 9.3f}")

        label_work_x.config(text=f"{machine_status.work_coord.x: > 9.3f}")
        label_work_y.config(text=f"{machine_status.work_coord.y: > 9.3f}")
        label_work_z.config(text=f"{machine_status.work_coord.z: > 9.3f}")

        spindle_settings = machine.spindle_settings
        label_spindle_status.config(text="ON" if spindle_settings.is_on else "OFF")
        label_spindle_speed.config(text=f"{spindle_settings.speed: >7,.0f}  RPM")

        machine_settings = machine.machine_settings
        label_feed_rate.config(text=f"{machine_settings.jog_feed_rate: >7.2f} mm/s")
        label_step_size.config(text=f"{machine_settings.jog_step_size_xy: >7.2f}   mm")

    while True:
        sync_model()
        root.update_idletasks()
        root.update()

