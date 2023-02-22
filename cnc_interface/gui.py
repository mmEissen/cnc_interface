import tkinter
from cnc_interface import machine


UPDATE_DELAY = 100


def launch_window(cnc: machine.Machine) -> None:
    root = tkinter.Tk()

    root.attributes("-fullscreen", True)

    status_label = tkinter.Label()
    status_label.pack()

    coords_frame = tkinter.Frame(root)
    coords_font = ("Courier", 17)

    tkinter.Label(coords_frame, text="X", font=coords_font).grid(sticky="E", row=1, column=0)
    tkinter.Label(coords_frame, text="Y", font=coords_font).grid(sticky="E", row=2, column=0)
    tkinter.Label(coords_frame, text="Z", font=coords_font).grid(sticky="E", row=3, column=0)

    tkinter.Label(coords_frame, text="Machine", font=coords_font).grid(sticky="E", row=0, column=1)
    label_machine_x = tkinter.Label(coords_frame, font=coords_font)
    label_machine_y = tkinter.Label(coords_frame, font=coords_font)
    label_machine_z = tkinter.Label(coords_frame, font=coords_font)
    label_machine_x.grid(sticky="E", row=1, column=1)
    label_machine_y.grid(sticky="E", row=2, column=1)
    label_machine_z.grid(sticky="E", row=3, column=1)

    tkinter.Label(coords_frame, text="Work", font=coords_font).grid(sticky="E", row=0, column=2)
    label_work_x = tkinter.Label(coords_frame, font=coords_font)
    label_work_y = tkinter.Label(coords_frame, font=coords_font)
    label_work_z = tkinter.Label(coords_frame, font=coords_font)
    label_work_x.grid(sticky="E", row=1, column=2)
    label_work_y.grid(sticky="E", row=2, column=2)
    label_work_z.grid(sticky="E", row=3, column=2)

    coords_frame.pack()

    def sync_model():
        machine_status = cnc.machine_status.value()
        label_machine_x.config(text=f"{machine_status.machine_coord.x: > 9.3f}")
        label_machine_y.config(text=f"{machine_status.machine_coord.y: > 9.3f}")
        label_machine_z.config(text=f"{machine_status.machine_coord.z: > 9.3f}")

        label_work_x.config(text=f"{machine_status.work_coord.x: > 9.3f}")
        label_work_y.config(text=f"{machine_status.work_coord.y: > 9.3f}")
        label_work_z.config(text=f"{machine_status.work_coord.z: > 9.3f}")

    while True:
        sync_model()
        root.update_idletasks()
        root.update()

