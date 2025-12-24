#! /usr/bin/env python3

################################################################################
""" Thingy trimpath command

    Copyright (C) 2017 John Skilleter

    Given a path, truncate it to less than 25% of the width of the console by
    replacing intermediate directories with '...' """
################################################################################

import sys
import os
import argparse
import shutil
import logging

from skilleter_modules import path

################################################################################

def main():
    """ Trim a path to a specified width """

    # Set up the command line parser

    parser = argparse.ArgumentParser(description='Trim a path for display to a specified with by replacing intermediate directory names with "..."')

    parser.add_argument('--width', '-w', default=None, help='Specify the width to trim to the path to. Default is 25%% of the current console width')
    parser.add_argument('path', nargs='?', default=None, help='The path to trim. Default is the current directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # Set the width, defaulting to 25% of the console width

    if args.width:
        try:
            trim_width = int(args.width)
        except ValueError:
            trim_width = -1

        if trim_width <= 0:
            logging.critical('Invalid width: "%s"', args.width)
            sys.exit(1)
    else:
        console = shutil.get_terminal_size()
        trim_width = console.columns // 4

    # Set the path, defaulting to the current directory

    try:
        full_path = args.path or os.getcwd()
    except FileNotFoundError:
        logging.critical('Unable to locate directory')
        sys.exit(1)

    trimmed = path.trimpath(full_path, trim_width)

    sys.stdout.write(trimmed)

################################################################################

def trimpath():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)
    except Exception:
        sys.exit(3)

################################################################################

if __name__ == '__main__':
    trimpath()
