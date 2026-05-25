#!/usr/bin/env python3
"""Generate Serendipity theme ports from VS Code theme JSON files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
PROJECTS = ROOT.parent
PALETTE_OUT = PROJECTS / "color-palette"
TEMPLATE_OUT = PROJECTS / "template-for-repositories"

VARIANTS = [
    ("midnight", "serendipity-midnight.json"),
    ("morning", "serendipity-morning.json"),
    ("sunset", "serendipity-sunset.json"),
]

LICENSE = """MIT License

Copyright (c) 2022 Serendipity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

HEADER = "https://raw.githubusercontent.com/Serendipity-Theme/assets/main/githubHeader.png"
WEBSITE = "https://www.michaelandreuzza.com/vscode/serendipity/"
PREFIX = "serendipity"


@dataclass
class Tokens:
    variant_id: str
    name: str
    appearance: str
    background: str
    foreground: str
    surface: str
    cursor: str
    selection_bg: str
    comment: str
    accent: str
    accent_fg: str
    muted: str
    keyword: str
    string: str
    variable: str
    function: str
    type_color: str
    constant: str
    operator: str
    error: str
    terminal: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "appearance": self.appearance,
            "background": self.background,
            "foreground": self.foreground,
            "surface": self.surface,
            "cursor": self.cursor,
            "selection_bg": self.selection_bg,
            "comment": self.comment,
            "accent": self.accent,
            "accent_fg": self.accent_fg,
            "muted": self.muted,
            "syntax": {
                "keyword": self.keyword,
                "string": self.string,
                "variable": self.variable,
                "function": self.function,
                "type": self.type_color,
                "constant": self.constant,
                "operator": self.operator,
                "error": self.error,
            },
            "terminal": self.terminal,
        }


def hex6(value: str | None, fallback: str = "#000000") -> str:
    if not value:
        return fallback
    value = value.strip().lower()
    if value in ("#0000", "transparent"):
        return fallback
    if len(value) >= 7:
        return value[:7]
    return fallback


def with_alpha(color: str, alpha: str = "33") -> str:
    return f"{hex6(color)}{alpha}"


def hex_rgb_float(color: str) -> tuple[float, float, float]:
    c = hex6(color).lstrip("#")
    return int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255


def scope_fg(token_colors: list, *needles: str) -> str | None:
    for rule in token_colors:
        scopes = rule.get("scope")
        fg = rule.get("settings", {}).get("foreground")
        if not fg:
            continue
        items = [scopes] if isinstance(scopes, str) else scopes or []
        for item in items:
            for needle in needles:
                if item == needle or item.startswith(needle):
                    return fg
    return None


