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


def hex_to_hsl(color: str) -> tuple[int, str, str]:
    r, g, b = hex_rgb_float(color)
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    lightness = (max_c + min_c) / 2
    if max_c == min_c:
        hue = 0.0
        saturation = 0.0
    else:
        delta = max_c - min_c
        saturation = delta / (2 - max_c - min_c) if lightness > 0.5 else delta / (max_c + min_c)
        if max_c == r:
            hue = (g - b) / delta + (6 if g < b else 0)
        elif max_c == g:
            hue = (b - r) / delta + 2
        else:
            hue = (r - g) / delta + 4
        hue /= 6
    return round(hue * 360), f"{round(saturation * 100)}%", f"{round(lightness * 100)}%"


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


def obsidian_css_vars(tokens: Tokens) -> str:
    scheme = "dark" if tokens.appearance == "dark" else "light"
    accent_h, accent_s, accent_l = hex_to_hsl(tokens.accent)
    return f"""  color-scheme: {scheme};
  --accent-h: {accent_h};
  --accent-s: {accent_s};
  --accent-l: {accent_l};
  --color-base-00: {tokens.background};
  --color-base-05: {tokens.background};
  --color-base-10: {tokens.background};
  --color-base-20: {tokens.surface};
  --color-base-25: {tokens.surface};
  --color-base-30: {tokens.muted};
  --color-base-35: {tokens.operator};
  --color-base-40: {tokens.operator};
  --color-base-50: {tokens.muted};
  --color-base-60: {tokens.muted};
  --color-base-70: {tokens.foreground};
  --color-base-100: {tokens.foreground};
  --background-primary: {tokens.background};
  --background-primary-alt: {tokens.background};
  --background-secondary: {tokens.surface};
  --background-secondary-alt: {tokens.background};
  --background-modifier-border: {with_alpha(tokens.muted, "40")};
  --background-modifier-border-hover: {with_alpha(tokens.muted, "66")};
  --background-modifier-hover: {tokens.selection_bg};
  --background-modifier-active-hover: {tokens.selection_bg};
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
  --titlebar-background-focused: {tokens.background};
  --tab-background-active: {tokens.background};
  --ribbon-background: {tokens.surface};
  --nav-item-background-hover: {tokens.selection_bg};
  --nav-item-background-active: {tokens.selection_bg};
  --checkbox-color: {tokens.accent};
"""


def obsidian_css(tokens: Tokens, *, brand: str = "Serendipity") -> str:
    selector = "body.theme-dark" if tokens.appearance == "dark" else "body.theme-light"
    return f"""/* {brand} {tokens.name} for Obsidian */
{selector} {{
{obsidian_css_vars(tokens)}}}
"""


def obsidian_theme_css(light: Tokens, dark: Tokens, *, brand: str) -> str:
    return f"""/* {brand} for Obsidian — community theme */
body.theme-light {{
{obsidian_css_vars(light)}}}

body.theme-dark {{
{obsidian_css_vars(dark)}}}
"""


def obsidian_manifest(*, name: str) -> str:
    return json.dumps(
        {
            "name": name,
            "version": "1.0.1",
            "minAppVersion": "1.0.0",
            "author": "Micheal Andreuzza",
            "authorUrl": "https://github.com/michael-andreuzza",
        },
        indent=2,
    ) + "\n"


def obsidian_versions_json() -> str:
    return json.dumps({"1.0.0": "1.0.0", "1.0.1": "1.0.0"}, indent=2) + "\n"


