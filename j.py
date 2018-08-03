#!/usr/bin/env python
from __future__ import print_function

import os
import pickle
import sys


J_PICKLE = os.path.expanduser('~/.j.pickle')


def load(pickle_name):
    if os.path.exists(pickle_name):
        with open(pickle_name, 'rb') as f:
            return pickle.load(f)
    else:
        return {}


def save(pickle_name, dirmap):
    with open(pickle_name, 'wb') as f:
        pickle.dump(dirmap, f)


def add(dirname, dirmap):
    basename = os.path.basename(dirname)
    dirmap[basename] = dirname


def get(basename, dirmap):
    if basename in dirmap:
        return dirmap[basename]
    else:
        return '.'


def main():
    if len(sys.argv) == 1:
        print('')
    elif sys.argv[1] == '-a':
        dirmap = load(J_PICKLE)
        cwd = os.getcwd()
        add(cwd, dirmap)
        save(J_PICKLE, dirmap)
    elif sys.argv[1] == '-p':
        dirmap = load(J_PICKLE)
        print('\n'.join(dirmap.keys()))
    else:
        dirmap = load(J_PICKLE)
        basename = sys.argv[1]
        dirname = get(basename, dirmap)
        print(dirname)
        save(J_PICKLE, dirmap)


if __name__ == '__main__':
    main()
