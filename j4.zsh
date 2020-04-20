
J4_DATA_DIR=~/.j/data

j4() {
  if [ -z $1 ]; then
    cd
    return
  fi
  case "$1" in
    -l|--list)
      _j4_list_one "$2"
    ;;
    -p|--purge)
      echo TODO: requires selector
    ;;
    -h|--help)
      echo 'j [options] dir'
      echo ''
      echo 'options:'
      echo '  -h, --help   show this help message and exit'
      echo '  -l, --list   list all entries for dir'
      echo '  -p, --purge  interactively delete entries for dir'
    ;;
    *)
      # If no options are passed, the most recent path with the given basename
      # is cd'd to.
      # TODO need to add selector
      _j4_clean_one "$1"
      local d=$(_j4_list_one "$1" | tail -n 1)
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
  local lines=($(cat "$j_path"))
  local tmp_file=$(mktemp)

  # Gather lines which point to still-existing directories.
  for line in $lines; do
    local d=$(echo "$line" | cut -d' ' -f2-)
    if [ -d "$d" ]; then
      echo "$line" >> "$tmp_file"
    fi
  done
  mv "$tmp_file" "$j_path"
}

# List paths associated with a single key.
_j4_list_one() {
  if [ -f "$J4_DATA_DIR/$1" ]; then
    cat "$J4_DATA_DIR/$1" | cut -d' ' -f2-
  fi
}

# List all keys.
_j4_list_all() {
  ls $J4_DATA_DIR
}

# Add current working directory to the list of keys.
_j4_add_cwd() {
  # exit if current working directory doesn't exist
  [ -d $PWD ] || return

  local j_name=$(basename $PWD)
  local j_path="$J4_DATA_DIR/$j_name"

  # remove existing entry of this path
  if [ -f $j_path ]; then
    local tmp_file=$(mktemp)
    grep -v "$PWD$" "$j_path" > "$tmp_file"
    mv "$tmp_file" "$j_path"
  fi

  # append time and path to the file
  echo "$(date +%s) ${PWD}" >> "$j_path"
}


# Add to list of precmd functions.
[[ -n "${precmd_functions[(r)_j4_add_cwd]}" ]] || {
  precmd_functions[$(($#precmd_functions+1))]=_j4_add_cwd
}
