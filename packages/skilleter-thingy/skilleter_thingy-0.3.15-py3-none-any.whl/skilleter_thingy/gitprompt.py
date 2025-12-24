#! /usr/bin/env python3

""" Thingy gitprompt command

    Copyright (C) 2017 John Skilleter

    Used to create the portion of the shell prompt that optionally shows
    the current git repo name and branch and to output a colour code indicating
    the status of the current working tree.

    Normally used in the shell setup scripts (e.g. ~/.bashrc) as:

        export PS1=$(gitprompt OPTIONS)

    Command line options:

    '--colour'

        Output a background colour code indicating the status of the
        current tree, rather than the repo name and branch.

        Colours used are:

            Green   - Clean repo, no local changes
            Cyan    - Clean repo with untracked file(s)
            Yellow  - Uncommitted local changes (added, copied or renamed files)
            Red     - Local changes that have not been added (files modified or deleted)
            Magenta - Unmerged files

    Other options are set via the Git configuration:

        prompt.prefix: 0 - No prefix
                       1 - Single letter indications of git status (untracked, modified, etc)
                       2 - One word indications (untracked, modified, etc)

    TODO: Limit the total prompt length more 'intelligently', rather than just bits of it.
    TODO: Indicate whether current directory is writeable and/or put current owner in prompt if no the current user
"""

################################################################################

# Try and reduce the scope for an auto-repeating ^C to screw up the shell prompt

import signal

signal.signal(signal.SIGINT, signal.SIG_IGN)

import os
import sys
import argparse

from skilleter_modules import git
from skilleter_modules import colour

################################################################################
# Constants

# Prefix text used when showing git status in the prompt - first entry is the
# abbreviated form and the second is the verbose.

STATUS_PREFIX = \
    {
        'untracked': ('u', 'untracked'),
        'added': ('A', 'added'),
        'modified': ('M', 'modified'),
        'unmerged': ('U', 'unmerged'),
        'deleted': ('D', 'deleted'),
        'copied': ('C', 'copied'),
        'renamed': ('R', 'renamed'),
        'stash': ('S', 'stashed')
    }

MAX_BRANCH_NAME_LENGTH = int(os.environ.get('COLUMNS', 96)) / 3

################################################################################

def colour_prompt(gitstate: dict):
    """ Return the colour for the prompt, according to the current state of the
        working tree. """

    output = []

    output.append('[NORMAL]')

    if gitstate['modified'] or gitstate['deleted']:
        output.append('[REVERSE][RED]')

    elif gitstate['added'] or gitstate['copied'] or gitstate['renamed']:
        output.append('[REVERSE][YELLOW]')

    elif gitstate['unmerged']:
        output.append('[REVERSE][MAGENTA]')

    elif gitstate['untracked']:
        output.append('[REVERSE][CYAN]')

    elif gitstate['merging'] or gitstate['bisecting'] or gitstate['rebasing']:
        output.append('[REVERSE][BLACK]')

    else:
        output.append('[REVERSE][GREEN]')

    if output:
        output.append(' ')

    return output

################################################################################

