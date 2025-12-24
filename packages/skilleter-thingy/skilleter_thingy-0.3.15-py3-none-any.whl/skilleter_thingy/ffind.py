#! /usr/bin/env python3

################################################################################
""" Really simple file find utility

    Implements the functionality of the find command that is regularly used
    in a simpler fashion and ignores all the options that nobody ever uses.

    Copyright (C) 2018 John Skilleter

    TODO: Option for Partial matching - x matches '*x*'
    TODO: Mixed case matching - lower case search matches case-independently - if search contains upper case then it is case-dependent
    TODO: Optional hidden hyphen/underscore detection - 'xyz' matches '_x-y_z-'
    TODO: Option to Use .gitignore
    TODO: More checks on --exec parameter - only one '^', check quoting.
"""
################################################################################

import sys
import argparse
import os
import fnmatch
import stat
import grp
import pwd
import datetime
import re
import shlex
import logging
import subprocess

from skilleter_modules import git
from skilleter_modules import dircolors
from skilleter_modules import colour

################################################################################

def error(msg, status=1):
    """ Report an error message and exit """

    sys.stderr.write(f'{msg}\n')
    sys.exit(status)

################################################################################

def report_exception(exc):
    """ Handle an exception triggered inside os.walk - currently just reports
        the exception - typically a permission error. """

    sys.stderr.write(f'{exc}\n')

################################################################################

def report_file(args, filepath, filestat, dircolour):
    """ Report details of a file or directory in the appropriate format """

    # If we are just counting files we don't report anything

    if args.count_only:
        return

    if args.abspath:
        filepath = os.path.abspath(filepath)

    # Either run the exec command on the file and/or report it

    if args.exec:
        # Copy the exec string and insert the file

        cmd = []
        for i in args.exec:
            cmd.append(i.replace('^', filepath))

        logging.debug('Running "%s"', ' '.join(cmd))

        # Attempt to run the command

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            error('%s failed with status=%d' % (' '.join(cmd), exc.returncode))
        except FileNotFoundError:
            error('File not found attempting to run "%s"' % ' '.join(cmd))
        except PermissionError:
            error('Permission error attempting to run "%s"' % ' '.join(cmd))

    if args.verbose or not args.exec:
        if args.zero:
            sys.stdout.write(f'{filepath}\0')
        else:
            # Colourise output if required

            if dircolour:
                filepath = dircolour.format(filepath)

            # Quote the file if necessary

            if not args.unquoted and ' ' in filepath:
                filepath = f'"{filepath}"'

            # Output full details or just the filename

            if args.long:
                filedate = datetime.datetime.fromtimestamp(filestat[stat.ST_MTIME])

                print('%s %-10s %-10s %8d %-10s %s' %
                      (stat.filemode(filestat.st_mode),
                       pwd.getpwuid(filestat[stat.ST_UID])[0],
                       grp.getgrgid(filestat[stat.ST_GID])[0],
                       filestat[stat.ST_SIZE],
                       filedate,
                       filepath))
            else:
                print(filepath)

################################################################################

def ismatch(args, root, file):
    """ Return True if pattern is a match for the current search parameters
        (based on name, not type) """

    file = os.path.join(root, file) if args.fullpath else file

    check_file = file.lower() if args.iname else file

    for pattern in args.patterns:
        if args.regex:
            if pattern.match(check_file):
                return True
        else:
            check_pattern = pattern.lower() if args.iname else pattern

            if fnmatch.fnmatch(check_file, check_pattern):
                return True

    return False

################################################################################

def istype(args, filestat):
    """ Return True if the stat data is for an entity we are interested in """

    return args.any or \
        (args.file and stat.S_ISREG(filestat.st_mode)) or \
        (args.block and stat.S_ISBLK(filestat.st_mode)) or \
        (args.char and stat.S_ISCHR(filestat.st_mode)) or \
        (args.pipe and stat.S_ISFIFO(filestat.st_mode)) or \
        (args.symlink and stat.S_ISLNK(filestat.st_mode)) or \
        (args.socket and stat.S_ISSOCK(filestat.st_mode))