def load_tokens(variant_id: str, filename: str) -> Tokens:
    data = json.loads((THEMES / filename).read_text(encoding="utf-8"))
    colors = data["colors"]
    token_colors = data.get("tokenColors", [])

    bg = hex6(colors.get("editor.background"))
    fg = hex6(colors.get("editor.foreground"))
    surface = hex6(
        colors.get("banner.background")
        or colors.get("sideBar.background")
        or colors.get("activityBar.background")
        or bg
    )

    terminal = {
        "black": hex6(colors.get("terminal.ansiBlack")),
        "red": hex6(colors.get("terminal.ansiRed")),
        "green": hex6(colors.get("terminal.ansiGreen")),
        "yellow": hex6(colors.get("terminal.ansiYellow")),
        "blue": hex6(colors.get("terminal.ansiBlue")),
        "magenta": hex6(colors.get("terminal.ansiMagenta")),
        "cyan": hex6(colors.get("terminal.ansiCyan")),
        "white": hex6(colors.get("terminal.ansiWhite")),
        "bright_black": hex6(colors.get("terminal.ansiBrightBlack")),
        "bright_red": hex6(colors.get("terminal.ansiBrightRed")),
        "bright_green": hex6(colors.get("terminal.ansiBrightGreen")),
        "bright_yellow": hex6(colors.get("terminal.ansiBrightYellow")),
        "bright_blue": hex6(colors.get("terminal.ansiBrightBlue")),
        "bright_magenta": hex6(colors.get("terminal.ansiBrightMagenta")),
        "bright_cyan": hex6(colors.get("terminal.ansiBrightCyan")),
        "bright_white": hex6(colors.get("terminal.ansiBrightWhite")),
    }

    return Tokens(
        variant_id=variant_id,
        name=data["name"],
        appearance=data.get("type", "dark"),
        background=bg,
        foreground=fg,
        surface=surface,
        cursor=hex6(colors.get("editorCursor.foreground"), fg),
        selection_bg=colors.get("editor.selectionBackground", with_alpha(fg)),
        comment=hex6(scope_fg(token_colors, "comment") or colors.get("descriptionForeground")),
        accent=hex6(colors.get("button.background")),
        accent_fg=hex6(colors.get("button.foreground"), bg),
        muted=hex6(colors.get("descriptionForeground")),
        keyword=hex6(scope_fg(token_colors, "keyword", "storage.type"), fg),
        string=hex6(scope_fg(token_colors, "string"), fg),
        variable=hex6(scope_fg(token_colors, "variable"), fg),
        function=hex6(scope_fg(token_colors, "support.function"), fg),
        type_color=hex6(
            scope_fg(token_colors, "entity.name.type", "entity.name.tag", "entity.name.section"),
            fg,
        ),
        constant=hex6(scope_fg(token_colors, "constant"), fg),
        operator=hex6(scope_fg(token_colors, "punctuation"), colors.get("descriptionForeground", fg)),
        error=hex6(colors.get("errorForeground") or scope_fg(token_colors, "invalid"), fg),
        terminal=terminal,
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def port_readme(title: str, install: str, files: list[str]) -> str:
    variants = "\n".join(
        f"- **{vid.title()}** — {appearance}"
        for vid, appearance in [
            ("midnight", "dark"),
            ("morning", "light"),
            ("sunset", "dark"),
        ]
    )
    file_list = ", ".join(f"`{name}`" for name in files)
    return f"""![Serendipity]({HEADER})

# {title}

Elegant, minimal, and clean color palette for your tools.

See other interfaces at the [official website]({WEBSITE}).

## Available themes

{variants}

## Installation

{install}

Available files: {file_list}.

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
"""


def write_port(port: str, install: str, title: str, files: list[str], extra: dict[str, str] | None = None) -> None:
    port_dir = PROJECTS / port
    write(port_dir / "LICENSE", LICENSE + "\n")
    write(port_dir / "README.md", port_readme(title, install, files))
    if extra:
        for rel, content in extra.items():
            write(port_dir / rel, content)


def terminal_palette_lines(t: dict[str, str]) -> list[str]:
    order = [
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
    ]
    return [t[k] for k in order]


# --- Existing port emitters (adapted for Serendipity) ---


def ghostty(tokens: Tokens) -> str:
    t = tokens.terminal
    lines = [
        f"background = {tokens.background}",
        f"foreground = {tokens.foreground}",
        f"cursor-color = {tokens.cursor}",
        f"cursor-text = {tokens.background}",
        f"selection-background = {tokens.selection_bg}",
        f"selection-foreground = {tokens.foreground}",
    ]
    for idx, key in enumerate([
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
    ]):
        lines.append(f"palette = {idx}={t[key]}")
    return "\n".join(lines) + "\n"


def starship(tokens: Tokens) -> str:
    palette = tokens.variant_id
    return f"""# Serendipity {tokens.name}
palette = "{palette}"

[palettes.{palette}]
background = "{tokens.background}"
current_line = "{tokens.surface}"
foreground = "{tokens.foreground}"
comment = "{tokens.comment}"
cyan = "{tokens.function}"
green = "{tokens.type_color}"
orange = "{tokens.variable}"
pink = "{tokens.variable}"
purple = "{tokens.string}"
red = "{tokens.error}"
yellow = "{tokens.constant}"

[character]
success_symbol = "[✔]({tokens.keyword})"
error_symbol = "[✘]({tokens.error})"

[directory]
style = "bold {tokens.type_color}"

[git_branch]
style = "bold {tokens.function}"

[git_status]
style = "bold {tokens.variable}"
"""


def lazygit(tokens: Tokens) -> str:
    return f"""# Serendipity {tokens.name}
theme:
  activeBorderColor:
    - "{tokens.accent}"
    - bold
  inactiveBorderColor:
    - "{tokens.type_color}"
  searchingActiveBorderColor:
    - "{tokens.function}"
    - bold
  optionsTextColor:
    - "{tokens.muted}"
  selectedLineBgColor:
    - "{tokens.selection_bg}"
  cherryPickedCommitFgColor:
    - "{tokens.muted}"
  cherryPickedCommitBgColor:
    - "{tokens.function}"
  markedBaseCommitFgColor:
    - "{tokens.function}"
  markedBaseCommitBgColor:
    - "{tokens.type_color}"
  unstagedChangesColor:
    - "{tokens.muted}"
  defaultFgColor:
    - "{tokens.foreground}"
"""


def neovim(tokens: Tokens) -> str:
    bg = tokens.background
    vid = tokens.variant_id
    return f"""-- Serendipity {tokens.name} for Neovim
vim.cmd('hi clear')
if vim.fn.exists('syntax_on') then
  vim.cmd('syntax reset')
end
vim.o.background = '{tokens.appearance}'
vim.g.colors_name = '{PREFIX}-{vid}'

local M = {{}}
function M.setup()
  vim.cmd('hi Normal guifg={tokens.foreground} guibg={bg}')
  vim.cmd('hi Cursor guifg={tokens.cursor} guibg={bg}')
  vim.cmd('hi Visual guifg={tokens.foreground} guibg={tokens.selection_bg}')
  vim.cmd('hi LineNr guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi CursorLineNr guifg={tokens.foreground} guibg={bg} gui=bold')
  vim.cmd('hi CursorLine guibg={with_alpha(tokens.muted, "1a")}')
  vim.cmd('hi Comment guifg={tokens.comment} gui=italic')
  vim.cmd('hi Constant guifg={tokens.constant}')
  vim.cmd('hi String guifg={tokens.string}')
  vim.cmd('hi Identifier guifg={tokens.variable} gui=italic')
  vim.cmd('hi Function guifg={tokens.function} gui=italic')
  vim.cmd('hi Statement guifg={tokens.keyword}')
  vim.cmd('hi Keyword guifg={tokens.keyword}')
  vim.cmd('hi Operator guifg={tokens.operator}')
  vim.cmd('hi Type guifg={tokens.type_color}')
  vim.cmd('hi Error guifg={tokens.error}')
  vim.cmd('hi StatusLine guifg={tokens.foreground} guibg={tokens.surface}')
  vim.cmd('hi StatusLineNC guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi Pmenu guifg={tokens.foreground} guibg={tokens.surface}')
  vim.cmd('hi PmenuSel guifg={tokens.foreground} guibg={tokens.selection_bg}')
  vim.cmd('hi @variable guifg={tokens.variable} gui=italic')
  vim.cmd('hi @function guifg={tokens.function} gui=italic')
  vim.cmd('hi @keyword guifg={tokens.keyword}')
  vim.cmd('hi @type guifg={tokens.type_color}')
  vim.cmd('hi @string guifg={tokens.string}')
  vim.cmd('hi @comment guifg={tokens.comment} gui=italic')
end

M.setup()
return M
"""


def zed_theme_variant(tokens: Tokens) -> dict:
    t = tokens.terminal
    ff = lambda c: f"{c}ff" if len(c) == 7 else c
    border = with_alpha(tokens.muted, "33")
    return {
        "name": tokens.name,
        "appearance": tokens.appearance,
        "style": {
            "accents": [
                ff(tokens.type_color), ff(tokens.variable), ff(tokens.function),
                ff(tokens.keyword), ff(tokens.string), ff(tokens.error), ff(tokens.muted),
            ],
            "background": ff(tokens.background),
            "border": border,
            "border.focused": with_alpha(tokens.accent, "77"),
            "border.selected": with_alpha(tokens.accent, "bb"),
            "border.transparent": "#00000000",
            "elevated_surface.background": ff(tokens.surface),
            "surface.background": ff(tokens.background) + "ee",
            "element.background": ff(tokens.surface),
            "element.hover": ff(tokens.muted),
            "element.selected": ff(tokens.muted),
            "text": ff(tokens.foreground),
            "text.muted": ff(tokens.muted),
            "text.accent": ff(tokens.accent),
            "icon": ff(tokens.foreground),
            "icon.muted": ff(tokens.muted),
            "status_bar.background": ff(tokens.background),
            "title_bar.background": ff(tokens.background),
            "toolbar.background": ff(tokens.surface),
            "tab_bar.background": ff(tokens.background),
            "tab.inactive_background": ff(tokens.background),
            "tab.active_background": ff(tokens.background),
            "panel.background": ff(tokens.background),
            "editor.foreground": ff(tokens.foreground),
            "editor.background": ff(tokens.background),
            "editor.gutter.background": ff(tokens.background),
            "editor.active_line.background": border,
            "editor.line_number": ff(tokens.muted),
            "editor.active_line_number": ff(tokens.foreground),
            "scrollbar.thumb.background": with_alpha(tokens.muted, "77"),
            "scrollbar.track.background": ff(tokens.background),
            "terminal.background": ff(tokens.background),
            "terminal.foreground": ff(tokens.foreground),
            "terminal.ansi.black": ff(t["black"]),
            "terminal.ansi.red": ff(t["red"]),
            "terminal.ansi.green": ff(t["green"]),
            "terminal.ansi.yellow": ff(t["yellow"]),
            "terminal.ansi.blue": ff(t["blue"]),
            "terminal.ansi.magenta": ff(t["magenta"]),
            "terminal.ansi.cyan": ff(t["cyan"]),
            "terminal.ansi.white": ff(t["white"]),
            "terminal.ansi.bright_black": ff(t["bright_black"]),
            "terminal.ansi.bright_red": ff(t["bright_red"]),
            "terminal.ansi.bright_green": ff(t["bright_green"]),
            "terminal.ansi.bright_yellow": ff(t["bright_yellow"]),
            "terminal.ansi.bright_blue": ff(t["bright_blue"]),
            "terminal.ansi.bright_magenta": ff(t["bright_magenta"]),
            "terminal.ansi.bright_cyan": ff(t["bright_cyan"]),
            "terminal.ansi.bright_white": ff(t["bright_white"]),
            "syntax": {
                "comment": {"color": ff(tokens.comment), "font_style": "italic"},
                "keyword": {"color": ff(tokens.keyword)},
                "string": {"color": ff(tokens.string)},
                "function": {"color": ff(tokens.function), "font_style": "italic"},
                "variable": {"color": ff(tokens.variable), "font_style": "italic"},
                "type": {"color": ff(tokens.type_color)},
                "constant": {"color": ff(tokens.constant)},
                "tag": {"color": ff(tokens.type_color)},
                "attribute": {"color": ff(tokens.function), "font_style": "italic"},
                "punctuation": {"color": ff(tokens.operator)},
            },
        },
    }


def zed_theme(tokens: Tokens) -> dict:
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": tokens.name,
        "author": "Micheal Andreuzza",
        "themes": [zed_theme_variant(tokens)],
    }


