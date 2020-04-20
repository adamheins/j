#!/usr/bin/env python3
import time
import curses
import fnmatch
import os
import pickle
import sys


J_DIR = os.path.expanduser('~/.j')
J_PICKLE = os.path.join(J_DIR, 'data.pickle')
J_IGNORE = os.path.join(J_DIR, 'ignore')
J_JSON_PATH = os.path.join(J_DIR, 'data.json')


# Curses CLI key codes.
UP_KEYS = [ord('k'), curses.KEY_UP]
DOWN_KEYS = [ord('j'), curses.KEY_DOWN]
QUIT_KEYS = [ord('q')]
SELECT_KEYS = [curses.KEY_ENTER, 10, 13]
DELETE_KEYS = [ord('d')]

SELECT_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <Enter> to select, <q> to quit.'
PURGE_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <d> to delete, <q> to quit.'


def path_is_ignored(dir_path, ignore_path):
    ''' Returns True if the dir should be ignored as per the ignore file, False
        otherwise. '''
    if not os.path.exists(ignore_path):
        return False
    with open(ignore_path, 'r') as f:
        lines = f.read().strip().split('\n')
    patterns = [line for line in lines if line.strip()[0] != '#']
    for pattern in patterns:
        if fnmatch.fnmatch(dir_path, pattern):
            return True
    return False


class Lister(object):
    ''' Curses CLI for interacting with list of paths. '''
    def __init__(self, items, instructions):
        self.items = items
        self.instructions = instructions
        self.index = 0

    def _refresh(self, screen):
        ''' Refresh the screen and wait for key input. '''
        for index, item in enumerate(self.items):
            if index == self.index:
                style = curses.A_REVERSE
            else:
                style = curses.A_NORMAL
            screen.addstr(index+2, 0, item, style)

        screen.addstr(0, 0, self.instructions, curses.A_BOLD)

        screen.refresh()
        return screen.getch()

    def _navigate(self, key_code):
        ''' Screen navigation. '''
        if key_code in DOWN_KEYS:
            self.index = (self.index + 1) % len(self.items)
        elif key_code in UP_KEYS:
            self.index = (self.index - 1) % len(self.items)
        else:
            return False
        return True

    def select(self, screen):
        ''' Select an item from the list. '''
        curses.curs_set(False)
        while True:
            key_code = self._refresh(screen)
            if self._navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return -1
            elif key_code in SELECT_KEYS:
                return self.index

    def purge(self, screen):
        ''' Delete items from the list. '''
        curses.curs_set(False)
        while True:
            key_code = self._refresh(screen)
            if self._navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return self.items
            elif key_code in DELETE_KEYS:
                del self.items[self.index]
                if len(self.items) == 0:
                    return self.items
                elif self.index > len(self.items) - 1:
                    self.index -= 1
                screen.erase()


class DirectoryMap(object):
    ''' Maps directory basenames to full paths. '''
    def __init__(self, db_path):
        self.db_path = db_path
        self.map = self._load()

    def _load(self):
        ''' Load the mapping of basenames to full paths from disk. '''
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                return pickle.load(f)
        else:
            return {}

    def save(self):
        ''' Save the directory map to the pickle. '''
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.map, f)

        # NOTE experimental JSON backend
        # with open(J_JSON_PATH, 'w') as f:
        #     json.dump(self.map, f)

    def keys(self):
        return self.map.keys()

    def get(self, basename):
        return self.map[basename]

    def _remove_stale_paths(self, basename):
        ''' Remove paths pointed to by key that no longer exist or that are now
            ignored. '''
        if basename not in self.map:
            return

        # Remove paths for this key that no longer exist or are ignored.
        for idx, path in enumerate(self.map[basename]):
            if not os.path.exists(path) or path_is_ignored(path, J_IGNORE):
                del self.map[basename][idx]

        # If there are no paths left, remove the key entirely.
        if len(self.map[basename]) == 0:
            self.map.pop(basename)
            return False
        return True

    def add_entry(self, entry):
        ''' Add a directory path to the map. The path should be a full absolute
            path. '''
        basename = os.path.basename(entry)
        self._remove_stale_paths(basename)

        # If this directory path is being ignored, don't add it.
        if path_is_ignored(entry, J_IGNORE):
            return

        if basename in self.map:
            # Add the path to the front of the list in the map, removing it if
            # it already exists.
            if entry in self.map[basename]:
                self.map[basename].remove(entry)
            self.map[basename].insert(0, entry)
        else:
            self.map[basename] = [entry]

    def purge(self, basename):
        ''' Open a curses CLI to allow the user to purge paths from the directory
            list. '''
        self._remove_stale_paths(basename)
        if basename in self.map:
            lister = Lister(self.map[basename], PURGE_INSTR)
            items = curses.wrapper(lister.purge)
            self.map[basename] = items

    def select(self, basename):
        ''' Select the desired path when multiple exist. It is necessary to
            separate this from the get function so that it can be called
            separately from the shell wrapper script.

            Return False if there were multiple items from which to select but
            the user quit, True otherwise. '''
        self._remove_stale_paths(basename)
        if basename in self.map and len(self.map[basename]) > 1:
            lister = Lister(self.map[basename], SELECT_INSTR)
            idx = curses.wrapper(lister.select)
            if idx > 0:
                # Selected path is inserted at the front of list.
                dir_path = self.map[basename][idx]
                del self.map[basename][idx]
                self.map[basename].insert(0, dir_path)
                return True
            # Only return False if the user quit the selection process.
            if idx < 0:
                return False
        return True

    def get_path(self, basename):
        ''' Get the directory path for the basename. '''
        if basename in self.map:
            return self.map[basename][0]
        else:
            return '.'


def main():
    if len(sys.argv) == 1:
        return 1

    args = sys.argv[1:]

    t0 = time.time()
    dirmap = DirectoryMap(J_PICKLE)

    # Add directory.
    if args[0] == '--add-cwd':
        # It is possible to end up in a directory that doesn't actually exist
        # when another process removes it or a parent. One example is checking
        # out a git branch with a different directory structure.
        try:
            cwd = os.getcwd()
        except FileNotFoundError:
            return 1
        t1 = time.time()
        dirmap.add_entry(cwd)
        t2 = time.time()
        dirmap.save()
        t3 = time.time()
        # print('j load = {}\nj add = {}\nj save = {}'.format(t1 - t0, t2 - t1, t3 - t2))
        return 0

    # Print all directories.
    elif args[0] == '--list-all-keys':
        print('\n'.join(dirmap.keys()))
        return 0

    # The following commands all require a directory name as an argument.
    if len(args) < 2:
        print('Directory name required.')
        return 1

    # Select a directory.
    if args[0] == '--select':
        basename = args[1]
        did_selection = dirmap.select(basename)
        dirmap.save()
        return 0 if did_selection else 1

    elif args[0] == '--purge':
        basename = args[1]
        dirmap.purge(basename)
        dirmap.save()

    elif args[0] == '--list':
        basename = args[1]
        if basename in dirmap.keys():
            print('\n'.join(dirmap.get(basename)))

    # Default is print path of directory passed as first argument.
    elif args[0] == '--print':
        basename = args[1]
        dirname = dirmap.get_path(basename)
        print(dirname)
        dirmap.save()

    else:
        print('Unrecognized command.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
