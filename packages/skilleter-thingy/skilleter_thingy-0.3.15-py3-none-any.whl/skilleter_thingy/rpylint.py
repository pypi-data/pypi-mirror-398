#! /usr/bin/env python3

################################################################################
""" Run pylint on all the Python source files in the current tree

    Copyright (C) 2017-18 John Skilleter """
################################################################################

import os
import sys
import argparse
import glob
import subprocess

################################################################################

PYLINT = 'pylint'

################################################################################

def main():
    """ Main code. Exits directly on failure to locate source files, or returns
        the status code from Pylint otherwise. """

    # Parse the command line

    parser = argparse.ArgumentParser(description='Run pylint in the current (or specified) directory/ies')

    parser.add_argument('paths', nargs='*', help='List of files or paths to lint')

    args = parser.parse_args()

    if not args.paths:
        args.paths = ['.']

    sourcefiles = []

    # Use rgrep to find source files that have a Python 3 hashbang

    for entry in args.paths:
        if os.path.isdir(entry):
            result = subprocess.run(['rgrep', '-E', '--exclude-dir=.git', '-l', '#![[:space:]]*/usr/bin/(env[[:space:]])?python3'] + args.paths,
                                    capture_output=True, check=False, text=True)

            if result.returncode == 1:
                sys.stderr.write('No Python3 source files found\n')
                sys.exit(2)

            if result.returncode:
                sys.stderr.write(f'ERROR #{result.returncode}: {result.stderr}')
                sys.exit(1)

            sourcefiles += result.stdout.split('\n')

        elif os.path.isfile(entry):
            sourcefiles.append(entry)
        else:
            files = glob.glob(entry)

            if not files:
                sys.stderr.write(f'No files found matching "{entry}"')
                sys.exit(2)

            sourcefiles += files

    # Run pylint on all the files

    try:
        result = subprocess.run([PYLINT, '--output-format', 'parseable'] + sourcefiles, capture_output=False, check=False, text=True)

    except FileNotFoundError:
        sys.stderr.write(f'Unable to locate {PYLINT}\n')
        sys.exit(1)

    if result.returncode >= 64:
        sys.stderr.write(f'Unexpected error: {result.returncode}\n')
        sys.exit(3)

    # Function return code is the status return from pylint

    return result.returncode

################################################################################

def rpylint():
    """Entry point"""

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    rpylint()
