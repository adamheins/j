#!/usr/bin/env python3
import curses
import fnmatch
import os
import pickle
import sys


J_DIR = os.path.expanduser('~/.j')
J_PICKLE = os.path.join(J_DIR, 'data.pickle')
J_IGNORE = os.path.join(J_DIR, 'ignore')


UP_KEYS = [ord('k'), curses.KEY_UP]
DOWN_KEYS = [ord('j'), curses.KEY_DOWN]
QUIT_KEYS = [ord('q')]
SELECT_KEYS = [curses.KEY_ENTER, 10, 13]
DELETE_KEYS = [ord('d')]


def selector(screen, items, purge=False):
    ''' Open a curses selector to choose a desired item. '''
    curses.curs_set(False)
    idx = 0

    while True:
        for index, item in enumerate(items):
            if index == idx:
                style = curses.A_REVERSE
            else:
                style = curses.A_NORMAL
            screen.addstr(index, 0, item, style)

        screen.refresh()
        ch = screen.getch()

        # Navigation
        if ch in DOWN_KEYS:
            idx = (idx + 1) % len(items)
        elif ch in UP_KEYS:
            idx = (idx - 1) % len(items)
        elif ch in QUIT_KEYS:
            return -1

        # Select or purge an item.
        else:
            if purge and ch in DELETE_KEYS:
                del items[idx]
                if len(items) == 0:
                    return -1
            elif ch in SELECT_KEYS:
                return idx


class Lister(object):
    def __init__(self, items):
        curses.curs_set(False)
        self.items = items
        self.index = 0

    def refresh(self, screen):
        for index, item in enumerate(self.items):
            if index == self.index:
                style = curses.A_REVERSE
            else:
                style = curses.A_NORMAL
            screen.addstr(index, 0, item, style)

        screen.refresh()
        return screen.getch()

    def navigate(self, key_code):
        if key_code in DOWN_KEYS:
            self.index = (self.index + 1) % len(self.items)
        elif key_code in UP_KEYS:
            self.index = (self.index - 1) % len(self.items)
        else:
            return False
        return True

    def select(self, screen):
        while True:
            key_code = self.refresh(screen)
            if self.navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return -1
            elif key_code in SELECT_KEYS:
                return self.index

    def purge(self, screen):
        while True:
            key_code = self.refresh(screen)
            if self.navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return self.items
            elif key_code in DELETE_KEYS:
                del self.items[self.index]
                if len(self.items) == 0:
                    return self.items
                elif self.index > len(self.items) - 1:
                    self.index -= 1


def remove_stale_paths(dirmap, key):
    ''' Remove paths pointed to by key that no longer exist or that are now
        ignored. '''
    if key not in dirmap:
        return

    # Remove paths for this key that no longer exist or are ignored.
    for idx, path in enumerate(dirmap[key]):
        if not os.path.exists(path) or path_is_ignored(path, J_IGNORE):
            del dirmap[key][idx]

    # If there are no paths left, remove the key entirely.
    if len(dirmap[key]) == 0:
        dirmap.pop(key)
        return False
    return True


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


def load(pickle_path):
    ''' Load the directory dictionary from pickle. '''
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as f:
            return pickle.load(f)
    else:
        return {}


def save(pickle_path, dirmap):
    ''' Save the directory map to the pickle. '''
    with open(pickle_path, 'wb') as f:
        pickle.dump(dirmap, f)


def add_dir_path(dir_path, dirmap):
    ''' Add a directory path to the map. The path should be a full absolute
        path. '''
    basename = os.path.basename(dir_path)
    remove_stale_paths(dirmap, basename)

    # If this directory path is being ignored, don't add it.
    if path_is_ignored(dir_path, J_IGNORE):
        return

    if basename in dirmap:
        # Add the path to the front of the list in the map, removing it if it
        # already exists.
        if dir_path in dirmap[basename]:
            dirmap[basename].remove(dir_path)
        dirmap[basename].insert(0, dir_path)
    else:
        dirmap[basename] = [dir_path]


def select(basename, dirmap):
    ''' Select the desired path when multiple exist. It is necessary to
        separate this from the get function so that it can be called separately
        from the shell wrapper script. '''
    remove_stale_paths(dirmap, basename)
    if basename in dirmap and len(dirmap[basename]) > 1:
        lister = Lister(dirmap[basename])
        idx = curses.wrapper(lister.select)
        if idx > 0:
            # Selected path is inserted at the front of list.
            dir_path = dirmap[basename][idx]
            del dirmap[basename][idx]
            dirmap[basename].insert(0, dir_path)


def get_dir_path(basename, dirmap):
    ''' Get the directory path for the basename. '''
    if basename in dirmap:
        return dirmap[basename][0]
    else:
        return '.'


def main():
    if len(sys.argv) == 1:
        print('')
        return

    args = sys.argv[1:]

    # Add directory.
    if args[0] == '--add-cwd':
        dirmap = load(J_PICKLE)
        cwd = os.getcwd()
        add_dir_path(cwd, dirmap)
        save(J_PICKLE, dirmap)
        return 0

    # Print all directories.
    elif args[0] == '--list-all-keys':
        dirmap = load(J_PICKLE)
        print('\n'.join(dirmap.keys()))
        return 0

    # The following commands all require a directory name as an argument.
    if len(args) < 2:
        print('Directory name required.')
        return 1

    # Select a directory.
    if args[0] == '--select':
        dirmap = load(J_PICKLE)
        basename = args[1]
        select(basename, dirmap)
        save(J_PICKLE, dirmap)

    elif args[0] == '--list':
        dirmap = load(J_PICKLE)
        basename = args[1]
        if basename in dirmap:
            print('\n'.join(dirmap[basename]))

    # Default is print path of directory passed as first argument.
    elif args[0] == '--print':
        dirmap = load(J_PICKLE)
        basename = args[1]
        dirname = get_dir_path(basename, dirmap)
        print(dirname)
        save(J_PICKLE, dirmap)

    else:
        print('Unrecognized command.')
        return 1


if __name__ == '__main__':
    main()
