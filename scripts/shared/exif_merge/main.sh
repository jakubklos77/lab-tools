#!/bin/bash

# Resolve the real path of this script, following symlinks
path="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# Set up the venv if it doesn't exist yet
if [ ! -d "$path/venv" ]; then
    echo "Creating virtual environment..."
    virtualenv "$path/venv"
    source "$path/venv/bin/activate"
    echo "Installing pillow-heif..."
    pip install pillow-heif
else
    source "$path/venv/bin/activate"
fi

# Run the merge script
"$path/venv/bin/python" "$path/merge.py"
