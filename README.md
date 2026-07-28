# Prompt-CLI

Terminal client for the [Google Gemini API](https://ai.google.dev) with markdown rendering.
Installed as `ask`.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Bash](https://img.shields.io/badge/Bash-5.0%2B-4EAA25?logo=gnubash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Debian](https://img.shields.io/badge/Debian-Supported-A81D33?logo=debian&logoColor=white)](https://www.debian.org)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-Supported-E95420?logo=ubuntu&logoColor=white)](https://ubuntu.com)

## Why this exists

A minimal way to query Google Gemini from the terminal without installing Node.js or a full agent.

- One command → one answer
- Free tier via Google AI Studio (no card required to start)
- Markdown rendered as ANSI in the terminal
- No conversation history, no tools, no file access — by design

If you need an agent that edits files, runs shell commands, or keeps chat context, use the official [Gemini CLI](https://github.com/google-gemini/gemini-cli) instead.

## Usage

### Syntax

```bash
ask [--model NAME] <text>
```

### Examples

```bash
ask "explain bash syntax"
ask --model gemini-2.5-pro "review this diff"
```

## Structure

```text
prompt-cli/
├── ask            # entry point: argument parsing + orchestration only
├── install.sh     # copies files into place, sets up PATH, installs deps
├── uninstall.sh   # reverses install.sh
├── lib/
│   ├── paths.sh   # shared path/config constants (sourced by all three scripts above)
│   ├── ui.sh      # colors, box-drawing helpers
│   ├── config.sh  # API key setup/reset
│   ├── api.sh     # Gemini request + timing
│   └── render.py  # markdown -> ANSI renderer
└── README.md
```

## Install

```bash
git clone https://github.com/rebootless/prompt-cli
cd prompt-cli
chmod +x install.sh
./install.sh
source ~/.bashrc
ask --setup
```

`install.sh` installs `python3`, `jq`, `curl` via `apt-get` if missing, copies
`ask` and `lib/` to `~/.local/lib/prompt-cli/`, symlinks `~/.local/bin/ask`,
and adds `~/.local/bin` to `PATH` in `.bashrc` (idempotent marker block).

## Getting an API key

1. Open [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with a Google account
3. Create an API key (free tier is available)
4. Run:

```bash
ask --setup
```

Paste the key when prompted. It is stored at ~/.config/prompt-cli/keys.env with mode 600.

To replace the key later:

```bash
ask --reset
```

## Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Removes the installed files and PATH block. Asks separately before deleting
`~/.config/prompt-cli` (your stored API key), since that step is irreversible.

## Notes

- API key is stored at `~/.config/prompt-cli/keys.env`, `chmod 600`.
- `ask` resolves its own real path at runtime, so `lib/` is always found
  relative to wherever `install.sh` copied it — no hardcoded paths.
- `prompt` is already taken by oh-my-bash.

## License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.
