#!/usr/bin/env python3

"""mg - MultiGit - utility for managing multiple Git working trees in a hierarchical directory tree"""

import os
import sys
import fnmatch
import configparser
import subprocess

from dataclasses import dataclass, field

from skilleter_modules import git
from skilleter_modules import colour

################################################################################
# TODO: 2. If run in a subdirectory, only process working trees in that tree (or have an option to do so, or an option _not_ to do so; --all)
# TODO: 2. select_git_repos() and +dir should use consist way of selecting repos if possible
# TODO: 3 .init option '--set-default' to update the default branch to the current one for specified working trees
# TODO: 3. Verbose option
# TODO: 3. When filtering by tag or by repo name, if name starts with '!' only match if tag isn't present or repo name doesn't match (and don't allow '!' at start of tag otherwise)
# TODO: 3. (alternative to above) A '--not' option that inverts all the matching criteria, so '--not --branched --modified' selects all unmodified repos which aren't branched
# TODO: 3. (alternative to both above) Additional options; --!modified --!branched --!tag which act as the inverse of each option, so --!branched selects all unbranched repos.
# TODO: 3. (another alternative) - Use 'not-' instead of '!', so have --not-branched, --not-modified, --not-tag (single-letter options -B, -M, -T).
# TODO: 4. Option to +dir to return all matches so that caller can select one they want
# TODO: 4. Shell autocomplete for +dir
# TODO: 5. -j option to run in parallel - yes, but it will only work with non-interactive Git commands
################################################################################

DEFAULT_CONFIG_FILE = 'multigit.toml'

# If a branch name is specified as 'DEFAULT' then the default branch for the
# repo is used instead.

DEFAULT_BRANCH = 'DEFAULT'

################################################################################
# Command line help - we aren't using argparse since it isn't flexible enough to handle arbtirary git
# commands are parameters so we have to manually create the help and parse the command line

HELP_INFO = """usage: multigit [--help|-h] [--verbose|-v] [--quiet|-q] [--config|-c CONFIG] [--repos|-r REPOS] [--modified|-m] [--branched|-b] [--sub|-s] [--tag|-t TAGS] [--continue|-o] [--path|-C PATH]
                {+clone, +init, +config, +dir, +list, +run, +add, GIT_COMMAND} ...

Run git commands in multiple Git repos. DISCLAIMER: This is beta-quality software, with missing features and liable to fail with a stack trace, but shouldn't eat your data

options:
  -h, --help            show this help message and exit
  --verbose, -v         Verbosity to the maximum
  --quiet, -q           Minimal console output
  --config CONFIG, -c CONFIG
                        The configuration file (defaults to multigit.toml)
  --repos REPOS, -r REPOS
                        The repo names to work on (defaults to all repos and can contain shell wildcards and can be issued multiple times on the command line)
  --modified, -m        Select repos that have local modifications
  --branched, -b        Select repos that do not have the default branch checked out
  --tag TAG, -t TAG     Select repos that have the specified tag (can be issued multiple times on the command line)
  --sub, -s             Select only the repos in the current directory and subdirectories
  --continue, -o        Continue if a git command returns an error (by default, executation terminates when a command fails)
  --path, -C PATH       Run as if the command was started in PATH instead of the current working directory

Sub-commands:
  {+clone, +init, +dir, +config, +list, +run, +add, +update, GIT_COMMAND}
    +clone REPO {BRANCH} Clone a repo containing a multigit configuration file, then clone all the child repos and check out the default branch in each
    +init                Build or update the configuration file using the current branch in each repo as the default branch
    +config              Output the name and location of the configuration file
    +dir                 Output the location of a working tree, given the repo name, or if no parameter specified, the root directory of the multigit tree
    +list                Output a list of the top level directories of each of the Git repos
    +tag TAG             Apply a configuration tag to repos filtered by the command line options (list configuration tags if no parameter specified)
    +untag TAG           Remove a configuration tag to repos filtered by the command line options
    +run COMMAND         Run the specified command in repos filtered by the command line options
    +add REPO DIR        Clone REPO into the DIR directory and add it to the multigit configuration
    +update              Clone any repos in the current configuration that do not have working trees
    GIT_COMMAND          Any git command, including options and parameters - this is then run in all specified working trees

"""

