#!/usr/bin/env python3
import time
import curses
import fnmatch
import os
import sys
from msgpack import packb, unpackb
from shutil import copyfile

J_DIR = os.path.expanduser('~/.j')
J_IGNORE = os.path.join(J_DIR, 'ignore')
J_DB_PATH = os.path.join(J_DIR, 'data.msgpack')


# Curses CLI key codes.
UP_KEYS = [ord('k'), curses.KEY_UP]
DOWN_KEYS = [ord('j'), curses.KEY_DOWN]
QUIT_KEYS = [ord('q')]
SELECT_KEYS = [curses.KEY_ENTER, 10, 13]
DELETE_KEYS = [ord('d')]

SELECT_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <Enter> to select, <q> to quit.'
PRUNE_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <d> to delete, <q> to quit.'


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
                return None
            elif key_code in SELECT_KEYS:
                return self.items[self.index]

    def prune(self, screen):
        ''' Delete items from the list. '''
        curses.curs_set(False)
        items_removed = []
        while True:
            key_code = self._refresh(screen)
            if self._navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return items_removed
            elif key_code in DELETE_KEYS:
                items_removed.append(self.items[self.index])
                del self.items[self.index]
                if len(self.items) == 0:
                    return self.items
                elif self.index > len(self.items) - 1:
                    self.index -= 1
                screen.erase()


class JDatabase(object):
    def __init__(self, path):
        self.path = path
        self.map = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'rb') as f:
            data = f.read()
        return unpackb(data, raw=False)

    def save(self):
        packed = packb(self.map)
        backup_path = self.path + '.back'
        with open(backup_path, 'wb') as f:
            f.write(packed)
        copyfile(backup_path, self.path)
        os.remove(backup_path)

    def add(self, key, path):
        ''' Add path to given key. '''
        accessed = int(time.time())
        if key in self.map:
            self.map[key][path] = accessed
        else:
            self.map[key] = {path: accessed}

    def remove(self, key, path):
        ''' Remove the path from this key. '''
        # remove the path from this key
        self.map[key].pop(path, None)

        # if there are no more paths for this key, remove it entirely
        if len(self.map[key].keys()) == 0:
            self.map.pop(key)

    def keys(self):
        ''' Get all keys in the map. '''
        return self.map.keys()

    def latest(self, key):
        ''' Get the first path associated with the key. '''
        return self.paths(key)[0]

    def paths(self, key):
        ''' Return all paths associated with the key. '''
        return sorted(self.map[key], key=self.map[key].get, reverse=True)

    def items(self, key):
        ''' Return all (path, time) pairs for the key. '''
        return sorted(self.map[key].items(), key=lambda x: x[1], reverse=True)

    def __contains__(self, key):
        return key in self.map


class JInterface(object):
    ''' Maps directory basenames to full paths. '''
    def __init__(self, path):
        self.db = JDatabase(path)

    def save(self):
        self.db.save()

    def keys(self):
        return self.db.keys()

    def paths(self, basename):
        return self.db.paths(basename)

    def _remove_stale_paths(self, basename):
        ''' Remove paths pointed to by key that no longer exist or that are now
            ignored. '''
        if basename not in self.db:
            return

        for idx, path in enumerate(self.db.paths(basename)):
            if not os.path.exists(path) or path_is_ignored(path, J_IGNORE):
                self.db.remove(basename, path)

    def add_entry(self, path):
        ''' Add a directory path to the map. The path should be a full absolute
            path. '''
        basename = os.path.basename(path)
        self._remove_stale_paths(basename)

        # If this directory path is being ignored, don't add it.
        if path_is_ignored(path, J_IGNORE):
            return

        self.db.add(basename, path)

    def prune(self, basename):
        ''' Open a curses CLI to allow the user to prune paths from the directory
            list. '''
        self._remove_stale_paths(basename)
        if basename in self.db:
            paths = self.db.paths(basename)
            lister = Lister(paths, PRUNE_INSTR)
            paths_removed = curses.wrapper(lister.prune)
            for path in paths_removed:
                self.db.remove(basename, path)

    def select(self, basename):
        ''' Select the desired path when multiple exist. '''
        if basename not in self.db:
            return None

        self._remove_stale_paths(basename)
        paths = self.db.paths(basename)
        if len(paths) > 1:
            lister = Lister(paths, SELECT_INSTR)
            path = curses.wrapper(lister.select)
            return path
        return paths[0]

    def clean(self, seconds_ago=None):
        ''' Clean up all directories that no longer exist or have expired a
            given number of days ago. '''
        min_accessed = 0
        if seconds_ago:
            min_accessed = int(time.time()) - seconds_ago

        basenames = self.db.keys()
        for basename in basenames:
            items = self.db.items(basename)
            for item in items:
                path, accessed = item
                if not os.path.isdir(path) or accessed < min_accessed:
                    self.db.remove(basename, path)


def main():
    if len(sys.argv) == 1:
        return 1

    args = sys.argv[1:]

    dirmap = JInterface(J_DB_PATH)

    # Add directory.
    if args[0] == '--add-cwd':
        # It is possible to end up in a directory that doesn't actually exist
        # when another process removes it or a parent. One example is checking
        # out a git branch with a different directory structure.
        try:
            cwd = os.getcwd()
        except FileNotFoundError:
            return 1
        dirmap.add_entry(cwd)
        dirmap.save()
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
        path = dirmap.select(basename)
        if not path:
            return 1
        print(path)
        return 0
    elif args[0] == '--prune':
        basename = args[1]
        dirmap.prune(basename)
        dirmap.save()
    elif args[0] == '--list':
        basename = args[1]
        if basename in dirmap.keys():
            print('\n'.join(dirmap.paths(basename)))
    else:
        print('Unrecognized command.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
