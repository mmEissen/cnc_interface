import socket

from cnc_interface import gui, machine


def main():
    socket.setdefaulttimeout(1)

    ugs_client = machine.UGSClient("192.168.2.223")
    controls = machine.Controls(
        ugs_client,
        x_dial=machine.Dial(0, 5, 6),
        y_dial=machine.Dial(13, 19, 26),
        z_dial=machine.Dial(21, 20, 16),
    )
    cnc = machine.DigitalReadout(ugs_client, controls)

    with controls.connected(), cnc.syncing():
        gui.launch_window(cnc)


if __name__ == "__main__":
    main()
    pass
