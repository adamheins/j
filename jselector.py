#!/usr/bin/env python3
import curses
import os
from pathlib import Path
import sys


# Curses CLI key codes.
UP_KEYS = [ord('k'), curses.KEY_UP]
DOWN_KEYS = [ord('j'), curses.KEY_DOWN]
QUIT_KEYS = [ord('q')]
SELECT_KEYS = [curses.KEY_ENTER, 10, 13]
DELETE_KEYS = [ord('d')]

SELECT_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <Enter> to select, <q> to quit.'
PRUNE_INSTR = 'Use <j>/<k> or <up>/<down> to navigate, <d> to delete, <q> to quit.'


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

    def prune(self, screen):
        ''' Delete items from the list. '''
        curses.curs_set(False)
        removed = []
        while True:
            key_code = self._refresh(screen)
            if self._navigate(key_code):
                continue
            elif key_code in QUIT_KEYS:
                return removed
            elif key_code in DELETE_KEYS:
                del self.items[self.index]
                removed.append(self.index)
                if len(self.items) == 0:
                    return removed
                elif self.index > len(self.items) - 1:
                    self.index -= 1
                screen.erase()


def read_lines(path):
    ''' Read lines from a file. '''
    with open(path) as f:
        return f.read().strip().split('\n')


def write_lines(path, lines):
    ''' Write lines to a file. '''
    with open(path, 'w') as f:
        f.write('\n'.join(lines))


def prettify_paths(paths):
    ''' Prettify full paths for viewing. '''
    home_dir = str(Path.home())
    paths = [path.replace(home_dir, '~') for path in paths]
    return paths


def do_prune(path):
    ''' Prune directories from the list in the file at the given path. '''
    lines = read_lines(path)
    lines_reversed = lines[::-1]
    files = [line.split()[1] for line in lines_reversed]
    lister = Lister(prettify_paths(files), PRUNE_INSTR)

    removed = curses.wrapper(lister.prune)

    # delete lines pruned by user
    n = len(lines)
    for idx in removed:
        del lines[n - 1 - idx]

    # write out new subset of lines
    if len(lines) == 0:
        os.remove(path)
    else:
        write_lines(path, lines)
    return 0


def do_select(path):
    ''' Select a directory from the list in the file at the given path. '''
    lines = read_lines(path)
    lines_reversed = lines[::-1]
    files = [line.split()[1] for line in lines_reversed]
    lister = Lister(prettify_paths(files), SELECT_INSTR)

    idx = curses.wrapper(lister.select)
    if idx == -1:
        return 1

    # move selected line to the end of the file so it can be identified later
    n = len(lines)
    line = lines[n - 1 - idx]
    del lines[n - 1 - idx]
    lines.append(line)

    write_lines(path, lines)
    return 0


def do_recent(path):
    ''' Select a directory from the list in the file at the given path. '''
    lines = read_lines(path)
    lines_reversed = lines[::-1]
    files = [line.split()[1] for line in lines_reversed]

    # don't pass the first directory, which is the CWD
    lister = Lister(prettify_paths(files[1:]), SELECT_INSTR)

    idx = curses.wrapper(lister.select)
    if idx == -1:
        return 1

    # add 1 to account for the first directory being removed from the Lister
    idx += 1

    # move selected line to the end of the file so it can be identified later
    n = len(lines)
    line = lines[n - 1 - idx]
    del lines[n - 1 - idx]
    lines.append(line)

    write_lines(path, lines)
    return 0


def main():
    if len(sys.argv) == 1:
        return 1

    if sys.argv[1] == '--prune':
        path = sys.argv[2]
        return do_prune(path)
    elif sys.argv[1] == '--recent':
        path = sys.argv[2]
        return do_recent(path)
    else:
        path = sys.argv[1]
        return do_select(path)


if __name__ == '__main__':
    sys.exit(main())
