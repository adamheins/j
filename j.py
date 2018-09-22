#!/usr/bin/env python
from __future__ import print_function

import curses
import os
import pickle
import sys


J_PICKLE = os.path.expanduser('~/.j.pickle')


def selector(screen, items):
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
        if ch == ord('j') or ch == curses.KEY_DOWN:
            idx = (idx + 1) % len(items)
        elif ch == ord('k') or ch == curses.KEY_UP:
            idx = (idx - 1) % len(items)
        elif ch == ord('q'):
            return -1
        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            return idx


def remove_stale_paths(dirmap, key):
    ''' Remove paths pointed to by key that no longer exist. '''
    if key not in dirmap:
        return

    # Remove paths for this key that no longer exist.
    for idx, path in enumerate(dirmap[key]):
        if not os.path.exists(path):
            del dirmap[key][idx]

    # If there are no paths left, remove the key entirely.
    if len(dirmap[key]) == 0:
        dirmap.pop(key)
        return False
    return True


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


def add(dir_path, dirmap):
    ''' Add a directory path to the map. The path should be a full absolute
        path. '''
    basename = os.path.basename(dir_path)
    remove_stale_paths(dirmap, basename)

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
        idx = curses.wrapper(selector, dirmap[basename])
        if idx > 0:
            dir_path = dirmap[basename][idx]
            del dirmap[basename][idx]
            dirmap[basename].insert(0, dir_path)


def get(basename, dirmap):
    ''' Get the directory path for the basename. '''
    if basename in dirmap:
        return dirmap[basename][0]
    else:
        return '.'


def main():
    if len(sys.argv) == 1:
        print('')

    # Add directory.
    elif sys.argv[1] == '-a':
        dirmap = load(J_PICKLE)
        cwd = os.getcwd()
        add(cwd, dirmap)
        save(J_PICKLE, dirmap)

    # Print all directories.
    elif sys.argv[1] == '-p':
        dirmap = load(J_PICKLE)
        print('\n'.join(dirmap.keys()))

    elif sys.argv[1] == '-s':
        dirmap = load(J_PICKLE)
        basename = sys.argv[2]
        select(basename, dirmap)
        save(J_PICKLE, dirmap)

    # Default is print path of directory passed as first argument.
    else:
        dirmap = load(J_PICKLE)
        basename = sys.argv[1]
        dirname = get(basename, dirmap)
        print(dirname)
        save(J_PICKLE, dirmap)


if __name__ == '__main__':
    main()
