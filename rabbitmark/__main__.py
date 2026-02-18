"""
RabbitMark - main module
Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.

All rights reserved (temporary; if you read this and want such, contact me
for relicensing under some FOSS license).
"""

import sys

from rabbitmark import cli


def main():
    if len(sys.argv) > 1:
        result = cli.call()
        if result is not None:
            print(result)
    else:
        from rabbitmark.gui import main_window  # pylint: disable=import-outside-toplevel
        main_window.start()

main()
