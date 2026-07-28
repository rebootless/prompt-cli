#!/bin/bash

run_setup() {
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"

    echo "==> Gemini (Google) setup"
    echo "Free tier available, no billing required."
    echo "Get an API key here: $GEMINI_KEY_URL"
    read -rsp "Enter Gemini API key: " key
    echo

    if [[ -z "$key" ]]; then
        echo "Empty key, aborting setup" >&2
        exit 1
    fi

    printf 'GEMINI_API_KEY=%s\n' "$key" > "$KEYS_FILE"
    chmod 600 "$KEYS_FILE"
    echo "Setup complete. Key stored in $KEYS_FILE"
}

run_reset() {
    if [[ -f "$KEYS_FILE" ]]; then
        read -rp "Clear the stored API key and enter a new one? [y/N]: " confirm
        case "${confirm,,}" in
            y|yes)
                rm -f "$KEYS_FILE"
                echo "Stored key cleared."
                ;;
            *)
                echo "Cancelled."
                return 0
                ;;
        esac
    fi
    run_setup
}