################################################################################

@dataclass
class Arguments():
    """Data class to contain command line options and parameters"""

    # Command line options for output noise

    quiet: bool = False
    verbose: bool = False

    # True if we continue after a git command returns an error

    error_continue: bool = False

    # Default and current configuration file

    default_configuration_file: str = DEFAULT_CONFIG_FILE
    configuration_file: str = None

    # Command line filter options

    repos: list[str] = field(default_factory=list)
    tag: list[str] = field(default_factory=list)
    modified: bool = False
    branched: bool = False
    subdirectories: bool = False

    # Command to run with parameters

    command: str = None
    parameters: list[str] = field(default_factory=list)

    # True if running an internal command

    internal_command: bool = False

    # True if the configuration data needs to be written back on completion

    config_modified: bool = False

################################################################################

def verbose(args, msg):
    """Output a message to stderr if running verbosely"""

    if args.verbose:
        colour.write(f'>>>{msg}', stream=sys.stderr)

################################################################################

def absolute_repo_path(args, relative_path=''):
    """Given a path relative to the multigit configuration file, return
       the absolute path thereto"""

    return os.path.join(os.path.dirname(args.configuration_file), relative_path)

################################################################################

def relative_repo_path(args, relative_path=''):
    """Given a path relative to the multigit configuration file, return
       the relative path from the current directory"""

    return os.path.relpath(absolute_repo_path(args, relative_path))

################################################################################

def safe_clone(args, location, origin):
    """If location exists then fail with an error if it isn't a directory, or
    or is a directory, but isn't a working tree, or is a working tree for a
    different Git repo than remote otherwise do nothing.
    If it doesn't exist, then clone the specified remote there."""

    if os.path.exists(location):
        if not os.path.isdir(os.path.join(location, '.git')):
            colour.error(f'"[BLUE:{location}]" already exists and is not a Git working tree', prefix=True)

        remotes = git.remotes(path=location)

        for remote in remotes:
            if origin == remotes[remote]:
                break
        else:
            colour.error(f'"[BLUE:{location}]" already exists and was not cloned from [BLUE:{origin}]', prefix=True)

    else:
        if not args.quiet:
            colour.write(f'Cloning [BOLD:{origin}] into [BLUE:{location}]')

        git.clone(origin, working_tree=location)

################################################################################

def find_configuration(default_config_file):
    """If the configuration file name has path elements, try and read it, otherwise
       search up the directory tree looking for the configuration file.
       Returns configuration file path or None if the configuration file
       could not be found."""

    if '/' in default_config_file:
        config_file = default_config_file
    else:
        try:
            config_path = os.getcwd()
        except FileNotFoundError:
            colour.error('Unable to determine current directory', prefix=True)

        config_file = os.path.join(config_path, default_config_file)

        while not os.path.isfile(config_file) and config_path != '/':
            config_path = os.path.dirname(config_path)
            config_file = os.path.join(config_path, default_config_file)

    return config_file if os.path.isfile(config_file) else None

################################################################################

def show_progress(width, msg):
    """Show a single line progress message without moving the cursor to the next
       line."""

    colour.write(msg[:width-1], newline=False, cleareol=True, cr=True)

################################################################################

def find_working_trees(args):
    """Locate and return a list of '.git' directory parent directories in the
       specified path.

       If wildcard is not None then it is treated as a list of wildcards and
       only repos matching at least one of the wildcards are returned.

       If the same repo matches multiple times it will only be returned once. """

    repos = set()

    for root, dirs, _ in os.walk(os.path.dirname(args.configuration_file), topdown=True):
        if '.git' in dirs:
            relative_path = os.path.relpath(root)

            if args.repos:
                for card in args.repos:
                    if fnmatch.fnmatch(relative_path, card):
                        if relative_path not in repos:
                            yield relative_path
                            repos.add(relative_path)
                        break
            else:
                if relative_path not in repos:
                    yield relative_path
                    repos.add(relative_path)

        # Don't recurse down into hidden directories

        dirs[:] = [d for d in dirs if d[0] != '.']

