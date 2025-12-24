#! /usr/bin/env python3

################################################################################
""" Thingy "git-ca" command - an intelligent version of "git commit --amend"

    Copyright (C) 2017-18 John Skilleter

    Licence: GPL v3 or later

    TODO: Handle attempt to amend commit in newly-initialised repo with no commits in.
    TODO: Fix failure with "fatal: pathspec "FILENAME" did not match any files" whilst amending a commit to include a deleted file.
"""
################################################################################

import os
import argparse
import sys
import logging

from skilleter_modules import colour
from skilleter_modules import git

################################################################################

def main():
    """ Amend a comment, updating modified files that are already committed and
        adding files that are listed on the command line """

    # Files to add to git before committing and files to commit

    files_to_add = []
    files_to_commit = []

    # Parse the command line

    parser = argparse.ArgumentParser(
        description='Amend changes to the current commit. Updates files that are already in the commit and, optionally, adds additional files.')

    parser.add_argument('--added', '-A', action='store_true', help='Update files in the current commit, including files added with "git add"')
    parser.add_argument('--all', '-a', action='store_true', help='Append all locally-modified, tracked files to the current commit')
    parser.add_argument('--everything', '-e', action='store_true', help='Append all modified and untracked files to the current commit (implies --all)')
    parser.add_argument('--ignored', '-i', action='store_true', dest='ignored', help='Include files normally hidden by .gitignore')
    parser.add_argument('--patch', '-p', action='store_true', help='Use the interactive patch selection interface to chose which changes to commit.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mode')
    parser.add_argument('--dry-run', '-D', action='store_true', help='Dry-run')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')

    parser.add_argument('files', nargs='*', help='List of files to add to the commit')

    args = parser.parse_args()

    # Configure logger

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
        logging.info('Debug logging enabled')

    # Change directory, if specified

    if args.path:
        os.chdir(args.path[0])

    # 'Add' implies 'all'

    if args.everything:
        args.all = True

    # If there are any files on the command line then add them
    # to the list of files to be committed

    if args.files:
        for filename in args.files:
            rel_path = git.tree_path(filename)
            files_to_add.append(rel_path)

    # Move to the working tree

    working_tree = git.working_tree()

    if not working_tree:
        colour.error('fatal: not a git repository (or any of the parent directories)')

    os.chdir(working_tree)

    # Get the list of files modified in the most recent commit

    current_commit = git.commit_changes()

    # Get the list of locally-modified and untracked files, including
    # files matching .gitignore, if necessary

    logging.info('Getting list of changed files')
    local_changes = git.status_info(args.ignored)

    for change in local_changes:
        logging.info('Changed: %s (%s)', change, local_changes[change])

        if change in current_commit or (args.added and local_changes[change][0] == 'A'):
            # Locally changed and already in the commit or, optionally, added to it, so update it

            files_to_commit.append(change)

        elif args.all and (local_changes[change][1] in ('M', 'A', 'D', 'T') or local_changes[change][0] == 'D'):
            # Tracked and 'all' option specified so add it to the commit

            files_to_commit.append(change)

        elif args.everything and local_changes[change][0] in ('!', '?'):
            # Untracked and 'add' option specified so add it to Git and the commit

            files_to_add.append(change)

    if files_to_add:
        try:
            git.add(files_to_add)
        except git.GitError as exc:
            colour.error(exc.msg, status=exc.status)

        files_to_commit += files_to_add

    # Perform the commit running in the foreground in case the user is using a console
    # mode text editor for commit comments.

    logging.info('Files to commit: %s', files_to_commit)

    try:
        git.commit(files_to_commit, amend=True, foreground=True, patch=args.patch, dry_run=args.dry_run)
    except git.GitError as exc:
        sys.exit(exc.status)

################################################################################

def git_ca():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    git_ca()
