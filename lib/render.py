#!/usr/bin/env python3
"""
Markdown-to-ANSI renderer for ask.

Reads markdown from stdin and prints ANSI-styled terminal output.
Called by `ask` as: MD_WIDTH="$width" python3 lib/render.py

Width comes from the MD_WIDTH environment variable (default 76, min 50).
"""

import os
import re
import sys
from typing import List

WIDTH = max(50, int(os.environ.get("MD_WIDTH", "76")))
ACCENT = "\033[36m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def style(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def strip_control(s: str) -> str:
    return CONTROL_RE.sub("", s)


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def vislen(s: str) -> int:
    return len(strip_ansi(s))


def truncate_ansi(s: str, max_width: int) -> str:
    """Truncate an ANSI-styled string to at most max_width visible columns,
    appending an ellipsis. ANSI escape sequences don't count toward width."""
    if max_width <= 0:
        return ""
    if vislen(s) <= max_width:
        return s
    if max_width == 1:
        return "…"

    out = []
    visible = 0
    limit = max_width - 1
    i = 0
    while i < len(s):
        m = ANSI_RE.match(s, i)
        if m:
            out.append(m.group(0))
            i = m.end()
            continue
        if visible >= limit:
            break
        out.append(s[i])
        visible += 1
        i += 1
    out.append(RESET)
    out.append("…")
    return "".join(out)


def protect_escapes(text: str):
    stash = {}
    i = 0

    def repl(m):
        nonlocal i
        key = f"\x00ESC{i}\x00"
        stash[key] = m.group(1)
        i += 1
        return key

    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>|~])", repl, text)
    return text, stash


def restore_escapes(text: str, stash):
    for k, v in stash.items():
        text = text.replace(k, v)
    return text


def inline_format(text: str) -> str:
    text = strip_control(text)
    text, stash = protect_escapes(text)

    # Images
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]+)")?\)',
        lambda m: style(f"🖼  {m.group(1)} ({m.group(2)})", DIM),
        text,
    )

    # Autolinks
    text = re.sub(r'<(https?://[^>]+)>', lambda m: style(m.group(1), UNDERLINE), text)

    # Inline code placeholders
    code_stash = {}
    ci = 0

    def code_repl(m):
        nonlocal ci
        key = f"\x01CODE{ci}\x01"
        code_stash[key] = style(m.group(1), ACCENT)
        ci += 1
        return key

    text = re.sub(r'`([^`]+)`', code_repl, text)

    # Links
    def link_repl(m):
        label = inline_format(m.group(1)) if any(x in m.group(1) for x in "*`_~[") else m.group(1)
        return f"{style(label, UNDERLINE)} {style(f'({m.group(2)})', DIM)}"

    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]+)")?\)', link_repl, text)

    # Strong / Emphasis / Strike
    text = re.sub(r'(\*\*\*|___)(.+?)\1', lambda m: style(m.group(2), BOLD, ITALIC), text)
    text = re.sub(r'(\*\*|__)(.+?)\1', lambda m: style(m.group(2), BOLD), text)
    text = re.sub(r'~~(.+?)~~', lambda m: style(m.group(1), DIM), text)
    text = re.sub(r'(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)', lambda m: style(m.group(1), ITALIC), text)
    text = re.sub(r'(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)', lambda m: style(m.group(1), ITALIC), text)

    for k, v in code_stash.items():
        text = text.replace(k, v)

    return restore_escapes(text, stash)


def wrap_ansi(text: str, width: int, indent: str = "", subsequent_indent: str | None = None) -> List[str]:
    if subsequent_indent is None:
        subsequent_indent = indent
    if width <= 1:
        return [text]

    raw_tokens = re.split(r'(\s+)', text)
    lines = []
    current = indent
    current_len = vislen(indent)
    limit = max(10, width)

    for tok in raw_tokens:
        if tok == "":
            continue
        if tok.isspace():
            if current.strip():
                current += tok
                current_len += len(tok)
            continue
        tok_len = vislen(tok)
        if current_len + tok_len > limit and current.strip():
            lines.append(current.rstrip())
            current = subsequent_indent + tok
            current_len = vislen(subsequent_indent) + tok_len
        else:
            current += tok
            current_len += tok_len
    if current.strip() or not lines:
        lines.append(current.rstrip())
    return lines