################################################################################

def select_git_repos(args, config):
    """Return git repos from the configuration that match the criteria on the
       multigit command line (the --repos, --tag, --modified, --sub and --branched options)
       or, return them all if no relevant options specified"""

    for repo_path in config.sections():
        # If repos are specified, then only match according to exact name match,
        # exact path match or wildcard match

        repo_abs_path = absolute_repo_path(args, repo_path)

        if args.repos:
            for entry in args.repos:
                if config[repo_path]['repo name'] == entry:
                    matching = True
                    break

                if repo_path == entry:
                    matching = True
                    break

                if '?' in entry or '*' in entry:
                    if fnmatch.fnmatch(repo_path, entry) or fnmatch.fnmatch(config[repo_path]['repo name'], entry):
                        matching = True
                        break

            else:
                matching = False
        else:
            matching = True

        # If branched specified, only match if the repo is matched _and_ branched

        if matching and args.branched:
            if git.branch(path=repo_abs_path) == config[repo_path]['default branch']:
                matching = False

        # If modified specified, only match if the repo is matched _and_ modified

        if matching and args.modified:
            if not git.status(path=repo_abs_path):
                matching = False

        # If tag filtering specified, only match if the repo is tagged with one of the specified tags

        if matching and args.tag:
            for entry in args.tag:
                try:
                    tags = config[repo_path]['tags'].split(',')
                    if entry in tags:
                        break
                except KeyError:
                    pass
            else:
                matching = False

        # If subdirectories specified, only match if the repo is in the current directory tree

        if matching and args.subdirectories:
            repo_path_rel = os.path.relpath(absolute_repo_path(args, repo_path))

            if repo_path_rel == '..' or repo_path_rel.startswith('../'):
                matching = False

        # If we have a match, yield the config entry to the caller

        if matching:
            yield config[repo_path]

################################################################################

def branch_name(name, default_branch):
    """If name is None or DEFAULT_BRANCH return default_branch, otherwise return name"""

    return default_branch if not name or name == DEFAULT_BRANCH else name

################################################################################

def add_new_repo(args, config, repo_path, default_branch=None):
    """Add a new configuration entry containing the default branch, remote origin
    (if there is one), name and default branch"""

    abs_repo_path = absolute_repo_path(args, repo_path)

    added = repo_path not in config

    config[repo_path] = {}

    if not default_branch:
        default_branch = git.branch(path=abs_repo_path)

    if not default_branch:
        colour.error(f'Unable to determine default branch in [BLUE:{abs_repo_path}]', prefix=True)

    config[repo_path]['default branch'] = default_branch

    remote = git.remotes(path=abs_repo_path)

    if 'origin' in remote:
        config[repo_path]['origin'] = remote['origin']
        config[repo_path]['repo name'] = os.path.basename(remote['origin']).removesuffix('.git')
    else:
        config[repo_path]['repo name'] = os.path.basename(repo_path)

    if not args.quiet:
        if added:
            colour.write(f'Added [BLUE:{repo_path}] with default branch [BLUE:{default_branch}]')
        else:
            colour.write(f'Reset [BLUE:{repo_path}] with default branch [BLUE:{default_branch}]')

################################################################################

