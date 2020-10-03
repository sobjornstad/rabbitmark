"""
RabbitMark - main module
Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.

All rights reserved (temporary; if you read this and want such, contact me
for relicensing under some FOSS license).
"""

import sys

from . import cli
from . import gui


if len(sys.argv) > 1:
    print(cli.call())
else:
    gui.main_window.start()
