import tkinter
from cnc_interface import machine





def create_window() -> tkinter.Tk:
    window = tkinter.Tk()

    cnc = machine.Machine()
    window.attributes("-fullscreen", True)

    status_label = tkinter.Label(textvariable=cnc.status_error)
    status_label.pack()

    label_machine_x = tkinter.Label(textvariable=cnc.machine_x)
    label_machine_y = tkinter.Label(textvariable=cnc.machine_y)
    label_machine_z = tkinter.Label(textvariable=cnc.machine_z)
    label_machine_x.pack()
    label_machine_y.pack()
    label_machine_z.pack()

    return window, cnc
