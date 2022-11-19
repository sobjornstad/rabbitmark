"""
RabbitMark - main module
Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.

All rights reserved (temporary; if you read this and want such, contact me
for relicensing under some FOSS license).
"""

import sys

import rabbitmark.cli
import rabbitmark.gui.main_window


def main():
    if len(sys.argv) > 1:
        print(rabbitmark.cli.call())
    else:
        rabbitmark.gui.main_window.start()

main()