def mg_clone(args, config, console):
    """Clone a repo, optionally check out a branch and attempt to read the
       multigit configuration file and clone all the repos listed therein, checkouting
       the default branch in each one"""

    _ = console

    # Sanity checks

    if not args.parameters:
        colour.error('The "[BOLD:clone]" subcommand takes 1 or 2 parameters - the repo to clone and, optionally, the branch to check out', prefix=True)

    if args.branched or args.modified:
        colour.error('The "[BOLD:modified]" and "[BOLD:branched]" options cannot be used with the "[BOLD:clone]" subcommand', prefix=True)

    # Destination directory is the last portion of the repo URL with the extension removed

    directory = os.path.splitext(os.path.basename(args.parameters[0]))[0]

    if os.path.exists(directory):
        if os.path.isdir(directory):
            colour.error(f'The "[BLUE:{directory}]" directory already exists', prefix=True)
        else:
            colour.error(f'"[BLUE:{directory}]" already exists', prefix=True)

    # Clone the repo and chdir into it

    if not args.quiet:
        colour.write(f'Cloning [BOLD:{args.parameters[0]}] into [BLUE:{directory}]')

    git.clone(args.parameters[0], working_tree=directory)

    os.chdir(directory)

    # Optionally checkout a branch, if specified

    if len(args.parameters) > 1:
        git.checkout(args.parameters[1])

    # Open the configuration file in the repo (if no configuration file has been specified, use the default)

    if not args.configuration_file:
        args.configuration_file = args.default_configuration_file

    if not os.path.isfile(args.configuration_file):
        colour.error(f'Cannot find the configuration file: [BLUE:{args.default_configuration_file}]', prefix=True)

    config.read(args.configuration_file)

    # Now iterate through the repos, creating directories and cloning them and checking
    # out the default branch

    for repo in select_git_repos(args, config):
        if repo.name != '.':
            directory = os.path.dirname(repo.name)

            if directory:
                os.makedirs(directory, exist_ok=True)

            if not args.quiet:
                colour.write(f'Cloning [BLUE:{repo["origin"]}] into [BLUE:{directory}]')

            git.clone(repo['origin'], working_tree=repo.name)

            if not args.quiet:
                colour.write(f'    Checking out [BLUE:{repo["default branch"]}]')

            git.checkout(repo['default branch'], path=repo.name)

################################################################################

def mg_init(args, config, console):
    """Create or update the configuration
       By default, it scans the tree for git directories and adds or updates them
       in the configuration, using the current branch as the default branch. """

    # Sanity checks

    if args.modified or args.branched or args.tag or args.subdirectories:
        colour.error('The "[BOLD:--tag]", "[BOLD:--modified]" "[BOLD:--sub]", and "[BOLD:--branched]" options cannot be used with the "[BOLD:init]" subcommand', prefix=True)

    # Search for .git directories and add any that aren't already in the configuration

    repo_list = []
    for repo_dir in find_working_trees(args):
        if not args.quiet:
            show_progress(console.columns, repo_dir)

        repo_list.append(repo_dir)

        if repo_dir not in config:
            add_new_repo(args, config, repo_dir)

    if not args.quiet:
        colour.write(cleareol=True)

    # Look for configuration entries that are no longer present and delete them

    removals = []

    for repo in config:
        if repo != 'DEFAULT' and repo not in repo_list:
            removals.append(repo)

    for entry in removals:
        del config[entry]
        colour.write(f'Removed [BLUE:{entry}] as it no longer exists')

    # The configuration file needs to be updated

    args.config_modified = True

################################################################################

def mg_add(args, config, console):
    """Add a new repo - takes 2 parameters; the repo to clone and the directory
       to clone it into. If successful, adds the repo to the configuration"""

    _ = console
    _ = config

    verbose(args, f'add: Parameters: {", ".join(args.parameters)}')

    if len(args.parameters) != 2:
        colour.error('The "[BOLD:+add]" command takes two parameters; the repo to clone the location to clone it into', prefix=True)

    if args.modified or args.branched or args.tag or args.subdirectories:
        colour.error('The "[BOLD:--tag]", "[BOLD:--modified]" "[BOLD:--sub]", and "[BOLD:--branched]" options cannot be used with the "[BOLD:+add]" subcommand', prefix=True)

    repo = args.parameters[0]
    location = args.parameters[1]

    # Attempt to clone it

    safe_clone(args, repo, location)

    # Add to the configuration

    add_new_repo(args, config, location)

    # The configuration file needs to be updated

    args.config_modified = True

