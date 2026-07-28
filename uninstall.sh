#!/bin/bash

set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=lib/paths.sh
source "$SCRIPT_DIR/lib/paths.sh"

if [[ ! -e "$ASK_PATH" && ! -d "$APP_DIR" && ! -d "$CONFIG_DIR" ]]; then
    echo "Nothing to remove: no ask install found."
    exit 0
fi

echo "==> Remove ask"

echo "This will permanently delete:"
echo "  $ASK_PATH"
echo "  $APP_DIR"

read -rp "Type 'yes' to confirm removal: " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Cancelled."
    exit 0
fi

rm -f "$ASK_PATH"
rm -rf "$APP_DIR"
echo "Removed $ASK_PATH and $APP_DIR"

if grep -qF "$MARK_START" "$BASHRC" 2>/dev/null; then
    sed -i "/${MARK_START}/,/${MARK_END}/d" "$BASHRC"
    echo "Removed PATH block from $BASHRC"
fi

if [[ -d "$CONFIG_DIR" ]]; then
    echo ""
    echo -e "${RED}$CONFIG_DIR still holds your stored Gemini API key.${NC}"
    read -rp "Also delete it? Type 'yes' to confirm: " confirm_key
    if [[ "$confirm_key" == "yes" ]]; then
        rm -rf "$CONFIG_DIR"
        echo "Removed $CONFIG_DIR"
    else
        echo "Kept $CONFIG_DIR"
    fi
fi

echo ""
echo "ask uninstalled."
