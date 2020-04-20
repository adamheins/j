#!/usr/bin/env python3
import curses
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
                return None
            elif key_code in SELECT_KEYS:
                return self.items[self.index]

    def prune(self, screen):
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


def main():
    if len(sys.argv) == 1:
        return 1

    if sys.argv[1] == '--prune':
        prune = True
        instructions = PRUNE_INSTR
        path = sys.argv[2]
    else:
        prune = False
        instructions = SELECT_INSTR
        path = sys.argv[1]

    with open(path) as f:
        lines = f.read().strip().split('\n')

    files = [line.split()[1] for line in lines]
    lister = Lister(files, instructions)

    if prune:
        result = curses.wrapper(lister.prune)
    else:
        result = curses.wrapper(lister.select)

    if result:
        print(result)


if __name__ == '__main__':
    sys.exit(main())
