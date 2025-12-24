#! /usr/bin/env python3

################################################################################
""" Output the top level directory of the git working tree or return
    an error if we are not in a git working tree.

    Copyright (C) 2017, 2018 John Skilleter

    Licence: GPL v3 or later
"""
################################################################################

import sys
import argparse
import os

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

def main():
    """ Main function """

    # Command line parameters

    parser = argparse.ArgumentParser(description='Report top-level directory of the current git working tree.')
    parser.add_argument('--parent', '-p', action='store_true',
                        help='If we are already at the top of the working tree, check if the parent directory is in a working tree and output the top-level directory of that tree.')
    parser.add_argument('--dir', '-d', action='store', default=None,
                        help='Find the location of the top-level directory in the working tree starting at the specified directory')

    args = parser.parse_args()

    try:
        start_dir = os.path.abspath(args.dir or os.getcwd())
    except FileNotFoundError:
        sys.stderr.write('Unable to determine initial directory\n')
        sys.exit(1)

    # Search for a .git directory in the current or parent directories

    working_tree = git.working_tree(start_dir)

    # If we are in a working tree and also looking for the parent working
    # tree, check if we are at the top of the current tree, and, if so,
    # hop up a level and try again.

    if args.parent and working_tree == start_dir:
        working_tree = git.working_tree(os.path.join(working_tree, os.pardir))

    if working_tree:
        print(working_tree)

################################################################################

def git_wt():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)
    except git.GitError as exc:
        colour.error(exc.msg, status=exc.status, prefix=True)

################################################################################

if __name__ == '__main__':
    git_wt()
