#! /usr/bin/env python3

################################################################################
""" Script invoked via the 'git cmp' alias, which sets GIT_EXTERNAL_DIFF so that
    this is called instead of using git diff.

    Copyright (C) 2017-18 John Skilleter

    Parameters passed by git are:

    For a normal diff between two versions of a file in Git:

    N    MEANING       EXAMPLE
    1    file path     tgy_git.py

    2    tmp old file  /tmp/OjfLZ8_tgy_git.py
    3    old SHA1      027422b8b6e945227b27abf4161ad38c5b6e9ff9
    4    old perm      100644

    5    tmp new file  tgy_git.py
    6    new SHA1      0000000000000000000000000000000000000000
    7    new perm      100644

    If the path is unmerged, only parameter #1 is passed

    Also sets:

    GIT_DIFF_PATH_COUNTER - incremented for each file compared
    GIT_DIFF_PATH_TOTAL   - total number of paths to be compared

    If GIT_SUBDIR is set in the environment it indicates the relative
    path of the current directory from the top-level directory of the
    working tree.
"""
################################################################################

################################################################################
# Imports

import sys
import os
import argparse
import filecmp
import re
import logging
import subprocess

from skilleter_modules import colour
from skilleter_modules import files
from skilleter_modules import git
from skilleter_modules import dircolors

################################################################################
# Constants

# A file must be at least this size to be considered binary - if it is smaller
# we give it the benefit of the doubt.

MIN_BINARY_SIZE = 8

################################################################################

def report_permissions(perm):
    """ Convert an octal value in a string to a description of file permissions
        e.g. given '644' it will return 'rw-r--r--' """

    mask_chars = ('r', 'w', 'x', 'r', 'w', 'x', 'r', 'w', 'x')

    # Convert the permissions from an octal string to an integer

    permissions = int(perm, 8)

    # Start at the topmost bit and work downwards adding the mask character
    # for bits that are set and '-' for ones that aren't.

    mask = 1 << (len(mask_chars) - 1)

    permtext = []

    for mask_char in mask_chars:
        permtext.append(mask_char if permissions & mask else '-')
        mask >>= 1

    return ''.join(permtext)

################################################################################