################################################################################

def git_ffind(args, dircolour):
    """ Do the finding in the git working tree """

    try:
        files = git.files(dir=args.path)
    except git.GitError as exc:
        error(exc.msg, exc.status)

    files.sort()
    found = []

    if files:
        # We normally follow symlinks, unless we're searching for them

        follow = args.follow and not args.symlink

        for file in files:
            root, filename = os.path.split(file)

            if ismatch(args, root, filename):
                filestat = os.stat(file, follow_symlinks=follow)

                if istype(args, filestat):
                    report_file(args, file, filestat, dircolour)
                    found.append(file)

    return found

################################################################################

def grep_match(regex, filename):
    """ Return True if the specified file contains a match with the specified
        regular expression """

    recomp = re.compile(regex)

    with open(filename, 'r', errors='ignore', encoding='utf8') as infile:
        for text in infile:
            if recomp.search(text):
                break
        else:
            return False

    return True

################################################################################

def find_stuff(args, dircolour):
    """ Do the finding """

    found = []

    # Recurse through the tree

    for root, dirs, files in os.walk(args.path,
                                     onerror=None if args.quiet else report_exception,
                                     followlinks=args.follow):

        logging.debug('Root=%s', root)
        logging.debug('Dirs=%s', dirs)
        logging.debug('Files=%s', files)

        if root[0:2] == './':
            root = root[2:]
        elif root == '.':
            root = ''

        # We normally follow symlinks, unless we're searching for them

        follow = args.follow and not args.symlink

        # Sort the directories and files so that they are reported in order

        dirs.sort()
        files.sort()

        # If not just searching for directories, check for a match in the files

        if not args.dironly:
            # Iterate through the files and patterns, looking for a match

            for file in files:
                is_match = ismatch(args, root, file)
                if (args.invert and not is_match) or (not args.invert and is_match):
                    filepath = os.path.join(root, file)
                    filestat = os.stat(filepath, follow_symlinks=follow)

                    if istype(args, filestat):
                        # If the grep option is in use and this is a file and it doesn't contain a match
                        # just continue and don't report it.

                        if args.grep and (stat.S_ISREG(filestat.st_mode) or stat.S_ISLNK(filestat.st_mode)):
                            if not grep_match(args.grep, filepath):
                                continue

                        report_file(args, filepath, filestat, dircolour)

                        found.append(filepath)

        # If searching for directories, check for a match there

        if args.dir:
            # Iterate through the directories and patterns looking for a match

            for dirname in dirs:
                is_match = ismatch(args, root, dirname)
                if (args.invert and not is_match) or (not args.invert and is_match):
                    dirpath = os.path.join(root, dirname)
                    dirstat = os.stat(dirpath, follow_symlinks=follow)
                    report_file(args, dirpath, dirstat, dircolour)
                    found.append(dirpath)

        # Prune directories that we aren't interested in so that we don't recurse into them
        # but they can still be found themselves (so 'ffind -d .git' will find the .git directory
        # even though it doesn't enter it.

        if not args.all:
            if '.git' in dirs:
                dirs.remove('.git')

    return found

################################################################################

