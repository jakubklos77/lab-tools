#!/bin/sh
#
# lgrep — log-aware grep for logs with continuation lines
# A record starts with a non-space / non-tab character
# Continuation lines start with space or tab
#
# Usage:
#   lgrep PATTERN FILE...
#

if [ $# -lt 2 ]; then
    echo "Usage: $0 PATTERN FILE..." >&2
    exit 1
fi

pat=$1
shift

awk -v pat="$pat" '
BEGIN {
    rec = ""
    found = 0
    IGNORECASE = 1
}

# Start of a new logical record
/^[^ \t]/ {
    if (NR > 1 && found) {
        print rec
    }

    rec = $0
    found = 0

    if ($0 ~ pat) {
        found = 1
    }
    next
}

# Continuation line
{
    rec = rec ORS $0
    if ($0 ~ pat) {
        found = 1
    }
}

END {
    if (found) {
        print rec
    }
}
' "$@"
