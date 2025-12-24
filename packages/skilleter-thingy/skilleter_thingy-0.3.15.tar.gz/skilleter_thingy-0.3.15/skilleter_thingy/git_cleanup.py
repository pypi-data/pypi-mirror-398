#! /usr/bin/env python3

################################################################################
""" Thingy 'git-cleanup' command - list or delete branches that have been merged.

    Author: John Skilleter

    Licence: GPL v3 or later
"""
################################################################################

import os
import sys
import argparse
import logging

from skilleter_modules import git
from skilleter_modules import colour

################################################################################
# Constants

# Branches that we will never delete

PROTECTED_BRANCHES = ['develop', 'master', 'main', 'release', 'hotfix']

################################################################################

def parse_command_line():
    """ Parse the command line, returning the arguments """

    parser = argparse.ArgumentParser(
        description='List or delete branches that have been merged.\nWhen deleting branches, also delete tracking branches that are not longer on the remote.')

    parser.add_argument('--delete', '-d', action='store_true', dest='delete', help='Delete all branches that have been merged')
    parser.add_argument('--master', '-m', '--main', dest='master',
                        help='Specify the master branch (Attempts to read this from GitLab or defaults to "develop" if present or "master" or "main" otherwise')
    parser.add_argument('--force', '-f', action='store_true', dest='force', help='Allow protected branches (e.g. master) to be removed')
    parser.add_argument('--unmerged', '-u', action='store_true', dest='list_unmerged', help='List branches that have NOT been merged')
    parser.add_argument('--yes', '-y', action='store_true', dest='force', help='Assume "yes" in response to any prompts (e.g. to delete branches)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')

    parser.add_argument('branches', nargs='*', help='List of branches to check (default is all branches)')

    return parser.parse_args()

################################################################################

def validate_options(args, all_branches):
    """ Check that the command line options make sense """

    # If the master branch has not been specified try to get it from GitLab and then default to either 'develop', 'main', or 'master'

    if not args.master:
        args.master = git.default_branch()

    if not args.master:
        if 'develop' in all_branches:
            args.master = 'develop'
        elif 'main' in all_branches:
            args.master = 'main'
        elif 'master' in all_branches:
            args.master = 'master'
        else:
            colour.error('You must specify a master branch as the repo contains no obvious master branch')

    # Check that the master branch actually exists

    if args.master not in all_branches:
        colour.error('The "%s" branch does not exist in the repo' % args.master)

    # Check that the user isn't trying to remove a branch that is normally sacrosanct

    if not args.force and args.branches:
        for branch in all_branches:
            if branch in PROTECTED_BRANCHES:
                colour.error('You must use the "--force" option to delete protected branches (%s)' % ', '.join(PROTECTED_BRANCHES))

    # If no list of branches to check has been specified, use all the branches

    if not args.branches:
        args.branches = all_branches

################################################################################