def obsidian_css(tokens: Tokens) -> str:
    selector = ".theme-dark" if tokens.appearance == "dark" else ".theme-light"
    return f"""/* Serendipity {tokens.name} for Obsidian */
{selector} {{
  --background-primary: {tokens.background};
  --background-primary-alt: {tokens.background};
  --background-secondary: {tokens.surface};
  --background-secondary-alt: {tokens.background};
  --text-normal: {tokens.foreground};
  --text-muted: {tokens.muted};
  --text-faint: {tokens.muted};
  --text-accent: {tokens.accent};
  --text-accent-hover: {tokens.function};
  --text-on-accent: {tokens.accent_fg};
  --interactive-accent: {tokens.accent};
  --interactive-accent-hover: {tokens.function};
  --text-selection: {tokens.selection_bg};
  --text-link: {tokens.function};
  --code-normal: {tokens.string};
  --code-comment: {tokens.comment};
  --code-function: {tokens.function};
  --code-keyword: {tokens.keyword};
  --code-important: {tokens.error};
  --code-property: {tokens.type_color};
  --code-punctuation: {tokens.operator};
  --code-string: {tokens.string};
  --code-tag: {tokens.type_color};
  --code-value: {tokens.constant};
  --titlebar-background: {tokens.background};
  --tab-background-active: {tokens.background};
  --nav-item-background-hover: {tokens.selection_bg};
  --nav-item-background-active: {tokens.selection_bg};
  --checkbox-color: {tokens.accent};
}}
"""


def prism_css(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} for Prism.js */
code[class*="language-"],
pre[class*="language-"] {{
  color: {tokens.foreground};
  background: {tokens.background};
}}
.token.comment, .token.prolog, .token.doctype, .token.cdata {{
  color: {tokens.comment};
  font-style: italic;
}}
.token.keyword, .token.atrule, .token.tag, .token.selector {{
  color: {tokens.keyword};
}}
.token.string, .token.char, .token.attr-value {{
  color: {tokens.string};
}}
.token.function, .token.class-name {{
  color: {tokens.function};
  font-style: italic;
}}
.token.number, .token.boolean, .token.constant {{
  color: {tokens.constant};
}}
.token.operator, .token.punctuation {{
  color: {tokens.operator};
}}
.token.variable {{
  color: {tokens.variable};
  font-style: italic;
}}
.token.property, .token.builtin {{
  color: {tokens.type_color};
}}
.token.deleted {{
  color: {tokens.error};
}}
"""


def shadcn_globals(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} — shadcn/ui CSS variables */
@layer base {{
  :root {{
    --background: {tokens.background};
    --foreground: {tokens.foreground};
    --card: {tokens.background};
    --card-foreground: {tokens.foreground};
    --popover: {tokens.surface};
    --popover-foreground: {tokens.foreground};
    --primary: {tokens.accent};
    --primary-foreground: {tokens.accent_fg};
    --secondary: {tokens.surface};
    --secondary-foreground: {tokens.foreground};
    --muted: {tokens.background};
    --muted-foreground: {tokens.muted};
    --accent: {tokens.function};
    --accent-foreground: {tokens.foreground};
    --destructive: {tokens.error};
    --destructive-foreground: {tokens.foreground};
    --border: {with_alpha(tokens.muted, "33")};
    --input: {with_alpha(tokens.muted, "33")};
    --ring: {tokens.accent};
    --chart-1: {tokens.keyword};
    --chart-2: {tokens.type_color};
    --chart-3: {tokens.string};
    --chart-4: {tokens.constant};
    --chart-5: {tokens.error};
    --radius: 0.5rem;
  }}
}}
"""


# --- New port emitters ---


def alacritty(tokens: Tokens) -> str:
    t = tokens.terminal
    return f"""# Serendipity {tokens.name} for Alacritty

[colors.primary]
background = "{tokens.background}"
foreground = "{tokens.foreground}"

[colors.cursor]
text = "{tokens.background}"
cursor = "{tokens.cursor}"

[colors.selection]
text = "CellForeground"
background = "{tokens.selection_bg}"

[colors.normal]
black = "{t['black']}"
red = "{t['red']}"
green = "{t['green']}"
yellow = "{t['yellow']}"
blue = "{t['blue']}"
magenta = "{t['magenta']}"
cyan = "{t['cyan']}"
white = "{t['white']}"

[colors.bright]
black = "{t['bright_black']}"
red = "{t['bright_red']}"
green = "{t['bright_green']}"
yellow = "{t['bright_yellow']}"
blue = "{t['bright_blue']}"
magenta = "{t['bright_magenta']}"
cyan = "{t['bright_cyan']}"
white = "{t['bright_white']}"
"""


def kitty(tokens: Tokens) -> str:
    t = tokens.terminal
    palette = terminal_palette_lines(t)
    lines = [
        f"# Serendipity {tokens.name} for Kitty",
        f"background {tokens.background}",
        f"foreground {tokens.foreground}",
        f"cursor {tokens.cursor}",
        f"selection_background {tokens.selection_bg}",
        f"selection_foreground {tokens.foreground}",
    ]
    for i, color in enumerate(palette):
        lines.append(f"color{i} {color}")
    return "\n".join(lines) + "\n"


