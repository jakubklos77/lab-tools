#!/bin/sh
#
# lgrep — log-aware grep: matches whole multi-line records (first line is flush-left,
# continuation lines are indented) that contain PATTERN anywhere in the record.
# Case-insensitive. Reads from FILE(s) or stdin if no file is given.
#
# Usage:
#   lgrep [-a] [-v] PATTERN [FILE...]
#   lgrep [-a] [-v] -e PATTERN [FILE...]
#   cat FILE | lgrep [-a] [-v] PATTERN
#
# Options:
#   -a   treat binary data as text (match byte-wise, ignore locale encoding)
#   -v   invert: print records that do NOT contain PATTERN
#   -e PATTERN
#        use PATTERN even if it starts with '-' (same as: lgrep -- PATTERN)
#

usage() {
    echo "Usage: $0 [-a] [-v] [-e PATTERN | PATTERN] [FILE...]" >&2
    exit "${1:-1}"
}

invert=0
binary=0
pat=
have_pat=0

while getopts "ave:h" opt; do
    case $opt in
        a) binary=1 ;;
        v) invert=1 ;;
        e) pat=$OPTARG; have_pat=1 ;;
        h) usage 0 ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

if [ "$have_pat" -eq 0 ]; then
    if [ $# -lt 1 ]; then
        usage
    fi
    pat=$1
    shift
fi

# If no files given and stdin is a terminal, there is nothing to read
if [ $# -eq 0 ] && [ -t 0 ]; then
    usage
fi

# -a: process raw bytes so invalid multibyte sequences / NULs don't affect matching
if [ "$binary" -eq 1 ]; then
    LC_ALL=C
    export LC_ALL
fi

awk -v pat="$pat" -v invert="$invert" '
BEGIN {
    rec = ""
    have = 0
    found = 0
    IGNORECASE = 1
}

function flush() {
    if (have && found != invert) {
        print rec
    }
}

# Start of a new logical record
/^[^ \t]/ {
    flush()
    rec = $0
    have = 1
    found = ($0 ~ pat)
    next
}

# Continuation line (or leading indented lines before the first record)
{
    rec = have ? rec ORS $0 : $0
    have = 1
    if (!found && $0 ~ pat) {
        found = 1
    }
}

END {
    flush()
}
' "$@"
