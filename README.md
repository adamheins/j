# j

A `zsh` tool for jumping to previously-visited directories by name. If there
are multiple matches, the user selects the correct absolute path from a list. A
cousin of [z](https://github.com/rupa/z) with a more obvious directory-priority
algorithm.

## Install

To install, run the following commands. The `install.zsh` script installs j's
data files to `~/.j`. To change this, export `$J_DIR` before running the
install script.
```
git clone git@github.com:adamheins/j.git /path/to/j
cd /path/to/j
./install.zsh
```

Then source `j.zsh` by adding something like
```
source /path/to/j/j.zsh
```
to your `.zshrc`.

## Usage

```
j [--] <basename>
j [options] [args]

Options:
  -           Jump to the last visited directory.
  -c, --clean [N]
              Remove all directories that no longer exist or that
              have been accessed more than <N> days ago.
  -h, --help  Show this help message and exit.
  -l, --list <basename>
              List all entries for <basename>.
  -p, --prune <basename>
              Interactively delete entries for <basename>.
  -r, --recent
              Select one of the past 10 last visited directories
              and jump to it.
```

## Configuration

Data and other files are stored in the directory pointed to by `$J_DIR`, which
is `~/.j` by default. A custom location can be used by exporting `$J_DIR`
before sourcing `j.zsh`.

Directories can be ignored by adding glob patterns to `$J_DIR/ignore`.

## Tests

Tests are run with [zunit](https://zunit.xyz). Run `zunit` in the root
directory to run the tests.

## License

MIT license. See the LICENSE file.
