#!/usr/bin/env python3

"""
Attempt to determine the parent branch of a commit by tracking down
the branch commit history and looking for other branches that share
the same commit. Can optionally ignore feature branches and/or report
the distance to the potential parent.
"""

import os
import argparse
import sys

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

def main():
    """ Main function """

    current_branch = git.branch()

    parser = argparse.ArgumentParser(description='Attempt to determine the parent branch for the specified branch (defaulting to the current one)')
    parser.add_argument('--all', '-a', action='store_true', help='Include feature branches as possible parents')
    parser.add_argument('--verbose', '-v', action='store_true', help='Report verbose results (includes number of commits between branch and parent)')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')
    parser.add_argument('branch', action='store', nargs='?', type=str, default=current_branch,
                        help=f'Branch, commit or commit (defaults to current branch; {current_branch})')

    args = parser.parse_args()

    if args.path:
        os.chdir(args.path[0])

    if args.all:
        any_parents, any_distance = git.parents(args.branch)
    else:
        any_parents = []

    parents, distance = git.parents(args.branch, ignore='feature/*')

    # If we have feature and non-feature branch candidates, decide which to report
    # (one or both) based on distance.

    if parents and any_parents:
        if any_distance < distance:
            parents = any_parents
            distance = any_distance
        elif any_distance == distance:
            for more in any_parents:
                if more not in parents:
                    parents.append(more)

    if parents:
        if args.verbose:
            if len(parents) == 1:
                colour.write(f'Parent branch [BLUE:{parents[0]}] is [BLUE:{distance}] commits away from [BLUE:{args.branch}]')
            else:
                colour.write(f'Parent branches [BLUE:%s] are [BLUE:{distance}] commits away from [BLUE:{args.branch}]' % (', '.join(parents)))
        else:
            print(', '.join(parents))
    else:
        colour.error('Could not determine parent branch\n', prefix=True)

################################################################################

def git_parent():
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
    git_parent()
