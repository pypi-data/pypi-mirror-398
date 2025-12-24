#! /usr/bin/env python3

################################################################################
""" xchmod - Equivalent to chmod but only modifies files that do not
             have the correct permissions - chmod will just set all to the
             correct permissions regardless of current permissions and update
             the file last-changed date whether or not the file has changed.

    Initial version has MAJOR RESTRICTIONS: It only allows permissions
    of 'a+rw' and applies them to all files and directories in the specified
    path and must be run with -R/--recursive.

    TODO: [ ] Support all file modes as per chmod
    TODO: [ ] Support all command line options of chmod
    TODO: [ ] Implement non-recursive mode
    TODO: [ ] Options for files/directories only

    Copyright (C) 2017 John Skilleter

    Licence: GPL v3 or later
"""
################################################################################

import os
import sys
import stat
import argparse

################################################################################
# Constants

# Required mode for files

MODE_ALL_RW = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH

MODE_ALL_RW_DIR = MODE_ALL_RW | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

################################################################################

def set_mode(filepath, mode, debug, verbose):
    """ Given the name of a file, the required mode and verbose
        and debug flags, attempt to set the mode of the file if it does not
        already have the specified mode bits set (it currently only sets
        mode bits - it will not unset them)

        If verbose or debug are true then the operation is reported
        If debug is true the operation is not performed """

    # File mode (the bits that can be changed via chmod)

    filemode = stat.S_IMODE(os.stat(filepath).st_mode)

    # If the current mode doesn't have all the right bits set
    # then either report it or set them (leaving other bits unchanged)

    if (filemode & mode) != mode:

        newfilemode = filemode | mode

        if verbose or debug:
            print('%s (%03o -> %03o)' % (filepath, filemode, newfilemode))

        if not debug:
            os.chmod(filepath, newfilemode)

################################################################################

def make_public():
    """ Search and make public everything in the paths specified on the command
        line """

    parser = argparse.ArgumentParser(description='Locate files that are not publically writeable and make them so')

    parser.add_argument('--debug', action='store_true', help='Output the list of files (if any) that need to be made publically writeable')
    parser.add_argument('--verbose', action='store_true', help='List files as they are updated')
    parser.add_argument('--recursive', '-R', action='store_true', help='Operate recursively')
    parser.add_argument('mode', help='Mode to set')
    parser.add_argument('paths', nargs='+', help='List of directory paths to search')

    args = parser.parse_args()

    # We only support a+rw in the first version! Future versions will allow all mode types
    # and command line options supported by the chmod command.

    if args.mode != 'a+rw':
        sys.stderr.write('Invalid mode "%s" - currently ONLY a+rw is supported\n' % args.mode)
        sys.exit(1)

    if not args.recursive:
        sys.stderr.write('Invalid command line - recursive option currently MUST be specified\n')
        sys.exit(1)

    # Make sure that we aren't doing anything reckless

    for path in args.paths:
        if os.path.abspath(path) == '/':
            sys.stderr.write('You cannot recurse from the root directory\n')
            sys.exit(1)

    # Process each path and each directory and each file & directory in each directory

    for path in args.paths:
        for root, dirs, files in os.walk(path):
            for filename in files:
                set_mode(os.path.join(root, filename), MODE_ALL_RW, args.debug, args.verbose)

            for dirname in dirs:
                set_mode(os.path.join(root, dirname) + '/', MODE_ALL_RW_DIR, args.debug, args.verbose)

################################################################################

def xchmod():
    """Entry point"""
    try:
        make_public()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    xchmod()
