# j - jump to files

[[ -z "$J_DIR" ]] && J_DIR=~/.j

J_DATA_DIR="$J_DIR/data"
J_IGNORE_FILE="$J_DIR/ignore"
J_RECENT_FILE="$J_DIR/recent"
J_SELECTOR="$J_DIR/jselector.py"

J_NUM_RECENT=10


# Main j function, called by the user.
# Globals:
#   J_DATA_DIR
#   J_SELECTOR
# Arguments:
#   $1 Flag or directory basename.
#   $2 If $1 is a flag, then this is a directory basename. Otherwise not used.
# Output:
#   Write updated directory paths to the directory basename file in the
#   J_DATA_DIR.
j() {
  if [ -z "$1" ]; then
    cd
    return
  fi

  case "$1" in
    -l|--list)
      if [ -z "$2" ]; then
        j::echo_err "A directory basename is required."
        return 1
      fi
      j::list_paths_from_file "$J_DATA_DIR/$2"
    ;;
    -p|--prune)
      if [ -z "$2" ]; then
        j::echo_err "A directory basename is required."
        return 1
      fi

      # Check if selector is found.
      if [ -z "$J_SELECTOR" ]; then
        j::echo_err "Selector not found."
        return 1
      fi

      # TODO to do this, we need multi-select with fzf, then delete all lines
      # in the file matching those returned
      # finally we keep the check to delete the file

      if [ -f "$J_DATA_DIR/$2" ]; then
        "$J_SELECTOR" --prune "$J_DATA_DIR/$2" || return 1

        # if the file is now empty, remove the key
        [ -s "$J_DATA_DIR/$2" ] || rm "$J_DATA_DIR/$2"
      else
        j::echo_err "No such key: $2"
        return 1
      fi
    ;;
    -c|--clean)
      local keys key
      IFS=$'\n'
      keys=($(j::list_all))

      for key in $keys; do
        j::clean_one "$key" "$2"
      done
    ;;
    -r|--recent)
      local directory
      # cut off the first line, because that is the CWD, the select directory
      # with fzf
      directory=$(j::list_paths_from_file "$J_RECENT_FILE" | tail -n "+2" | fzf --no-multi)
      if [ -d "$directory" ]; then
        cd "$directory"
      fi
    ;;
    -)
      # take second last directory from the list, since the last is the CWD
      local directory
      directory=$(j::list_paths_from_file "$J_RECENT_FILE" | head -n 2 | tail -n 1)
      if [ -d "$directory" ]; then
        cd "$directory"
      fi
    ;;
    -h|--help)
      echo 'j [--] <basename>'
      echo 'j [options] [args]'
      echo ''
      echo 'Options:'
      echo '  -           Jump to the last visited directory.'
      echo '  -c, --clean [N]'
      echo '              Remove all directories that no longer exist or that'
      echo '              have been accessed more than N days ago.'
      echo '  -h, --help  Show this help message and exit.'
      echo '  -l, --list <basename>'
      echo '              List all entries for <basename>.'
      echo '  -p, --prune <basename>'
      echo '              Interactively delete entries for <basename>.'
      echo '  -r, --recent'
      echo '              Select one of the past 10 last visited directories'
      echo '              and jump to it.'
    ;;
    *)
      # check for -- guard, which allows jumping to directories whose names
      # collide with other options
      local dirname
      if [ "$1" = "--" ]; then
        dirname="$2"
      else
        dirname="$1"
      fi

      if ! [ -f "$J_DATA_DIR/$dirname" ]; then
        return 1
      fi

      j::clean_one "$dirname"

      # if there are multiple directories with the same basename, the user
      # selects one with fzf
      local directory directories
      # directories=$(j::list_paths_from_file "$J_DATA_DIR/$dirname")
      directory=$(j::list_paths_from_file "$J_DATA_DIR/$dirname" | fzf --select-1)
      # if [[ -n "${directories[2]}" ]]; then
      #   directory=$(printf "%s\n" "${directories[@]}" | fzf)
      # else
      #   directory="${directories[1]}"
      # fi

      if [ -d "$directory" ]; then
        cd "$directory"
      fi
    ;;
  esac
  return 0
}


# Utility to print to stderr.
j::echo_err() {
  echo "$@" 1>&2
}