def obsidian_screenshot_png(tokens: Tokens, theme_name: str, path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Install Pillow to generate Obsidian screenshots: pip3 install pillow") from exc

    width, height = 512, 288
    img = Image.new("RGB", (width, height), tokens.background)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    sidebar_w = 96
    draw.rectangle((0, 0, width, 22), fill=tokens.surface)
    draw.text((10, 6), theme_name, fill=tokens.foreground, font=font)
    draw.rectangle((0, 22, sidebar_w, height), fill=tokens.surface)
    draw.text((12, 40), "Notes", fill=tokens.accent, font=font)
    draw.text((12, 58), "Daily", fill=tokens.muted, font=font)
    draw.text((12, 76), "Projects", fill=tokens.muted, font=font)

    tab_y = 22
    draw.rectangle((sidebar_w, tab_y, sidebar_w + 92, tab_y + 24), fill=tokens.background)
    draw.text((sidebar_w + 10, tab_y + 6), "Welcome", fill=tokens.foreground, font=font)
    draw.rectangle((sidebar_w + 92, tab_y, sidebar_w + 160, tab_y + 24), fill=tokens.surface)
    draw.text((sidebar_w + 102, tab_y + 6), "Ideas", fill=tokens.muted, font=font)

    content_x = sidebar_w + 16
    y = 58
    draw.text((content_x, y), "Welcome to Obsidian", fill=tokens.foreground, font=font)
    draw.text((content_x, y + 22), "Elegant notes with Serendipity.", fill=tokens.muted, font=font)
    draw.text((content_x, y + 48), "- Capture ideas", fill=tokens.foreground, font=font)
    draw.text((content_x, y + 64), "- Link thoughts", fill=tokens.function, font=font)
    draw.text((content_x, y + 80), "- Build knowledge", fill=tokens.string, font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


def obsidian_community_md(*, brand: str, theme_name: str, github: str, light_name: str, dark_name: str, extra_variants: list[str]) -> str:
    extras = "\n".join(f"- `{name}` — CSS snippet in `variants/`" for name in extra_variants)
    extras_block = f"\n\nExtra variants (CSS snippets):\n\n{extras}\n" if extras else ""
    return f"""# Publish {theme_name} to Obsidian Community Themes

## Repository checklist

- [x] `manifest.json` at repo root (name must match theme folder: **{theme_name}**)
- [x] `theme.css` at repo root — **{light_name}** (light) + **{dark_name}** (dark)
- [x] `screenshot.png` — 512×288 preview
- [x] `versions.json` — maps `1.0.0` → `1.0.0`
- [x] `README.md` and `LICENSE`
{extras_block}
## GitHub release

1. Create release tag **`1.0.0`** (must match `manifest.json` version).
2. Attach **`manifest.json`** and **`theme.css`** as release assets.
3. Push tag: `git tag 1.0.0 && git push origin 1.0.0`

Or with GitHub CLI:

```bash
gh release create 1.0.0 manifest.json theme.css --title "1.0.0" --notes "Initial community theme release."
```

## Submit

1. Sign in at [community.obsidian.md](https://community.obsidian.md) with your Obsidian account.
2. Link your GitHub account in profile settings.
3. **Themes → New theme** → enter `{github}`.
4. Agree to developer policies and submit.

Obsidian reads `manifest.json` from the default branch and installs `theme.css` + `manifest.json` from the GitHub release matching the manifest version.

## Updates

Bump `version` in `manifest.json`, add the new version to `versions.json`, commit, and create a new tagged release with updated assets.
"""


def obsidian_preview_section(*, brand: str, dark_name: str, light_name: str) -> str:
    if brand in ("Sequoia", "Serendipity"):
        return f"""## Preview

| {dark_name} | {light_name} |
| --- | --- |
| ![{dark_name}](screenshot.png) | ![{light_name}](screenshot-light.png) |

"""
    return f"""## Preview

![{dark_name}](screenshot.png)

"""


def obsidian_port_readme(
    *,
    brand: str,
    theme_name: str,
    github: str,
    light_name: str,
    dark_name: str,
    snippet_files: list[str],
    extra_variants: list[str],
) -> str:
    variants = "\n".join(
        f"- **{vid.replace('-', ' ').title()}** — {appearance}"
        for vid, appearance in [
            ("midnight", "dark"),
            ("morning", "light"),
            ("sunset", "dark"),
        ]
    ) if brand == "Serendipity" else "\n".join(
        f"- **{vid.replace('-', ' ').title()}** — {appearance}"
        for vid, appearance in [
            ("moonlight-dark", "dark"),
            ("moonlight-light", "light"),
            ("monochrome-dark", "dark"),
            ("monochrome-light", "light"),
            ("retro-dark", "dark"),
            ("retro-light", "light"),
        ]
    )
    snippet_list = ", ".join(f"`{name}`" for name in snippet_files)
    extra_block = ""
    if extra_variants:
        extra_list = ", ".join(f"`variants/{name}`" for name in extra_variants)
        extra_block = f"""

### Extra variants (CSS snippets)

Copy files from `variants/` into `.obsidian/snippets/` and enable in **Appearance → CSS snippets**. Only enable one dark snippet at a time.

Available: {extra_list}.
"""
    return f"""![{brand}]({HEADER})

# {brand} for Obsidian

Elegant, minimal, and clean color palette for your tools.

See other interfaces at the [official website]({WEBSITE}).

{obsidian_preview_section(brand=brand, dark_name=dark_name, light_name=light_name)}## Available themes

{variants}

## Installation

### Community theme (recommended)

Install **{theme_name}** from Obsidian **Settings → Appearance → Manage → Community themes**, or browse from [community.obsidian.md](https://community.obsidian.md).

The community theme ships **{light_name}** (light mode) and **{dark_name}** (dark mode) in `theme.css`.
{extra_block}
### CSS snippets (single variant)

Copy a CSS file into `.obsidian/snippets/` and enable in **Appearance → CSS snippets**.

Available files: {snippet_list}.

See `COMMUNITY.md` for publishing and release steps.

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
"""


def generate_obsidian_port(
    port_dir: Path,
    all_tokens: dict[str, Tokens],
    *,
    brand: str,
    theme_name: str,
    github: str,
    light_vid: str,
    dark_vid: str,
    fname_fn,
    extra_variant_ids: list[str],
) -> list[str]:
    files: list[str] = []
    light = all_tokens[light_vid]
    dark = all_tokens[dark_vid]

    write(port_dir / "manifest.json", obsidian_manifest(name=theme_name))
    files.append("manifest.json")

    write(port_dir / "theme.css", obsidian_theme_css(light, dark, brand=brand))
    files.append("theme.css")

    write(port_dir / "versions.json", obsidian_versions_json())
    files.append("versions.json")

    screenshot = "screenshot.png"
    obsidian_screenshot_png(dark, theme_name, port_dir / screenshot)
    files.append(screenshot)

    write(port_dir / "COMMUNITY.md", obsidian_community_md(
        brand=brand,
        theme_name=theme_name,
        github=github,
        light_name=light.name,
        dark_name=dark.name,
        extra_variants=[fname_fn(vid) + ".css" for vid in extra_variant_ids],
    ))
    files.append("COMMUNITY.md")

    snippet_files: list[str] = []
    extra_files: list[str] = []
    for vid, tok in all_tokens.items():
        css_name = f"{fname_fn(vid)}.css"
        write(port_dir / css_name, obsidian_css(tok, brand=brand))
        snippet_files.append(css_name)
        files.append(css_name)
        if vid in extra_variant_ids:
            variant_path = f"variants/{css_name}"
            write(port_dir / variant_path, obsidian_css(tok, brand=brand))
            extra_files.append(variant_path)
            files.append(variant_path)

    write(port_dir / "LICENSE", LICENSE + "\n")
    write(port_dir / "README.md", obsidian_port_readme(
        brand=brand,
        theme_name=theme_name,
        github=github,
        light_name=light.name,
        dark_name=dark.name,
        snippet_files=snippet_files,
        extra_variants=[fname_fn(vid) + ".css" for vid in extra_variant_ids],
    ))
    files.extend(["LICENSE", "README.md"])
    return files


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
        "version": 1,
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


def spicetify_manifest(entries: list[tuple[str, Tokens]], brand: str) -> str:
    items = []
    for folder, tok in entries:
        items.append(
            {
                "name": folder,
                "description": f"{brand} for Spicetify — {tok.name} ({tok.appearance} mode).",
                "preview": "preview.png",
                "readme": "README.md",
                "usercss": f"{folder}/user.css",
                "schemes": f"{folder}/color.ini",
                "authors": [
                    {"name": "Micheal Andreuzza", "url": "https://github.com/michael-andreuzza"}
                ],
                "tags": [tok.appearance, brand.lower(), "minimal"],
            }
        )
    return json.dumps(items, indent=2) + "\n"


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


def jetbrains_scheme_name(tokens: Tokens) -> str:
    return f"Serendipity {tokens.variant_id.title()}"


def jetbrains_icls(tokens: Tokens, scheme_name: str | None = None) -> str:
    scheme_name = scheme_name or jetbrains_scheme_name(tokens)
    parent = "Darcula" if tokens.appearance == "dark" else "Default"

    def h(color: str) -> str:
        return hex6(color).lstrip("#")

    def fg_attr(name: str, color: str) -> str:
        return (
            f'    <option name="{name}">\n'
            f'      <value>\n'
            f'        <option name="FOREGROUND" value="{h(color)}" />\n'
            f"      </value>\n"
            f"    </option>"
        )

    bg = tokens.background
    fg = tokens.foreground
    surface = tokens.surface
    selection = tokens.selection_bg[:7]

    attributes = "\n".join(
        [
            f'    <option name="TEXT">\n      <value>\n        <option name="FOREGROUND" value="{h(fg)}" />\n        <option name="BACKGROUND" value="{h(bg)}" />\n      </value>\n    </option>',
            fg_attr("DEFAULT_KEYWORD", tokens.keyword),
            fg_attr("DEFAULT_STRING", tokens.string),
            fg_attr("DEFAULT_NUMBER", tokens.constant),
            fg_attr("DEFAULT_LINE_COMMENT", tokens.comment),
            fg_attr("DEFAULT_BLOCK_COMMENT", tokens.comment),
            fg_attr("DEFAULT_DOC_COMMENT", tokens.comment),
            fg_attr("DEFAULT_FUNCTION_CALL", tokens.function),
            fg_attr("DEFAULT_FUNCTION_DECLARATION", tokens.function),
            fg_attr("DEFAULT_LOCAL_VARIABLE", tokens.variable),
            fg_attr("DEFAULT_PARAMETER", tokens.variable),
            fg_attr("DEFAULT_GLOBAL_VARIABLE", tokens.variable),
            fg_attr("DEFAULT_IDENTIFIER", tokens.variable),
            fg_attr("DEFAULT_CLASS_NAME", tokens.type_color),
            fg_attr("DEFAULT_INTERFACE_NAME", tokens.type_color),
            fg_attr("DEFAULT_TYPE_PARAMETER", tokens.type_color),
            fg_attr("DEFAULT_INSTANCE_FIELD", tokens.variable),
            fg_attr("DEFAULT_STATIC_FIELD", tokens.constant),
            fg_attr("DEFAULT_METADATA", tokens.type_color),
            fg_attr("DEFAULT_CONSTANT", tokens.constant),
            fg_attr("DEFAULT_INVALID_STRING_ESCAPE", tokens.error),
            fg_attr("JSON.KEYWORD", tokens.keyword),
            fg_attr("JSON.STRING", tokens.string),
            fg_attr("JSON.NUMBER", tokens.constant),
            fg_attr("JSON.PROPERTY_KEY", tokens.keyword),
            fg_attr("JS.KEYWORD", tokens.keyword),
            fg_attr("JS.LOCAL_VARIABLE", tokens.variable),
            fg_attr("JS.GLOBAL_VARIABLE", tokens.variable),
            fg_attr("JS.GLOBAL_FUNCTION", tokens.function),
            fg_attr("JS.INSTANCE_MEMBER_FUNCTION", tokens.function),
        ]
    )

    return f"""<scheme name="{scheme_name}" version="142" parent_scheme="{parent}">
  <meta-info>
    <property name="created">2026-05-24</property>
    <property name="ide">idea</property>
    <property name="ideVersion">2024.1</property>
    <property name="modified">2026-05-24</property>
    <property name="originalScheme">{scheme_name}</property>
  </meta-info>
  <colors>
    <option name="CONSOLE_BACKGROUND_KEY" value="{h(bg)}" />
    <option name="CARET_COLOR" value="{h(tokens.cursor)}" />
    <option name="CARET_ROW_COLOR" value="{h(surface)}" />
    <option name="GUTTER_BACKGROUND" value="{h(bg)}" />
    <option name="LINE_NUMBERS_COLOR" value="{h(tokens.muted)}" />
    <option name="LINE_NUMBER_ON_CARET_ROW_COLOR" value="{h(tokens.cursor)}" />
    <option name="SELECTION_BACKGROUND" value="{h(selection)}" />
    <option name="INDENT_GUIDE" value="{h(tokens.muted)}" />
  </colors>
  <attributes>
{attributes}
  </attributes>
</scheme>
"""


def jetbrains_plugin_xml(
    scheme_names: list[str],
    *,
    plugin_id: str,
    plugin_name: str,
    brand: str,
    website: str,
    github: str,
) -> str:
    schemes = "\n".join(
        f'    <bundledColorScheme path="/colors/{name}" id="{name}"/>'
        for name in scheme_names
    )
    variants = ", ".join(name.replace(f"{brand} ", "") for name in scheme_names)
    return f"""<idea-plugin>
  <id>{plugin_id}</id>
  <name>{plugin_name}</name>
  <vendor email="hello@michaelandreuzza.com" url="{website}">Micheal Andreuzza</vendor>
  <description><![CDATA[
<p><strong>{brand}</strong> editor color schemes for JetBrains IDEs.</p>
<p>Includes {variants}.</p>
<p>Source: <a href="{github}">{github}</a></p>
  ]]></description>
  <depends>com.intellij.modules.lang</depends>
  <idea-version since-build="231"/>
  <extensions defaultExtensionNs="com.intellij">
{schemes}
  </extensions>
</idea-plugin>
"""


def jetbrains_gradle_properties(*, plugin_group: str, plugin_name: str, root_name: str) -> str:
    return f"""pluginGroup={plugin_group}
pluginName={plugin_name}
pluginVersion=1.0.1
pluginSinceBuild=231
platformVersion=2024.2.5
javaVersion=21
org.gradle.configuration-cache=true
rootProjectName={root_name}
"""


def jetbrains_settings_gradle(root_name: str) -> str:
    return f"""rootProject.name = "{root_name}"

pluginManagement {{
  repositories {{
    mavenCentral()
    gradlePluginPortal()
  }}
  plugins {{
    id("org.jetbrains.intellij.platform") version "2.16.0"
  }}
}}

plugins {{
  id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}}
"""


def jetbrains_build_gradle() -> str:
    return """plugins {
    id("java")
    id("org.jetbrains.intellij.platform") version "2.16.0"
}

group = providers.gradleProperty("pluginGroup").get()
version = providers.gradleProperty("pluginVersion").get()

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        intellijIdea(providers.gradleProperty("platformVersion").get())
    }
}

intellijPlatform {
    buildSearchableOptions = false
    pluginConfiguration {
        id = providers.gradleProperty("pluginGroup")
        name = providers.gradleProperty("pluginName")
        version = providers.gradleProperty("pluginVersion")
        ideaVersion {
            sinceBuild = providers.gradleProperty("pluginSinceBuild")
        }
    }
}
"""


def jetbrains_plugin_icon_svg(accent: str, background: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="{background}"/>
  <rect x="24" y="24" width="80" height="12" rx="4" fill="{accent}" opacity="0.9"/>
  <rect x="24" y="44" width="56" height="8" rx="3" fill="{accent}" opacity="0.55"/>
  <rect x="24" y="60" width="64" height="8" rx="3" fill="{accent}" opacity="0.35"/>
  <rect x="24" y="76" width="48" height="8" rx="3" fill="{accent}" opacity="0.55"/>
  <rect x="24" y="92" width="72" height="8" rx="3" fill="{accent}" opacity="0.35"/>
</svg>
"""


def jetbrains_gitignore() -> str:
    return """.gradle/
build/
.idea/
*.iml
out/
"""


def jetbrains_github_workflow() -> str:
    return """name: Build Plugin

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "21"
      - name: Build plugin
        run: ./gradlew buildPlugin --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: plugin-distribution
          path: build/distributions/*.zip
"""


def jetbrains_screenshot_path(scheme_name: str) -> str:
    return f"screenshots/{scheme_name.lower().replace(' ', '-')}.png"


def jetbrains_preview_section(scheme_names: list[str]) -> str:
    if len(scheme_names) <= 3:
        header = " | ".join(scheme_names)
        div = " | ".join("---" for _ in scheme_names)
        imgs = " | ".join(f"![{name}]({jetbrains_screenshot_path(name)})" for name in scheme_names)
        return f"| {header} |\n| {div} |\n| {imgs} |\n"
    blocks = []
    for i in range(0, len(scheme_names), 2):
        pair = scheme_names[i : i + 2]
        if len(pair) == 2:
            left, right = pair
            blocks.append(
                f"| {left} | {right} |\n| --- | --- |\n"
                f"| ![{left}]({jetbrains_screenshot_path(left)}) | ![{right}]({jetbrains_screenshot_path(right)}) |"
            )
        else:
            name = pair[0]
            blocks.append(f"| {name} |\n| --- |\n| ![{name}]({jetbrains_screenshot_path(name)}) |")
    return "\n\n".join(blocks) + "\n"


def jetbrains_variants_md(brand: str) -> str:
    if brand == "Serendipity":
        return "\n".join(
            f"- **{name}** — {appearance}"
            for name, appearance in [
                ("Midnight", "dark"),
                ("Morning", "light"),
                ("Sunset", "dark"),
            ]
        )
    return "\n".join(
        f"- **{name}** — {appearance}"
        for name, appearance in [
            ("Moonlight Dark", "dark"),
            ("Moonlight Light", "light"),
            ("Monochrome Dark", "dark"),
            ("Monochrome Light", "light"),
            ("Retro Dark", "dark"),
            ("Retro Light", "light"),
        ]
    )


def jetbrains_port_readme(*, brand: str, scheme_names: list[str]) -> str:
    return f"""![{brand}]({HEADER})

# {brand} for JetBrains

Elegant, minimal, and clean color palette for your tools.

See other interfaces at the [official website]({WEBSITE}).

## Preview

{jetbrains_preview_section(scheme_names)}
## Available themes

{jetbrains_variants_md(brand)}

## Installation

Install from JetBrains Marketplace (see `MARKETPLACE.md`) or import `.icls` files manually (see `INSTALL.md`).

See `MARKETPLACE.md` for publishing and release steps.

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
"""


def jetbrains_marketplace_md(*, brand: str, plugin_name: str, github: str, scheme_names: list[str]) -> str:
    screenshot_lines = "\n".join(
        f"- `{name}` → `screenshots/{name.lower().replace(' ', '-')}.png`"
        for name in scheme_names
    )
    return f"""# Publish {brand} to JetBrains Marketplace

This repository includes a ready-to-build IntelliJ Platform plugin with bundled editor color schemes.

## What is included

- Gradle plugin project (build with `./gradlew buildPlugin`)
- Bundled schemes: {", ".join(scheme_names)}
- Marketplace screenshots in `screenshots/` (1280×800 IDE captures)
- GitHub Actions workflow that uploads a `.zip` artifact on every push to `main`

## You do not need a JetBrains IDE locally

1. Push this repo (or download the **plugin-distribution** artifact from the latest GitHub Actions run).
2. Unzip the artifact — it is the file you upload to Marketplace.

Screenshots in `screenshots/` are real IDE captures used for the Marketplace listing and README preview.

## Create a JetBrains account (one time)

1. Go to [plugins.jetbrains.com](https://plugins.jetbrains.com).
2. Sign in with GitHub or create a JetBrains Account.
3. Open your profile menu → **Upload plugin**.
4. Accept the **Marketplace Developer Agreement** and create a **Vendor profile** (your name or `{brand}-Theme`).

## Upload {plugin_name}

1. Download the plugin ZIP from GitHub Actions (**Actions → Build Plugin → plugin-distribution**).
2. On [plugins.jetbrains.com/author/me](https://plugins.jetbrains.com/author/me), click **Upload plugin**.
3. Select the ZIP file.
4. Fill in the listing:
   - **Name**: {plugin_name}
   - **Tags**: Theme, Color Scheme
   - **License**: MIT — link `{github}`
   - **Description**: copy from README; mention {brand} variants
5. Upload screenshots from `screenshots/`:

{screenshot_lines}

6. Submit for review ([upload guide](https://plugins.jetbrains.com/docs/marketplace/uploading-a-new-plugin.html)).

Approval usually takes a few business days. After approval, users install via **Settings → Plugins → Marketplace**.

## Manual scheme import (no plugin)

See `INSTALL.md` to import `.icls` files directly.

## Rebuild locally (optional)

Requires Java 21+:

```bash
./gradlew buildPlugin
open build/distributions/
```
"""


def jetbrains_screenshot_png(tokens: Tokens, scheme_name: str, path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Install Pillow to generate JetBrains screenshots: pip3 install pillow") from exc

    width, height = 1280, 800
    img = Image.new("RGB", (width, height), tokens.background)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    title_font = ImageFont.load_default()

    draw.rectangle((0, 0, width, 48), fill=tokens.surface)
    draw.text((24, 16), scheme_name, fill=tokens.foreground, font=title_font)
    draw.text((width - 260, 16), "JetBrains Color Scheme", fill=tokens.muted, font=font)

    gutter = 72
    draw.rectangle((0, 48, gutter, height), fill=tokens.surface)
    code_x = gutter + 28
    y = 88
    line_h = 34

    sample_lines = [
        ("// Syntax preview", tokens.comment, False),
        ("fun greet(name: String) {{", tokens.keyword, False),
        ('    val message = "Hello"', tokens.variable, True),
        ("    println(message)", tokens.function, False),
        ("}}", tokens.keyword, False),
    ]

    for i, (text, color, selected) in enumerate(sample_lines, start=1):
        line_y = y + (i - 1) * line_h
        draw.text((16, line_y + 6), str(i), fill=tokens.muted, font=font)
        if selected:
            draw.rectangle(
                (gutter, line_y, width, line_y + line_h - 4),
                fill=tokens.selection_bg[:7] if len(tokens.selection_bg) >= 7 else tokens.selection_bg,
            )
        parts = []
        if text.startswith("fun "):
            parts = [("fun ", tokens.keyword), ("greet", tokens.function), ("(name: ", tokens.foreground), ("String", tokens.type_color), (") {", tokens.foreground)]
        elif text.startswith("    val "):
            parts = [("    val ", tokens.keyword), ('message = "Hello"', tokens.string)]
        elif text.startswith("    println"):
            parts = [("    ", tokens.foreground), ("println", tokens.function), ("(message)", tokens.foreground)]
        else:
            parts = [(text, color)]
        x = code_x
        for segment, seg_color in parts:
            draw.text((x, line_y + 6), segment, fill=seg_color, font=font)
            x += draw.textlength(segment, font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


def generate_jetbrains_plugin(
    port_dir: Path,
    all_tokens: dict[str, Tokens],
    *,
    brand: str,
    plugin_id: str,
    plugin_name: str,
    github: str,
    root_name: str,
    scheme_name_fn,
) -> list[str]:
    scheme_entries = [(scheme_name_fn(tok), tok) for tok in all_tokens.values()]
    scheme_names = [name for name, _ in scheme_entries]
    files: list[str] = []

    for scheme_name, tok in scheme_entries:
        icls_name = f"{scheme_name}.icls"
        files.append(icls_name)
        write(port_dir / icls_name, jetbrains_icls(tok, scheme_name))

        color_path = port_dir / "src/main/resources/colors" / f"{scheme_name}.xml"
        write(color_path, jetbrains_icls(tok, scheme_name))

        shot_name = f"screenshots/{scheme_name.lower().replace(' ', '-')}.png"
        shot_path = port_dir / shot_name
        files.append(shot_name)
        if not shot_path.exists():
            jetbrains_screenshot_png(tok, scheme_name, shot_path)

    write(port_dir / "src/main/resources/META-INF/plugin.xml", jetbrains_plugin_xml(
        scheme_names,
        plugin_id=plugin_id,
        plugin_name=plugin_name,
        brand=brand,
        website=WEBSITE,
        github=github,
    ))
    accent = next(iter(all_tokens.values())).accent
    background = next(iter(all_tokens.values())).background
    write(port_dir / "src/main/resources/META-INF/pluginIcon.svg", jetbrains_plugin_icon_svg(accent, background))
    write(port_dir / "build.gradle.kts", jetbrains_build_gradle())
    write(port_dir / "settings.gradle.kts", jetbrains_settings_gradle(root_name))
    write(port_dir / "gradle.properties", jetbrains_gradle_properties(
        plugin_group=plugin_id,
        plugin_name=plugin_name,
        root_name=root_name,
    ))
    write(port_dir / ".gitignore", jetbrains_gitignore())
    write(port_dir / ".github/workflows/build-plugin.yml", jetbrains_github_workflow())
    write(port_dir / "MARKETPLACE.md", jetbrains_marketplace_md(
        brand=brand,
        plugin_name=plugin_name,
        github=github,
        scheme_names=scheme_names,
    ))
    write(port_dir / "INSTALL.md", f"""# Install {brand} color schemes in JetBrains IDEs

## Marketplace (recommended)

Install **{plugin_name}** from [JetBrains Marketplace](https://plugins.jetbrains.com) after publishing.
See `MARKETPLACE.md` for upload steps and GitHub Actions build artifacts.

## Manual import

1. Open **Settings → Editor → Color Scheme → Gear icon → Import Scheme…**
2. Select a `.icls` file from this repository.
3. Choose **{scheme_names[0]}** or another variant.

These `.icls` files are the same schemes bundled in the plugin.
""")
    write(port_dir / "README.md", jetbrains_port_readme(brand=brand, scheme_names=scheme_names))
    files.append("README.md")

    plugin_files = [
        "build.gradle.kts",
        "settings.gradle.kts",
        "gradle.properties",
        "src/main/resources/META-INF/plugin.xml",
        "src/main/resources/META-INF/pluginIcon.svg",
        "MARKETPLACE.md",
        "INSTALL.md",
        ".gitignore",
        ".github/workflows/build-plugin.yml",
    ]
    plugin_files.extend(f"src/main/resources/colors/{name}.xml" for name in scheme_names)
    files.extend(plugin_files)
    return files


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
    write(PROJECTS / "zed" / "extension.toml", """id = "serendipity"
name = "Serendipity Themes"
version = "1.1.0"
schema_version = 1
authors = [
  "Nguyen Dang Vinh <meocoder@gmail.com>",
  "Micheal Andreuzza <michael@andreuzza.com>",
]
description = "Relaxed, gentle and modern | Serendipity theme for Zed"
repository = "https://github.com/meocoder31099/Serendipity-Theme-Zed"
""")
    write_port(
        "zed",
        """Install from [Zed Extensions](https://zed.dev/extensions/serendipity) (search **Serendipity Themes**).

Source of truth: [meocoder31099/Serendipity-Theme-Zed](https://github.com/meocoder31099/Serendipity-Theme-Zed). Regenerate `themes/serendipity.json` from this folder when opening a PR there.""",
        "Serendipity for Zed",
        zed_files + ["extension.toml"],
    )

    obsidian_files = generate_obsidian_port(
        PROJECTS / "obsidian",
        all_tokens,
        brand="Serendipity",
        theme_name="Serendipity",
        github="https://github.com/Serendipity-Theme/obsidian",
        light_vid="morning",
        dark_vid="midnight",
        fname_fn=fname,
        extra_variant_ids=["sunset"],
    )

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
    write_port("raycast", "Import JSON via Raycast → Settings → Appearance → Import theme, or browse on [themes.ray.so](https://themes.ray.so).", "Serendipity for Raycast", raycast_files)

    typora_files = []
    for vid, tok in all_tokens.items():
        d = f"{fname(vid)}"
        typora_files.append(f"{d}/theme.css")
        write(PROJECTS / "typora" / d / "theme.css", typora_css(tok))
    write_port("typora", "Copy a theme folder to Typora's themes directory. Mark Text can import the same CSS.", "Serendipity for Typora", typora_files)

    spicetify_files = []
    spicetify_entries: list[tuple[str, Tokens]] = []
    for vid, tok in all_tokens.items():
        d = f"Serendipity-{vid.title()}"
        spicetify_files.append(f"{d}/color.ini")
        spicetify_files.append(f"{d}/user.css")
        spicetify_entries.append((d, tok))
        write(PROJECTS / "spicetify" / d / "color.ini", spicetify_color_ini(tok))
        write(PROJECTS / "spicetify" / d / "user.css", spicetify_user_css(tok))
    write(PROJECTS / "spicetify" / "manifest.json", spicetify_manifest(spicetify_entries, "Serendipity"))
    spicetify_files.extend(["manifest.json", "preview.png"])
    write_port(
        "spicetify",
        """### Spicetify Marketplace

Published for the [Spicetify Marketplace](https://github.com/spicetify/marketplace). Open Marketplace in Spotify and search **Serendipity**.

### Manual installation

Copy a theme folder into Spicetify's Themes directory and apply with `spicetify config current_theme`.""",
        "Serendipity for Spicetify",
        spicetify_files,
    )

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
    jetbrains_files = generate_jetbrains_plugin(
        PROJECTS / "jetbrains",
        all_tokens,
        brand="Serendipity",
        plugin_id="com.michaelandreuzza.serendipity.jetbrains",
        plugin_name="Serendipity Theme",
        github="https://github.com/Serendipity-Theme/jetbrains",
        root_name="serendipity-jetbrains",
        scheme_name_fn=jetbrains_scheme_name,
    )
    write(PROJECTS / "jetbrains" / "LICENSE", LICENSE + "\n")

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
