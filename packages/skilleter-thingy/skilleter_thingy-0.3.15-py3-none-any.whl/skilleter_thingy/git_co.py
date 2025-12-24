#! /usr/bin/env python3

################################################################################
""" Enhanced version of 'git checkout'

    Currently only supports the '-b' option in addition to the default
    behaviour (may be extended to other options later, but otherwise, just
    use the 'git checkout' command as normal.

    Differs from standard checkout in that if the branch name specified is not
    an exact match for an existing local or remote branch it will look for
    branches where the specified name is a substring (e.g. '12345' will match
    'feature/fix-1234567') and, if there is a unique match, it will check that
    out. If there are multiple matches it will just list them.

    Note - partial matching ONLY works for branch names - tag names only
           do full matching and commits only match against the start of the SHA1

    TODO: Should prioritise branch names over SHA1 - for instance git co 69772
"""
################################################################################

import os
import logging
import sys
import argparse

from skilleter_modules import git
from skilleter_modules import colour

assert sys.version_info.major >= 3 and sys.version_info.minor >= 6

################################################################################

DESCRIPTION = \
"""
Enhanced version of 'git checkout'

Differs from standard checkout in that if the branch name specified is
not an exact match for an existing branch it will look for branches
where the specified name is a substring (e.g. '12345' will match
'feature/fix-1234567')

If there is a single match, it will check that out.

If there are multiple matches it will just list them.

If no local branches match, it will match against remote branches.

If no matching branches exist will will try commit IDs or tags.

Currently only supports the '-b' option in addition to the default
behaviour (may be extended to other options later, but otherwise, just
use the 'git checkout' command as normal).
"""

################################################################################

def parse_arguments():
    """ Parse and return command line arguments """

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter, epilog='Note that the "owner" of a branch is deemed to be the person who made the most-recent commit on that branch')
    parser.add_argument('--branch', '-b', action='store_true', help='Create the specified branch')
    parser.add_argument('--update', '-u', action='store_true', help='If a remote branch exists, and the branch isn\'t owned by the current user, delete any local branch and check out the remote version')
    parser.add_argument('--rebase', '-r', action='store_true', help='Rebase the branch onto its parent after checking it out')
    parser.add_argument('--force', '-f', action='store_true',
                        help='When using the update option, recreate the local branch even if it is owned by the current user')
    parser.add_argument('--exact', '-e', action='store_true', help='Do not use branch name matching - check out the branch as specified (if it exists)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('branchname', nargs=1, type=str,
                        help='The branch name (or a partial name that matches uniquely against a local branch, remote branch, commit ID or tag)')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')

    args = parser.parse_args()

    # Enable logging if requested

    if args.debug:
        logging.basicConfig(level=logging.INFO)

    if args.path:
        os.chdir(args.path[0])

    if args.force and not args.update:
        colour.error('The --force option only works with the --update option')

    return args

################################################################################

def checkout_matching_branch(args, branchname):
    """ Look for a commit matching the specified name and check it out if it is
        an exact match or there is only one partial match.
        If there are multiple branches that match, just list them
        """

    # If we are doing an update, then make sure we have all the remote info up-to-date

    if args.update:
        colour.write('Fetching updates from remote server(s)')
        git.fetch(all=True)

    # Get the list of matching commits.
    # * If an exact match to the branch, tag or SHA branch exists use it without checking partial matches
    # * Otherwise, unless --exact was specified, check for a partial match

    if git.iscommit(branchname, remote=True):
        commits = [branchname]

        logging.info('Exact match found for %s', branchname)
    elif not args.exact:
        commits = git.matching_branch(branchname)

        if not commits:
            commits = git.matching_commit(branchname)

        logging.info('Commits matching %s = %s', branchname, commits)

    # Can't do anything with multiple/no matching commits/branches

    if not commits:
        colour.error(f'[BOLD]No branches or commits matching [NORMAL][BLUE]{branchname}[NORMAL]')
    elif len(commits) > 1:
        colour.write(f'[RED:ERROR]: [BOLD]Multiple matches for [NORMAL][BLUE]{branchname}[NORMAL]:')
        for item in commits:
            colour.write(f'    {item}')
        sys.exit(1)

    # If we have one match, then we can do stuff

    logging.info('Only one matching commit: %s', commits[0])

    commit = commits[0]

    if args.update:
        # TODO: Should check all remotes if more than one

        remote = git.remote_names()[0]

        if commit.startswith(f'{remote}/'):
            remote_branch = commit
        else:
            remote_branch = f'remotes/{remote}/{commit}'

        logging.info('Remote branch: %s', remote_branch)

        # If the remote branch exists, then update, delete the local branch and re-create it

        if git.isbranch(remote_branch):
            logging.info('Remote branch exists')

            default_branch = git.default_branch()

            colour.write(f'Updating the [BLUE:{default_branch}] branch')

            git.checkout(default_branch)
            git.merge(f'{remote}/{default_branch}')

            # If the local branch exists, delete it

            # TODO: Should prompt rather than using force

            if git.isbranch(commit):
                logging.info('Local branch %s exists', commit)

                # Don't overwrite our own branches, just to be on the safe side

                if not args.force:
                    author = git.author(commit)
                    if author == git.config_get('user', 'name'):
                        colour.write(f'ERROR: Most recent commit on {commit} is {author} - Use the --force option to force-update your own branch!')
                        sys.exit(1)

                colour.write('Removing existing [BLUE:{commit}] branch')
                git.delete_branch(commit, force=True)
        else:
            colour.write(f'No corresponding remote branch [BLUE:{remote_branch}] exists')
            return

    # Check out the commit and report the name (branch, tag, or if nowt else, commit ID)

    logging.info('Checking out %s', commit)

    git.checkout(commit)
    colour.write('[BOLD]Checked out [NORMAL][BLUE]%s[NORMAL]' % (git.branch() or git.tag() or git.current_commit()))

    if args.rebase:
        colour.write('Rebasing branch against its parent')

        output = git.update()

        for text in output:
            print(text)

################################################################################

def main():
    """ Main function - parse the command line and create or attempt to checkout
        the specified branch """

    args = parse_arguments()

    if args.branch:
        git.checkout(args.branchname[0], create=True)
    else:
        checkout_matching_branch(args, args.branchname[0])

################################################################################

def git_co():
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
    git_co()