# Remove directories that no longer exist from a single key.
# Globals:
#   J_DATA_DIR
# Arguments:
#   $1 Directory basename
#   $2 Days since last access after which directory should be removed (optional).
# Output:
#   Write updated directory paths to the file $1 in the J_DATA_DIR.
j::clean_one() {
  # if the key does not exist, do nothing
  local j_path="$J_DATA_DIR/$1"
  [ -f "$j_path" ] || return

  IFS=$'\n'
  local lines tmp_file
  lines=($(<"$j_path"))
  tmp_file=$(mktemp)

  # Calculate minimum accessed time stamp to not remove.
  local now min_stamp
  min_stamp=0
  if [ -n "$2" ]; then
    now=$(date +%s)
    min_stamp=$(( $now - $2*86400 ))
  fi

  # Gather lines which point to still-existing directories.
  for line in $lines; do
    local stamp=${line%% *}
    if [ "$stamp" -le "$min_stamp" ]; then
      continue
    fi

    # directory is all parts of the line after the timestamp
    local d=${line#* }
    if [ -d "$d" ]; then
      echo "$line" >> "$tmp_file"
    fi
  done

  # If the file is non-empty, replace the current file with the temp file.
  # Otherwise, remove both.
  if [ -s "$tmp_file" ]; then
    mv "$tmp_file" "$j_path"
  else
    rm "$j_path"
    rm "$tmp_file"
  fi
}

j::cut_path() {
  while read line; do
    echo "${(@)line:1}"
    # cut -d' ' -f2- "$line"
  done
}


# List paths from a file, which is formatted as a list of date, path pairs,
# separated by a space.
# Arguments:
#   $1 File path
# Output:
#   List all directory paths listed in $1 to stdout.
j::list_paths_from_file() {
  if [ -f "$1" ]; then
    tac "$1" | cut -d' ' -f2-
    # cut -d' ' -f2- < "$1"
  fi
}


# List all keys.
# Globals:
#   J_DATA_DIR
# Output:
#   Print all directory basenames to stdout.
j::list_all() {
  find "$J_DATA_DIR" -type f -printf '%f\n'
}


# Exit status 0 if path should be ignored, otherwise non-zero status.
# Globals:
#   J_IGNORE_FILE
# Arguments:
#   $1 Path to directory
j::is_ignored() {
  local patterns
  patterns=($(<$J_IGNORE_FILE))
  for pattern in $patterns; do
    [[ "$1" == $~pattern ]] && return 0
  done
  return 1
}


# Add a directory path to a file in j.
# Arguments:
#   $1 Path to be added
#   $2 File to add to
#   $3 Limit for number of entries in the file (optional)
# Outputs:
#   Writes time and path to a file in the $J_DIR.
j::append_path_to_file() {
  local tmp_file

  # remove existing entry of this path
  if [ -f "$2" ]; then
    tmp_file=$(mktemp)

    # keep only unique entries
    grep -v "$1$" "$2" > "$tmp_file"

    # optionally limit the number of entries kept
    if [ -n "$3" ]; then
      tail -n "$3" "$tmp_file" > "$2"
    else
      mv "$tmp_file" "$2"
    fi
  fi

  # append time and path to the file
  echo "$(date +%s) ${1}" >> "$2"
}


# Add a directory to the j database.
# Globals:
#   J_IGNORE_FILE
#   J_DATA_DIR
# Arguments:
#   $1 Path to directory
# Outputs:
#   Writes time and path to a file in the $J_DIR.
j::add_directory() {
  # exit if directory doesn't exist
  [ -d "$1" ] || return 1

  # if the path is ignored, exit
  if [ -f "$J_IGNORE_FILE" ]; then
    j::is_ignored "$1" && return 0
  fi

  # Don't add the root directory: we can't name it as a file and there is no
  # ambiguity in it's name, so j'ing to it adds no value. We do however add it
  # to the list of recent files.
  if [ "$1" != / ]; then
    j::append_path_to_file "$1" "$J_DATA_DIR/$(basename $1)"
  fi

  j::append_path_to_file "$1" "$J_RECENT_FILE" "$J_NUM_RECENT"

  return 0
}


# Add current working directory to the j database.
j::add_cwd() {
  j::add_directory "$PWD"
}


# Add to list of functions executed whenever working directory is changed. Only
# done if the shell is interactive.
if [[ $- == *i* ]]; then
  autoload -U add-zsh-hook
  add-zsh-hook chpwd j::add_cwd
fi