def is_table_candidate(line: str) -> bool:
    stripped = line.strip()
    return stripped.count("|") >= 2 and not stripped.startswith("```")


def split_table_row(line: str):
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def parse_alignment(cell: str) -> str:
    cell = cell.strip().replace(" ", "")
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    if cell.startswith(":"):
        return "left"
    if cell.endswith(":"):
        return "right"
    return "left"


def is_separator_row(cells):
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells)


def render_table(rows: List[str]):
    if len(rows) < 2:
        for r in rows:
            print(inline_format(r))
        return

    parsed = [split_table_row(r) for r in rows]
    sep_idx = None
    for i, cells in enumerate(parsed):
        if is_separator_row(cells):
            sep_idx = i
            break

    if sep_idx is None:
        for r in rows:
            print(inline_format(r))
        return

    header = parsed[0]
    align_row = parsed[sep_idx]
    body = [r for i, r in enumerate(parsed) if i not in (0, sep_idx)]
    cols = max(len(header), max((len(r) for r in body), default=0), len(align_row))
    widths = [0] * cols

    all_rows = [header] + body
    for row in all_rows:
        for i in range(cols):
            cell = inline_format(row[i]) if i < len(row) else ""
            widths[i] = max(widths[i], vislen(cell))

    aligns = [parse_alignment(align_row[i]) if i < len(align_row) else "left" for i in range(cols)]

    # If the natural table width overflows the terminal, shrink the widest
    # columns one column-width at a time until it fits (down to a minimum
    # width); overflowing cells get truncated with an ellipsis when rendered.
    overhead = 3 * cols + 1
    avail = max(20, WIDTH)
    min_w = 3
    total_width = sum(widths) + overhead
    if total_width > avail:
        excess = total_width - avail
        while excess > 0 and any(w > min_w for w in widths):
            idx = max(range(cols), key=lambda i: widths[i])
            widths[idx] -= 1
            excess -= 1
        total_width = sum(widths) + overhead

    def pad(cell: str, idx: int) -> str:
        target = widths[idx]
        cell = truncate_ansi(cell, target)
        vis = vislen(cell)
        if vis >= target:
            return cell
        gap = target - vis
        if aligns[idx] == "right":
            return " " * gap + cell
        if aligns[idx] == "center":
            left = gap // 2
            right = gap - left
            return " " * left + cell + " " * right
        return cell + " " * gap

    def render_row(row, header_row=False):
        cells = []
        for i in range(cols):
            cell = inline_format(row[i]) if i < len(row) else ""
            if header_row:
                cell = style(cell, BOLD)
            cells.append(pad(cell, i))
        print(style("│", ACCENT) + " " + f" {style('│', ACCENT)} ".join(cells) + " " + style("│", ACCENT))

    print(style("┌" + "─" * (total_width - 2) + "┐", ACCENT))
    render_row(header, header_row=True)
    print(style("├" + "─" * (total_width - 2) + "┤", ACCENT))
    for row in body:
        render_row(row)
    print(style("└" + "─" * (total_width - 2) + "┘", ACCENT))


def flush_paragraph(buf):
    if not buf:
        return
    text = " ".join(buf).strip()
    if not text:
        buf.clear()
        return
    for line in wrap_ansi(inline_format(text), WIDTH):
        print(line)
    buf.clear()


in_code = False
code_lang = ""
table_buf = []
para_buf = []


def flush_table():
    global table_buf
    if table_buf:
        render_table(table_buf)
        table_buf = []


def flush_para():
    global para_buf
    if para_buf:
        flush_paragraph(para_buf)
        para_buf = []


def flush_all():
    flush_table()
    flush_para()