def tmux(tokens: Tokens) -> str:
    t = tokens.terminal
    palette = terminal_palette_lines(t)
    lines = [
        f"# Serendipity {tokens.name} for tmux",
        f"set -g @dracula-theme '{PREFIX}-{tokens.variant_id}'",
        f"set -g status-style 'bg={tokens.background},fg={tokens.foreground}'",
        f"set -g status-left-style 'bg={tokens.surface},fg={tokens.foreground}'",
        f"set -g status-right-style 'bg={tokens.surface},fg={tokens.muted}'",
        f"set -g window-status-current-style 'bg={tokens.accent},fg={tokens.accent_fg},bold'",
        f"set -g window-status-style 'bg={tokens.background},fg={tokens.muted}'",
        f"set -g message-style 'bg={tokens.surface},fg={tokens.foreground}'",
        f"set -g pane-border-style 'fg={tokens.muted}'",
        f"set -g pane-active-border-style 'fg={tokens.accent}'",
    ]
    for i, color in enumerate(palette):
        lines.append(f"set -g @dracula-color{i} '{color}'")
    return "\n".join(lines) + "\n"


def wezterm(tokens: Tokens) -> str:
    t = tokens.terminal
    normal = [t[k] for k in ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]]
    bright = [t[k] for k in [
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
    ]]
    fmt = lambda xs: ",\n    ".join(f"'{c}'" for c in xs)
    return f"""# Serendipity {tokens.name} for WezTerm

[colors]
ansi = [
    {fmt(normal)}
]
background = '{tokens.background}'
brights = [
    {fmt(bright)}
]
cursor_bg = '{tokens.cursor}'
cursor_border = '{tokens.cursor}'
cursor_fg = '{tokens.background}'
foreground = '{tokens.foreground}'
selection_bg = '{tokens.selection_bg}'
selection_fg = '{tokens.foreground}'
"""


def terminal_color_dict(color: str) -> str:
    r, g, b = hex_rgb_float(color)
    return f"""<dict>
  <key>Color Space</key>
  <string>sRGB</string>
  <key>Red Component</key>
  <real>{r:.6f}</real>
  <key>Green Component</key>
  <real>{g:.6f}</real>
  <key>Blue Component</key>
  <real>{b:.6f}</real>
</dict>"""


def apple_terminal(tokens: Tokens) -> str:
    t = tokens.terminal
    palette = terminal_palette_lines(t)
    entries = [
        f"  <key>Background Color</key>\n{terminal_color_dict(tokens.background)}",
        f"  <key>Text Color</key>\n{terminal_color_dict(tokens.foreground)}",
        f"  <key>Selection Color</key>\n{terminal_color_dict(tokens.selection_bg)}",
        f"  <key>Cursor Color</key>\n{terminal_color_dict(tokens.cursor)}",
    ]
    for i, color in enumerate(palette):
        entries.append(f"  <key>Ansi {i} Color</key>\n{terminal_color_dict(color)}")
    body = "\n".join(entries)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>name</key>
  <string>Serendipity {tokens.variant_id.title()}</string>
{body}
</dict>
</plist>
"""


def hyper(tokens: Tokens) -> str:
    t = tokens.terminal
    return f"""// Serendipity {tokens.name} for Hyper
module.exports = {{
  scheme: '{tokens.name}',
  author: 'Micheal Andreuzza',
  colors: {{
    background: '{tokens.background}',
    foreground: '{tokens.foreground}',
    cursor: '{tokens.cursor}',
    cursorAccent: '{tokens.background}',
    selection: '{tokens.selection_bg}',
    black: '{t['black']}',
    red: '{t['red']}',
    green: '{t['green']}',
    yellow: '{t['yellow']}',
    blue: '{t['blue']}',
    magenta: '{t['magenta']}',
    cyan: '{t['cyan']}',
    white: '{t['white']}',
    lightBlack: '{t['bright_black']}',
    lightRed: '{t['bright_red']}',
    lightGreen: '{t['bright_green']}',
    lightYellow: '{t['bright_yellow']}',
    lightBlue: '{t['bright_blue']}',
    lightMagenta: '{t['bright_magenta']}',
    lightCyan: '{t['bright_cyan']}',
    lightWhite: '{t['bright_white']}',
  }},
}};
"""


def warp(tokens: Tokens) -> str:
    t = tokens.terminal
    return f"""# Serendipity {tokens.name} for Warp
name: Serendipity {tokens.variant_id.title()}
accent: '{tokens.accent}'
background: '{tokens.background}'
foreground: '{tokens.foreground}'
details: {'darker' if tokens.appearance == 'dark' else 'lighter'}
terminal_colors:
  normal:
    black: '{t['black']}'
    red: '{t['red']}'
    green: '{t['green']}'
    yellow: '{t['yellow']}'
    blue: '{t['blue']}'
    magenta: '{t['magenta']}'
    cyan: '{t['cyan']}'
    white: '{t['white']}'
  bright:
    black: '{t['bright_black']}'
    red: '{t['bright_red']}'
    green: '{t['bright_green']}'
    yellow: '{t['bright_yellow']}'
    blue: '{t['bright_blue']}'
    magenta: '{t['bright_magenta']}'
    cyan: '{t['bright_cyan']}'
    white: '{t['bright_white']}'
"""


def bat_tmtheme(tokens: Tokens) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>name</key>
  <string>Serendipity {tokens.variant_id.title()}</string>
  <key>settings</key>
  <array>
    <dict><key>settings</key><dict><key>background</key><string>{tokens.background}</string><key>foreground</key><string>{tokens.foreground}</string><key>caret</key><string>{tokens.cursor}</string><key>selection</key><string>{tokens.selection_bg}</string></dict></dict>
    <dict><key>scope</key><string>comment</string><key>settings</key><dict><key>foreground</key><string>{tokens.comment}</string><key>fontStyle</key><string>italic</string></dict></dict>
    <dict><key>scope</key><string>keyword</string><key>settings</key><dict><key>foreground</key><string>{tokens.keyword}</string></dict></dict>
    <dict><key>scope</key><string>string</string><key>settings</key><dict><key>foreground</key><string>{tokens.string}</string></dict></dict>
    <dict><key>scope</key><string>entity.name.function</string><key>settings</key><dict><key>foreground</key><string>{tokens.function}</string><key>fontStyle</key><string>italic</string></dict></dict>
    <dict><key>scope</key><string>variable</string><key>settings</key><dict><key>foreground</key><string>{tokens.variable}</string><key>fontStyle</key><string>italic</string></dict></dict>
    <dict><key>scope</key><string>entity.name.type</string><key>settings</key><dict><key>foreground</key><string>{tokens.type_color}</string></dict></dict>
    <dict><key>scope</key><string>constant</string><key>settings</key><dict><key>foreground</key><string>{tokens.constant}</string></dict></dict>
    <dict><key>scope</key><string>invalid</string><key>settings</key><dict><key>foreground</key><string>{tokens.error}</string></dict></dict>
  </array>
</dict>
</plist>
"""


def delta_gitconfig(tokens: Tokens) -> str:
    t = tokens.terminal
    return f"""# Serendipity {tokens.name} for delta
[delta]
  minus-color = "{t['red']}"
  minus-emph-color = "{t['bright_red']}"
  plus-color = "{t['green']}"
  plus-emph-color = "{t['bright_green']}"
  commit-decoration-style = "box ul"
  commit-color = "{tokens.foreground}"
  file-style = "bold {tokens.type_color}"
  hunk-header-decoration-style = "box {tokens.surface}"
  hunk-header-file-style = "bold {tokens.muted}"
  hunk-header-line-number-style = "{tokens.muted}"
  syntax-theme = "Serendipity {tokens.variant_id.title()}"
"""