def prompt_prefix(gitstate: dict):
    """ Build a prompt prefix containing the type and number
      of changes in the repo. """

    prefix = []

    # Get the status configuration from gitconfig and restrict it to the
    # range 0..2

    try:
        status_prefix = int(git.config_get('prompt', 'prefix', defaultvalue='0'))
    except ValueError:
        status_prefix = 0
    else:
        status_prefix = max(min(status_prefix, 2), 0)

    # Only output the status information if the prefix is non-zero

    if status_prefix > 0:
        i = status_prefix - 1

        stashed = len(git.stash())

        if stashed:
            prefix.append('%s:%d' % (STATUS_PREFIX['stash'][i], stashed))

        if gitstate['untracked']:
            prefix.append('%s:%d' % (STATUS_PREFIX['untracked'][i], gitstate['untracked']))

        if gitstate['added']:
            prefix.append('%s:%d' % (STATUS_PREFIX['added'][i], gitstate['added']))

        if gitstate['modified']:
            prefix.append('%s:%d' % (STATUS_PREFIX['modified'][i], gitstate['modified']))

        if gitstate['unmerged']:
            prefix.append('%s:%d' % (STATUS_PREFIX['unmerged'][i], gitstate['unmerged']))

        if gitstate['deleted']:
            prefix.append('%s:%d' % (STATUS_PREFIX['deleted'][i], gitstate['deleted']))

        if gitstate['copied']:
            prefix.append('%s:%d' % (STATUS_PREFIX['copied'][i], gitstate['copied']))

        if gitstate['renamed']:
            prefix.append('%s:%d' % (STATUS_PREFIX['renamed'][i], gitstate['renamed']))

    if prefix:
        prefix = ['[' + ' '.join(prefix) + ']']

    # Get the current branch, tag or commit

    branch = git.branch() or git.tag() or git.current_commit(short=True)

    # TODO: More intelligent branch name pruning - currently just trims it if longer than limit
    # TODO: Keep branch name up to minimum characters long - use more components if still shorter

    if len(branch) > MAX_BRANCH_NAME_LENGTH:
        truncated_name = None

        for sep in (' ', '-', '_', '/'):
            shortname = sep.join(branch.split(sep)[0:2])
            if (truncated_name and len(truncated_name) > len(shortname)) or not truncated_name:
                truncated_name = shortname

        if truncated_name:
            branch = '%s...' % truncated_name

    if gitstate['rebasing']:
        prefix.append('(rebasing)')
    elif gitstate['bisecting']:
        prefix.append('(bisecting)')
    elif gitstate['merging']:
        prefix.append('(merging)')

    project = git.project(short=True)

    if project:
        prefix.append(project + ':')

    prefix.append(branch)

    return ' '.join(prefix)

################################################################################

def git_status(colour_output: str, prompt_output: str):
    """ Catalogue the current state of the working tree then call the function
        to either output a suitable colour or the prompt text or both """

    # Get the working tree, just return if there's an error

    try:
        working_tree = git.working_tree()
    except git.GitError:
        return None

    # Return if we are not in a working tree

    if not working_tree:
        return None

    # gitstate contains counters for numbers of modified (etc.) elements in the tree and flags to indicate
    # whether we're currently in a merge/rebase/bisect state.

    gitstate = {'modified': 0, 'added': 0, 'untracked': 0, 'unmerged': 0, 'deleted': 0, 'renamed': 0, 'copied': 0}

    # Set flags if we are currently merging/rebasing/bisecting and get the current status

    try:
        gitstate['merging'] = git.merging()
        gitstate['rebasing'] = git.rebasing()
        gitstate['bisecting'] = git.bisecting()

        status = git.status(untracked=True)
    except git.GitError as exc:
        # Major failure of gitness - report the error and quit

        msg = exc.msg.split('\n')[0]

        if colour_output:
            return f'[WHITE][BRED] {msg}'

        return f' ERROR: {msg} '

    # Count the number of files in each state

    for st in status:
        gitstate['untracked'] += '?' in st[0]
        gitstate['added'] += 'A' in st[0]
        gitstate['modified'] += 'M' in st[0]
        gitstate['unmerged'] += 'U' in st[0]
        gitstate['deleted'] += 'D' in st[0]
        gitstate['copied'] += 'C' in st[0]
        gitstate['renamed'] += 'R' in st[0]

    # Set the output colour or output the prompt prefix

    output = []

    if colour_output:
        output += colour_prompt(gitstate)

    if prompt_output or not colour_output:
        output.append(prompt_prefix(gitstate))

    if output:
        output.append(' ')

    return ''.join(output)

################################################################################

def main():
    """ Parse the command line and output colour or status """

    parser = argparse.ArgumentParser(description='Report current branch and, optionally, git repo name to be embedded in shell prompt')
    parser.add_argument('--colour', action='store_true', help='Output colour code indicating working tree status')
    parser.add_argument('--prompt', action='store_true', help='Output the prompt (default if --colour not specified)')

    args = parser.parse_args()

    output = git_status(args.colour, args.prompt)

    if output:
        colour.write(output, newline=False)

################################################################################

def gitprompt():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    gitprompt()