################################################################################

def mg_update(args, config, console):
    """Clone any repos in the current configuration that do not have working trees
       Similar to the '+init' command except that it updates an existing multigit
       tree rather than creating one from scratch."""

    _ = console

    # Don't allow pointless options

    if args.modified or args.branched or args.tag:
        colour.error('The "[BOLD:--tag]", "[BOLD:--modified]" and "[BOLD:--branched]" options cannot be used with the "[BOLD:+update]" subcommand', prefix=True)

    # Now iterate through the repos, cloning any that don't already have working trees

    for repo in select_git_repos(args, config):
        if repo.name != '.':
            safe_clone(args, repo.name, repo['origin'])

################################################################################

def mg_dir(args, config, console):
    """Return the location of a working tree, given the name, or the root directory
       of the tree if not
       Returns an error unless there is a unique match"""

    _ = console
    _ = config

    verbose(args, f'dir: Parameters: {", ".join(args.parameters)}')

    if len(args.parameters) > 1:
        colour.error('The "[BOLD:+dir]" command takes no more than one parameter - the name of the working tree to search for', prefix=True)

    # TODO: mg_dir _should_ use these options

    if args.modified or args.branched or args.tag or args.subdirectories:
        colour.error('The "[BOLD:--tag]", "[BOLD:--modified]" "[BOLD:--sub]", and "[BOLD:--branched]" options cannot be used with the "[BOLD:+dir]" subcommand', prefix=True)

    # If a parameter is specified, look for matches, otherwise just return the location of the
    # configuration file

    if not args.parameters:
        colour.write(os.path.dirname(args.configuration_file))
        return

    locations = []

    search_name = args.parameters[0]

    # Search for wildcard matches, or matches that contain the search term if it
    # doesn't already contain a wildcard

    if '*' in search_name or '?' in search_name:
        search_name = f'*{search_name}*'
        for repo in select_git_repos(args, config):
            if fnmatch.fnmatch(repo['repo name'], search_name):
                locations.append(repo.name)
    else:
        for repo in select_git_repos(args, config):
            if search_name in repo['repo name']:
                locations.append(repo.name)

    if not locations:
        colour.error(f'No matches with [BLUE:{search_name}]', prefix=True)

    colour.write("\n".join([relative_repo_path(args, loc) for loc in locations]))


################################################################################

def mg_tag(args, config, console):
    """Apply a configuration tag"""

    _ = console

    if len(args.parameters) > 1:
        colour.error('The "[BOLD:+tag]" command takes no more than one parameter', prefix=True)

    for repo in select_git_repos(args, config):
        try:
            tags = repo.get('tags').split(',')
        except AttributeError:
            tags = []

        if args.parameters:
            if args.parameters[0] not in tags:
                tags.append(args.parameters[0])
                repo['tags'] = ','.join(tags)
                args.config_modified = True
        elif tags:
            colour.write(f'[BLUE:{repo["repo name"]}] - {", ".join(tags)}')

################################################################################

def mg_untag(args, config, console):
    """Remove a configuration tag"""

    _ = console

    if len(args.parameters) > 1:
        colour.error('The "[BOLD:+tag]" command takes no more than one parameter', prefix=True)

    for repo in select_git_repos(args, config):
        try:
            tags = repo.get('tags', '').split(',')
        except AttributeError:
            tags = []

        if args.parameters[0] in tags:
            tags.remove(args.parameters[0])
            repo['tags'] = ','.join(tags)
            args.config_modified = True

################################################################################

def mg_config(args, config, console):
    """Output the path to the configuration file"""

    _ = config
    _ = console

    if len(args.parameters):
        colour.error('The "[BOLD:+config]" command does not take parameters', prefix=True)

    colour.write(os.path.relpath(args.configuration_file))

################################################################################

def mg_list(args, config, console):
    """List the top-level directories of the Git repos in the configuration"""

    _ = console

    for repo in select_git_repos(args, config):
        print(repo.name)