def pygments_style(tokens: Tokens) -> str:
    cls = f"Serendipity{tokens.variant_id.title()}Style"
    return f'''# -*- coding: utf-8 -*-
"""Serendipity {tokens.name} for Pygments."""

from pygments.style import Style
from pygments.token import (
    Comment, Name, String, Error, Number, Operator, Punctuation,
    Keyword, Generic, Text,
)


class {cls}(Style):
    background_color = "{tokens.background}"
    default_style = ""

    styles = {{
        Text: "{tokens.foreground}",
        Comment: "{tokens.comment}",
        Keyword: "{tokens.keyword}",
        Name: "{tokens.variable}",
        Name.Function: "{tokens.function}",
        Name.Class: "{tokens.type_color}",
        String: "{tokens.string}",
        Number: "{tokens.constant}",
        Operator: "{tokens.operator}",
        Punctuation: "{tokens.operator}",
        Error: "{tokens.error}",
        Generic.Deleted: "{tokens.error}",
        Generic.Inserted: "{tokens.type_color}",
        Generic.Heading: "{tokens.type_color} bold",
    }}
'''


def helix(tokens: Tokens) -> str:
    t = tokens.terminal
    palette = terminal_palette_lines(t)
    lines = [
        f"# Serendipity {tokens.name} for Helix",
        'inherit = "default_dark"' if tokens.appearance == "dark" else 'inherit = "default_light"',
        "",
        "[ui]",
        f'primary = {{ background = "{tokens.background}", foreground = "{tokens.foreground}" }}',
        f'cursor = {{ normal = {{ background = "{tokens.cursor}", foreground = "{tokens.background}" }} }}',
        f'selection = {{ primary = {{ background = "{tokens.selection_bg}", foreground = "{tokens.foreground}" }} }}',
        f'highlight = {{ background = "{tokens.selection_bg}", foreground = "{tokens.foreground}" }}',
        "",
        "[syntax]",
        f'comment = {{ fg = "{tokens.comment}", modifiers = ["italic"] }}',
        f'keyword = {{ fg = "{tokens.keyword}" }}',
        f'string = {{ fg = "{tokens.string}" }}',
        f'function = {{ fg = "{tokens.function}", modifiers = ["italic"] }}',
        f'variable = {{ fg = "{tokens.variable}", modifiers = ["italic"] }}',
        f'type = {{ fg = "{tokens.type_color}" }}',
        f'constant = {{ fg = "{tokens.constant}" }}',
        f'attribute = {{ fg = "{tokens.function}", modifiers = ["italic"] }}',
        f'punctuation = {{ fg = "{tokens.operator}" }}',
        "",
        "[palette]",
    ]
    for i, color in enumerate(palette):
        lines.append(f'{i} = "{color}"')
    return "\n".join(lines) + "\n"


def emacs(tokens: Tokens) -> str:
    return f""";;; Serendipity {tokens.name} for Emacs -*- lexical-binding: t; -*-

(deftheme serendipity-{tokens.variant_id}
  "Serendipity {tokens.name} theme")

(custom-theme-set-faces
 `(default ((t (:foreground "{tokens.foreground}" :background "{tokens.background}"))))
 `(cursor ((t (:background "{tokens.cursor}"))))
 `(font-lock-comment-face ((t (:foreground "{tokens.comment}" :slant italic))))
 `(font-lock-keyword-face ((t (:foreground "{tokens.keyword}"))))
 `(font-lock-string-face ((t (:foreground "{tokens.string}"))))
 `(font-lock-function-name-face ((t (:foreground "{tokens.function}" :slant italic))))
 `(font-lock-variable-name-face ((t (:foreground "{tokens.variable}" :slant italic))))
 `(font-lock-type-face ((t (:foreground "{tokens.type_color}"))))
 `(font-lock-constant-face ((t (:foreground "{tokens.constant}"))))
 `(font-lock-builtin-face ((t (:foreground "{tokens.type_color}"))))
 `(error ((t (:foreground "{tokens.error}"))))
 `(mode-line ((t (:foreground "{tokens.foreground}" :background "{tokens.surface}"))))
 `(region ((t (:background "{tokens.selection_bg}")))))

(provide-theme 'serendipity-{tokens.variant_id})
"""


def vim_colorscheme(tokens: Tokens) -> str:
    return f"""\" Serendipity {tokens.name} for Vim
hi clear
if exists('syntax_on')
  syntax reset
endif
set background={tokens.appearance}
let g:colors_name = '{PREFIX}-{tokens.variant_id}'

hi Normal guifg={tokens.foreground} guibg={tokens.background}
hi Cursor guifg={tokens.background} guibg={tokens.cursor}
hi Visual guibg={tokens.selection_bg}
hi LineNr guifg={tokens.muted} guibg={tokens.background}
hi Comment guifg={tokens.comment} gui=italic
hi Constant guifg={tokens.constant}
hi String guifg={tokens.string}
hi Identifier guifg={tokens.variable} gui=italic
hi Function guifg={tokens.function} gui=italic
hi Statement guifg={tokens.keyword}
hi Type guifg={tokens.type_color}
hi Error guifg={tokens.error}
hi StatusLine guifg={tokens.foreground} guibg={tokens.surface}
hi Pmenu guifg={tokens.foreground} guibg={tokens.surface}
hi PmenuSel guifg={tokens.foreground} guibg={tokens.selection_bg}
"""


def raycast(tokens: Tokens) -> str:
    t = tokens.terminal
    data = {
        "author": "Micheal Andreuzza",
        "authorUsername": "michael-andreuzza",
        "version": "1",
        "name": f"Serendipity {tokens.variant_id.title()}",
        "appearance": tokens.appearance,
        "colors": {
            "background": tokens.background.upper(),
            "backgroundSecondary": tokens.surface.upper(),
            "text": tokens.foreground.upper(),
            "selection": tokens.accent.upper(),
            "loader": tokens.accent.upper(),
            "red": t["red"].upper(),
            "orange": tokens.variable.upper(),
            "yellow": t["yellow"].upper(),
            "green": t["green"].upper(),
            "blue": t["blue"].upper(),
            "purple": tokens.string.upper(),
            "magenta": t["magenta"].upper(),
        },
    }
    return json.dumps(data, indent=2) + "\n"


