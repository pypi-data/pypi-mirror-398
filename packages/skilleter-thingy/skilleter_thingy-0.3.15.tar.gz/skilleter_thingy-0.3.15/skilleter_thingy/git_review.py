#! /usr/bin/env python3

################################################################################
""" Thingy git-review command - menu-driven code review tool

    Copyright (C) 2020 John Skilleter

    TODO:
        * Check for nothing to review before starting curses to avoid screen flicker when we start and immediately quit.
        * Use inotify to watch files in the review and prompt to reload if they have changed
        * Better status line
        * Mouse functionality?
        * delete command
        * revert command
        * reset command
        * sort command
        * info command
        * add command
        * commit command
        * ability to embed colour changes in strings when writing with curses
        * Bottom line of the display should be menu that changes to a prompt if necc when running a command
        * Scroll, rather than jump, when moving down off the bottom of the screen - start scrolling when within 10% of top or bottom
        * Bottom line of display should show details of current file rather than help?
        * Mark/Unmark as reviewed by wildcard
        * Think that maintaining the list of files as a dictionary may be better than a list
        * Filter in/out new/deleted files
        * Universal filter dialog replace individual options and allow selection of:
            * Show:  all / deleted / updated files
            * Show:  all / wildcard match / wildcard non-match
            * Show:  all / reviewed / unreviewed files
        * Tag files for group operations (reset, delete, add, commit)
        * Handle renamed files properly - need to show old and new names, but need to return this info from git.commit_info()

    BUGS:
        * If console window is too small, popups aren't displayed - should handle this better - scrollable popup?
        * Switching between hiding reviewed files and not does not maintain cursor position
        * In hide mode, ins should not move down
        * "r" resets reviewed status for all files to False
        * If all reviewed then hidden, then move cursor around empty screen then unhide first redraw has blank line at the top.
        * Need better way of handling panels - does not cope with resize when one is active - help sort-of does,
          but doesn't pass the refrefsh down when closing - need flag for it
"""
################################################################################

import os
import sys
import argparse
import curses
import curses.panel
import pickle
import fnmatch
import subprocess
import time
from enum import IntEnum

from skilleter_modules import git
from skilleter_modules import dc_curses
from skilleter_modules import colour

################################################################################
# Colour pair codes

COLOUR_NORMAL = 1
COLOUR_STATUS = 2
COLOUR_REVIEWED = 3
COLOUR_BACKGROUND = 4

RESERVED_COLOURS = 5

# Version - used to update old pickle data

VERSION = 11

# Minimum console window size for functionality

MIN_CONSOLE_WIDTH = 32
MIN_CONSOLE_HEIGHT = 16

################################################################################

class SortOrder(IntEnum):
    """ Sort order for filename list """

    PATH = 0
    FILENAME = 1
    EXTENSION = 2
    NUM_SORTS = 3

################################################################################

class GitReviewError(BaseException):
    """ Exception for the application """

    def __init__(self, msg, status=1):
        super().__init__(msg)
        self.msg = msg
        self.status = status

################################################################################

def error(msg, status=1):
    """ Report an error """

    sys.stderr.write(f'{msg}\n')
    sys.exit(status)

################################################################################

def in_directory(root, entry):
    """ Return True if a directory lies within another """

    return os.path.commonpath([root, entry]) == root

################################################################################

def pickle_filename(working_tree, branch):
    """ Return the name of the pickle file for this git working tree """

    pickle_dir = os.path.join(os.environ['HOME'], '.config', 'git-review')

    if not os.path.isdir(pickle_dir):
        os.mkdir(pickle_dir)

    pickle_file = '%s-%s' % (working_tree.replace('/', '~'), branch.replace('/', '~'))

    return os.path.join(pickle_dir, pickle_file)

################################################################################

def read_input(prompt):
    """ Read input from the user """

    win = curses.newwin(3, 60, 3, 10)
    win.attron(curses.color_pair(COLOUR_STATUS))
    win.box()

    win.addstr(1, 1, prompt)
    curses.curs_set(2)
    win.refresh()
    curses.echo()
    text = win.getstr().decode(encoding='utf-8')
    curses.noecho()
    curses.curs_set(0)

    return text

################################################################################

