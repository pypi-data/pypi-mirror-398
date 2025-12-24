#! /usr/bin/env python3

################################################################################
""" Textual search and replace

   For those occasions when you want to search and replace strings with
   regexppy characters that upset sed.

   Copyright (C) 2018 John Skilleter """
################################################################################

import os
import sys
import argparse
import tempfile

################################################################################

def main():
    """ Main function """

    parser = argparse.ArgumentParser(description='Textual search and replace')
    parser.add_argument('--inplace', '-i', action='store_true', help='Do an in-place search and replace on the input file')
    parser.add_argument('search', nargs=1, action='store', help='Search text')
    parser.add_argument('replace', nargs=1, action='store', help='Replacment text')
    parser.add_argument('infile', nargs='?', action='store', help='Input file')
    parser.add_argument('outfile', nargs='?', action='store', help='Output file')

    args = parser.parse_args()

    # Sanity check

    if args.inplace and not args.infile or args.outfile:
        print('For in-place operations you must specify and input file and no output file')

    # Open the input file

    if args.infile:
        infile = open(args.infile, 'r')
    else:
        infile = sys.stdin

    # Open the output file, using a temporary file in the same directory as the input file
    # if we are doing in-place operations

    if args.outfile:
        outfile = open(args.outfile, 'w')
    elif args.inplace:
        outfile = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(args.infile))
    else:
        outfile = sys.stdout

    # Perform the searchy-replacey-ness

    for data in infile:
        outfile.write(data.replace(args.search[0], args.replace[0]))

    # If we doing in-place then juggle the temporary and input files

    if args.inplace:
        mode = os.stat(args.infile).st_mode
        outfile.close()
        infile.close()
        os.rename(outfile.name, args.infile)
        os.chmod(args.infile, mode)

################################################################################

def strreplace():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    strreplace()
