#!/bin/bash

# Where the launcher symlink lives (must be on PATH; install.sh adds it if needed)
INSTALL_DIR="$HOME/.local/bin"
ASK_PATH="$INSTALL_DIR/ask"

# Where the actual app files (ask + lib/) get copied to
APP_DIR="$HOME/.local/lib/prompt-cli"

# API key storage
CONFIG_DIR="$HOME/.config/prompt-cli"
KEYS_FILE="$CONFIG_DIR/keys.env"

# .bashrc PATH block markers
MARK_START="# >>> prompt-cli >>>"
MARK_END="# <<< prompt-cli <<<"
BASHRC="$HOME/.bashrc"

# Gemini API
GEMINI_KEY_URL="https://aistudio.google.com/app/apikey"
GEMINI_API_BASE="https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL="gemini-2.5-flash"
