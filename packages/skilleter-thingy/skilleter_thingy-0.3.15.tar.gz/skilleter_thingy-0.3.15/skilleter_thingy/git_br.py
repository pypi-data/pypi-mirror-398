#! /usr/bin/env python3

################################################################################
""" Thingy 'git-br' command - output branch information

    Author: John Skilleter

    Licence: GPL v3 or later

    TODO: Command line options for list of fields to output
    TODO: Command line options for sort order
    TODO: Debate the delete option, which currently isn't implemented
"""
################################################################################

import os
import sys
import argparse
import fnmatch
import datetime

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

def parse_command_line():
    """ Parse the command line """

    parser = argparse.ArgumentParser(description='List or delete branches that have been merged')

    parser.add_argument('--all', '-a', action='store_true', help='List all branches, including remotes')
    parser.add_argument('--delete', '-d', action='store_true',
                        help='Delete the specified branch(es), even if it is the current one (list of branches to delete must be supplied as parameters)')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')
    parser.add_argument('branches', nargs='*', help='Filter the list of branches according to one or more patterns')

    args = parser.parse_args()

    if args.path:
        os.chdir(args.path[0])

    if args.delete and not args.branches:
        colour.error('You must specify the branches to delete', prefix=True)

    return args

################################################################################

def branch_match(ref, matching_branches):
    """ Return True if ref matches an entry in matching_branches """

    if matching_branches:
        for branch in matching_branches:
            if '?' in branch or '*' in branch:
                if branch[0] not in ['?', '*']:
                    branch = f'*{branch}'
                if branch[-1] not in ['?', '*']:
                    branch = f'{branch}*'

                if fnmatch.fnmatch(ref, branch):
                    return True
            elif branch in ref:
                return True

        return False

    return True

################################################################################

def get_matching_branches(args):
    """ Get a list of branches matching those specified in the script arguments  """

    # Get the SHA1, date, author and name of the tip commit on each branch, including remotes
    # and keep track of the maximum length of each field

    branches = []

    for ref in git.ref(sort='-committerdate', fields=('objectname:short', 'committerdate', 'authorname', 'refname:short'), remotes=args.all):
        if branch_match(ref[3], args.branches):
            branches.append(ref)

    return branches

################################################################################

def list_branches(branches):
    """ List branches. """

    max_len = [0] * len(branches[0])

    user = git.config_get('user', 'name')

    # Output the fields in columns, highlighting user's own branches and those owned by Jenkins
    # Replacing references to today and yesterday's dates with 'today' and 'yesterday' and
    # reformatting dates and time for readability.

    today = datetime.date.today()
    yesterday = today - relativedelta(days=1)

    all_output = []

    current_branch = git.branch()

    for branch in branches:
        output = []

        for i, field in enumerate(branch):
            if i == 1:
                field = parse(field)
                time_str = field.strftime('%H:%M:%S')

                if field.date() == today:
                    field = 'today      ' + time_str
                elif field.date() == yesterday:
                    field = 'yesterday  ' + time_str
                else:
                    field = field.date().strftime('%d/%m/%Y') + ' ' + time_str

            output.append('%-*s' % (max_len[i], field))
            max_len[i] = max(max_len[i], len(field))

        highlight = 'GREEN' if branch[3] in ('master', 'main', 'develop') \
                    else 'BOLD' if branch[3] == current_branch \
                    else 'BLUE' if branch[2] == user \
                    else 'NORMAL'

        all_output.append({'highlight': highlight, 'output': output})

    for output in all_output:
        line = []
        for i, field in enumerate(output['output']):
            line.append('%-*s' % (max_len[i], field))

        colour.write('[%s:%s]' % (output['highlight'], '  '.join(line).rstrip()))

################################################################################

def delete_branches(branches):
    """ Delete matching branches. Report an error if no branches specified """

    if not branches:
        print('ERROR: The branches to delete must be specified')
        sys.exit(1)

    print('TODO: Deleting %s' % branches)

    # TODO: List branches, prompt user, delete each branch - if current branch then checkout develop, main or master first

################################################################################

def main():
    """ Main function """

    args = parse_command_line()

    branches = get_matching_branches(args)

    if args.delete:
        delete_branches(branches)
    else:
        list_branches(branches)

################################################################################

def git_br():
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
    git_br()
