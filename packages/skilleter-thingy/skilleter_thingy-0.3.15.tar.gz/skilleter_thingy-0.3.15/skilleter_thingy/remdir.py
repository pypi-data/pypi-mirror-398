#! /usr/bin/env python3

################################################################################
""" remdir - remove empty directories

    Given the name of a directory tree and, optionally, a list of files to ignore,
    recursively deletes any directory in the tree that is either completely empty
    or contains nothing but files matching the list.

    For example:

        remdir /backup --ignore '*.bak' --keep .stfolder

    would remove any directory within the /backup tree that is empty
    or contains only files that match the '*.bak' wildcard so long as
    it isn't called '.stfolder'.

    TODO: Using os.walk() means that, if a directory is deleted, it still shows
          up in the list of directories in the parent directory (?)
"""
################################################################################

import sys
import os
import argparse
import fnmatch
import shutil
import logging

from skilleter_modules import colour

################################################################################

def main():
    """ Entry point """

    # Parse the command line

    parser = argparse.ArgumentParser(description='Remove empty directories')
    parser.add_argument('--dry-run', '-D', action='store_true', help='Dry-run - report what would be done without doing anything')
    parser.add_argument('--debug', action='store_true', help='Output debug information')
    parser.add_argument('--verbose', action='store_true', help='Output verbose information')
    parser.add_argument('--ignore', '-I', action='append', help='Files to ignore when considering whether a directory is empty')
    parser.add_argument('--keep', '-K', action='append', help='Directories that should be kept even if they are empty')
    parser.add_argument('dirs', nargs='+', help='Directories to prune')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not args.keep:
        args.keep = []

    # Go through each directory

    for directory in args.dirs:
        if not os.path.isdir(directory):
            colour.write(f'"{directory}" is not a directory')
            continue

        # Walk through the directory tree in bottom-up order

        for root, dirs, files in os.walk(directory, topdown=False):
            logging.debug('')
            logging.debug('Directory: %s', root)
            logging.debug('     Sub-directories : %s', dirs)
            logging.debug('     Files           : %s', files)

            # Only consider directories with no subdirectories

            if dirs:
                logging.debug('Ignoring directory "%s" as it has %d subdirectories', root, len(dirs))
            else:
                # Count of files (if any) to preserve in the directory

                filecount = len(files)

                # If any file matches an entry in the ignore list (if we have one) then decrement the file count

                if args.ignore:
                    for file in files:
                        for ignore in args.ignore:
                            if fnmatch.fnmatch(file, ignore):
                                filecount -= 1
                                break

                # If no non-matching files then delete the directory unless it is in the keep list

                if filecount == 0:
                    keep_dir = False
                    for keep in args.keep:
                        if fnmatch.fnmatch(os.path.basename(root), keep):
                            keep_dir = True
                            break

                    if keep_dir:
                        colour.write(f'Keeping empty directory [BLUE:{root}]')
                    else:
                        logging.debug('Deleting directory: %s', root)
                        colour.write(f'Deleting "[BLUE:{root}]"')

                        if not args.dry_run:
                            # Delete the directory and contents

                            try:
                                shutil.rmtree(root)
                            except OSError:
                                colour.error('Unable to delete "[BLUE:{root}]"')
                else:
                    logging.debug('Ignoring directory "%s" as it has %d non-ignorable files', root, filecount)

################################################################################

def remdir():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    remdir()