def main():
    """ Main function - does everything """

    # Allow the log level to be configured in git config, as well as via the
    # GITCMP_DEBUG

    txt_debug = git.config_get('cmp', 'debug')
    env_debug = os.getenv('GITCMP_DEBUG', '0')

    if txt_debug.lower() in ('true', '1') or env_debug.lower() in ('true', '1'):
        logging.basicConfig(level=logging.INFO)

    # Parse the command line

    parser = argparse.ArgumentParser(description='Invoked via the "git cmp" alias. Works as an enhanced version of "git difftool"')

    parser.add_argument('file_path', nargs='?', help='File name and path')

    parser.add_argument('old_file', nargs='?', help='Name of temporary copy of old version')
    parser.add_argument('old_sha1', nargs='?', help='SHA1 of the old version')
    parser.add_argument('old_perm', nargs='?', help='Permissions for the old version')

    parser.add_argument('new_file', nargs='?', help='Name of temporary copy of the new version')
    parser.add_argument('new_sha1', nargs='?', help='SHA1 of the new version')
    parser.add_argument('new_perm', nargs='?', help='Permissions for the new version')

    parser.add_argument('new_name', nargs='?', help='New name (if file has been renamed)')
    parser.add_argument('rename', nargs='?', help='Description of rename')

    args = parser.parse_args()

    # Get configuration from the environment

    path_count = int(os.getenv('GIT_DIFF_PATH_COUNTER', '0'))
    path_total = int(os.getenv('GIT_DIFF_PATH_TOTAL', '0'))
    diff_binaries = int(os.getenv('GIT_DIFF_BINARIES', '0'))
    skip_deleted = int(os.getenv('GIT_IGNORE_DELETED', '0'))

    # Debug output

    logging.info('Parameters to gitcmp-helper:')
    logging.info('1: path:     %s', args.file_path)
    logging.info('2: old file: %s', args.old_file)
    logging.info('3: old sha1: %s', args.old_sha1)
    logging.info('4: old perm: %s', args.old_perm)
    logging.info('5: new file: %s', args.new_file)
    logging.info('6: new sha1: %s', args.new_sha1)
    logging.info('7: new perm: %s', args.new_perm)
    logging.info('8: new name: %s', args.new_name)
    logging.info('9: rename  : %s', args.rename)
    logging.info('path count:  %d/%d', path_count, path_total)

    # Sanity checks

    if args.file_path is None:
        sys.stderr.write('At least one parameter must be specified\n')
        sys.exit(1)

    # Check and handle for the simple case of an unmerged file

    if args.old_file is None:
        colour.write(f'[CYAN:{args.file_path}] is not merged')
        sys.exit(0)

    # Make sure that we have all the expected parameters

    if args.new_perm is None:
        sys.stderr.write('Either 1 or 7 parameters must be specified\n')
        sys.exit(1)

    # Make sure we can access the temporary files supplied

    if not os.access(args.old_file, os.R_OK):
        sys.stderr.write(f'Unable to read temporary old file: {args.old_file}\n')
        sys.exit(2)

    if not os.access(args.new_file, os.R_OK):
        sys.stderr.write(f'Unable to read temporary new file: {args.new_file}\n')
        sys.exit(2)

    dc = dircolors.Dircolors()

    # Determine the best way of reporting the path to the file

    try:
        working_tree_path = os.getcwd()
    except FileNotFoundError:
        sys.stderr.write('Unable to get current working directory')
        sys.exit(2)

    current_path = os.path.join(working_tree_path, os.getenv('GIT_SUBDIR', ''))

    current_file_path = os.path.relpath(args.file_path if args.new_name is None else args.new_name, current_path)

    logging.info('file path:   %s', current_file_path)

    # Heading printed first

    heading = ['[BOLD]Changes in [NORMAL]%s' % dc.format(current_file_path)]

    # If file was renamed, append the old name and the degree of similarity

    if args.new_name:
        similarity = re.sub(r'(similarity index) (.*)', r'\1 [CYAN:\2]', args.rename.split('\n')[0])

        heading.append('(rename from %s with %s)' % (dc.format(os.path.relpath(args.file_path, current_path)), similarity))

    # If processing more than one file, append he index and total number of files

    if path_total > 0:
        heading.append(f'({path_count}/{path_total})')

    # Check for newly created/deleted files (other version will be '/dev/null')

    created_file = args.old_file == '/dev/null'
    deleted_file = args.new_file == '/dev/null'

    if created_file:
        heading.append('(new file)')

    if deleted_file:
        heading.append('(deleted file)')

    colour.write(' '.join(heading))

    # Report permission(s) / permissions changes

    permissions_changed = not (created_file or deleted_file) and args.old_perm != args.new_perm

    if deleted_file:
        colour.write('    Old permissions:      [CYAN:%s]' % report_permissions(args.old_perm))
    elif created_file:
        colour.write('    New permissions:      [CYAN:%s]' % report_permissions(args.new_perm))
    elif permissions_changed:
        colour.write('    Changed permissions:  [CYAN:%s] -> [CYAN:%s]' % (report_permissions(args.old_perm), report_permissions(args.new_perm)))
    else:
        colour.write('    Permissions:          [CYAN:%s]' % report_permissions(args.new_perm))

    # Report size changes

    old_size = os.stat(args.old_file).st_size
    new_size = os.stat(args.new_file).st_size

    formatted_old_size = files.format_size(old_size, always_suffix=True)
    formatted_new_size = files.format_size(new_size, always_suffix=True)

    if created_file:
        colour.write(f'    New size:             [CYAN:{formatted_new_size}]')
    elif deleted_file:
        colour.write(f'    Original size:        [CYAN:{formatted_old_size}]')
    elif new_size == old_size:
        colour.write(f'    Size:                 [CYAN]{formatted_new_size}[NORMAL] (no change)')
    else:
        formatted_delta_size = files.format_size(abs(new_size - old_size), always_suffix=True)

        delta = '%s %s' % (formatted_delta_size, 'larger' if new_size > old_size else 'smaller')

        if formatted_old_size == formatted_new_size:
            colour.write('    Size:                 [CYAN:%s] (%s)' % (formatted_new_size, delta))
        else:
            colour.write('    Size:                 [CYAN:%s] -> [CYAN:%s] (%s)' %
                         (formatted_old_size, formatted_new_size, delta))

    # Report file type

    if created_file:
        old_type = None
    else:
        old_type = files.file_type(args.old_file)

    if deleted_file:
        new_type = None
    else:
        new_type = files.file_type(args.new_file)

    if created_file:
        colour.write('    File type:            [CYAN:%s]' % new_type)
    elif deleted_file:
        colour.write('    Original file type:   [CYAN:%s]' % old_type)
    elif old_type != new_type:
        colour.write('    File type:            [CYAN:%s] (previously [CYAN:%s)]' % (new_type, old_type))
    else:
        colour.write('    File type:            [CYAN:%s]' % new_type)

    # Report permissions and type

    if filecmp.cmp(args.old_file, args.new_file, shallow=False):
        # If the file is unchanged, just report the permissions change (if any)

        if permissions_changed:
            colour.write('    Revisions are identical with changes to permissions')
        else:
            colour.write('    Revisions are identical')
    else:
        # Check if the file is/was a binary

        old_binary = not created_file and old_size > MIN_BINARY_SIZE and files.is_binary_file(args.old_file)
        new_binary = not deleted_file and new_size > MIN_BINARY_SIZE and files.is_binary_file(args.new_file)

        # If both versions are binary and we're not risking diffing binaries, report it
        # otherwise, issue a warning if one version is binary then do the diff

        if (old_binary or new_binary) and not diff_binaries:
            colour.write('    Cannot diff binary files')
        else:
            difftool = git.config_get('cmp', 'difftool', defaultvalue='diffuse')

            if old_binary or new_binary:
                colour.write('    [BOLD:WARNING]: One or both files may be binaries')

            if not deleted_file or not skip_deleted:
                try:
                    subprocess.run([difftool, args.old_file, args.new_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                except subprocess.CalledProcessError as exc:
                    print(f'WARNING: Diff failed - status = {exc.returncode}')

                except FileNotFoundError:
                    print(f'ERROR: Unable to locate diff tool {difftool}')
                    sys.exit(1)

    # Separate reports with a blank line

    print('')

################################################################################

def gitcmp_helper():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    gitcmp_helper()
