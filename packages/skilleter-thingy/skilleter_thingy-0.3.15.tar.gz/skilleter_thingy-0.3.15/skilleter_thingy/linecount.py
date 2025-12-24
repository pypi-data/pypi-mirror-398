#! /usr/bin/env python3

################################################################################
""" Count lines of code by filetype
"""
################################################################################

import os
import sys
import argparse

import filetype
from skilleter_modules import files

################################################################################

def guess_filetype(filepath):
    """ Guess the type of a file """

    binary = False

    # Check for the filetype (usually detects binary files)

    ftype = filetype.guess(filepath)

    # If we have a type, store the extension and, as it is binary
    # set the number of lines to 0
    # Otherwise, work out the filetype and count the lines

    if ftype:
        ext = ftype.extension
        binary = True
    else:
        filename = os.path.split(filepath)[1]

        if '.' in filename:
            ext = filename.split('.')[-1]
        else:
            if filename.startswith('Jenkins'):
                ext = 'Jenkins'
            elif filename.startswith('Docker'):
                ext = 'Docker'
            else:
                ext = filename

    return ext, binary

################################################################################

def determine_filetype(filepath):
    """ Determine the type of a file """

    file_type = files.file_type(filepath)

    if file_type.startswith('a /usr/bin/env '):
        file_type = file_type[len('a /usr/bin/env '):]
    elif file_type.startswith('symbolic link to '):
        file_type = 'Symbolic link'

    if file_type[0].islower():
        file_type = file_type.capitalize()

    ext = file_type.split(',')[0]
    binary = 'text' not in file_type

    if file_type.startswith('ASCII text'):
        return guess_filetype(filepath)

    return ext, binary

################################################################################

def main():
    """ Report Summary of files by name or extension """

    parser = argparse.ArgumentParser(description='Summarise number of files, lines of text and total size of files in a directory tree')
    parser.add_argument('--ext', '-e', action='store_true', help='Identify file type using the file extension (faster but less accurrate)')

    args = parser.parse_args()

    filetypes = {}

    # Wander down the tree

    for dirpath, dirnames, filenames in os.walk('.'):
        # Skip .git directories

        if '.git' in dirnames:
            dirnames.remove('.git')

        for filename in filenames:
            # Get the file path and size

            filepath = os.path.join(dirpath, filename)
            size = os.stat(filepath).st_size

            if args.ext:
                ext, binary = guess_filetype(filepath)
            else:
                ext, binary = determine_filetype(filepath)

            if binary:
                lines = 0
            else:
                with open(filepath, 'rb') as infile:
                    lines = len(infile.readlines())

            # Update the summary

            if ext in filetypes:
                filetypes[ext]['files'] += 1
                filetypes[ext]['size'] += size
                filetypes[ext]['lines'] += lines
            else:
                filetypes[ext] = {'files': 1, 'size': size, 'lines': lines}

    # Work out the maximum size of each field of data

    total_files = 0
    total_lines = 0
    total_size = 0

    for ext in sorted(filetypes.keys()):
        total_files += filetypes[ext]['files']
        total_lines += filetypes[ext]['lines']
        total_size += filetypes[ext]['size']

        size = files.format_size(filetypes[ext]['size'])
        print(f"{ext}: {filetypes[ext]['files']:,} files, {filetypes[ext]['lines']:,} lines, {size}")

    size = files.format_size(total_size)

    print()
    print(f'Total files: {total_files:,}')
    print(f'Total lines: {total_lines:,}')
    print(f'Total size:  {size}')

################################################################################

def linecount():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    linecount()