for raw in sys.stdin:
    line = raw.rstrip("\n").rstrip("\r")

    if line.startswith("```"):
        flush_all()
        fence_lang = line[3:].strip()
        if not in_code:
            in_code = True
            code_lang = fence_lang
            label = f" {code_lang}" if code_lang else ""
            print(style(f"╭─ code{label}", ACCENT))
        else:
            in_code = False
            print(style("╰─", ACCENT))
        continue

    if in_code:
        if line.strip():
            print(style("  " + strip_control(line), DIM))
        else:
            print("")
        continue

    if not line.strip():
        flush_all()
        print("")
        continue

    if is_table_candidate(line):
        flush_para()
        table_buf.append(line)
        continue
    elif table_buf:
        flush_table()

    if re.match(r'^(?:-{3,}|\*{3,}|_{3,})\s*$', line):
        flush_para()
        print(style("─" * min(WIDTH, 72), DIM))
        continue

    # Headings
    m = re.match(r'^(#{1,6})\s+(.*)$', line)
    if m:
        flush_all()
        level = len(m.group(1))
        title = inline_format(m.group(2).strip())
        plain = strip_ansi(title)
        if level == 1:
            print(style(title, ACCENT, BOLD, UNDERLINE))
            print(style("═" * min(WIDTH, max(24, len(plain))), ACCENT))
        elif level == 2:
            print(style(title, ACCENT, BOLD))
            print(style("─" * min(WIDTH, max(20, len(plain))), ACCENT))
        else:
            indent = "  " * (level - 3)
            print(f"{indent}{style(title, ACCENT, BOLD)}")
        continue

    # Blockquotes
    m = re.match(r'^(\s*(?:>\s*)+)(.*)$', line)
    if m:
        flush_para()
        prefix = m.group(1)
        depth = prefix.count('>')
        body = m.group(2).strip()
        quote = "  " * (depth - 1)
        marker = style("▌", ACCENT)
        rendered = inline_format(body)
        for wrapped in wrap_ansi(rendered, WIDTH - len(quote) - 2, indent="", subsequent_indent=""):
            print(f"{quote}{marker} {wrapped}")
        continue

    # Task list
    m = re.match(r'^(\s*)([-*+])\s+\[( |x|X)\]\s+(.*)$', line)
    if m:
        flush_para()
        indent, _, checked, body = m.groups()
        mark = "☑" if checked.lower() == "x" else "☐"
        print(f"{indent}{style(mark, ACCENT)} {inline_format(body)}")
        continue

    # Bullets
    m = re.match(r'^(\s*)([-*+])\s+(.*)$', line)
    if m:
        flush_para()
        indent, _, body = m.groups()
        rendered = inline_format(body)
        for i, wrapped in enumerate(wrap_ansi(rendered, WIDTH - len(indent) - 2, indent="", subsequent_indent="  ")):
            bullet = style("•", ACCENT) if i == 0 else " "
            print(f"{indent}{bullet} {wrapped}" if i == 0 else f"{indent}  {wrapped}")
        continue

    # Numbered lists
    m = re.match(r'^(\s*)(\d+)[.)]\s+(.*)$', line)
    if m:
        flush_para()
        indent, num, body = m.groups()
        rendered = inline_format(body)
        prefix = f"{indent}{style(num + '.', ACCENT)} "
        subsequent = " " * vislen(prefix)
        for i, wrapped in enumerate(wrap_ansi(rendered, WIDTH - vislen(prefix), indent="", subsequent_indent=subsequent)):
            if i == 0:
                print(prefix + wrapped)
            else:
                print(wrapped)
        continue

    # Definition lines: "Term: definition text" (short label, non-empty body)
    m = re.match(r'^(\s*)([^\s:][^:]{0,48})\s*:\s+(\S.*)$', line)
    if m:
        flush_para()
        term, definition = m.group(2), m.group(3)
        print(style(term, BOLD))
        for wrapped in wrap_ansi(inline_format(definition), WIDTH - 2, indent="  ", subsequent_indent="  "):
            print(f"  {style('→', ACCENT)} {wrapped.strip()}")
        continue

    para_buf.append(line)

flush_all()
