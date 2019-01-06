
# Get script's directory.
J_SRC_DIR=${0:a:h}

# If the script is a symlink, we want to follow the symlink back to we can
# access the executable.
if [ -h $0 ]; then
  J_SRC_DIR=$(dirname $(readlink $0))
fi

J_EXE=$J_SRC_DIR/j.py

j() {
  if [ -z $1 ]; then
    cd
    return
  fi
  case $1 in
    -l|--list)
      $J_EXE --list $2
    ;;
    --purge)
      $J_EXE --purge $2
    ;;
    *)
      # First allow the user to select the desired path, then cd to it.
      $J_EXE --select $1 && cd $($J_EXE --print $1)
    ;;
  esac
}

# Prints all keys. Used by the completion system.
_j_print() {
  $J_EXE --list-all-keys
}

_j_precmd() {
  $J_EXE --add-cwd
}

# Add to list of precmd functions.
[[ -n "${precmd_functions[(r)_j_precmd]}" ]] || {
  precmd_functions[$(($#precmd_functions+1))]=_j_precmd
}
