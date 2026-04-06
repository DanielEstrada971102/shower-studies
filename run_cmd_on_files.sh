#!/bin/bash

DEFAULT_CONDA_ENV="showers-destrada"

echo "Running job"

# -----------------
# INPUT ARGUMENTS
# -----------------
COMMAND="$1"
ARGS="$2"
CONDA_ENV="${3:-$DEFAULT_CONDA_ENV}"   # default value

shift 3 || true
FILES=("$@")

# -----------------
# CONDA SETUP
# -----------------
if [ "$CONDA_ENV" != "none" ]; then
    
    # Initialize conda if it's not already available
    if ! declare -f conda &> /dev/null; then
        echo "Initializing conda..."
        eval "$(/nfs/fanae/anaconda3/bin/conda shell.bash hook)" && conda deactivate
    fi

    # Check current env
    CURRENT_ENV="${CONDA_DEFAULT_ENV:-}"

    if [ "$CURRENT_ENV" != "$CONDA_ENV" ]; then
        echo "Activating conda env: $CONDA_ENV"
        conda activate "$CONDA_ENV"
    else
        echo "Conda env already active: $CONDA_ENV"
    fi
fi

echo "Using python: $(which python)"

# ----------------------------------------------
# CD to shower-studies directory and SETUP path
# ----------------------------------------------
cd /nfs/fanae/user/destrada/Public/shower-studies
eval "$(make -s set-path-command)"

# -----------------
# DEBUG INFO
# -----------------
echo "Files:"
printf "%s\n" "${FILES[@]}"

# -----------------
# RUN
# -----------------
time $COMMAND $ARGS -i "${FILES[@]}"