def typora_css(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} for Typora */
:root {{
  --bg-color: {tokens.background};
  --side-bar-bg-color: {tokens.surface};
  --text-color: {tokens.foreground};
  --select-text-bg-color: {tokens.selection_bg};
  --item-hover-bg-color: {tokens.surface};
  --control-text-color: {tokens.foreground};
  --control-text-hover-color: {tokens.accent};
  --active-file-bg-color: {tokens.selection_bg};
  --active-file-text-color: {tokens.foreground};
  --window-border: 1px solid {with_alpha(tokens.muted, '33')};
  --primary-color: {tokens.accent};
  --search-select-bg-color: {tokens.selection_bg};
  --rawblock-edit-panel-bd: {tokens.surface};
  --monospace: "JetBrains Mono", "Fira Code", monospace;
}}

#write {{
  max-width: 860px;
  color: {tokens.foreground};
  background: {tokens.background};
}}

#write h1, #write h2, #write h3, #write h4, #write h5, #write h6 {{
  color: {tokens.type_color};
}}

#write a {{ color: {tokens.function}; }}
#write blockquote {{ border-left: 4px solid {tokens.accent}; color: {tokens.muted}; }}
#write code {{ background: {tokens.surface}; color: {tokens.string}; }}
#write pre {{ background: {tokens.surface}; }}
"""


def spicetify_color_ini(tokens: Tokens) -> str:
    t = tokens.terminal
    return f"""[Variables]
main_fg = {tokens.foreground}
main_bg = {tokens.background}
sidebar_and_player_bg = {tokens.surface}
card_bg = {tokens.surface}
secondary_fg = {tokens.muted}
selected_row = {tokens.selection_bg}
button = {tokens.accent}
button_active = {tokens.function}
button_disabled = {tokens.muted}
tab_active = {tokens.accent}
notification = {tokens.surface}
notification_error = {tokens.error}
miscellaneous_hover = {tokens.selection_bg}
"""


def spicetify_user_css(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} for Spicetify */
:root {{
  --spice-main: {tokens.background};
  --spice-sidebar: {tokens.surface};
  --spice-player: {tokens.surface};
  --spice-card: {tokens.surface};
  --spice-subtext: {tokens.muted};
  --spice-text: {tokens.foreground};
  --spice-button: {tokens.accent};
  --spice-button-active: {tokens.function};
  --spice-tab-active: {tokens.accent};
  --spice-notification: {tokens.surface};
  --spice-notification-error: {tokens.error};
}}
"""


def firefox_userchrome(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} — Firefox userChrome.css */
@namespace url("http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul");

:root {{
  --toolbar-bgcolor: {tokens.background} !important;
  --toolbar-color: {tokens.foreground} !important;
  --lwt-accent-color: {tokens.accent} !important;
  --lwt-text-color: {tokens.foreground} !important;
  --tab-selected-bgcolor: {tokens.surface} !important;
  --arrowpanel-background: {tokens.surface} !important;
  --arrowpanel-color: {tokens.foreground} !important;
}}

#navigator-toolbox {{
  background-color: {tokens.background} !important;
}}

.tab-background[selected="true"] {{
  background-color: {tokens.surface} !important;
}}
"""


def chrome_usercss(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} — Chrome user stylesheet */
html, body {{
  background-color: {tokens.background} !important;
  color: {tokens.foreground} !important;
}}
a {{ color: {tokens.function} !important; }}
"""


def homarr_css(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} for Homarr custom CSS */
:root {{
  --primary-color: {tokens.accent};
  --primary-color-dark: {tokens.function};
  --background-color: {tokens.background};
  --background-color-secondary: {tokens.surface};
  --text-color: {tokens.foreground};
  --text-color-secondary: {tokens.muted};
  --border-color: {with_alpha(tokens.muted, '33')};
  --card-background: {tokens.surface};
  --card-border: {with_alpha(tokens.muted, '33')};
}}
"""


def homepage_css(tokens: Tokens) -> str:
    return f"""/* Serendipity {tokens.name} for Homepage (gethomepage) custom CSS */
:root {{
  --color-background: {tokens.background};
  --color-background-highlight: {tokens.surface};
  --color-foreground: {tokens.foreground};
  --color-muted: {tokens.muted};
  --color-primary: {tokens.accent};
  --color-secondary: {tokens.function};
  --color-border: {with_alpha(tokens.muted, '33')};
}}
"""


def jetbrains_icls(tokens: Tokens) -> str:
    t = tokens.terminal
    entries = [
        ("Background", tokens.background),
        ("Foreground", tokens.foreground),
        ("Caret", tokens.cursor),
        ("SelectionBackground", tokens.selection_bg),
        ("Line numbers", tokens.muted),
        ("Gutter background", tokens.background),
        ("Comment", tokens.comment),
        ("Keyword", tokens.keyword),
        ("String", tokens.string),
        ("Number", tokens.constant),
        ("Function call", tokens.function),
        ("Function declaration", tokens.function),
        ("Local variable", tokens.variable),
        ("Class name", tokens.type_color),
        ("Type name", tokens.type_color),
        ("Errors", tokens.error),
        ("Default text", tokens.foreground),
    ]
    options = "\n".join(
        f'    <option name="{name}">\n      <value>\n        <option name="FOREGROUND" value="{hex6(c).lstrip("#")}" />\n      </value>\n    </option>'
        if "Background" not in name and "Gutter" not in name and "Selection" not in name
        else (
            f'    <option name="{name}">\n      <value>\n        <option name="BACKGROUND" value="{hex6(c).lstrip("#")}" />\n      </value>\n    </option>'
            if "Background" in name or "Gutter" in name or "Selection" in name
            else f'    <option name="{name}">\n      <value>\n        <option name="FOREGROUND" value="{hex6(c).lstrip("#")}" />\n      </value>\n    </option>'
        )
        for name, c in entries
    )
    return f"""<scheme name="Serendipity {tokens.variant_id.title()}" version="142" parent_scheme="Darcula">
  <meta-info>
    <property name="created">2026-05-24</property>
    <property name="ide">idea</property>
    <property name="ideVersion">2024.1</property>
    <property name="modified">2026-05-24</property>
    <property name="originalScheme">Serendipity {tokens.variant_id.title()}</property>
  </meta-info>
  <colors>
    <option name="CONSOLE_BACKGROUND_KEY" value="{tokens.background.lstrip('#')}" />
    <option name="CARET_COLOR" value="{tokens.cursor.lstrip('#')}" />
    <option name="GUTTER_BACKGROUND" value="{tokens.background.lstrip('#')}" />
    <option name="SELECTION_BACKGROUND" value="{tokens.selection_bg[:7].lstrip('#')}" />
    <option name="TEXT" value="{tokens.foreground.lstrip('#')}" />
  </colors>
  <attributes>
{options}
  </attributes>
