#!/bin/bash

set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=lib/paths.sh
source "$SCRIPT_DIR/lib/paths.sh"

echo "==> Checking dependencies"

missing=()
for bin in python3 jq curl; do
    command -v "$bin" &>/dev/null || missing+=("$bin")
done

if (( ${#missing[@]} > 0 )); then
    sudo_cmd=""
    if [[ $EUID -ne 0 ]]; then
        if command -v sudo &>/dev/null; then
            sudo_cmd="sudo"
            echo "Requesting root privileges to install missing packages..."
        else
            echo "Root privileges required but 'sudo' is not installed. Please run as root." >&2
            exit 1
        fi
    fi
    echo "Installing: ${missing[*]}"
    $sudo_cmd apt-get update -y
    $sudo_cmd apt-get install -y "${missing[@]}"
    echo "Dependencies installed."
else
    echo "All dependencies already present."
fi

echo "==> Installing app files"

mkdir -p "$APP_DIR"
cp "$SCRIPT_DIR/ask" "$APP_DIR/ask"
chmod +x "$APP_DIR/ask"
rm -rf "$APP_DIR/lib"
cp -r "$SCRIPT_DIR/lib" "$APP_DIR/lib"
echo "Copied ask + lib/ to $APP_DIR"

mkdir -p "$INSTALL_DIR"
ln -sf "$APP_DIR/ask" "$ASK_PATH"
echo "Linked $ASK_PATH -> $APP_DIR/ask"

echo "==> PATH setup"

if grep -qF "$MARK_START" "$BASHRC" 2>/dev/null; then
    echo "PATH already configured in $BASHRC, skipping."
else
    {
        echo ""
        echo "$MARK_START"
        echo "export PATH=\"\$PATH:$INSTALL_DIR\""
        echo "$MARK_END"
    } >> "$BASHRC"
    echo "Added $INSTALL_DIR to PATH in $BASHRC"
fi

echo ""
echo "==> Summary"

echo ""
echo "Installed:"
echo "  $ASK_PATH -> $APP_DIR/ask"
echo "Update PATH (or open a new terminal) with:"
echo "  source $BASHRC"
echo "Start with:"
echo "  ask --setup"
