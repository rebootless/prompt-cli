#!/bin/bash

ACCENT=$'\033[36m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
UNDERLINE=$'\033[4m'
RED=$'\033[0;31m'
RESET=$'\033[0m'

repeat_char() {
    local char="$1" count="$2" out
    if (( count <= 0 )); then return 0; fi
    printf -v out '%*s' "$count" ''
    printf '%s' "${out// /$char}"
}

box_top() {
    local title="$1" width="$2"
    local label=" ${title} "
    local inner=$(( width - ${#label} - 3 ))
    (( inner < 1 )) && inner=1
    printf '%s╭─%s%s%s%s╮%s\n' "$ACCENT" "$RESET$BOLD" "$label" "$RESET$ACCENT" "$(repeat_char '─' "$inner")" "$RESET"
}

box_bottom() {
    local info="$1" width="$2"
    local label=" ${info} "
    local inner=$(( width - ${#label} - 3 ))
    (( inner < 1 )) && inner=1
    printf '%s╰─%s%s%s%s╯%s\n' "$ACCENT" "$RESET$DIM" "$label" "$RESET$ACCENT" "$(repeat_char '─' "$inner")" "$RESET"
}
