#!/usr/bin/env python3

import sys
import os
import stat
import argparse

from skilleter_modules import venv_template

################################################################################

def main():
    """Create the venv script and make it executable"""

    parser = argparse.ArgumentParser(description='Create a script to run Python code in a virtual environment')
    parser.add_argument('name', nargs=1, help='Name of the script to create')

    args = parser.parse_args()

    script = args.name[0]

    with open(script, 'wt') as scriptfile:
        scriptfile.write(venv_template.TEMPLATE)

    statinfo = os.stat(script)

    os.chmod(script, statinfo.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f'Created virtual environment: {script}')

################################################################################

def venv_create():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    venv_create()
