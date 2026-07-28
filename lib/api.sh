#!/bin/bash

# Compute end - start (both in $EPOCHREALTIME "seconds.microseconds" format)
# as a "N.N" seconds string, using only bash builtins.
elapsed_seconds() {
    local start="$1" end="$2"
    local s_sec="${start%%.*}" s_us="${start#*.}"
    local e_sec="${end%%.*}" e_us="${end#*.}"
    local total_us=$(( (10#$e_sec - 10#$s_sec) * 1000000 + (10#$e_us - 10#$s_us) ))
    (( total_us < 0 )) && total_us=0
    printf '%d.%01d' $(( total_us / 1000000 )) $(( (total_us / 100000) % 10 ))
}

# Fetches the model list from the Gemini API and prints the ones that
# support generateContent, with display name and token limits. Requires
# $GEMINI_API_KEY to be set (sourced from $KEYS_FILE by the caller).
list_models() {
    local resp err_msg

    resp=$(curl -sS --max-time 30 "${GEMINI_API_BASE}?pageSize=1000&key=${GEMINI_API_KEY}")

    if [[ -z "$resp" ]]; then
        echo "Empty response from Gemini API." >&2
        exit 1
    fi

    err_msg=$(jq -r '.error.message // empty' <<< "$resp" 2>/dev/null || true)
    if [[ -n "$err_msg" ]]; then
        echo "Gemini error: $err_msg" >&2
        exit 1
    fi

    echo "==> Available models (generateContent)"
    echo ""

    jq -r '
        .models[]
        | select(.supportedGenerationMethods // [] | index("generateContent"))
        | [(.name | sub("^models/"; "")), (.displayName // ""), (.inputTokenLimit | tostring), (.outputTokenLimit | tostring)]
        | @tsv
    ' <<< "$resp" | while IFS=$'\t' read -r name display in_lim out_lim; do
        printf "  %s%-28s%s %s%s%s\n" "$ACCENT$BOLD" "$name" "$RESET" "$DIM" "$display" "$RESET"
        printf "  %sin: %s tok · out: %s tok%s\n\n" "$DIM" "$in_lim" "$out_lim" "$RESET"
    done

    echo "Use with: ask --model NAME <text>"
}

# Sends $1 as a prompt to model $2, polls a spinner while curl runs in the
# background, and sets:
#   REPLY        - raw response body (JSON, or empty on connection failure)
#   REPLY_STATUS - curl exit status
fetch_gemini() {
    local prompt="$1" model="$2"
    local body tmpfile pid status=0 spin i=0

    body=$(jq -n --arg p "$prompt" '{contents:[{parts:[{text:$p}]}]}')
    tmpfile=$(mktemp)
    spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    curl -sS --max-time 120 \
        "${GEMINI_API_BASE}/${model}:generateContent?key=${GEMINI_API_KEY}" \
        -H "content-type: application/json" \
        -d "$body" -o "$tmpfile" &
    pid=$!

    trap 'kill "$pid" 2>/dev/null; rm -f "$tmpfile"; printf "\r\033[2K"; echo "Cancelled." >&2; exit 130' INT TERM

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r\033[2K%s%s%s %sAsking%s %s%s%s..." \
            "$ACCENT" "${spin:i++%${#spin}:1}" "$RESET" \
            "$DIM" "$RESET" "$BOLD$ACCENT" "$model" "$RESET"
        sleep 0.08
    done
    wait "$pid" || status=$?
    trap - INT TERM
    printf "\r\033[2K"

    REPLY=$(cat "$tmpfile")
    REPLY_STATUS=$status
    rm -f "$tmpfile"
}
