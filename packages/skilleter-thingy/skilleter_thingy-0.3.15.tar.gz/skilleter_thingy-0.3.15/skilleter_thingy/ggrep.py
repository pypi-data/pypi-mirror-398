#! /usr/bin/env python3

""" Run 'git grep' in all Git working trees under the current directory or just
   in the current directory if the current director is in a working tree.

   Copyright (C) 2019-21 John Skilleter
"""

################################################################################

import os
import re
import sys
import argparse

from skilleter_modules import colour
from skilleter_modules import git

################################################################################

BINARY_RE = re.compile(r'(Binary file )(.*)( matches)')

################################################################################

def parse_command_line():
    """ Validate the command line, return the arguments """

    parser = argparse.ArgumentParser(
        description='Run a git grep in either the current working tree or all working git working trees under the current directory')

    parser.add_argument('--follow', '-f', action='store_true', help='Follow symlinks')
    parser.add_argument('--text', '-a', action='store_true', help='Process binary files as if they were text.')
    parser.add_argument('--ignore-case', '-i', action='store_true', help='Ignore case differences between the patterns and the files.')
    parser.add_argument('--word-regexp', '-w', action='store_true',
                        help='Match the pattern only at word boundary (either begin at the beginning of a line, or preceded by a non-word character; end at the end of a line or followed by a non-word character).')
    parser.add_argument('--invert-match', '-v', action='store_true', help='Select non-matching lines.')
    parser.add_argument('--fixed-strings', '-F', action='store_true', help='Use fixed strings for patterns (don’t interpret pattern as a regex).')
    parser.add_argument('--line-number', '-n', action='store_true', help='Prefix the line number to matching lines.')
    parser.add_argument('--files-with-matches', '-l', action='store_true', help='Show only the names of files that contain matches')
    parser.add_argument('--files-without-matches', '-L', action='store_true', help='Show only the names of files that do NOT contain matches')
    parser.add_argument('--wildcard', '-W', action='append', help='Only search files matching the wildcard(s)')
    parser.add_argument('--only-matching', '-o', action='store_true',
                        help='Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line.')
    parser.add_argument('--no-color', action='store_true', help='Turn off match highlighting')
    parser.add_argument('pattern', action='store', help='Regular expression to search for')
    parser.add_argument('paths', nargs='*', help='Optional list of one or more paths to search')

    return parser.parse_args()

################################################################################

def git_grep(args, path, pattern):
    """ Grep a git """

    if path == '.':
        path = ''
    elif path[0:2] == './':
        path = path[2:]

    grep_options = {'color': True, 'extended_regexp': True}

    if args.text:
        grep_options['text'] = True

    if args.ignore_case:
        grep_options['ignore_case'] = True

    if args.word_regexp:
        grep_options['word_regexp'] = True

    if args.invert_match:
        grep_options['invert_match'] = True

    if args.fixed_strings:
        grep_options['fixed_strings'] = True

    if args.line_number:
        grep_options['line_number'] = True

    if args.files_without_matches:
        grep_options['files_without_matches'] = True

    if args.files_with_matches:
        grep_options['files_with_matches'] = True

    if args.only_matching:
        grep_options['only_matching'] = True

    if path:
        output, status = git.grep(pattern, git_dir=os.path.join(path, '.git'), work_tree=path, options=grep_options, wildcards=args.wildcard)
    else:
        output, status = git.grep(pattern, options=grep_options, wildcards=args.wildcard)

    if status > 1:
        colour.error(output)
    elif status == 0:
        for out in output.split('\n'):
            if out:
                bin_match = BINARY_RE.match(out)
                if bin_match:
                    match_path = os.path.join(path, bin_match.group(2))
                    colour.write(f'[BOLD:{match_path}]: Binary file match')
                else:
                    subdir = os.path.join(path, out.split(':', 1)[0])
                    data = out.split(':', 1)[1]

                    colour.write(f'[BLUE:{subdir}]: {data.strip()}')

################################################################################

def git_grep_path(args, path):
    """ Look for git working trees under the specified path and grep them """

    for root, dirs, _ in os.walk(path, followlinks=args.follow):
        if '.git' in dirs:
            git_grep(args, root, args.pattern)

################################################################################

def main():
    """ If we are in a repo, just run git grep, otherwise, hunt for
        repos and git grep them. """

    args = parse_command_line()

    if not args.paths:
        # No paths specified so if the current directory is in a working tree
        # just run git grep, otherwise, look for working trees in subdirectories

        if git.working_tree():
            git_grep(args, '.', args.pattern)
        else:
            args.paths = ['.']

    if args.paths:
        for path in args.paths:
            git_grep_path(args, path)

################################################################################

def ggrep():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    ggrep()
