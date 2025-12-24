#! /usr/bin/env python3

################################################################################
""" Thingy file manager

    Copyright (C) 2022 John Skilleter

    Stuff not working:

        BUG: 1. If both panes showing same directory, non-current pane doesn't update if current one changes
        BUG: 2. Allows an attempt to move/copy directory into its own subdirectory
        BUG: 2. If pane showing a subdirectory and parent is deleted in other pane nothing updates
        BUG: 3. Inefficient redraw (better, but could be better, although curses hides most of the inefficiencies)
        BUG: 4. Many untrapped exceptions (e.g. deleting stuff)
        BUG: 6. Slightly odd scrolling at page top/bottom

    Stuff that's been fixed but not fully tested:

        FIXED: 1. If a tagged file is hidden by a filter it shouldn't be processed by move/copy/delete - check this

    DONE:
        DONE: 1. If you exit a directory via Backspace then re-enter it hasn't saved the current position
        DONE: 1. Implement inotify as background thread as it is far too slow to run everytime we process a keypress
        DONE: 1. When changing direcrories, save current location in current directory and return there when we return to the same directory
        DONE: 2. Copy (file or directory)
        DONE: 2. Move (file or directory)
        DONE: 2. Use inotify to check for updates and update panes
        DONE: 3. Directory delete - with warning if directory not empty) and/or count of total number of files

    CONSIDERED, BUT WON'T DO:
        NOPE: 3. Look at lfm source code to see how it does things (check licence for compatibility first) - Have looked at feature list and 'borrowed' some
        NOPE: 8. Multiple panes (fixed at 2 to start with)
        NOPE: 9. GUI version

    TODO:
        TODO: 1. Config file - keyboard config, override apps used to open particular file types
        TODO: 2. '>' marker on current file or don't use background colours except for current file
        TODO: 2. Scrolling help window
        TODO: 2. Wildcard tagging/untagging
        TODO: 2. ^R - redraw
        TODO: 3. '.' show/hide hidden files
        TODO: 3. '=' sets other pane to same directory as current one
        TODO: 3. Allow copy/move to overwrite files (prompt first, with Y/N/A)
        TODO: 3. Configurable shortcuts
        TODO: 3. Create directory
        TODO: 3. Menu for things like sort order
        TODO: 3. Search - name or content
        TODO: 3. Sort by date, size, owner, group, cheese preference, etc.
        TODO: 3. Tagging - invert selection
        TODO: 3. Use inotify and cache file data, or at least use inotify and update when current directory changes
        TODO: 3. Use pygments/pymentize for syntax highlighting in file viewer
        TODO: 3. When moving between panes move to same line on screen in new pane if possible
        TODO: 4. Bookmarks for directories
        TODO: 4. F12 = file info = show permissions, times, etc. in pop-up
        TODO: 4. File list - proper formatting, nicer dates/times, support uid, gid, mode, size adjusted for KiB/MiB/GiB and with commas
        TODO: 4. File search/grep
        TODO: 4. Highlight current pane - draw border around it?
        TODO: 4. Main loop is inefficient - we call filemanager.show_file_list() on every event
        TODO: 4. Menu system with menu bar and pull-down menus
        TODO: 4. Rename
        TODO: 4. Tab to switch panes, left arrow to move up a directory level, right arrow to move into directory under cursor (if it is one)
        TODO: 4. Treat symlinks to directories as directories not files
        TODO: 4. ^F+string = go to first entry matching 'string'
        TODO: 4. ^N = go to next ^F/^S match
        TODO: 4. ^S+strign = go to first entry starting with 'string'
        TODO: 4. ^U - Swap panes
        TODO: 5. Built-in editor/viewer for text files (can use for help)
        TODO: 5. Create symlink
        TODO: 5. F11 = directory info = show number of files, size
        TODO: 5. Option to echo cwd on exit so shell can pick up current location as pwd
        TODO: 5. Scroll bar or per-pane status line showing current file index and number of files
        TODO: 5. Shell window - enter command and run it in current tab
        TODO: 5. Status at bottom of pane, tagged, hiddenm, total files & directories
        TODO: 5. Verify it works in 16-colour terminal
        TODO: 6. Config file - saves bookmarks, current keyboard config
        TODO: 6. Configuration load/save - global, not directory-specific
        TODO: 6. Control file details visible (user/group/size/permissions/times)
        TODO: 6. F12 window with edit option to change permissions, owner
        TODO: 6. Consider splitting TFM out from skilleter-thingy as a separate project; I don't think there's any overlap with the rest of skilleter-thingy
        TODO: 6. File viewer
        TODO: 6. File/directory info
        TODO: 6. More command line parameters & options (directrories, search order, filters)
        TODO: 6. Open/close tab
        TODO: 6. Pickle and unpickle state
        TODO: 6. Save settings in config file - bookmarks, key configuration, colours, etc.
        TODO: 6. Search for file, wildcards, show list, select and move to directory
        TODO: 6. Swap panes
        TODO: 6. Synchronised scrolling across multiple panes
        TODO: 6. Tree view
        TODO: 6. Tree view for navigation
        TODO: 6. Update progress when copying/moving/deleting
        TODO: 7. Configurable colours
        TODO: 7. Navigation by partial name (press prefix then start typing name and it moves to matching file)
        TODO: 7. Use pads for panes (might be expensive in directories with lots of files)
        TODO: 8. Allow copy/move to merge directories
        TODO: 8. Better help
        TODO: 8. Chmod/chown
        TODO: 8. Directory bookmarks with selection menu
        TODO: 8. Special environment vars in shell window  - e.g. $:d for current directory $:od for current directory in other pane, $:f - current file $:of current file in other pane
        TODO: 8. Touch file
        TODO: 8. Trying to suspend tfm, run a command in the current shell and resume it doesn't work since I added threads for keyboard and inotify
        TODO: 9. Git commands
        TODO: 9. Mouse support
        TODO: 9. multigit integration

"""
################################################################################