</scheme>
"""


def figma_palette(tokens: Tokens) -> str:
    data = {
        "name": f"Serendipity {tokens.variant_id.title()}",
        "appearance": tokens.appearance,
        "colors": tokens.to_dict(),
        "usage": "Import these values as Figma color variables (Local variables → Create variable → Color).",
    }
    return json.dumps(data, indent=2) + "\n"


def generate_port_files(all_tokens: dict[str, Tokens]) -> None:
    def fname(vid: str, ext: str = "") -> str:
        return f"{PREFIX}-{vid}{ext}"

    # --- Existing 8 ports ---
    ghostty_files = []
    for vid, tok in all_tokens.items():
        name = fname(vid)
        ghostty_files.append(name)
        write(PROJECTS / "ghostty" / name, ghostty(tok))
    write_port("ghostty", "Add `config-file = ~/.config/ghostty/serendipity-midnight` to your Ghostty config.", "Serendipity for Ghostty", ghostty_files)

    starship_files = []
    for vid, tok in all_tokens.items():
        f = f"starship-{vid}.toml"
        starship_files.append(f)
        write(PROJECTS / "starship" / f, starship(tok))
    write_port("starship", "Copy a TOML file to `~/.config/starship.toml` and set `palette`.", "Serendipity for Starship", starship_files)

    lazygit_files = []
    for vid, tok in all_tokens.items():
        f = f"lazygit-{vid}.yml"
        lazygit_files.append(f)
        write(PROJECTS / "lazygit" / f, lazygit(tok))
    write_port("lazygit", "Merge a YAML file into your Lazygit config under `gui.theme`.", "Serendipity for Lazygit", lazygit_files)

    neovim_files = []
    for vid, tok in all_tokens.items():
        f = f"colors/{fname(vid)}.lua"
        neovim_files.append(f)
        write(PROJECTS / "neovim" / f, neovim(tok))
    write_port("neovim", "Copy `colors/` into your Neovim config and run `:colorscheme serendipity-midnight`.", "Serendipity for Neovim", neovim_files)

    zed_files = []
    for vid, tok in all_tokens.items():
        f = f"themes/{fname(vid)}.json"
        zed_files.append(f)
        write(PROJECTS / "zed" / f, json.dumps(zed_theme(tok), indent=2) + "\n")
    write(PROJECTS / "zed" / "extension.toml", f"""id = "serendipity"
name = "Serendipity"
version = "1.0.0"
schema_version = 1
authors = ["Micheal Andreuzza <michael@andreuzza.com>"]
description = "Serendipity theme for Zed — Midnight, Morning, and Sunset"
repository = "https://github.com/Serendipity-Theme/zed"
""")
    write_port("zed", "Install as a dev extension in Zed (**zed: extensions**).", "Serendipity for Zed", zed_files + ["extension.toml"])

    obsidian_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.css"
        obsidian_files.append(f)
        write(PROJECTS / "obsidian" / f, obsidian_css(tok))
    write_port("obsidian", "Copy CSS into `.obsidian/snippets/` and enable in Appearance settings.", "Serendipity for Obsidian", obsidian_files)

    prism_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.css"
        prism_files.append(f)
        write(PROJECTS / "prism" / f, prism_css(tok))
    write_port("prism", "Include the CSS in your site alongside Prism.js.", "Serendipity for Prism.js", prism_files)

    shadcn_dirs = []
    preset_entries = []
    for vid, tok in all_tokens.items():
        shadcn_dirs.append(f"{vid}/globals.css")
        write(PROJECTS / "shadcn-ui" / vid / "globals.css", shadcn_globals(tok))
        preset_entries.append(f"""      "{vid}": {{
            "background": "{tok.background}",
            "foreground": "{tok.foreground}",
            "surface": "{tok.surface}",
            "accent": "{tok.accent}",
            "muted": "{tok.muted}",
            "keyword": "{tok.keyword}",
            "string": "{tok.string}",
            "error": "{tok.error}"
      }}""")
    preset_body = ",\n".join(preset_entries)
    write(
        PROJECTS / "shadcn-ui" / "tailwind.preset.js",
        f"/** @type {{import('tailwindcss').Config}} */\nmodule.exports = {{\n  theme: {{\n    extend: {{\n      colors: {{\n{preset_body}\n      }}\n    }},\n  }},\n}};\n",
    )
    write_port("shadcn-ui", "Copy a variant `globals.css` into your app and import in the root layout.", "Serendipity for shadcn/ui", shadcn_dirs + ["tailwind.preset.js"])

    # --- New terminal ports ---
    alacritty_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.toml"
        alacritty_files.append(f)
        write(PROJECTS / "alacritty" / f, alacritty(tok))
    write_port("alacritty", "Import the TOML in `alacritty.toml` via `import = [\"path/to/serendipity-midnight.toml\"]`", "Serendipity for Alacritty", alacritty_files)

    kitty_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.conf"
        kitty_files.append(f)
        write(PROJECTS / "kitty" / f, kitty(tok))
    write_port("kitty", "Add `include serendipity-midnight.conf` to `~/.config/kitty/kitty.conf`.", "Serendipity for Kitty", kitty_files)

    tmux_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.conf"
        tmux_files.append(f)
        write(PROJECTS / "tmux" / f, tmux(tok))
    write_port("tmux", "Source a conf file from `~/.tmux.conf`: `run-shell 'tmux source-file ~/.config/tmux/serendipity-midnight.conf'`", "Serendipity for tmux", tmux_files)

    wezterm_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.toml"
        wezterm_files.append(f)
        write(PROJECTS / "wezterm" / f, wezterm(tok))
    write_port("wezterm", "Import in `wezterm.lua`: `config.color_scheme = \"Serendipity Midnight\"` after loading the TOML.", "Serendipity for WezTerm", wezterm_files)

    terminal_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.terminal"
        terminal_files.append(f)
        write(PROJECTS / "terminal" / f, apple_terminal(tok))
    write_port("terminal", "Double-click a `.terminal` file or import via Terminal → Settings → Profiles.", "Serendipity for Terminal.app", terminal_files)

    hyper_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.js"
        hyper_files.append(f)
        write(PROJECTS / "hyper" / f, hyper(tok))
    write_port("hyper", "Set `config.theme` to the path of a theme JS file in `~/.hyper.js`.", "Serendipity for Hyper", hyper_files)

    warp_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.yaml"
        warp_files.append(f)
        write(PROJECTS / "warp" / f, warp(tok))
    write_port("warp", "Import via Warp Settings → Appearance → Custom themes.", "Serendipity for Warp", warp_files)

    # --- CLI ports ---
    bat_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.tmTheme"
        bat_files.append(f)
        write(PROJECTS / "bat" / f, bat_tmtheme(tok))
    write_port("bat", "Copy to `$(bat --config-dir)/themes/` and set `BAT_THEME=Serendipity Midnight`.", "Serendipity for bat", bat_files)

    delta_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.gitconfig"
        delta_files.append(f)
        write(PROJECTS / "delta" / f, delta_gitconfig(tok))
    write_port("delta", "Include a fragment in `~/.gitconfig` under `[include]` or merge the `[delta]` section.", "Serendipity for delta", delta_files)

    pygments_files = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}_{vid}.py"
        pygments_files.append(f)
        write(PROJECTS / "pygments" / f, pygments_style(tok))
    write_port("pygments", "Import the style class in your Pygments config or Sphinx `pygments_style`.", "Serendipity for Pygments", pygments_files)

    # --- Editor ports ---
    helix_files = []
    for vid, tok in all_tokens.items():
        f = f"themes/{fname(vid)}.toml"
        helix_files.append(f)
        write(PROJECTS / "helix" / f, helix(tok))
    write_port("helix", "Copy to `~/.config/helix/themes/` and set `theme = \"serendipity-midnight\"` in config.toml.", "Serendipity for Helix", helix_files)

    emacs_files = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}-theme.el"
        emacs_files.append(f)
        write(PROJECTS / "emacs" / f, emacs(tok))
    write_port("emacs", "Add to `load-path` and `(load-theme 'serendipity-midnight t)`.", "Serendipity for Emacs", emacs_files)

    vim_files = []
    for vid, tok in all_tokens.items():
        f = f"colors/{fname(vid)}.vim"
        vim_files.append(f)
        write(PROJECTS / "vim" / f, vim_colorscheme(tok))
    write_port("vim", "Copy `colors/` to `~/.vim/colors/` and `:colorscheme serendipity-midnight`.", "Serendipity for Vim", vim_files)

    # --- App ports ---
    raycast_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.json"
        raycast_files.append(f)
        write(PROJECTS / "raycast" / f, raycast(tok))
    write_port("raycast", "Import JSON via Raycast → Settings → Appearance → Import theme.", "Serendipity for Raycast", raycast_files)

    typora_files = []
    for vid, tok in all_tokens.items():
        d = f"{fname(vid)}"
        typora_files.append(f"{d}/theme.css")
        write(PROJECTS / "typora" / d / "theme.css", typora_css(tok))
    write_port("typora", "Copy a theme folder to Typora's themes directory. Mark Text can import the same CSS.", "Serendipity for Typora", typora_files)

    spicetify_files = []
    for vid, tok in all_tokens.items():
        d = f"Serendipity-{vid.title()}"
        spicetify_files.append(f"{d}/color.ini")
        spicetify_files.append(f"{d}/user.css")
        write(PROJECTS / "spicetify" / d / "color.ini", spicetify_color_ini(tok))
        write(PROJECTS / "spicetify" / d / "user.css", spicetify_user_css(tok))
    write_port("spicetify", "Copy a theme folder into Spicetify's Themes directory and apply with `spicetify config current_theme`.", "Serendipity for Spicetify", spicetify_files)

    # --- Web / dashboards ---
    browser_files = []
    for vid, tok in all_tokens.items():
        browser_files.append(f"firefox/{fname(vid)}/userChrome.css")
        browser_files.append(f"chrome/{fname(vid)}.css")
        write(PROJECTS / "browsers" / f"firefox/{fname(vid)}/userChrome.css", firefox_userchrome(tok))
        write(PROJECTS / "browsers" / f"chrome/{fname(vid)}.css", chrome_usercss(tok))
    write_port("browsers", "Firefox: enable `toolkit.legacyUserProfileCustomizations.stylesheets` and place `userChrome.css` in your profile chrome folder. Chrome: use Stylus or a similar user stylesheet extension.", "Serendipity for Browsers", browser_files)

    homarr_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.css"
        homarr_files.append(f)
        write(PROJECTS / "homarr" / f, homarr_css(tok))
    write_port("homarr", "Paste CSS into Homarr Settings → Customization → Custom CSS.", "Serendipity for Homarr", homarr_files)

    homepage_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}.css"
        homepage_files.append(f)
        write(PROJECTS / "homepage" / f, homepage_css(tok))
    write_port("homepage", "Add CSS to your Homepage config `settings.customCss` array.", "Serendipity for Homepage", homepage_files)

    # --- Complex ports ---
    jetbrains_files = []
    for vid, tok in all_tokens.items():
        f = f"Serendipity {vid.title()}.icls"
        jetbrains_files.append(f)
        write(PROJECTS / "jetbrains" / f, jetbrains_icls(tok))
    write(PROJECTS / "jetbrains" / "INSTALL.md", """# Install Serendipity color schemes in JetBrains IDEs

