#! /usr/bin/env python3

################################################################################
"""Thingy 'git-update' command - update the repo and rebase one more branches
   against their parent branch, if this can be unambiguously determined.

   Author: John Skilleter

   Licence: GPL v3 or later

   TODO: This is a partial solution - to do things properly, we'd have to work
         out the branch tree structure, start at the bottom, pull and/or rebase
         each one working upwards.

         As it is, I'm assuming that we don't have a tree, but a bush, with
         most things branched off a main, master or develop branch, so we pull
         fixed branches first then rebase everything in no particular order.

   TODO: Avoid lots of pulls - should be able to fetch then updated each local branch.
   TODO: Add option to specify name of master branch or additional names to add to the list
   TODO: Config entry for regularly-ignored branches
   TODO: Config entry for branches that shouldn't be rebased (main, master, release/*)
   TODO: Command line option when using -a to skip working trees that are modified
"""
################################################################################

import os
import sys
import argparse
import fnmatch
import logging

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

def parse_command_line():
    """Parse the command line"""

    parser = argparse.ArgumentParser(description='Rebase branch(es) against their parent branch, updating both in the process')

    parser.add_argument('--cleanup', '-c', action='store_true',
                        help='After updating a branch, delete it if there are no differences between it and its parent branch')
    parser.add_argument('--all', '-a', action='store_true', help='Update all local branches, not just the current one')
    parser.add_argument('--everything', '-A', action='store_true',
                        help='Update all local branches, not just the current one and ignore the default ignore list specified in the Git configuration')
    parser.add_argument('--default', '-d', action='store_true', help='Checkout the main or master branch on completion')
    parser.add_argument('--parent', '-p', action='store', help='Specify the parent branch, rather than trying to work it out')
    parser.add_argument('--all-parents', '-P', action='store_true',
                        help='Feature branches are not considered as alternative parents unless this option is specified')
    parser.add_argument('--stop', '-s', action='store_true', help='Stop if a rebase problem occurs, instead of skipping the branch')
    parser.add_argument('--ignore', '-i', action='store', default=None,
                        help='List of one or more wildcard branch names not to attempt to update (uses update.ignore from the Git configuration if not specified)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Report what would be done without actually doing it')

    return parser.parse_args()

################################################################################

class UpdateFailure(Exception):
    """Exception raised when a branch fails to update"""

    def __init__(self, branchname: str) -> None:
        self.branchname = branchname
        super().__init__()

################################################################################

def branch_rebase(args, results, branch):
    """Attempt to rebase a branch"""

    # Either use the specified parent or try to determine the parent branch

    if args.parent:
        parent = args.parent
    else:
        try:
            git.checkout(branch)
        except git.GitError as exc:
            colour.error(exc.msg)
            sys.exit(1)

        # Ignore feature branches as potential alternative parents unless told otherwise
        # If they are the only possible parent(s) then we still consider them.

        if args.all_parents:
            parents, _ = git.parents()
        else:
            parents, _ = git.parents(ignore='feature/*')

            logging.debug('Probable parents of %s: %s', branch, parents)

            if not parents:
                parents, _ = git.parents()

                logging.debug('No non-feature-branch parents found for %s. Feature branch parents could be: %s', branch, parents)

        if not parents:
            colour.write(f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] branch as unable to determine its parent (no obvious candidates))', indent=4)
            results['failed'].add(branch)
            return

        # Cheat - if we have multiple possible parents and one is 'develop', 'main' or 'master'
        # choose it.

        if len(parents) > 1:
            if 'master' in parents:
                parent = 'master'
            if 'main' in parents:
                parent = 'main'
            elif 'develop' in parents:
                parent = 'develop'
            elif 'scv-poc' in parents:
                parent = 'scv-poc'
            else:
                colour.write(f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] branch as unable to determine its parent (could be any of {", ".join(parents)})',
                             indent=4)
                results['failed'].add(branch)
                return

        elif len(parents) == 1:
            parent = parents[0]

    if args.dry_run:
        colour.write(f'[BOLD:Checking if] [BLUE:{branch}] [BOLD:needs to be rebased onto] [BLUE:{parent}]', indent=4)

    else:
        if parent not in results['pulled'] and parent not in results['unchanged']:
            colour.write(f'[BOLD:Updating] [BLUE:{parent}]')

            if not branch_pull(args, results, parent):
                return

        if branch not in results['pulled']:
            if git.iscommit(branch, remote_only=True):
                colour.write(f'[BOLD:Updating] [BLUE:{branch}]')

                branch_pull(args, results, branch)
            else:
                results['no-tracking'].add(branch)

        if git.rebase_required(branch, parent):
            colour.write(f'Rebasing [BLUE:{branch}] [BOLD:onto] [BLUE:{parent}]', indent=4)

            git.checkout(branch)
            output, status = git.rebase(parent)

            if status:
                colour.write(f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] onto [BLUE:{parent}]', indent=4)

                if args.verbose:
                    colour.write(output)

                results['failed'].add(branch)

                if args.stop:
                    raise UpdateFailure(branch)

                git.abort_rebase()
                return

            results['rebased'].add(branch)
        else:
            colour.write(f'[BLUE:{branch}] is already up-to-date on parent branch [BLUE:{parent}]', indent=4)

            results['unchanged'].add(branch)

    if args.cleanup:
        if args.dry_run:
            colour.write(f'[GREEN:Dry-run: Checking to see if {branch} and {parent} are the same - deleting {branch} if they are]', indent=4)

        elif git.diff_status(branch, parent):
            git.checkout(parent)
            git.delete_branch(branch, force=True)

            results['deleted'].add(branch)

            colour.write(f'Deleted branch [BLUE:{branch}] as it is not different to its parent branch ([BLUE:{parent}])', indent=4)

