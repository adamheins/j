# j - jump to files

# TODO it doesn't make sense to declare these here
[[ -z "$J4_DATA_DIR" ]] && J4_DATA_DIR=~/.j/data
[[ -z "$J4_IGNORE_FILE" ]] && J4_IGNORE_FILE=~/.j/ignore

# if the selector isn't set, check if it is on the path
if [[ -z "$J4_SELECTOR" ]]; then
  if command -v jselector > /dev/null 2>&1; then
    J4_SELECTOR=jselector
  fi
fi


# Main j function.
j() {
  if [ -z $1 ]; then
    cd
    return
  fi
  case "$1" in
    -l|--list)
      if [ -z "$2" ]; then
        echo A directory name is required.
        return 1
      fi
      _j4_list_one "$2"
    ;;
    -p|--prune)
      if [ -z "$2" ]; then
        echo A directory name is required.
        return 1
      fi

      # Check if selector is found.
      if [ -z "$J4_SELECTOR" ]; then
        echo "Selector not found."
      fi

      if [ -f "$J4_DATA_DIR/$2" ]; then
        "$J4_SELECTOR" --prune "$J4_DATA_DIR/$2"

        # if the file is now empty, remove the key
        [ -s "$J4_DATA_DIR/$2" ] || rm "$J4_DATA_DIR/$2"
      else
        echo "No such key: $2"
      fi
    ;;
    -c|--clean)
      local keys key
      IFS=$'\n'
      keys=($(_j4_list_all))
      echo $keys

      for key in $keys; do
        j4_clean_one "$key" "$2"
      done
    ;;
    -h|--help)
      echo 'j [options] dir'
      echo ''
      echo 'options:'
      echo '  -c, --clean  remove all directories that no longer exist'
      echo '  -h, --help   show this help message and exit'
      echo '  -l, --list   list all entries for dir'
      echo '  -p, --prune  interactively delete entries for dir'
    ;;
    *)
      if ! [ -f "$J4_DATA_DIR/$1" ]; then
        return 1
      fi

      _j4_clean_one "$1"

      # 1. do selection
      local d=($(_j4_list_one "$1"))
      if [[ -n "$d[2]" && -n "$J4_SELECTOR" ]]; then
        "$J4_SELECTOR" "$J4_DATA_DIR/$1"
      fi

      # 2. do regular change
      d=$(_j4_list_one "$1" | tail -n 1)
      if [ -n "$d" ]; then
        cd "$d"
      fi
    ;;
  esac
}


# Remove directories that no longer exist from a single key.
_j4_clean_one() {
  # if the key does not exist, do nothing
  local j_path="$J4_DATA_DIR/$1"
  [ -f "$j_path" ] || return

  IFS=$'\n'
  local lines=($(<"$j_path"))
  local tmp_file=$(mktemp)

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


# List paths associated with a single key.
_j4_list_one() {
  if [ -f "$J4_DATA_DIR/$1" ]; then
    cut -d' ' -f2- < "$J4_DATA_DIR/$1"
  fi
}


# List all keys.
_j4_list_all() {
  ls "$J4_DATA_DIR"
}


# Exit status 0 if path should be ignored, otherwise non-zero status.
_j4_is_ignored() {
  local patterns=($(<$J4_IGNORE_FILE))
  for pattern in $patterns; do
    [[ "$1" == $~pattern ]] && return 0
  done
  return 1
}


# Add a directory to the j database.
# Globals:
#   J4_IGNORE_FILE
#   J4_DATA_DIR
# Arguments:
#   $1 Path to directory
# Outputs:
#   Writes time and path to a file in the j data directory.
j::add_directory() {
  # exit if current working directory doesn't exist
  [ -d "$1" ] || return

  # if the path is ignored, exit
  if [ -f "$J4_IGNORE_FILE" ]; then
    _j4_is_ignored "$1" && return
  fi

  local j_path tmp_file
  j_path="$J4_DATA_DIR/$(basename $1)"

  # remove existing entry of this path
  if [ -f $j_path ]; then
    tmp_file=$(mktemp)
    grep -v "$1$" "$j_path" > "$tmp_file"
    mv "$tmp_file" "$j_path"
  fi

  # append time and path to the file
  echo "$(date +%s) ${1}" >> "$j_path"
}


# Add current working directory to the j database.
j::add_cwd() {
  j::add_directory "$PWD"
}


# Add to list of functions executed whenever working directory is changed.
[[ -n "${chpwd_functions[(r)j::add_cwd]}" ]] || {
  chpwd_functions[$(($#chpwd_functions+1))]=j::add_cwd
}