def main():
    """ Entry point """

    # Handle the command line

    args = parse_command_line()

    # Enable logging if requested

    if args.debug:
        logging.basicConfig(level=logging.INFO)

    # Change directory, if specified

    if args.path:
        os.chdir(args.path[0])

    # Get the list of all local branches

    try:
        all_branches = git.branches()
    except git.GitError as exc:
        colour.error(exc.msg, status=exc.status)

    logging.info('Branches=%s', all_branches)

    # Check that the command line options are sensible, including the list of branches (if any)

    validate_options(args, all_branches)

    # Checkout and update the master branch then switch back

    logging.info('Checking out %s branch', args.master)

    try:
        git.checkout(args.master)

        logging.info('Running git pull')

        git.pull()

        logging.info('Checking out previous branch')

        git.checkout('-')

    except git.GitError as exc:
        colour.error(exc.msg, status=exc.status)

    # 'reported' is True when we've reported something so we can put a blank line before the
    # next item (if there is one).

    reported = False

    # List of branches that we will delete (if we aren't just listing possibilities)

    logging.info('Determining whether any branches can be deleted (not master branch, not protected and no outstanding commits)')

    branches_to_delete = []

    # Iterate through the branches, ignoring protected branches and the current master

    for branch in args.branches:
        if branch not in PROTECTED_BRANCHES and branch not in args.master:

            # Has the branch got commits that haven't been merged to the master branch?

            logging.info('Checking for unmerged commits on %s (against %s)', branch, args.master)

            try:
                unmerged = git.git(['log', '--no-merges', '--oneline', branch, '^%s' % args.master, '--'])
            except git.GitError as exc:
                sys.stderr.write('%s\n' % exc.msg)
                sys.exit(exc.status)

            # Either mark merged branches to be deleted or list unmerged or merged ones

            if args.delete:
                # Mark the branch as deleteable if the branch doesn't have unmerged commits
                # and it either isn't protected or we're forcing

                if not unmerged and (args.force or branch not in PROTECTED_BRANCHES):
                    logging.info('Branch %s can be deleted', branch)

                    branches_to_delete.append(branch)

            elif args.list_unmerged:
                if unmerged:
                    # if the branch has commits that are not on the master branch then list it as unmerged

                    if reported:
                        print()
                    else:
                        colour.write('Branches that have not been merged to [BLUE:%s]:' % args.master)

                    colour.write('    [BLUE:%s]: [BOLD:%d] unmerged commits' % (branch, len(unmerged)))

                    for commit in unmerged:
                        print('        %s' % commit)

                    reported = True

            elif not unmerged:
                # If the branch hasn't got unique commits then it has been merged (or is empty)

                if not reported:
                    colour.write('Branches that have %sbeen merged to [BLUE:%s]' % ('not ' if args.list_unmerged else '', args.master))

                colour.write('    [BLUE:%s]' % branch)

                reported = True

    # If we have branches to delete then delete them

    if args.delete:
        if branches_to_delete:

            logging.info('Deleting branch(es): %s', branches_to_delete)

            if not args.force:
                colour.write('The following branches have already been merged to the [BLUE:%s] branch and can be deleted:' % args.master)
                for branch in branches_to_delete:
                    colour.write('    [BLUE:%s]' % branch)

                print()
                confirm = input('Are you sure that you want to delete these branches? ')

                if confirm.lower() not in ('y', 'yes'):
                    colour.error('**aborted**')

                print()

            # Delete the branches, switching to the master branch before attempting to delete the current one

            for branch in branches_to_delete:
                if branch == git.branch():
                    colour.write('Switching to [BLUE:%s] branch before deleting current branch.' % args.master)
                    git.checkout(args.master)

                try:
                    logging.info('Deleting %s', branch)

                    git.delete_branch(branch, force=True)
                except git.GitError as exc:
                    colour.error(str(exc), status=exc.status)

                colour.write('Deleted [BLUE:%s]' % branch)
        else:
            colour.write('There are no branches that have been merged to the [BLUE:%s] branch.' % args.master)

    # Finally run remote pruning (note that we don't have an option to
    # list branches that *can't* be pruned (yet))

    reported = False
    prunable = False

    # Look for prunable branches and report them

    logging.info('Looking for remote tracking branches that can be pruned')

    for remote in git.remotes():
        for prune in git.remote_prune(remote, dry_run=True):
            if not reported:
                print()
                if args.force:
                    print('Deleting remote tracking branches:')
                else:
                    print('Remote tracking branches that can be deleted:')
                reported = True

            colour.write('    [BLUE:%s]' % prune)
            prunable = True

    # If we are deleting things and have things to delete then delete things

    if args.delete and prunable:
        if not args.force:
            print()
            confirm = input('Are you sure that you want to prune these branches? ')

            if confirm.lower() not in ('y', 'yes'):
                colour.error('**aborted**')

            print()

        for remote in git.remotes():
            logging.info('Pruning remote branches from %s', remote)

            pruned = git.remote_prune(remote)

            for branch in pruned:
                colour.write('Deleted [BLUE:%s]' % branch)

################################################################################

def git_cleanup():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)
    except git.GitError as exc:
        colour.error(exc.msg, status=exc.status, prefix=True)

################################################################################

if __name__ == '__main__':
    git_cleanup()
