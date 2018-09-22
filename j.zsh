
# Get script's directory.
j_dir=${0:a:h}

# If the script is a symlink, we want to follow the symlink back to we can
# access the executable.
if [ -h $0 ]; then
  j_dir=$(dirname $(readlink $0))
fi

j() {
  # First allow the user to select the desired path, then cd to it.
  $j_dir/j.py -s $1
  cd $($j_dir/j.py $1)
}

_j_print() {
  $j_dir/j.py -p
}

_j_precmd() {
  $j_dir/j.py -a
}

# Add to list of precmd functions.
[[ -n "${precmd_functions[(r)_j_precmd]}" ]] || {
  precmd_functions[$(($#precmd_functions+1))]=_j_precmd
}
