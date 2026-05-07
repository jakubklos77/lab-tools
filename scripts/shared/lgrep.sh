#!/bin/sh
#
# lgrep — log-aware grep: matches whole multi-line records (first line is flush-left,
# continuation lines are indented) that contain PATTERN anywhere in the record.
# Case-insensitive. Reads from FILE(s) or stdin if no file is given.
#
# Usage:
#   lgrep PATTERN [FILE...]
#   cat FILE | lgrep PATTERN
#

if [ $# -lt 1 ]; then
    echo "Usage: $0 PATTERN [FILE...]" >&2
    exit 1
fi

pat=$1
shift

# If no files given and stdin is not a terminal, read from stdin
if [ $# -eq 0 ] && [ -t 0 ]; then
    echo "Usage: $0 PATTERN [FILE...]" >&2
    exit 1
fi

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