1. Open **Settings → Editor → Color Scheme → Gear icon → Import Scheme…**
2. Select a `.icls` file from this repository.
3. Choose **Serendipity Midnight**, **Morning**, or **Sunset**.

These are importable color schemes, not a plugin.
""")
    write_port("jetbrains", "See `INSTALL.md` for import steps.", "Serendipity for JetBrains", jetbrains_files + ["INSTALL.md"])

    figma_files = []
    for vid, tok in all_tokens.items():
        f = f"{fname(vid)}-palette.json"
        figma_files.append(f)
        write(PROJECTS / "figma" / f, figma_palette(tok))
    write(PROJECTS / "figma" / "INSTALL.md", """# Import Serendipity colors into Figma

1. Open a Figma file → **Local variables** → create a color collection.
2. Use `serendipity-*-palette.json` values for background, foreground, accent, and syntax tokens.
3. Map semantic names (Background, Text, Accent, Error) to your components.

A Figma plugin is not included in v1.
""")
    write_port("figma", "See `INSTALL.md` for manual variable import.", "Serendipity for Figma", figma_files + ["INSTALL.md"])


def generate_tokens_json(all_tokens: dict[str, Tokens]) -> None:
    payload = {vid: tok.to_dict() for vid, tok in all_tokens.items()}
    PALETTE_OUT.mkdir(parents=True, exist_ok=True)
    write(PALETTE_OUT / "tokens.json", json.dumps(payload, indent=2) + "\n")
    write(PALETTE_OUT / "LICENSE", LICENSE + "\n")
    write(PALETTE_OUT / "README.md", f"""![Serendipity]({HEADER})

# Serendipity Color Palette

Canonical semantic tokens for all Serendipity theme ports.

## Files

- **`tokens.json`** — UI, terminal, syntax, and git tokens for **Midnight**, **Morning**, and **Sunset**
- `palette.css`, `palettes.scss`, `tailwind.config.js` — raw color values (legacy)

## Regenerate

```bash
python3 vs-code/scripts/generate-ports.py
```

See the [official website]({WEBSITE}) for all available interfaces.
""")


def generate_template() -> None:
    TEMPLATE_OUT.mkdir(parents=True, exist_ok=True)
    write(TEMPLATE_OUT / "LICENSE", LICENSE + "\n")
    write(TEMPLATE_OUT / "README.md", f"""![Serendipity]({HEADER})

# Serendipity theme port — {{APP_NAME}}

Port of the [Serendipity](https://github.com/Serendipity-Theme/vs-code) theme for **{{APP_NAME}}**.

See other interfaces at the [official website]({WEBSITE}).

## Variants

- **Midnight** (dark)
- **Morning** (light)
- **Sunset** (dark)

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
""")


def main() -> None:
    all_tokens = {vid: load_tokens(vid, fname) for vid, fname in VARIANTS}
    generate_port_files(all_tokens)
    generate_tokens_json(all_tokens)
    generate_template()
    print("Generated Serendipity ports in", PROJECTS)
    print("Updated palette in", PALETTE_OUT)


if __name__ == "__main__":
    main()