def validate_arguments(args):
    """ Validate and sanitise the command line arguments """

    # Enable logging

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Debug logging enabled')

    # Report conflicting options

    if args.zero and args.long:
        error('The zero and long options cannot be used together')

    if args.human_readable:
        error('Sorry - the -h/--human-readable option has not been implemented yet')

    if (args.exec and (args.diff or args.long or args.zero or args.colour)):
        error('The exec and formatting options cannot be used together')

    # If we have a --type option validate the types.

    if args.type:
        for t in args.type:
            if t not in ['b', 'c', 'd', 'p', 'f', 'l', 's']:
                error(f'Invalid type "{t}"')

    # Precompile regexes if using them

    if args.regex:
        regexes = []
        flags = re.IGNORECASE if args.iname else 0

        for pat in args.patterns:
            try:
                regexes.append(re.compile(pat, flags))
            except re.error as exc:
                error(f'Invalid regular expression "{pat}": {exc}')

        args.patterns = regexes

    # Convert the type entries (if any) into individual options (which are easier to check)

    if args.type:
        if 'b' in args.type:
            args.block = True

        if 'c' in args.type:
            args.char = True

        if 'd' in args.type:
            args.dir = True

        if 'p' in args.type:
            args.pipe = True

        if 'f' in args.type:
            args.file = True

        if 'l' in args.type:
            args.symlink = True

        if 's' in args.type:
            args.socket = True

    # Default to searching for filename matches

    if not (args.block or args.char or args.dir or args.pipe or args.file or args.symlink or args.socket):
        args.file = True

    if not args.file and args.diff:
        error('The "diff" option only works with files')

    # Set a flag to indicate that we are only searching for directories

    args.dironly = args.dir and not (args.any or args.block or args.char or args.pipe or args.file or args.symlink or args.socket)

    if args.verbose:
        if args.dironly:
            print('Searching for directories only')
        elif args.any:
            print('Searching for any match')
        else:
            print('Searching for:')

            print('    block devices    : %s' % ('y' if args.block else 'n'))
            print('    character devices: %s' % ('y' if args.char else 'n'))
            print('    directories      : %s' % ('y' if args.dir else 'n'))
            print('    pipes            : %s' % ('y' if args.pipe else 'n'))
            print('    regular files    : %s' % ('y' if args.file else 'n'))
            print('    symlinks         : %s' % ('y' if args.symlink else 'n'))
            print('    sockets          : %s' % ('y' if args.socket else 'n'))

    # If we have the iname option convert the patterns to lower case

    if args.iname and not args.regex:
        lc_patterns = []
        for pattern in args.patterns:
            lc_patterns.append(pattern.lower())

        args.patterns = lc_patterns

    # If the git option has been specified, check that we are in a git working tree

    if args.git:
        if git.working_tree() is None:
            colour.error('The current directory is not inside a git working tree', prefix=True)

        if args.dir:
            colour.error('Git does not track directories, so you cannot search for them in a git working tree', prefix=True)

    if args.verbose:
        print(f'Searching directory "{args.path}" for matches with "{args.patterns}"')

    # If the exec option is used, convert the exec string to an array and add the '^' parameter
    # marker if it isn't there.

    if args.exec:
        replacements = args.exec.count('^')

        if replacements > 1:
            error('Too many "^" characters in the exec string')
        elif not replacements:
            args.exec = f'{args.exec} ^'

        args.exec = shlex.split(args.exec)

    # If the path option has been used, try to switch to the specified directory

    if args.path:
        if not os.path.isdir(args.path):
            error(f'"{args.path}" is not a directory')

        os.chdir(args.path)

    # Default if no patterns specified

    if not args.patterns:
        args.patterns = ['*']

    return args

################################################################################