import os
import sys
import argparse
import curses
import subprocess
import shutil
from collections import defaultdict
import threading
import queue

from skilleter_modules import popup
from skilleter_modules import tfm_pane

################################################################################
# Colour pair codes

COLOUR_NORMAL = 1
COLOUR_STATUS = 2
COLOUR_BACKGROUND = 3
COLOUR_WARNING = 4

RESERVED_COLOURS = 5

# TODO: Find a better way of sharing colours with the tfm_pane class

PANE_COLOURS = {'normal': 1, 'status': 2, 'background': 3, 'warning': 4, 'reserved_colours': 5}

# Version - used to update old pickle data

VERSION = 1

# Minimum console window size for functionality

MIN_CONSOLE_WIDTH = 64
MIN_CONSOLE_HEIGHT = 16

# Number of panes (TODO: Make this variable, rather than fixed)

NUM_PANES = 2

# Function key labels

FN_KEY_FN = ('Help', 'View', 'Search', 'Edit', 'Copy', 'Move', 'Mkdir', 'Delete', 'Rename', 'Quit')

################################################################################

class FileManagerError(BaseException):
    """ Exception for the application """

    def __init__(self, msg, status=1):
        super().__init__(msg)
        self.msg = msg
        self.status = status

################################################################################

def error(msg, status=1):
    """ Report an error """

    sys.stderr.write('%s\n' % msg)
    sys.exit(status)

################################################################################

def in_directory(root, entry):
    """ Return True if a directory lies within another """

    return os.path.commonpath([root, entry]) == root

################################################################################

def pickle_filename(working_tree):
    """ Return the name of the pickle file for this working tree """

    pickle_dir = os.path.join(os.environ['HOME'], '.config', 'tfm')

    if not os.path.isdir(pickle_dir):
        os.mkdir(pickle_dir)

    pickle_file = working_tree.replace('/', '~')

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

def keyboard_wait(self):
    """Thread to wait for keypresses and post them onto the event queue"""

    while True:
        keypress = self.screen.getch()
        self.event_queue.put(('key', keypress))