################################################################################

def branch_pull(args, results, branch, fail=True):
    """Attempt to update a branch, logging any failure except no remote tracking branch
       unless fail is False"""

    colour.write(f'Pulling updates for the [BLUE:{branch}] branch', indent=4)

    if not args.dry_run:
        if branch not in results['pulled'] and branch not in results['unchanged']:
            try:
                git.checkout(branch)
                output = git.pull()

                colour.write(output, indent=4)

                if output[0] == 'Already up-to-date.':
                    results['unchanged'].add(branch)

                results['pulled'].add(branch)

            except git.GitError as exc:
                if exc.msg.startswith('There is no tracking information for the current branch.'):
                    colour.write(f'[RED:WARNING]: There is no tracking information for the [BLUE:{branch}] branch.', indent=4)
                    fail = False

                elif exc.msg.startswith('Your configuration specifies to merge with the ref'):
                    colour.write('[RED:WARNING]: The upstream branch no longer exists', indent=4)
                    fail = False

                elif 'no such ref was fetched' in exc.msg:
                    colour.write(f'[RED:WARNING]: {exc.msg}', indent=4)

                else:
                    colour.write(f'[RED:ERROR]: Unable to merge upstream changes onto [BLUE:{branch}] branch.', indent=4)

                if git.merging():
                    git.abort_merge()
                elif git.rebasing():
                    git.abort_rebase()

                if fail:
                    results['failed'].add(branch)

                return False

    return True

################################################################################

def fixed_branch(branch):
    """Return True if a branch is 'fixed' (master, develop, release, etc.)
       and shouldn't be rebased automatically"""

    return branch.startswith(('release/', 'hotfix/')) or \
           branch in ('master', 'main', 'develop') or \
           '/PoC-' in branch

################################################################################

def report_branches(msg, branches):
    """Report a list of branches with a message"""

    colour.write(newline=True)
    colour.write(msg)

    for branch in branches:
        colour.write(f'[BLUE:{branch}]', indent=4)

################################################################################

def main():
    """Entry point"""

    # Handle the command line

    args = parse_command_line()

    # Enable logging if requested

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Check we are in the right place

    if not git.working_tree():
        colour.error('Not in a git repo')

    # Set the default ignore list if none specified and if not using the '-A' option

    if args.ignore is None and not args.everything:
        args.ignore = git.config_get('update', 'ignore')

    args.ignore = args.ignore.split(',') if args.ignore else []

    logging.info('Ignore list: %s', ', '.join(args.ignore))

    # Make sure we've got no locally-modified files

    status = git.status_info(ignored=True)

    for entry in status:
        if status[entry][1] == 'M':
            colour.error('You have unstaged changes - cannot update.')

    # Get the current branch

    current_branch = git.branch()

    if not current_branch:
        colour.error('No branch currently checked out - cannot update.')

    colour.write(f'[BOLD:Current branch:] [BLUE:{current_branch}]')

    # Switch the current directory in case it vanishes when we switch branches

    os.chdir(git.working_tree())

    # Optionally pull or rebase everything - pull things first, then rebase
    # the rest.

    branches = git.branches() if args.all or args.everything else [current_branch]

    logging.info('Updating %s', ', '.join(branches))

    # Filter out branches that the user wants to ignore

    if args.ignore:
        for ignore in args.ignore:
            for name in branches[:]:
                if fnmatch.fnmatch(name, ignore) and name in branches:
                    branches.remove(name)

    if not branches:
        colour.error('No matching branches to update')

    # List of stuff that's been done, to report in the summary

    results = {'deleted': set(), 'pulled': set(), 'failed': set(), 'rebased': set(), 'unchanged': set(), 'no-tracking': set()}

    to_rebase = set()

    try:
        for branch in branches:
            if fixed_branch(branch):
                branch_pull(args, results, branch)
            else:
                to_rebase.add(branch)

        for branch in to_rebase:
            branch_rebase(args, results, branch)

        # Return to the original branch if it still exists or the master

        all_branches = git.branches()

        return_branch = current_branch if current_branch in all_branches \
            else 'develop' if 'develop' in all_branches \
            else 'main' if 'main' in all_branches \
            else 'master' if 'master' in all_branches else None

        if return_branch:
            colour.write('')
            colour.write(f'[BOLD]Checking out the [BLUE:{return_branch}] [BOLD:branch]')

            if not args.dry_run:
                git.checkout(return_branch)

    except UpdateFailure as exc:
        update_failed = exc.branchname

    else:
        update_failed = None

    for entry in ('rebased', 'unchanged', 'pulled', 'failed', 'no-tracking'):
        results[entry] -= results['deleted']

    results['pulled'] -= results['unchanged']

    if results['rebased']:
        report_branches('[BOLD:The following branches have been rebased:]', results['rebased'])

    if results['unchanged']:
        report_branches('[BOLD:The following branches were already up-to-date:]', results['unchanged'])

    if results['pulled']:
        report_branches('[BOLD:The following branches have been updated:]', results['pulled'])

    if results['deleted']:
        report_branches('[BOLD:The following branches have been deleted:]', results['deleted'])

    if results['failed']:
        report_branches('[RED:WARNING:] [BOLD:The following branches failed to update:]', results['failed'])

    if results['no-tracking']:
        report_branches('[YELLOW:NOTE:] [BOLD:The following branches have been rebased, but no upstream branch exists]', results['no-tracking'])

    if update_failed:
        colour.write('')
        colour.write(f'Halted during failed rebase of branch [BLUE:{update_failed}]')

################################################################################

def git_update():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    git_update()
