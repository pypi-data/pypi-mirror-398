#! /usr/bin/env python3

################################################################################
""" Output all console colours

    Copyright (C) 2017-18 John Skilleter

    Licence: GPL v3 or later
"""
################################################################################

import sys

from skilleter_modules import colour

################################################################################

def main():
    """ Main function - draw the colour grid """

    # Extended ANSI colour are slightly weird.
    # Colours 0-15 are the standard basic colours
    # Colours 16-231 form a 6x6x6 colour cube
    # Colours 232-255 are greyscale range with colours 0 and 15 as black and white

    for code in range(0, 256):
        if code in (8, 16) or (code > 16 and (code - 16) % 6 == 0):
            colour.write('')

        if (code - 16) % 36 == 0:
            colour.write('')

        # Set the foreground code to be white for dark backgrounds

        foreground = 15 if code in (0, 1, 4, 5, 8, 12) \
            or (16 <= code <= 33) \
            or (52 <= code <= 69) \
            or (88 <= code <= 105) \
            or (124 <= code <= 135) \
            or (160 <= code <= 171) \
            or (196 <= code <= 201) \
            or (232 <= code <= 243) else 0

        colour.write('[B%d][%d] %3d [NORMAL] ' % (code, foreground, code), newline=False)

    print()

################################################################################

def console_colours():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    console_colours()
