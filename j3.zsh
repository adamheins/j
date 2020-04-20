
# Get script's directory.
J3_SRC_DIR=${0:a:h}

# If the script is a symlink, we want to follow the symlink back to we can
# access the executable.
if [ -h $0 ]; then
  J3_SRC_DIR=$(dirname $(readlink $0))
fi

J3_EXE=$J3_SRC_DIR/j3.py

j3() {
  if [ -z $1 ]; then
    cd
    return
  fi
  case $1 in
    -l|--list)
      $J3_EXE --list $2
    ;;
    -p|--purge)
      $J3_EXE --purge $2
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
      # First allow the user to select the desired path, then cd to it.
      local path=$($J3_EXE --select $1)
      if $?; then
        cd $path
      fi
    ;;
  esac
}

# Prints all keys. Used by the completion system.
_j3_print() {
  $J3_EXE --list-all-keys
}

_j3_precmd() {
  # Abort if the CWD doesn't exist (i.e. it was removed by some other process).
  # This avoids error spam in the terminal.
  [ -d $PWD ] || return
  $J3_EXE  --add-cwd
}

# Add to list of precmd functions.
[[ -n "${precmd_functions[(r)_j3_precmd]}" ]] || {
  precmd_functions[$(($#precmd_functions+1))]=_j3_precmd
}