class PopUp():
    """ Class to enable popup windows to be used via with statements """

    def __init__(self, screen, msg, colour=COLOUR_STATUS, waitkey=False, sleep=True, centre=True):
        """ Initialisation - just save the popup parameters """

        self.panel = None
        self.screen = screen
        self.msg = msg
        self.centre = centre
        self.colour = curses.color_pair(colour)
        self.sleep = sleep and not waitkey
        self.waitkey = waitkey
        self.start_time = 0

    def __enter__(self):
        """ Display the popup """

        lines = self.msg.split('\n')
        height = len(lines)

        width = 0
        for line in lines:
            width = max(width, len(line))

        width += 2
        height += 2

        size_y, size_x = self.screen.getmaxyx()

        window = curses.newwin(height, width, (size_y - height) // 2, (size_x - width) // 2)
        self.panel = curses.panel.new_panel(window)

        window.bkgd(' ', self.colour)
        for y_pos, line in enumerate(lines):
            x_pos = (width - len(line)) // 2 if self.centre else 1
            window.addstr(y_pos + 1, x_pos, line, self.colour)

        self.panel.top()
        curses.panel.update_panels()
        self.screen.refresh()

        self.start_time = time.monotonic()

        if self.waitkey:
            while True:
                keypress = self.screen.getch()
                if keypress == curses.KEY_RESIZE:
                    curses.panel.update_panels()
                    self.screen.refresh()
                else:
                    break

    def __exit__(self, _exc_type, _exc_value, _exc_traceback):
        """ Remove the popup """

        if self.panel:
            if self.sleep:
                elapsed = time.monotonic() - self.start_time

                if elapsed < 1:
                    time.sleep(1 - elapsed)

            del self.panel

################################################################################

# pylint: disable=too-many-instance-attributes
class GitReview():
    """ Review function as a class """

    PATH_CURRENT = 0
    PATH_WORKING_TREE = 1
    PATH_ABSOLUTE = 2

    NUM_PATH_TYPES = 3

    def __init__(self, screen, args):

        # Move to the top-level directory in the working tree

        try:
            self.current_dir = os.getcwd()
        except FileNotFoundError:
            raise GitReviewError('Unable to locate current directory')

        self.working_tree_dir = git.working_tree()

        if not self.working_tree_dir:
            raise GitReviewError('Not a git working tree')

        self.commit = git.branch() or git.current_commit()

        self.__init_key_despatch_table()

        # Commits being compared

        self.commits = args.commits
        self.paths = args.paths

        # Default sort order

        self.sort_order = SortOrder.PATH
        self.reverse_sort = False

        # Get the list of changed files restricted to the specified paths (if any)

        self.changed_files = []
        self.__update_changed_files()

        if not self.changed_files:
            msg = [f'There are no changes between {args.commits[0]} and ']

            if args.commits[1]:
                msg.append(args.commits[1])
            else:
                msg.append('local files')

            if args.paths:
                msg.append(f' in the {args.paths[0]} directory')

            raise GitReviewError(''.join(msg))

        # Get the repo name

        self.repo_name = git.project()

        # Set the attributes of the current review (some are initialised
        # when the screen is drawn)

        self.current = 0
        self.offset = 0

        self.searchstring = None

        self.screen = screen

        self.height = self.width = -1
        self.file_list_y = 1
        self.file_list_h = -1

        self.file_list = []

        self.filter_dir = self.filter_in = self.filter_out = None
        self.filter_added = self.filter_modified = self.filter_deleted = self.filter_moved = False
        self.filter_none_whitespace_only = False

        self.show_none_whitespace_stats = False

        self.finished = False
        self.status_code = 0

        # Use paths relative to the current directory

        self.path_display = self.PATH_CURRENT

        # Diff tool to use

        self.diff_tool = args.difftool or os.environ.get('DIFFTOOL', 'diffuse')

        # Reviewed files are visible

        self.hide_reviewed_files = False

        # See if we have saved state for this repo

        self.__load_state()

        # Configure the colours, set the background & hide the cursor

        self.__init_colors()

        # Generate the list of files to be shown (takes filtering into account)

        self.__update_file_list()

        # Get the current console dimensions

        self.__get_console_size()

    ################################################################################

    def __constrain_display_parameters(self):
        """ Ensure that the current display parameters are within range - easier
            to do it in one place for all of them than check individually whenever we
            change any of them """

        self.current = max(min(self.current, len(self.file_list) - 1), 0)
        self.offset = min(len(self.file_list) - 1, max(0, self.offset))

        # Keep the current entry on-screen

        if self.current >= self.offset + self.height - 2:
            self.offset = self.current
        elif self.current < self.offset:
            self.offset = self.current

    ################################################################################

    def __init_key_despatch_table(self):
        """ Initialise the keyboard despatch table """

        # The table is indexed by the keycode and contains help and a reference to the
        # function that is called when the key is pressed. For clarity, all the function
        # names are prefixed with '__key_'.

        self.key_despatch_table = \
            {
                curses.KEY_RESIZE: {'function': self.__key_console_resize},

                curses.KEY_UP: {'key': 'UP', 'help': 'Move up 1 line', 'function': self.__key_move_up},
                curses.KEY_DOWN: {'key': 'DOWN', 'help': 'Move down 1 line', 'function': self.__key_move_down},
                curses.KEY_NPAGE: {'key': 'PGDN', 'help': 'Move down by a page', 'function': self.__key_move_page_down},
                curses.KEY_PPAGE: {'key': 'PGUP', 'help': 'Move up by a page', 'function': self.__key_move_page_up},
                curses.KEY_END: {'key': 'END', 'help': 'Move to the end of the file list', 'function': self.__key_move_end},
                curses.KEY_HOME: {'key': 'HOME', 'help': 'Move to the top of the file list', 'function': self.__key_move_top},
                curses.KEY_IC: {'key': 'INS', 'help': 'Toggle review status for file', 'function': self.__key_toggle_reviewed},
                curses.KEY_F1: {'key': 'F1', 'help': 'Show help', 'function': self.__key_show_help},
                curses.KEY_F3: {'key': 'F3', 'help': 'Search for next match', 'function': self.__key_search_again},
                ord('\n'): {'key': 'ENTER', 'help': 'Review file', 'function': self.__key_review_file},
                ord(' '): {'key': 'SPACE', 'help': 'Show file details', 'function': self.__key_show_file_info},
                ord('/'): {'help': 'Search', 'function': self.__key_search_file},
                ord('F'): {'help': 'Show only files matching a wildcard', 'function': self.__key_filter_in},
                ord('f'): {'help': 'Hide files matching a wildcard', 'function': self.__key_filter_out},
                ord('-'): {'help': 'Toggle hiding deleted files', 'function': self.__key_filter_deleted},
                ord('+'): {'help': 'Toggle hiding moved files', 'function': self.__key_filter_moved},
                ord('a'): {'help': 'Toggle hiding added files', 'function': self.__key_filter_added},
                ord('*'): {'help': 'Toggle hiding modified files', 'function': self.__key_filter_modified},
                ord('w'): {'help': 'Toggle hiding files with only whitespace changes', 'function': self.__key_filter_whitespace},
                ord('W'): {'help': 'Toggle showing non-whitespace diff stats', 'function': self.__key_filter_show_non_whitespace},
                ord('m'): {'help': 'Mark files as reviewed that match a wildcard', 'function': self.__key_mark_reviewed},
                ord('M'): {'help': 'Unmark files as reviewed that match a wildcard', 'function': self.__key_mark_unreviewed},
                ord('d'): {'help': 'Only show files in the directory of the current file and subdirectories', 'function': self.__key_filter_dir},
                ord('D'): {'help': 'Only show files in the current directory and subdirectories', 'function': self.__key_filter_current_dir},
                ord('c'): {'help': 'Clear filtering', 'function': self.__key_clear_filters},
                ord('R'): {'help': 'Reload the changes and reset the review', 'function': self.__key_reload_changes_and_reset},
                ord('h'): {'help': 'Toggle hiding reviewed files', 'function': self.__key_toggle_hide_reviewed_files},
                ord('p'): {'help': 'Toggle path display', 'function': self.__key_toggle_path_display},
                ord('q'): {'help': 'Quit', 'function': self.__key_quit_review},
                ord('r'): {'help': 'Reload the changes', 'function': self.__key_reload_changes},
                ord('$'): {'help': 'Open shell at location of current file', 'function': self.__key_open_shell},
                ord('e'): {'help': 'Edit the current file', 'function': self.__key_edit_file},
                ord('s'): {'help': 'Cycle sort order', 'function': self.__key_cycle_search},
                ord('S'): {'help': 'Reverse sort order', 'function': self.__key_reverse_sort},
                3: {'help': 'Exit', 'function': self.__key_error_review},
            }

    ################################################################################

    def save_state(self):
        """ Save the current state (normally called on exit) """

        pickle_file_name = pickle_filename(self.working_tree_dir, self.commit)

        pickle_data = {'changed_files': self.changed_files,
                       'current': self.current,
                       'offset': self.offset,
                       'searchstring': self.searchstring,
                       'filter_in': self.filter_in,
                       'filter_out': self.filter_out,
                       'filter_dir': self.filter_dir,
                       'filter_deleted': self.filter_deleted,
                       'filter_moved': self.filter_moved,
                       'filter_modified': self.filter_modified,
                       'filter_added': self.filter_added,
                       'filter_whitespace': self.filter_none_whitespace_only,
                       'filter_show_non_whitespace': self.show_none_whitespace_stats,
                       'sort_order': self.sort_order,
                       'reverse_sort': self.reverse_sort,
                       'version': VERSION}

        with open(pickle_file_name, 'wb') as outfile:
            pickle.dump(pickle_data, outfile)

    ################################################################################

    def __load_state(self):
        """ Unpickle saved state if it exists """

        pickle_file_name = pickle_filename(self.working_tree_dir, self.commit)

        if os.path.isfile(pickle_file_name):
            try:
                with open(pickle_file_name, 'rb') as infile:
                    pickle_data = pickle.load(infile)

                # Extract pickle data, allowing for out-of-date pickle files
                # where the data might be missing.

                self.current = pickle_data.get('current', self.current)
                self.offset = pickle_data.get('offset', self.offset)
                self.searchstring = pickle_data.get('searchstring', self.searchstring)
                self.filter_in = pickle_data.get('filter_in', self.filter_in)
                self.filter_out = pickle_data.get('filter_out', self.filter_out)
                self.filter_dir = pickle_data.get('filter_dir', self.filter_dir)
                self.filter_deleted = pickle_data.get('filter_deleted', self.filter_deleted)
                self.filter_moved = pickle_data.get('filter_moved', self.filter_moved)
                self.filter_added = pickle_data.get('filter_added', self.filter_added)
                self.filter_modified = pickle_data.get('filter_modified', self.filter_modified)
                self.sort_order = pickle_data.get('sort_order', self.sort_order)
                self.reverse_sort = pickle_data.get('reverse_sort', self.reverse_sort)
                self.filter_none_whitespace_only = pickle_data.get('filter_none_whitespace_only', self.filter_none_whitespace_only)
                self.show_none_whitespace_stats = pickle_data.get('show_none_whitespace_stats', self.show_none_whitespace_stats)

                # Transfer the reviewed flag for each file in the pickle
                # to the corresponding current file

                for oldfile in pickle_data['changed_files']:
                    for newfile in self.changed_files:
                        if oldfile['name'] == newfile['name']:
                            newfile['reviewed'] = oldfile['reviewed']
                            break

            except (EOFError, pickle.UnpicklingError, ModuleNotFoundError, AttributeError):  # TODO: Why did I get ModuleNotFoundError or AttributeError????
                pass

            self.__constrain_display_parameters()

    ################################################################################

    def __init_colors(self):
        """ Set up the colours and initialise the display """

        curses.start_color()
        curses.use_default_colors()

        curses.init_color(15, 1000, 1000, 1000)
        curses.init_color(7, 500, 500, 500)

        if os.getenv('THINGY_DARK_MODE'):
            curses.init_pair(COLOUR_NORMAL, 15, curses.COLOR_BLACK)
            curses.init_pair(COLOUR_STATUS, 15, curses.COLOR_GREEN)
            curses.init_pair(COLOUR_REVIEWED, 15, 7)
            curses.init_pair(COLOUR_BACKGROUND, 15, curses.COLOR_BLACK)
        else:
            curses.init_pair(COLOUR_NORMAL, curses.COLOR_BLACK, 15)
            curses.init_pair(COLOUR_STATUS, 15, curses.COLOR_GREEN)
            curses.init_pair(COLOUR_REVIEWED, 7, 15)
            curses.init_pair(COLOUR_BACKGROUND, curses.COLOR_BLACK, 15)

        self.screen.bkgdset(' ', curses.color_pair(COLOUR_BACKGROUND))

        curses.curs_set(0)

        # Set up dircolor highlighting

        self.dc = dc_curses.CursesDircolors(reserved=RESERVED_COLOURS)

        # Clear and refresh the screen for a blank canvas

        self.screen.clear()
        self.screen.refresh()

    ################################################################################

    def __centre_text(self, y_pos, color, text):
        """ Centre text """

        if len(text) >= self.width:
            output = text[:self.width - 1]
        else:
            output = text

        x_pos = max(0, (self.width - len(output)) // 2)

        self.screen.attron(color)
        self.screen.hline(y_pos, 0, ' ', self.width)
        self.screen.addstr(y_pos, x_pos, output)
        self.screen.attroff(color)

    ################################################################################

    def show_file_list(self):
        """ Draw the current page of the file list """

        def format_change(prefix, value):
            """If value is 0 just return it as a string, otherwise apply the prefix and
               return it (e.g. '+' or '-')"""

            return f'{prefix}{value}' if value else '0'

        for ypos in range(0, self.file_list_h):

            normal_colour = curses.color_pair(COLOUR_NORMAL)

            if 0 <= self.offset + ypos < len(self.file_list):
                # Work out what colour to render the file details in

                current_file = self.file_list[self.offset + ypos]

                current = self.offset + ypos == self.current

                if current_file['reviewed']:
                    normal_colour = curses.color_pair(COLOUR_REVIEWED)

                # The text to render

                filename = current_file['name']

                # Diff stats, with or without non-whitespace changes

                if self.show_none_whitespace_stats:
                    added = format_change('+', current_file["non-ws added"])
                    deleted = format_change('-', current_file["non-ws deleted"])
                else:
                    added = format_change('+', current_file["added"])
                    deleted = format_change('-', current_file["deleted"])

                status = f'{current_file["status"]} {deleted:>4}/{added:>4}'

                abspath = os.path.join(self.working_tree_dir, filename)

                if self.path_display == self.PATH_CURRENT:
                    filename = os.path.relpath(abspath, self.current_dir)
                elif self.path_display == self.PATH_WORKING_TREE:
                    filename = os.path.relpath(abspath, self.working_tree_dir)
                else:
                    filename = abspath

                data = '%3d %s ' % (self.offset + ypos + 1, status)

                if len(data) + len(filename) > self.width:
                    filename = filename[:self.width - len(data) - 3] + '...'

            else:
                data = filename = ''
                current = False

            # Render the current line

            file_colour = self.dc.get_colour_pair(filename) if filename else normal_colour

            # Reverse the colours if this the cursor line

            if current:
                file_colour |= curses.A_REVERSE
                normal_colour |= curses.A_REVERSE

            # Write the prefix, filename, and, if necessary, padding

            if data:
                self.screen.addstr(self.file_list_y + ypos, 0, data, normal_colour)

                if filename:
                    self.screen.addstr(self.file_list_y + ypos, len(data), filename, file_colour)

            if len(data) + len(filename) < self.width:
                self.screen.addstr(self.file_list_y + ypos, len(data) + len(filename), ' ' * (self.width - len(data) - len(filename)), normal_colour)

        # Pop up a message if there are no visible files

        if not self.changed_files:
            with PopUp(self.screen, 'There are no changed files in the review'):
                pass

        elif not self.file_list:
            with PopUp(self.screen, 'All files are hidden - Press \'c\' to clear filters.'):
                pass

    ################################################################################

    def draw_screen(self):
        """ Draw the review screen """

        # Render status bar

        reviewed = 0
        for file in self.changed_files:
            if file['reviewed']:
                reviewed += 1

        status_bar = ['F1=Help, %d file(s), %d visible, %d reviewed, %s' % (len(self.changed_files), len(self.file_list), reviewed, self.__sort_type_msg())]

        if self.hide_reviewed_files:
            status_bar.append(', hiding reviewed files')

        if self.__active_filters:
            status_bar.append(', Active filters: %s' % self.__filter_description())

        self.__centre_text(self.status_y, curses.color_pair(COLOUR_STATUS), ''.join(status_bar))

        if not self.commits[0] and not self.commits[1]:
            title_bar = 'Reviewing local changes'
        elif not self.commits[1]:
            title_bar = 'Reviewing changes between local working tree and %s' % self.commits[0]
        else:
            title_bar = 'Reviewing changes between %s and %s' % (self.commits[0], self.commits[1])

        if self.repo_name:
            title_bar = '%s in %s' % (title_bar, self.repo_name)

        if self.paths:
            title_bar = '%s within path(s) %s' % (title_bar, ', '.join(self.paths))

        self.__centre_text(0, curses.color_pair(COLOUR_STATUS), title_bar)

    ################################################################################

    def __active_filters(self):
        """ Return true if any filters are active """

        return self.hide_reviewed_files or \
               self.filter_out or \
               self.filter_in or \
               self.filter_dir or \
               self.filter_deleted or \
               self.filter_moved or \
               self.filter_added or \
               self.filter_modified or \
               self.filter_none_whitespace_only

    ################################################################################

    def filtered(self, entry):
        """ Return True if an entry is hidden by one or more filters """

        result = False

        if self.hide_reviewed_files and entry['reviewed']:
            result = True

        elif self.filter_out and fnmatch.fnmatch(entry['name'], self.filter_out):
            result = True

        elif self.filter_dir and not in_directory(self.filter_dir, os.path.join(self.working_tree_dir, entry['name'])):
            result = True

        elif self.filter_in and not fnmatch.fnmatch(entry['name'], self.filter_in):
            result = True

        elif self.filter_moved and entry['status'] == 'R':
            result = True

        elif self.filter_deleted and entry['status'] == 'D':
            result = True

        elif self.filter_modified and entry['status'] == 'M':
            result = True

        elif self.filter_added and entry['status'] == 'A':
            result = True

        elif self.filter_none_whitespace_only and entry['non-ws added'] == 0 and entry['non-ws deleted'] == 0:
            result = True

        return result

    ################################################################################

    def __filter_description(self):
        """ Return a textual description of the active filters """

        filters = []

        if self.hide_reviewed_files:
            filters.append('reviewed')

        if self.filter_out:
            filters.append('-wildcard')

        if self.filter_in:
            filters.append('+wildcard')

        if self.filter_dir:
            filters.append('directory')

        if self.filter_moved:
            filters.append('moved')

        if self.filter_deleted:
            filters.append('deleted ')

        if self.filter_added:
            filters.append('added')

        if self.filter_modified:
            filters.append('modified')

        if self.filter_none_whitespace_only:
            filters.append('whitespace')

        if not filters:
            filters = ['none']

        return ', '.join(filters)

    ################################################################################

    def __sort_file_list(self):
        """ Sort the file list according to the current sort order """

        if self.sort_order == SortOrder.PATH:
            self.changed_files.sort(reverse=self.reverse_sort, key=lambda entry: entry['name'])
        elif self.sort_order == SortOrder.FILENAME:
            self.changed_files.sort(reverse=self.reverse_sort, key=lambda entry: os.path.basename(entry['name']))
        elif self.sort_order == SortOrder.EXTENSION:
            self.changed_files.sort(reverse=self.reverse_sort, key=lambda entry: entry['name'].split('.')[-1])

    ################################################################################

    def __update_changed_files(self):
        """ Update the list of changed files between two commits
        """

        # Get the list of changes between the two commits

        try:
            change_info = git.commit_info(self.commits[0], self.commits[1], self.paths, diff_stats=True)
        except git.GitError as exc:
            raise GitReviewError(exc.msg)

        # Save the reviewed status of existing files

        reviewed = []
        for entry in self.changed_files:
            if entry['reviewed']:
                reviewed.append(entry['name'])

        # Convert the list of changed files from a dictionary to a list, adding the
        # reviewed state of any pre-existing files

        self.changed_files = []
        for entry in change_info:
            self.changed_files.append({'name': entry,
                                       'status': change_info[entry]['status'],
                                       'reviewed': entry in reviewed,
                                       'oldname': change_info[entry]['oldname'],
                                       'added': change_info[entry]['added'],
                                       'deleted': change_info[entry]['deleted'],
                                       'non-ws added': change_info[entry]['non-ws added'],
                                       'non-ws deleted': change_info[entry]['non-ws deleted'],
                                       })

        self.__sort_file_list()

    ################################################################################

    def __update_file_list(self):
        """ Generate the file list from the list of current files """

        self.__sort_file_list()

        if self.__active_filters():
            self.file_list = [entry for entry in self.changed_files if not self.filtered(entry)]
        else:
            self.file_list = self.changed_files

    ################################################################################

    def __get_console_size(self):
        """ Get current screen size and set up locations in the display """

        self.height, self.width = self.screen.getmaxyx()

        self.status_y = self.height - 1
        self.file_list_h = self.height - 2

        if self.width < MIN_CONSOLE_WIDTH or self.height < MIN_CONSOLE_HEIGHT:
            raise GitReviewError('Console window is too small!')

    ################################################################################

    def __review(self):
        """ Diff the current file """

        if git.config_get('diff', 'tool'):
            msg = 'Running diff on %s' % self.file_list[self.current]['name']

            with PopUp(self.screen, msg, sleep=False):

                os.chdir(self.working_tree_dir)

                files = [self.file_list[self.current]['oldname'], self.file_list[self.current]['name']]

                git.difftool(self.commits[0], self.commits[1], files, self.diff_tool)

                os.chdir(self.current_dir)

                self.file_list[self.current]['reviewed'] = True

            self.__update_file_list()
        else:
            with PopUp(self.screen, 'No git difftool is configured', sleep=5):
                pass

    ################################################################################

    def __clear_filters(self):
        """ Clear all filters """

        if self.filter_out or self.filter_in or self.filter_dir or self.filter_deleted or self.filter_moved or self.filter_added or self.filter_modified or self.filter_none_whitespace_only:
            self.filter_dir = self.filter_out = self.filter_in = None
            self.filter_added = self.filter_modified = self.filter_deleted = self.filter_moved = self.filter_none_whitespace_only = False
            self.__update_file_list()

    ################################################################################

    def __reload_changes(self):
        """ Update the list of files - reloads the git status in case something
            external has changed it. """

        self.__update_changed_files()
        self.__update_file_list()

    ################################################################################

    def __run_external_command(self, cmd):
        """ Run an external command, with the current directory being that of the
            current file and shutting down curses before running the command
            then restarting it """

        directory = os.path.join(self.working_tree_dir, os.path.dirname(self.file_list[self.current]['name']))

        # The directory may not exist so hop up until we find one that does

        while not os.path.isdir(directory):
            directory = os.path.normpath(os.path.join(directory, '..'))

        # Reset the terminal, run the command and re-initialise the display for review

        self.screen.erase()
        curses.endwin()
        subprocess.run(cmd, cwd=directory)
        self.screen = curses.initscr()
        self.__reload_changes()

    ################################################################################

    def __key_console_resize(self):
        """ Update the screen size variables when the console window is resized """

        self.__get_console_size()

    ################################################################################

    def __key_show_help(self):
        """ Show help information in a pop-up window """

        # Compile list of keyboard functions

        helpinfo = []

        for key in self.key_despatch_table:
            if 'help' in self.key_despatch_table[key]:
                if 'key' in self.key_despatch_table[key]:
                    keyname = self.key_despatch_table[key]['key']
                else:
                    keyname = chr(key)

                helpinfo.append('%-5s - %s' % (keyname, self.key_despatch_table[key]['help']))

        helptext = '\n'.join(helpinfo)

        with PopUp(self.screen, helptext, waitkey=True, centre=False):
            pass

    ################################################################################

    def __key_show_file_info(self):
        """ TODO: Show information about the current file in a pop-up window """

        pass

    ################################################################################

    def __key_toggle_path_display(self):
        """ Toggle the way in which file paths are displayed """

        self.path_display = (self.path_display + 1) % self.NUM_PATH_TYPES

    ################################################################################

    def __key_quit_review(self):
        """ Quit """

        self.finished = True

    ################################################################################

    def __key_error_review(self):
        """ Quit with an error"""

        self.finished = True
        self.status_code = 1

    ################################################################################

    def __key_toggle_reviewed(self):
        """ Toggle mark file as reviewed and move down unless hide mode enabled
            and file is now hidden """

        self.file_list[self.current]['reviewed'] ^= True

        if not self.hide_reviewed_files:
            self.current += 1

        self.__update_file_list()

    ################################################################################

    def __key_toggle_hide_reviewed_files(self):
        """ Toggle the display of reviewed files """

        self.hide_reviewed_files ^= True

        with PopUp(self.screen, '%s reviewed files' % ('Hiding' if self.hide_reviewed_files else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_review_file(self):
        """ Review the current file """

        self.__review()

    ################################################################################

    def __key_reload_changes(self):
        """ Reload the changes """

        with PopUp(self.screen, 'Reload changes'):
            self.__reload_changes()

    ################################################################################

    def __key_edit_file(self):
        """ Edit the current file """

        editor = os.environ.get('EDITOR', 'vim')
        self.__run_external_command([editor, os.path.basename(self.file_list[self.current]['name'])])

    ################################################################################

    def __key_open_shell(self):
        """ Open a shell in the same directory as the current file
        """

        self.__run_external_command([os.getenv('SHELL')])
        self.__get_console_size()

    ################################################################################

    def __key_reload_changes_and_reset(self):
        """ Reload changes and reset the review status of each file,
            the current file and unhide reviewed files """

        with PopUp(self.screen, 'Reload changes & reset reviewed status'):

            self.__update_changed_files()

            for entry in self.changed_files:
                entry['reviewed'] = False

            self.current = self.offset = 0
            self.hide_reviewed_files = False
            self.__clear_filters()
            self.__update_file_list()

    ################################################################################

    def __search_next_match(self):
        """ Search for the next match with the current search string """

        for i in list(range(self.current + 1, len(self.file_list))) + list(range(0, self.current)):
            if fnmatch.fnmatch(self.file_list[i]['name'], self.searchstring):
                self.current = i
                break

    ################################################################################

    def __key_search_file(self):
        """ Prompt for a search string and find a match """

        self.searchstring = '*' + read_input('Search for: ') + '*'

        self.__search_next_match()

    ################################################################################

    def __key_search_again(self):
        """ Prompt for a search string if none defined then search """

        if self.searchstring:
            self.__search_next_match()
        else:
            self.__key_search_file()

    ################################################################################

    def __key_filter_out(self):
        """ Hide files matching a wildcard """

        filter_out = read_input('Hide files matching: ')

        if filter_out:
            self.filter_out = filter_out
            self.filter_in = None
            self.__update_file_list()

    ################################################################################

    def __key_filter_in(self):
        """ Only show files matching a wildcard """

        filter_in = read_input('Only show files matching: ')

        if filter_in:
            self.filter_in = filter_in
            self.filter_out = None
            self.__update_file_list()

    ################################################################################

    def __key_filter_moved(self):
        """ Show/Hide moved files """

        self.filter_moved = not self.filter_moved

        with PopUp(self.screen, '%s moved files' % ('Hiding' if self.filter_moved else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_filter_deleted(self):
        """ Show/Hide deleted files """

        self.filter_deleted = not self.filter_deleted

        with PopUp(self.screen, '%s deleted files' % ('Hiding' if self.filter_deleted else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_filter_modified(self):
        """ Show/Hide modified files """

        self.filter_modified = not self.filter_modified

        with PopUp(self.screen, '%s modified files' % ('Hiding' if self.filter_modified else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_filter_added(self):
        """ Show/Hide added files """

        self.filter_added = not self.filter_added

        with PopUp(self.screen, '%s added files' % ('Hiding' if self.filter_added else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_filter_whitespace(self):
        """ Show/Hide files with only whitespace changes """

        self.filter_none_whitespace_only = not self.filter_none_whitespace_only

        with PopUp(self.screen, '%s files with only whitespace changes' % ('Hiding' if self.filter_none_whitespace_only else 'Showing')):
            self.__update_file_list()

    ################################################################################

    def __key_filter_show_non_whitespace(self):
        """ Show full or non-whitespace diff stats """

        self.show_none_whitespace_stats = not self.show_none_whitespace_stats

        with PopUp(self.screen, 'Showing non-whitespace diff stats' if self.show_none_whitespace_stats else 'Showing full diff stats'):
            self.__update_file_list()

    ################################################################################

    def __key_mark_reviewed(self):
        """ Mark files as reviewed that match a wildcard """

        reviewed = read_input('Mark files matching: ')

        if reviewed:
            for entry in self.changed_files:
                if fnmatch.fnmatch(entry['name'], reviewed):
                    entry['reviewed'] = True
            self.__update_file_list()

    ################################################################################

    def __key_mark_unreviewed(self):
        """ Unmark files as reviewed that match a wildcard """

        reviewed = read_input('Unmark files matching: ')

        if reviewed:
            for entry in self.changed_files:
                if fnmatch.fnmatch(entry['name'], reviewed):
                    entry['reviewed'] = False
            self.__update_file_list()

    ################################################################################

    def __key_filter_dir(self):
        """ Only show files in or under the current file's directory """

        self.filter_dir = os.path.dirname(os.path.join(self.working_tree_dir, self.file_list[self.current]['name']))

        with PopUp(self.screen, f'Only showing files in {self.filter_dir}'):
            self.__update_file_list()

    ################################################################################

    def __key_filter_current_dir(self):
        """ Only show files in or under the current directory """

        self.filter_dir = self.current_dir

        with PopUp(self.screen, f'Only showing files in {self.filter_dir}'):
            self.__update_file_list()

    ################################################################################

    def __key_clear_filters(self):
        """ Clear filters """

        with PopUp(self.screen, 'Cleared all filters'):
            self.__clear_filters()

    ################################################################################

    def __key_move_down(self):
        """ Move down 1 line """

        self.current += 1

    ################################################################################

    def __key_move_up(self):
        """ Move up 1 line """

        self.current -= 1

    ################################################################################

    def __key_move_page_down(self):
        """ Move down by a page """

        pos = self.current - self.offset
        self.offset += self.file_list_h - 1
        self.current = self.offset + pos

    ################################################################################

    def __key_move_page_up(self):
        """ Move up by a page """

        pos = self.current - self.offset
        self.offset -= self.file_list_h - 1
        self.current = self.offset + pos

    ################################################################################

    def __key_move_top(self):
        """ Move to the top of the file list """

        self.current = 0

    ################################################################################

    def __key_move_end(self):
        """ Move to the end of the file list """

        self.current = len(self.file_list) - 1

    ################################################################################

    def __key_cycle_search(self):
        """ Cycle through the various sort options """

        self.sort_order = (self.sort_order + 1) % SortOrder.NUM_SORTS

        self.__update_sort()

    ################################################################################

    def __sort_type_msg(self):
        if self.sort_order == SortOrder.PATH:
            sort_type = 'path'
        elif self.sort_order == SortOrder.FILENAME:
            sort_type = 'filename'
        if self.sort_order == SortOrder.EXTENSION:
            sort_type = 'extension'

        if self.reverse_sort:
            msg = f'Reverse-sorting by {sort_type}'
        else:
            msg = f'Sorting by {sort_type}'

        return msg

    ################################################################################

    def __update_sort(self):

        msg = self.__sort_type_msg()

        with PopUp(self.screen, msg):
            self.__update_file_list()

    ################################################################################

    def __key_reverse_sort(self):
        """ Reverse the current sort order """

        self.reverse_sort = not self.reverse_sort

        self.__update_sort()

    ################################################################################

    def done(self):
        """ Quit """

        return self.finished

    ################################################################################

    def handle_keypress(self, keypress):
        """ Handle a key press """

        if keypress in self.key_despatch_table:
            self.key_despatch_table[keypress]['function']()

            # Keep the current entry in range

            self.__constrain_display_parameters()

################################################################################

def parse_command_line():
    """ Parse the command line, return the arguments """

    parser = argparse.ArgumentParser(description='Menu-driven Git code review tool')

    parser.add_argument('--commit', '-c', type=str, help='Compare the specified commit with its parent')
    parser.add_argument('--branch', '-b', type=str, help='Compare the specified commit to branch point on specified branch')
    parser.add_argument('--change', '-C', action='store_true', help='Compare the current commit with its parent')
    parser.add_argument('--debug', '-d', action='store_true', help='Start a debug session over Telnet using pudb')
    parser.add_argument('--dir', action='store', help='Work in the specified directory')
    parser.add_argument('--difftool', type=str, default=None, help='Override the default git diff tool')

    parser.add_argument('commits', nargs='*', help='Commit(s) or paths to compare')

    args = parser.parse_args()

    args.paths = None

    if args.debug:
        from pudb.remote import set_trace
        set_trace()

    # Move to a new directory, if required

    if args.dir:
        os.chdir(args.dir)

    # Make sure that we're actually in a git working tree

    if not git.working_tree():
        colour.error('Not a git repository', prefix=True)

    # -C/--change is shorthand for '--commit HEAD^'

    if args.change:
        if args.commits:
            colour.error('The -C/--change option does not take parameters', prefix=True)

        args.commits = ['HEAD^']

    # Validate the parameters (if any) as commits or paths.
    # If the parameter matches a commit (SHA1, tag or branch) then assume it is one
    # If it matches an existing path, assume that is what it is and don't permit
    # following parameters to be commits.
    # Otherwise fail with an error.

    if args.commits:
        paths = []
        commits = []
        parsing_commits = True

        for entry in args.commits:
            if parsing_commits:
                matches = git.matching_commit(entry)

                if len(matches) == 1:
                    commits.append(matches[0])
                else:
                    parsing_commits = False

            if not parsing_commits:
                # TODO: Disabled as this does not work with files: elif os.path.exists(entry):
                if os.path.isdir(entry):
                    paths.append(entry)
                    parsing_commits = False
                else:
                    colour.error(f'Invalid path/commit: {entry}', prefix=True)

        args.commits = commits
        args.paths = paths

    # Validate the commits & paths

    if len(args.commits) > 2:
        colour.error('No more than 2 commits can be specified', prefix=True)

    if (args.branch or args.commit) and args.commits:
        colour.error('Additional commits should not be specified in conjunction with the -b/--branch option', prefix=True)

    if args.commit and args.branch:
        colour.error('The -c/--commit and -b/--branch options are mutually exclusive', prefix=True)

    # If the -c/--commit option is used, then review against its parent
    # If the -b/--branch option is used, then review against the oldest common ancestor
    # If no parameters or -c/--commit option then review against HEAD

    if args.branch:
        try:
            args.commits = [git.find_common_ancestor('HEAD', args.branch)]
        except git.GitError as exc:
            colour.error(exc, status=exc.status, prefix=True)

    elif args.commit:
        args.commits = ['%s^' % args.commit, args.commit]

    elif not args.commits:
        args.commits = ['HEAD']

    # Validate the commits we are comparing (yes, this partially duplicates the parameter check code but this
    # covers defaults and the -c/--commit parameter, if used).

    for i, entry in enumerate(args.commits):
        matches = git.matching_commit(entry)

        if matches:
            if len(matches) == 1:
                args.commits[i] = matches[0]
            else:
                colour.error(f'Multiple commits match {entry}', prefix=True)
        else:
            colour.error(f'{entry} is not a valid commit ID', prefix=True)

    # Things work easier if we always have two commits to compare

    if len(args.commits) == 1:
        args.commits.append(None)

    return args

################################################################################

def main(screen, args):
    """ Parse the command line and run the review """

    review = GitReview(screen, args)

    while not review.done():
        review.draw_screen()

        review.show_file_list()

        keypress = screen.getch()

        review.handle_keypress(keypress)

    review.save_state()

    return review.status_code

################################################################################

def git_review():
    """Entry point"""

    try:
        command_args = parse_command_line()

        statcode = curses.wrapper(main, command_args)

        sys.exit(statcode)

    except KeyboardInterrupt:
        sys.exit(1)

    except BrokenPipeError:
        sys.exit(2)

    except GitReviewError as exc:
        sys.stderr.write(exc.msg)
        sys.stderr.write('\n')
        sys.exit(exc.status)

################################################################################

if __name__ == '__main__':
    git_review()
