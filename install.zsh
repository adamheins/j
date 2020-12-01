#!/bin/zsh

# default directory is ~/.j
[[ -z "$J_DIR" ]] && J_DIR=~/.j

mkdir -p "$J_DIR/data"
cp jselector.py "$J_DIR"
