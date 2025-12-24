#! /usr/bin/env python3

################################################################################
""" Thingy addpath command

    Copyright (C) 2018 John Skilleter

    Update a $PATH-type variable by adding or removing entries.

    Intended to be used as in:

        export PATH=$(addpath $PATH --add /opt/bin)
"""
################################################################################

import sys
import os
import argparse

################################################################################

def pathmod(pathentries, separator, pathlist, prefix=False, suffix=False, delete=False, force=False):
    """ Modify a path.
    """

    # Only do something if the list of paths to add exists

    if pathlist:
        # Join the list path entries together then split them into individual entries
        # Allows for a list of entries in the form ['a:b:c', 'd', 'e']

        paths = separator.join(pathlist).split(separator)

        # Process each entry

        for entry in paths:
            # Do nothing (except delete) if the path does not exist and we aren't forcing

            if not entry or (not os.path.isdir(entry) and not (force or delete)):
                continue

            # If we are removing or adding/moving an entry remove any existing entry

            if (delete or prefix or suffix) and entry in pathentries:
                pathentries.remove(entry)

            # Prefix or suffix the entry

            if not delete and entry not in pathentries:
                if suffix:
                    pathentries.append(entry)
                else:
                    pathentries.insert(0, entry)

    return pathentries

################################################################################

def main():
    """ Main function - handles command line, outputs result to stdout """

    parser = argparse.ArgumentParser(description='Add or remove entries from a path list (e.g. as used by the PATH environment variable)')
    parser.add_argument('--add', action='append', help='Add an entry to the front of the path (do nothing if it is already present in the path)')
    parser.add_argument('--prefix', action='append', help='Add an entry to the front of the path (or move it there if it is already present)')
    parser.add_argument('--suffix', action='append', help='Add an entry to the end of the path (or move it there if it is already present)')
    parser.add_argument('--remove', action='append', help='Remove an entry from the path (do nothing if it is not present')
    parser.add_argument('--force', default=False, help='Add entries even if a corresponding directory does not exist')
    parser.add_argument('--separator', action='store', default=':', help='Override the default path separator')
    parser.add_argument('path', nargs=1, help='The path to modify')

    args = parser.parse_args()

    # Split the given path into component parts

    pathsplit = [pathentry for pathentry in args.path[0].split(args.separator) if pathentry]

    # Process the additions, suffixations, prefixanisms and deletes.

    pathmod(pathsplit, args.separator, args.add)
    pathmod(pathsplit, args.separator, args.prefix, prefix=True)
    pathmod(pathsplit, args.separator, args.suffix, suffix=True)
    pathmod(pathsplit, args.separator, args.remove, delete=True)

    # Glue the path back together

    pathjoin = args.separator.join(pathsplit)

    # Output the updated path to stdout

    print(pathjoin)

################################################################################

def addpath():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    addpath()
