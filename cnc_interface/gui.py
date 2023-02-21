import tkinter


def create_window() -> tkinter.Tk:
    window = tkinter.Tk()
    window.attributes("-fullscreen", True)

    return window
