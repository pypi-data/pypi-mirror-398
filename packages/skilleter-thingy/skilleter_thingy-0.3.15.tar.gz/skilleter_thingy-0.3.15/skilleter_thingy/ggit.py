#!/usr/bin/env python3

""" Run a git command in all working trees in/under the specified subdirectory """

import sys
import os
import subprocess
import argparse

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

def run_git(args, directory, command):
    """ Run a git command in the specified directory """

    if not args.quiet:
        colour.write('\n[BOLD][GREEN:Running git %s in %s][NORMAL]\n' % (' '.join(command), directory))

    sys.stdout.flush()

    subprocess.run(['git', '-C', directory] + command)

################################################################################

def parse_command_line():
    """ Parse the command line options """

    try:
        argpos = sys.argv.index('--')

        cmd = sys.argv[argpos + 1:]
        sys.argv = sys.argv[:argpos]
    except ValueError:
        cmd = sys.argv[1:]
        sys.argv = sys.argv[:1]

    parser = argparse.ArgumentParser(description='Run a git command recursively in subdirectories')

    parser.add_argument('--quiet', '-q', action='store_true', help='Run quietly - only output errors or output from git')
    parser.add_argument('path', nargs='?', action='store', default='.', help='Specify the path to run in')

    args = parser.parse_args()

    return args, cmd

################################################################################

def main():
    """ Main function """

    args, cmdline = parse_command_line()

    try:
        os.chdir(args.path)
    except FileNotFoundError:
        colour.error(f'Invalid path [BLUE:{args.path}]', prefix=True)

    # If the current directory is in a working tree and below the top-level
    # directory then we run the git command here as well as in subdirectories
    # that are working trees.

    if git.working_tree() and not os.path.isdir('.git'):
        run_git(args, os.getcwd(), cmdline)

    # Find working trees and run the command in them

    for root, dirs, _ in os.walk(args.path):
        if '.git' in dirs:
            run_git(args, root, cmdline)

################################################################################

def ggit():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    ggit()
