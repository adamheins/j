# j

A `zsh` tool for jumping to previously-visited directories by name. If there
are multiple matches, the user selects the correct absolute path from a list. A
cousin of [z](https://github.com/rupa/z) with a more obvious directory-priority
algorithm.

## Install

To install, first clone the repo:
```
git clone git@github.com:adamheins/j.git
```
Run the install script to create and setup the `$J_DIR`. Finally, source
`j.zsh` by adding something like
```
source /path/to/j.zsh
```
to your `.zshrc`.

## Configuration

Data and other files are stored in the directory pointed to by `$J_DIR`, which
is `~/.j` by default.

Directories can be ignored by adding glob patterns to `$J_DIR/ignore`.

## License

MIT license. See the LICENSE file.
