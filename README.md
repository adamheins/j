# j

Jump to previously-visited directories by name. If there are multiple matches,
the user selects the correct absolute path from a list. A cousin of
[z](https://github.com/rupa/z) with a more obvious directory-priority
algorithm.

## Install

`j` only works with zsh. To install, download `j.zsh` and source it. Something
like
```
source /path/to/j.zsh
```
in your `.zshrc`. You'll also need `jselector.py`, the path to which must be
specified at the top of `j.zsh`.
