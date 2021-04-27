# j

My version of a directory navigation tool. Inspired by but generally simpler
(and I think a bit more intuitive) than others like
[autojump](https://github.com/wting/autojump) and
[z](https://github.com/rupa/z). Currently zsh-only.

Instead of regex searching a list of directories weighted by "frecency" (recent + frequency),
I prefer to have a list of visited directories and just tab complete their
basenames. This is what `j` does. I typically remember the basename of the
directory I want to visit, just not the path, so this works very well for me.

When there are multiple directories with the same basename,
[fzf](https://github.com/junegunn/fzf) is used to select the desired one. The
list is ordered by time of last visit, so it is very easy to return to recent
directories. Overall, I like this process because it is very predictable: I
know I'm going to go where I expect.

I wrote a bit about the development process
[here](https://adamheins.com/blog/j-a-directory-navigation-tool). This is of
course mostly just a written-for-fun tool, that I happen to find useful. If you
do as well, great! 

## Install

First, install [fzf](https://github.com/junegunn/fzf).

Next, run the following commands. The `install.zsh` script installs j's
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
