#!/bin/bash

# add the following to /etc/xdg/lxsession/LXDE-pi/autostart
# @lxterminal -e "/home/momo/cnc_interface/run.sh"


cd "$(dirname "$0")"
poetry run python -m cnc_interface