################################################################################

def mg_run(args, config, console):
    """Run a command in each of the working trees, optionally continuing if
       there's an error"""

    _ = console

    if not args.parameters:
        colour.error('[BOLD:+run] command - missing parameter(s)', prefix=True)

    # Run the command in each of the working trees

    for repo in select_git_repos(args, config):
        if not args.quiet:
            colour.write(f'\n[BLUE:{os.path.relpath(repo.name)}]\n')

        repo_path = absolute_repo_path(args, repo.name)

        try:
            status = subprocess.run(args.parameters, cwd=repo_path, check=True)

        except FileNotFoundError:
            err_msg = f'"[BLUE:{args.parameters[0]}]" - Command not found'
            if args.error_continue:
                colour.write(f'[RED:WARNING]: {err_msg}')
            else:
                colour.error(f'[RED:ERROR]: {err_msg}')

        except subprocess.CalledProcessError as exc:                
            if not args.error_continue:
                sys.exit(exc.returncode)

################################################################################

def run_git_command(args, config, console):
    """Run a Git command in each of the working trees, optionally continuing if
       there's an error"""

    _ = console

    for repo in select_git_repos(args, config):
        repo_command = [args.command]

        # Replace 'DEFAULT' in the command with the default branch in the repo

        for cmd in args.parameters:
            repo_command.append(branch_name(cmd, repo['default branch']))

        colour.write(f'\n[BLUE:{os.path.relpath(repo.name)}]\n')

        # Run the command in the working tree

        repo_path = absolute_repo_path(args, repo.name)

        _, status = git.git_run_status(repo_command, path=repo_path, redirect=False)

        if status and not args.error_continue:
            sys.exit(status)

################################################################################

def parse_command_line():
    """Manually parse the command line as we want to be able to accept 'multigit <OPTIONS> <+MULTIGITCOMMAND | ANY_GIT_COMMAND_WITH_OPTIONS>
       and I can't see a way to get ArgumentParser to accept arbitrary command+options"""

    args = Arguments()

    # Parse the command line, setting options in the args dataclass appropriately

    arg_list = sys.argv[1:]

    # Iterate through each lump of options (e.g. '-xyz' is a lump of 3 options and
    # '--config' is a lump containing a single option, as is just '-x')

    while arg_list and arg_list[0].startswith('-'):
        # Split a parameter into a list, so --x becomes [x] but -xyz becomes [x, y, z]
        # Note that this means that an option with a parameter must always have a space
        # between the option and the parameter (e.g. '-C path' not '-Cpath'
        # Also note that we don't support '--option=VALUE' - it must be '--option VALUE'

        arg_entry = arg_list.pop(0)
        if arg_entry.startswith('--'):
            option_list = [arg_entry[2:]]
        else:
            option_list = list(arg_entry[1:])

        # Process each option in the current option lump.
        # For short options that take a parameter (e.g. '-C PATH') we check that the option list
        # is empty as '-Cx PATH' expands to '-C', '-x PATH', not '-C PATH', '-x'

        while option_list:
            option = option_list.pop(0)

            if option in ('verbose', 'v'):
                args.verbose = True

            elif option in ('quiet', 'q'):
                args.quiet = True

            elif option in ('config', 'c'):
                if option_list:
                    colour.error('The "[BLUE:--config]" option takes a configuration file parameter', prefix=True)

                try:
                    args.default_configuration_file = arg_list.pop(0)
                except IndexError:
                    colour.error('"The [BLUE:--config]" option takes a configuration file parameter', prefix=True)

            elif option in ('repos', 'r'):
                if option_list:
                    colour.error('The "[BLUE:--repos]" option takes a repo parameter', prefix=True)

                try:
                    args.repos.append(arg_list.pop(0))
                except IndexError:
                    colour.error('The "[BLUE:--repos]" option takes a repo parameter', prefix=True)

            elif option in ('tag', 't'):
                if option_list:
                    colour.error('The "[BLUE:--tag]" option takes a tag parameter', prefix=True)

                try:
                    args.tag.append(arg_list.pop(0))
                except IndexError:
                    colour.error('The "[BLUE:--tag]" option takes a tag parameter', prefix=True)

            elif option in ('modified', 'm'):
                args.modified = True

            elif option in ('branched', 'b'):
                args.branched = True

            elif option in ('sub', 's'):
                args.subdirectories = True

            elif option in ('continue', 'o'):
                args.error_continue = True

            elif option in ('path', 'C'):
                if option_list:
                    colour.error('The "[BOLD:--path]" option takes a path parameter')

                try:
                    workingdir = arg_list.pop(0)
                    os.chdir(workingdir)
                except IndexError:
                    colour.error('The "[BOLD:-C]" option takes a path parameter', prefix=True)
                except FileNotFoundError:
                    colour.error(f'"[BOLD:--path]" - path "[BLUE:{workingdir}]" not found', prefix=True)

            elif option in ('help', 'h'):
                colour.write(HELP_INFO)
                sys.exit(0)

            else:
                colour.error(f'Invalid option: "[BOLD:{option}]"', prefix=True)

    # After the options, we either have a multigit command (prefixed with '+') or a git command
    # followed by parameter

    try:
        command = arg_list.pop(0)

        if command[0] == '+':
            args.command = command[1:]
            args.internal_command = True
        else:
            args.command = command
            args.internal_command = False

    except IndexError:
        colour.error('Missing command', prefix=True)

    # Save the command parameters

    args.parameters = arg_list

    # Locate the configuration file

    args.configuration_file = find_configuration(args.default_configuration_file)

    return args

