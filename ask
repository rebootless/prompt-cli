#!/bin/bash

set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || echo "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=lib/paths.sh
source "$LIB_DIR/paths.sh"
# shellcheck source=lib/ui.sh
source "$LIB_DIR/ui.sh"
# shellcheck source=lib/config.sh
source "$LIB_DIR/config.sh"
# shellcheck source=lib/api.sh
source "$LIB_DIR/api.sh"

check_deps() {
    local missing=()
    for bin in python3 jq curl; do
        command -v "$bin" &>/dev/null || missing+=("$bin")
    done
    if (( ${#missing[@]} > 0 )); then
        echo "Missing dependencies: ${missing[*]}" >&2
        echo "Re-run install.sh from the prompt-cli repo, or install them manually." >&2
        exit 1
    fi
}

render_markdown() {
    local width="${1:-76}"
    MD_WIDTH="$width" python3 "$LIB_DIR/render.py"
}

print_help() {
    cat <<EOF
ask - send a prompt to Google Gemini from the command line

Note: \`prompt\` is already used by oh-my-bash; use \`ask\` instead.

Usage:
  ask [--model NAME] <text>      Send <text> as a prompt and print the response
  ask --models                   List models that support generateContent
  ask --setup                    Enter the API key (only if not set yet)
  ask --reset                    Clear the stored API key and enter a new one
  ask --help                     Show this help

Options:
  --model NAME   Override the model for this request (default: $DEFAULT_MODEL)
                 Examples: gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite
                 Availability depends on your account/region.

API key storage: $KEYS_FILE
To remove ask entirely, run uninstall.sh from the prompt-cli repo.

Note: token counts shown after each response come from the API response
itself. Rate limits and quotas are NOT part of that response - check and
manage them in Google AI Studio / Google Cloud Console.
EOF
}

main() {
    case "${1:-}" in
        --help|-h)
            print_help
            exit 0
            ;;
        --setup)
            if [[ -f "$KEYS_FILE" ]]; then
                echo "A key is already configured. Use 'ask --reset' to replace it."
                exit 0
            fi
            run_setup
            exit 0
            ;;
        --reset)
            run_reset
            exit 0
            ;;
        --models)
            check_deps
            if [[ ! -f "$KEYS_FILE" ]]; then
                echo "No API key configured yet, running first-time setup..."
                run_setup
            fi
            # shellcheck disable=SC1090
            source "$KEYS_FILE"
            list_models
            exit 0
            ;;
    esac

    if [[ $# -eq 0 ]]; then
        echo "Usage:" >&2
        echo "  ask [--model NAME] <text>" >&2
        echo "For details run:" >&2
        echo "  ask --help" >&2
        exit 1
    fi

    check_deps

    if [[ ! -f "$KEYS_FILE" ]]; then
        echo "No API key configured yet, running first-time setup..."
        run_setup
    fi

    # shellcheck disable=SC1090
    source "$KEYS_FILE"

    # Parse --model NAME / --model=NAME anywhere in the arguments;
    # everything else is joined back together as the prompt text.
    local model="$DEFAULT_MODEL"
    local -a prompt_words=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --model)
                if [[ $# -lt 2 ]]; then
                    echo "--model requires a value" >&2
                    exit 1
                fi
                model="$2"
                shift 2
                ;;
            --model=*)
                model="${1#--model=}"
                shift
                ;;
            *)
                prompt_words+=("$1")
                shift
                ;;
        esac
    done

    if [[ ${#prompt_words[@]} -eq 0 ]]; then
        echo "Usage: ask [--model NAME] <text>" >&2
        exit 1
    fi

    local prompt_text="${prompt_words[*]}"
    if [[ -z "${prompt_text// /}" ]]; then
        echo "Prompt text is empty." >&2
        exit 1
    fi

    local start end resp status
    start=$EPOCHREALTIME
    fetch_gemini "$prompt_text" "$model"
    end=$EPOCHREALTIME
    resp="$REPLY"
    status="$REPLY_STATUS"

    if [[ "$status" -ne 0 ]]; then
        echo "Connection to Gemini API failed (curl exit code $status)." >&2
        exit 1
    fi

    if [[ -z "$resp" ]]; then
        echo "Empty response from Gemini API." >&2
        exit 1
    fi

    local err_msg
    err_msg=$(jq -r '.error.message // empty' <<< "$resp" 2>/dev/null || true)
    if [[ -n "$err_msg" ]]; then
        echo "Gemini error. $err_msg" >&2
        echo "If your key may be invalid, run:" >&2
        echo "  ask --reset" >&2
        echo "Or check the model name with --model." >&2
        exit 1
    fi

    local block_reason
    block_reason=$(jq -r '.promptFeedback.blockReason // empty' <<< "$resp" 2>/dev/null || true)
    if [[ -n "$block_reason" ]]; then
        echo "Gemini blocked the prompt (reason: $block_reason)." >&2
        exit 1
    fi

    local text
    text=$(jq -r '[.candidates[0]?.content.parts[]? | select(.thought != true) | (.text // "")] | join("")' <<< "$resp" 2>/dev/null || true)

    if [[ -z "$text" ]]; then
        local finish
        finish=$(jq -r '.candidates[0].finishReason // "unknown"' <<< "$resp" 2>/dev/null || echo "unknown")
        echo "No text in response (finishReason: $finish)." >&2
        exit 1
    fi

    local width
    width=$(tput cols 2>/dev/null || echo 80)
    (( width > 120 )) && width=120
    (( width < 60 )) && width=60

    box_top "Gemini · ${model}" "$width"
    printf '%s\n' "$text" | render_markdown $((width - 4)) | sed "s/^/${ACCENT}│${RESET} /"

    local pt ct tt th elapsed info
    pt=$(jq -r '.usageMetadata.promptTokenCount // "?"' <<< "$resp")
    ct=$(jq -r '.usageMetadata.candidatesTokenCount // "?"' <<< "$resp")
    tt=$(jq -r '.usageMetadata.totalTokenCount // "?"' <<< "$resp")
    th=$(jq -r '.usageMetadata.thoughtsTokenCount // 0' <<< "$resp")
    elapsed=$(elapsed_seconds "$start" "$end")

    info="${pt} in · ${ct} out"
    if [[ "$th" != "0" ]]; then
        info+=" · ${th} think"
    fi
    info+=" · ${tt} total · ${elapsed}s"

    box_bottom "$info" "$width"
}

main "$@"