def parse_command_line():
    """ Command line arguments """

    parser = argparse.ArgumentParser(description='Find files, symlinks, directories, etc. according to criteria')

    # General options

    parser.add_argument('--path', '-p', action='store', default='.', help='Search the specified path, rather than the current directory')
    parser.add_argument('--long', '-l', action='store_true', help='Output details of any files that match (cannot be used with -0/--zero)')
    parser.add_argument('--colour', '-C', '--color', action='store_true', help='Colourise output even if not outputting to the terminal')
    parser.add_argument('--no-colour', '-N', '--no-color', action='store_true', help='Never colourise output')
    parser.add_argument('--all', action='store_true', help='Search all directories (do not skip .git, and similar control directories)')
    parser.add_argument('--zero', '-0', action='store_true', help='Output results separated by NUL characters')
    parser.add_argument('--iname', '-i', action='store_true', help='Perform case-independent search')
    parser.add_argument('--follow', '-F', action='store_true', help='Follow symlinks')
    parser.add_argument('--git', '-g', action='store_true', help='Only search for objects in the current git repository')
    parser.add_argument('--diff', '-D', '--diffuse', action='store_true', help='Run Diffuse to on all the found objects (files only)')
    parser.add_argument('--regex', '-R', action='store_true', help='Use regex matching rather than globbing')
    parser.add_argument('--fullpath', '-P', action='store_true', help='Match the entire path, rather than just the filename')
    parser.add_argument('--human-readable', '-H', action='store_true', help='When reporting results in long format, use human-readable sizes')
    parser.add_argument('--grep', '-G', action='store', help='Only report files that contain text that matches the specified regular expression')
    parser.add_argument('--abspath', '-A', action='store_true', help='Report the absolute path to matching entities, rather than the relative path')
    parser.add_argument('--unquoted', '-U', action='store_true', help='Do not use quotation marks around results containing spaces')
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not report permission errors that prevented a complete search')
    parser.add_argument('--invert', '-I', action='store_true', help='Invert the wildcard - list files that do not match')
    parser.add_argument('--exec', '-x', action='store', help='Execute the specified command on each match (optionally use ^ to mark the position of the filename)')
    parser.add_argument('--count', '-K', action='store_true', help='Report the number of objects found')
    parser.add_argument('--count-only', '-c', action='store_true', help='Just report the number of objects found')

    # Types of objects to include in the results

    parser.add_argument('--type', '-t', action='append',
                        help='Type of item(s) to include in the results, where b=block device, c=character device, d=directory, p=pipe, f=file, l=symlink, s=socket. Defaults to files and directories')
    parser.add_argument('--file', '-f', action='store_true', help='Include files in the results (the default if no other type specified)')
    parser.add_argument('--dir', '-d', action='store_true', help='Include directories in the results')
    parser.add_argument('--block', action='store_true', help='Include block devices in the results')
    parser.add_argument('--char', action='store_true', help='Include character devices in the results')
    parser.add_argument('--pipe', action='store_true', help='Include pipes in the results')
    parser.add_argument('--symlink', '--link', action='store_true', help='Include symbolic links in the results')
    parser.add_argument('--socket', action='store_true', help='Include sockets in the results')
    parser.add_argument('--any', '-a', action='store_true', help='Include all types of item (the default unless specific types specified)')

    # Debug

    parser.add_argument('--verbose', '-v', action='store_true', help='Output verbose data')
    parser.add_argument('--debug', action='store_true', help='Output debug data')

    # Arguments

    parser.add_argument('patterns', nargs='*', help='List of things to search for.')

    args = parser.parse_args()

    return validate_arguments(args)

################################################################################

def main():
    """ Main function """

    args = parse_command_line()

    # Set up a dircolors intance, if one is needed

    dircolour = dircolors.Dircolors() if args.colour or (sys.stdout.isatty() and not args.no_colour) else None

    # Do the find!

    if args.git:
        files = git_ffind(args, dircolour)
    else:
        files = find_stuff(args, dircolour)

    # Run diffuse, if required

    if files:
        if args.diff:
            diff_cmd = ['diffuse']

            for file in files:
                if os.path.isfile(file):
                    diff_cmd.append(file)

            try:
                subprocess.run(diff_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError as exc:
                error(f'Diff failed with status={exc.returncode}')
            except FileNotFoundError:
                error('Unable to run %s' % ' '.join(diff_cmd))

    # Report the number of objects found

    if args.count_only:
        print(len(files))

    if args.count:
        print()
        print(f'{len(files)} objects found')

################################################################################

def ffind():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    ffind()