################################################################################

COMMANDS = {
    'clone': mg_clone,
    'init': mg_init,
    'dir': mg_dir,
    'config': mg_config,
    'tag': mg_tag,
    'untag': mg_untag,
    'list': mg_list,
    'run': mg_run,
    'add': mg_add,
    'update': mg_update,
}

def main():
    """Main function"""

    # Parse the command line and santity check the command to run
    # (if it is an external command we let git worry about it)

    args = parse_command_line()

    if args.internal_command and args.command not in COMMANDS:
        colour.error(f'Invalid command "{args.command}"', prefix=True)

    # If the configuration file exists, read it

    config = configparser.ConfigParser()

    # If running the '+init' command without an existing configuration file
    # use the default one (which may have been overridden on the command line)
    # Otherwise, fail if we can't find the configuration file.

    if not args.configuration_file:
        if args.internal_command:
            if args.command == 'init':
                args.configuration_file = os.path.abspath(args.default_configuration_file)
        else:
            colour.error('Cannot locate configuration file', prefix=True)

    if args.configuration_file and os.path.isfile(args.configuration_file):
        config.read(args.configuration_file)

    # Get the console size

    try:
        console = os.get_terminal_size()
    except OSError:
        console = None
        args.quiet = True

    # Run an internal or external command-specific validation

    if args.internal_command:
        # Everything except '+init' and '+clone' requires the configuration file

        if args.command not in ('init', 'clone') and args.configuration_file is None:
            colour.error('Configuration file not found', prefix=True)

        COMMANDS[args.command](args, config, console)

        # Save the updated configuration file if it has changed (currently, only the init command will do this).

        if config and args.config_modified:
            with open(args.configuration_file, 'w', encoding='utf8') as configfile:
                config.write(configfile)

    else:
        # Run the external command, no need to update the config as it can't change here

        run_git_command(args, config, console)

################################################################################

def multigit():
    """Entry point"""

    try:
        main()

    # Catch keyboard aborts

    except KeyboardInterrupt:
        sys.exit(1)

    # Quietly fail if output was being piped and the pipe broke

    except BrokenPipeError:
        sys.exit(2)

    # Catch-all failure for Git errors

    except git.GitError as exc:
        sys.stderr.write(exc.msg)
        sys.stderr.write('\n')

        sys.exit(exc.status)

################################################################################

if __name__ == '__main__':
    multigit()