################################################################################

class FileManager():
    """ Review function as a class """

    def __init__(self, args):
        """ Initialisation """

        _ = args

        # Move to the top-level directory in the working tree

        self.init_key_despatch_table()

        # Initialise the screen

        self.screen = curses.initscr()

        # Configure the colours, set the background & hide the cursor

        self.init_colors()

        # See if we have saved state for this repo

        self.load_state()

        # Create the queue for keyboard, file events

        self.event_queue = queue.Queue()

        # Start the keyboard thread

        keyboard_thread = threading.Thread(target=keyboard_wait, args=(self, ), daemon=True)
        keyboard_thread.start()

        # Create the panes

        self.panes = []

        for i in range(NUM_PANES):
            self.panes.append(tfm_pane.Pane(i, NUM_PANES, PANE_COLOURS, self.event_queue))

        self.current_pane = self.panes[0]
        self.pane_index = 0

        self.searchstring = None

        # Directory history

        self.directory_history = defaultdict(str)

        # Get the current console dimensions

        self.update_console_size()

        self.finished = False

    ################################################################################

    def init_key_despatch_table(self):
        """ Initialise the keyboard despatch table """

        # The table is indexed by the keycode and contains help and a reference to the
        # function that is called when the key is pressed. For clarity, all the function
        # names are prefixed with '__key_'.
        # Note that the function key definitions should match FN_KEY_FN

        self.key_despatch_table = \
            {
                curses.KEY_RESIZE: {'function': self.key_console_resize},

                curses.KEY_UP: {'key': 'UP', 'help': 'Move up 1 line', 'function': self.key_move_up},
                curses.KEY_DOWN: {'key': 'DOWN', 'help': 'Move down 1 line', 'function': self.key_move_down},
                curses.KEY_LEFT: {'key': 'LEFT', 'help': 'Move to previous pane', 'function': self.key_switch_previous_pane},
                curses.KEY_RIGHT: {'key': 'RIGHT', 'help': 'Move to next pane', 'function': self.key_switch_next_pane},
                curses.KEY_NPAGE: {'key': 'PGDN', 'help': 'Move down by a page', 'function': self.key_move_page_down},
                ord('\t'): {'key': 'TAB', 'help': 'Switch panes', 'function': self.key_switch_next_pane},
                curses.KEY_PPAGE: {'key': 'PGUP', 'help': 'Move up by a page', 'function': self.key_move_page_up},
                curses.KEY_END: {'key': 'END', 'help': 'Move to the end of the file list', 'function': self.key_move_end},
                curses.KEY_HOME: {'key': 'HOME', 'help': 'Move to the top of the file list', 'function': self.key_move_top},
                curses.KEY_IC: {'key': 'INS', 'help': 'Tag file/directory', 'function': self.key_tag},
                curses.KEY_DC: {'key': 'DEL', 'help': 'Delete current or tagged files/directories', 'function': self.key_delete},
                curses.KEY_BACKSPACE: {'key': 'BACKSPACE', 'help': 'Move to the parent directory', 'function': self.key_parent},

                curses.KEY_F1: {'key': 'F1', 'help': 'Show help', 'function': self.key_show_help},
                curses.KEY_F2: {'key': 'F2', 'help': 'View file', 'function': self.key_view_file},
                curses.KEY_F3: {'key': 'F3', 'help': 'Search for next match', 'function': self.key_search_again},
                curses.KEY_F4: {'key': 'F4', 'help': 'Edit file', 'function': self.key_edit_file},
                curses.KEY_F5: {'key': 'F5', 'help': 'Copy', 'function': self.key_copy},
                curses.KEY_F6: {'key': 'F6', 'help': 'Move', 'function': self.key_move},
                curses.KEY_F7: {'key': 'F7', 'help': 'MkDir', 'function': self.key_mkdir},
                curses.KEY_F8: {'key': 'F8', 'help': 'Delete', 'function': self.key_delete},
                curses.KEY_F9: {'key': 'F9', 'help': 'Rename', 'function': self.key_rename},
                curses.KEY_F10: {'key': 'F10', 'help': 'Quit', 'function': self.key_quit_review},

                ord('\n'): {'key': 'ENTER', 'help': 'Change directory', 'function': self.key_open_file_or_directory},
                ord(' '): {'key': 'SPACE', 'help': 'Show file details', 'function': self.key_show_file_info},
                ord('/'): {'help': 'Search', 'function': self.key_search_file},
                ord('F'): {'help': 'Show only files matching a wildcard', 'function': self.key_filter_in},
                ord('f'): {'help': 'Hide files matching a wildcard', 'function': self.key_filter_out},
                ord('.'): {'help': 'Toggle display of hidden files', 'function': self.key_toggle_hidden},
                ord('m'): {'help': 'Tag files that match a wildcard', 'function': self.key_wild_tag},
                ord('M'): {'help': 'Untag files that match a wildcard', 'function': self.key_wild_untag},
                ord('c'): {'help': 'Clear tags', 'function': self.key_clear_tags},
                ord('R'): {'help': 'Reload', 'function': self.key_reload_changes_and_reset},
                ord('q'): {'help': 'Quit', 'function': self.key_quit_review},
                ord('$'): {'help': 'Open shell at location of current file', 'function': self.key_open_shell},
                ord('e'): {'help': 'Edit the current file', 'function': self.key_edit_file},
                ord('v'): {'help': 'View the current file', 'function': self.key_view_file},
                ord('s'): {'help': 'Cycle sort order', 'function': self.key_cycle_sort},
                ord('S'): {'help': 'Reverse sort order', 'function': self.key_reverse_sort},
            }

    ################################################################################

    def save_state(self):
        """ Save the current state (normally called on exit) """

        pass

    ################################################################################

    def load_state(self):
        """ Unpickle saved state if it exists """

        pass

    ################################################################################

    def init_colors(self):
        """ Set up the colours and initialise the display """

        curses.start_color()
        curses.use_default_colors()

        curses.init_color(15, 1000, 1000, 1000)

        if os.getenv('THINGY_DARK_MODE'):
            curses.init_pair(COLOUR_NORMAL, 15, curses.COLOR_BLACK)
            curses.init_pair(COLOUR_STATUS, 15, curses.COLOR_GREEN)
            curses.init_pair(COLOUR_BACKGROUND, 15, curses.COLOR_BLACK)
            curses.init_pair(COLOUR_WARNING, 15, curses.COLOR_RED)
        else:
            curses.init_pair(COLOUR_NORMAL, curses.COLOR_BLACK, 15)
            curses.init_pair(COLOUR_STATUS, 15, curses.COLOR_GREEN)
            curses.init_pair(COLOUR_BACKGROUND, curses.COLOR_BLACK, 15)
            curses.init_pair(COLOUR_WARNING, 15, curses.COLOR_RED)

        self.screen.bkgdset(' ', curses.color_pair(COLOUR_BACKGROUND))

        curses.curs_set(0)

        # Clear and refresh the screen for a blank canvas

        self.screen.clear()
        self.screen.refresh()

    ################################################################################

    def centre_text(self, y_pos, color, text):
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

    def draw_screen(self):
        """ Draw the review screen """

        # Render status bar

        status_bar = self.current_pane.sort_type_msg()

        # TODO: Each pane needs a status bar with this info on
        # if self.out_filter or self.in_filter:
        #    status_bar = '%s, active filters: %s' % (status_bar, self.filter_description())

        self.centre_text(self.status_y, curses.color_pair(COLOUR_STATUS), status_bar)

        title_bar = 'Thingy File Manager'

        self.centre_text(0, curses.color_pair(COLOUR_STATUS), title_bar)

        fn_width = self.width // 10

        self.screen.move(self.status_y + 1, 0)
        self.screen.clrtoeol()

        for fn_key in range(1, 11):
            self.screen.attron(curses.color_pair(COLOUR_STATUS))
            self.screen.addstr(self.status_y + 1, (fn_key - 1) * fn_width, f'F{fn_key}')
            self.screen.attron(curses.color_pair(COLOUR_BACKGROUND))
            self.screen.addstr(self.status_y + 1, (fn_key - 1) * fn_width + 3, f'{FN_KEY_FN[fn_key-1]}')

        self.screen.refresh()

    ################################################################################

    def update_console_size(self):
        """ Get current screen size and set up locations in the display """

        self.height, self.width = self.screen.getmaxyx()

        self.status_y = self.height - 2

        for pane in self.panes:
            pane.set_pane_coords(1, 0, self.height - 3, self.width)

        if self.width < MIN_CONSOLE_WIDTH or self.height < MIN_CONSOLE_HEIGHT:
            raise FileManagerError('Console window is too small!')

    ################################################################################

    def run_external_command(self, cmd):
        """ Run an external command, with the current directory being that of the
            current file and shutting down curses before running the command
            then restarting it """

        # Run the command in a separate xterm

        cmd = ['xterm', '-e'] + cmd

        try:
            subprocess.run(cmd, cwd=self.current_pane.get_current_dir(), check=True)
        except subprocess.CalledProcessError as exc:
            return_code = exc.returncode
        else:
            return_code = 0

        # Reload in case we've missed something

        for pane in self.panes:
            pane.reload_changes()

        self.key_console_resize()

        if return_code:
            with popup.PopUp(self.screen, f'Command returned status={return_code}', COLOUR_STATUS):
                pass

    ################################################################################

    def move_to_dir(self, dirname):
        """Move to a different directory, tracking directory history"""

        current_dir = self.current_pane.get_current_dir()

        self.directory_history[current_dir] = os.path.basename(self.current_pane.get_current_file()['name'])
        new_dir = os.path.abspath(os.path.join(current_dir, dirname))

        self.current_pane.set_current_dir(new_dir)
        self.current_pane.reload_changes()
        self.current_pane.move_to_file(self.directory_history[new_dir])

    ################################################################################

    def key_console_resize(self):
        """ Update the screen size variables when the console window is resized """

        self.update_console_size()
        self.draw_screen()
        self.screen.refresh()

    ################################################################################

    def key_show_help(self):
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

        with popup.PopUp(self.screen, helptext, COLOUR_STATUS, waitkey=True, centre=False):
            pass

    ################################################################################

    def key_show_file_info(self):
        """ TODO: Show information about the current file in a pop-up window """

        pass

    ################################################################################

    def key_switch_next_pane(self):
        """ Switch to the next pane """

        self.pane_index = (self.pane_index + 1) % NUM_PANES
        self.current_pane = self.panes[self.pane_index]

    ################################################################################

    def get_next_pane(self):
        """ Return the handle of the next pane """

        next_pane_index = (self.pane_index + 1) % NUM_PANES

        return self.panes[next_pane_index]

    ################################################################################

    def key_switch_previous_pane(self):
        """ Switch to the previous pane """

        self.pane_index = (self.pane_index - 1) % NUM_PANES
        self.current_pane = self.panes[self.pane_index]

    ################################################################################

    def key_open_file_or_directory(self):
        """ Open the current file or change directory """

        current_file = self.current_pane.get_current_file()

        if current_file['isdir']:
            self.move_to_dir(current_file['name'])
        else:
            # TODO: Needs to work on Mac and Windows (well, Mac, anyway!)
            self.run_external_command(['xdg-open', current_file['name']])
            # self.open_file(self.filtered_file_indices[self.current]['name'])

    ################################################################################

    def key_parent(self):
        """ Move to the parent directory """

        self.move_to_dir('..')

    ################################################################################

    def key_delete(self):
        """ Delete the current or tagged files or directories """

        files_to_delete = self.current_pane.get_tagged_files()

        with popup.PopUp(self.screen, f'Deleting {len(files_to_delete)} files...', COLOUR_STATUS):
            for entry in files_to_delete:
                if entry['isdir']:
                    shutil.rmtree(entry['name'])
                else:
                    os.unlink(entry['name'])

        self.current_pane.update_files()

    ################################################################################

    def key_move(self):
        """ Move the current or tagged files to the directory in the next pane """

        next_pane = self.get_next_pane()

        files_to_move = self.current_pane.get_tagged_files()

        current_dir = self.current_pane.get_current_dir()

        destination_dir = next_pane.get_current_dir()

        if current_dir == destination_dir:
            with popup.PopUp(self.screen, 'Source and destination directories are the same', COLOUR_WARNING):
                pass
        else:
            for entry in files_to_move:
                destination = os.path.join(destination_dir, os.path.basename(entry['name']))
                if os.path.exists(destination):
                    name = os.path.basename(entry['name'])

                    with popup.PopUp(self.screen, f'{name} already exists in the destination directory', COLOUR_WARNING):
                        pass
                    return

            with popup.PopUp(self.screen, f'Moving {len(files_to_move)} files/directories', COLOUR_STATUS):
                for entry in files_to_move:
                    shutil.move(entry['name'], os.path.join(destination_dir, os.path.basename(entry['name'])))

        self.current_pane.update_files()
        next_pane.update_files()

    ################################################################################

    def key_copy(self):
        """ Copy the current or tagged files to the directory in the next pane """

        next_pane = self.get_next_pane()

        files_to_copy = self.current_pane.get_tagged_files()

        current_dir = self.current_pane.get_current_dir()

        destination_dir = next_pane.get_current_dir()

        if current_dir == destination_dir:
            with popup.PopUp(self.screen, 'Source and destination directories are the same', COLOUR_WARNING):
                pass
        else:
            for entry in files_to_copy:
                destination = os.path.join(destination_dir, os.path.basename(entry['name']))
                if os.path.exists(destination):
                    name = os.path.basename(entry['name'])

                    with popup.PopUp(self.screen, f'{name} already exists in the destination directory', COLOUR_WARNING):
                        pass
                    return

            with popup.PopUp(self.screen, f'Copying {len(files_to_copy)} files/directories', COLOUR_STATUS):
                for entry in files_to_copy:
                    if entry['isdir']:
                        shutil.copytree(entry['name'], os.path.join(destination_dir, os.path.basename(entry['name'])))
                    else:
                        shutil.copy2(entry['name'], destination_dir)

        self.current_pane.update_files()
        next_pane.update_files()

    ################################################################################

    def key_rename(self):
        """ Rename current or tagged files or directories """

        # TODO
        pass

    ################################################################################

    def key_quit_review(self):
        """ Quit """

        self.finished = True

    ################################################################################

    def key_edit_file(self):
        """ Edit the current file """

        editor = os.environ.get('EDITOR', 'vim')
        self.run_external_command([editor, os.path.basename(self.current_pane.get_current_file()['name'])])

    ################################################################################

    def key_view_file(self):
        """ Edit the current file
            TODO: Write internal file viewer """

        pager = os.environ.get('TFM_PAGER', os.environ.get('PAGER', 'more'))
        self.run_external_command([pager, os.path.basename(self.current_pane.get_current_file()['name'])])

    ################################################################################

    def key_mkdir(self):
        """ TODO: mkdir """
        pass

    ################################################################################

    def key_wild_tag(self):
        """ TODO: """
        pass

    ################################################################################

    def key_wild_untag(self):
        """ TODO: """
        pass

    ################################################################################

    def key_clear_tags(self):
        """ Untag everything """

        self.current_pane.untag()

    ################################################################################

    def key_open_shell(self):
        """ Open a shell in the same directory as the current file
        """

        self.run_external_command([os.getenv('SHELL')])
        self.update_console_size()

    ################################################################################

    def key_reload_changes_and_reset(self):
        """ Reload changes and reset the review status of each file,
            the current file and unhide reviewed files """

        with popup.PopUp(self.screen, 'Reload changes & reset reviewed status', COLOUR_STATUS):
            self.current_pane.clear_filters()
            self.current_pane.update_files()
            self.current_pane.move_top()

    ################################################################################

    def key_search_file(self):
        """ Prompt for a search string and find a match """

        self.searchstring = '*' + read_input('Search for: ') + '*'

        self.current_pane.search_match(self.searchstring)

    ################################################################################

    def key_search_again(self):
        """ Prompt for a search string if none defined then search """

        if self.searchstring:
            self.current_pane.search_next_match()
        else:
            self.key_search_file()

    ################################################################################

    def key_filter_out(self):
        """ Hide files matching a wildcard """

        filter_out = read_input('Hide files matching: ')

        if filter_out:
            self.current_pane.filter_out(filter_out)

    ################################################################################

    def key_filter_in(self):
        """ Only show files matching a wildcard """

        filter_in = read_input('Only show files matching: ')

        if filter_in:
            self.current_pane.filter_in(filter_in)

    ################################################################################

    def key_clear_filters(self):
        """ Clear filters """

        with popup.PopUp(self.screen, 'Cleared all filters', COLOUR_STATUS):
            self.current_pane.clear_filters()

    ################################################################################

    def key_toggle_hidden(self):
        """ Toggle display of hidden files """

        current_state = self.current_pane.get_hidden_visibility()
        self.current_pane.set_hidden_visibility(not current_state)

    ################################################################################

    def key_move_down(self):
        """ Move down 1 line """

        self.current_pane.move(1)

    ################################################################################

    def key_move_up(self):
        """ Move up 1 line """

        self.current_pane.move(-1)

    ################################################################################

    def key_move_page_down(self):
        """ Move down by a page """

        self.current_pane.move_page_down()

    ################################################################################

    def key_move_page_up(self):
        """ Move up by a page """

        self.current_pane.move_page_up()

    ################################################################################

    def key_move_top(self):
        """ Move to the top of the file list """

        self.current_pane.move_top()

    ################################################################################

    def key_move_end(self):
        """ Move to the end of the file list """

        self.current_pane.move_end()

    ################################################################################

    def key_cycle_sort(self):
        """ Cycle through the various sort options """

        self.current_pane.set_sort_order(1)

    ################################################################################

    def key_reverse_sort(self):
        """ Reverse the current sort order """

        self.current_pane.reverse_sort_order()

    ################################################################################

    def key_tag(self):
        """ Tag/Untag the current file """

        self.current_pane.tag_current()
        self.key_move_down()

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

            self.current_pane.constrain_display_parameters()

    ################################################################################

    def show_file_list(self):
        """ Show all file lists """

        for pane in self.panes:
            pane.show_file_list(pane == self.current_pane)

    ################################################################################

    def event(self):
        """Wait for, and return the next event from the event queue"""

        return self.event_queue.get()

################################################################################

def parse_command_line():
    """ Parse the command line, return the arguments """

    # TODO: Options and arguments

    parser = argparse.ArgumentParser(description='Console file manager')

    parser.add_argument('--pudb', action='store_true', help='Invoke pudb debugger over Telnet')

    args = parser.parse_args()

    args.paths = None

    return args

################################################################################

def main(screen, args):
    """ Parse the command line and run the review """

    filemanager = FileManager(args)

    filemanager.draw_screen()

    while not filemanager.done():
        filemanager.show_file_list()

        event, data = filemanager.event()

        if event == 'key':
            filemanager.handle_keypress(data)
        elif event == 'inotify':
            filemanager.panes[data].reload_changes()

    filemanager.save_state()

################################################################################

def tfm():
    """Main function"""

    try:
        command_args = parse_command_line()

        if command_args.pudb:
            from pudb.remote import set_trace
            set_trace(term_size=(190, 45))

        curses.wrapper(main, command_args)

    except KeyboardInterrupt:
        sys.exit(1)

    except BrokenPipeError:
        sys.exit(2)

    except FileManagerError as exc:
        print(exc.msg)

################################################################################

if __name__ == '__main__':
    tfm()
