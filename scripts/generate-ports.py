#!/usr/bin/env python3
"""Generate Serendipity theme ports from VS Code theme JSON files."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT.parent
THEMES_DIR = ROOT / "themes"
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

VARIANTS = {
    "midnight": "serendipity-midnight.json",
    "sunset": "serendipity-sunset.json",
    "morning": "serendipity-morning.json",
}

HEADER = "https://raw.githubusercontent.com/Serendipity-Theme/assets/main/githubHeader.png"
SITE = "https://www.michaelandreuzza.com/vscode/serendipity/"
CREDIT = "[Micheal Andreuzza](https://github.com/michael-andreuzza)"

ANSI_MAP = [
    ("ansiBlack", 0),
    ("ansiRed", 1),
    ("ansiGreen", 2),
    ("ansiYellow", 3),
    ("ansiBlue", 4),
    ("ansiMagenta", 5),
    ("ansiCyan", 6),
    ("ansiWhite", 7),
    ("ansiBrightBlack", 8),
    ("ansiBrightRed", 9),
    ("ansiBrightGreen", 10),
    ("ansiBrightYellow", 11),
    ("ansiBrightBlue", 12),
    ("ansiBrightMagenta", 13),
    ("ansiBrightCyan", 14),
    ("ansiBrightWhite", 15),
]

SYNTAX_SCOPES = {
    "comment": ["comment"],
    "constant": ["constant"],
    "keyword": ["keyword"],
    "string": ["string"],
    "function": ["support.function"],
    "type": ["entity.name.section", "entity.name.tag", "entity.name.namespace", "entity.name.type"],
    "variable": ["variable"],
    "tag": ["entity.name.tag"],
    "attribute": ["entity.other.attribute-name", "entity.other.inherited-class"],
    "error": ["invalid"],
    "punctuation": ["punctuation"],
    "support": ["support"],
}


def load_theme(name: str) -> dict:
    with open(THEMES_DIR / VARIANTS[name], encoding="utf-8") as f:
        return json.load(f)


def scope_matches(rule_scope, target_scopes):
    if isinstance(rule_scope, str):
        scopes = [rule_scope]
    else:
        scopes = rule_scope
    for s in scopes:
        for t in target_scopes:
            if s == t or s.startswith(t + "."):
                return True
    return False


def syntax_color(theme: dict, target_scopes: list[str]) -> str:
    for rule in theme.get("tokenColors", []):
        if scope_matches(rule.get("scope", ""), target_scopes):
            fg = rule.get("settings", {}).get("foreground")
            if fg:
                return fg.lower()
    return theme["colors"]["foreground"].lower()


def syntax_style(theme: dict, target_scopes: list[str]) -> str:
    for rule in theme.get("tokenColors", []):
        if scope_matches(rule.get("scope", ""), target_scopes):
            return rule.get("settings", {}).get("fontStyle", "")
    return ""


def extract_tokens(name: str) -> dict:
    theme = load_theme(name)
    c = theme["colors"]
    terminal = {}
    for key, idx in ANSI_MAP:
        terminal[f"ansi{idx}"] = c[f"terminal.{key}"].lower()

    syntax = {}
    styles = {}
    for key, scopes in SYNTAX_SCOPES.items():
        syntax[key] = syntax_color(theme, scopes)
        styles[key] = syntax_style(theme, scopes)

    return {
        "name": theme["name"],
        "type": theme["type"],
        "ui": {
            "background": c["editor.background"].lower(),
            "surface": c.get("sideBar.background", c["editor.background"]).lower(),
            "surfaceAlt": c.get("banner.background", c["editor.background"]).lower(),
            "foreground": c["foreground"].lower(),
            "muted": c["descriptionForeground"].lower(),
            "accent": c["button.background"].lower(),
            "border": c.get("focusBorder", c["descriptionForeground"]).lower(),
            "selection": c["editor.selectionBackground"].lower(),
            "cursor": c["editorCursor.foreground"].lower(),
            "lineHighlight": c["editor.lineHighlightBackground"].lower(),
        },
        "terminal": {
            **terminal,
            "foreground": c["terminal.foreground"].lower(),
            "background": c["editor.background"].lower(),
            "selection": c["terminal.selectionBackground"].lower(),
            "cursor": c["terminalCursor.foreground"].lower(),
        },
        "syntax": syntax,
        "syntaxStyles": styles,
        "git": {
            "added": c["gitDecoration.addedResourceForeground"].lower(),
            "modified": c["gitDecoration.modifiedResourceForeground"].lower(),
            "deleted": c["gitDecoration.deletedResourceForeground"].lower(),
            "untracked": c["gitDecoration.untrackedResourceForeground"].lower(),
            "conflict": c["gitDecoration.conflictingResourceForeground"].lower(),
        },
    }


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def readme(app: str, install: str, extra: str = "") -> str:
    return f"""![Midnight]({HEADER})

# Serendipity for {app}

Elegant, minimal, and clean color palette to give your eyes rest.

See other interfaces at the [official website]({SITE}).

## Available themes

- **Midnight** — dark
- **Sunset** — dark
- **Morning** — light

## Installation

{install}

{extra}

## Created by

{CREDIT}
"""


def ghostty_config(t: dict) -> str:
    lines = [
        f"background = {t['terminal']['background']}",
        f"foreground = {t['terminal']['foreground']}",
        f"cursor-color = {t['terminal']['cursor']}",
        f"cursor-text = {t['terminal']['background']}",
        f"selection-background = {t['ui']['selection']}",
        f"selection-foreground = {t['terminal']['foreground']}",
    ]
    for i in range(16):
        lines.append(f"palette = {i}={t['terminal'][f'ansi{i}']}")
    return "\n".join(lines) + "\n"


def starship_config(t: dict, variant: str) -> str:
    s = t["syntax"]
    u = t["ui"]
    g = t["git"]
    palette = variant.replace("-", "_")
    return f"""# Serendipity {t['name']}
palette = "{palette}"

[palettes.{palette}]
background = "{u['background']}"
current_line = "{u['surfaceAlt']}"
foreground = "{u['foreground']}"
comment = "{s['comment']}"
cyan = "{s['attribute']}"
green = "{g['added']}"
orange = "{u['accent']}"
pink = "{s['variable']}"
purple = "{s['string']}"
red = "{s['error']}"
yellow = "{s['type']}"

[character]
success_symbol = "[✔]({s['keyword']})"
error_symbol = "[✘]({s['error']})"

[directory]
style = "bold {s['type']}"

[git_branch]
style = "bold {s['attribute']}"

[git_status]
style = "bold {g['modified']}"
"""


def lazygit_config(t: dict) -> str:
    s = t["syntax"]
    u = t["ui"]
    g = t["git"]
    return f"""# Serendipity {t['name']}
theme:
  activeBorderColor:
    - "{u['accent']}"
    - bold
  inactiveBorderColor:
    - "{s['string']}"
  searchingActiveBorderColor:
    - "{s['attribute']}"
    - bold
  optionsTextColor:
    - "{u['muted']}"
  selectedLineBgColor:
    - "{u['selection']}"
  cherryPickedCommitFgColor:
    - "{u['muted']}"
  cherryPickedCommitBgColor:
    - "{s['attribute']}"
  markedBaseCommitFgColor:
    - "{s['attribute']}"
  markedBaseCommitBgColor:
    - "{s['type']}"
  unstagedChangesColor:
    - "{g['deleted']}"
  defaultFgColor:
    - "{u['foreground']}"
"""


def neovim_colorscheme(t: dict, variant: str) -> str:
    s = t["syntax"]
    u = t["ui"]
    bg = "dark" if t["type"] == "dark" else "light"
    italic_comment = "italic" if "italic" in t["syntaxStyles"].get("comment", "") else ""
    italic_var = "italic" if "italic" in t["syntaxStyles"].get("variable", "") else ""
    italic_fn = "italic" if "italic" in t["syntaxStyles"].get("function", "") else ""
    italic_attr = "italic" if "italic" in t["syntaxStyles"].get("attribute", "") else ""

    def hi(group, fg=None, bg=None, style=""):
        parts = [f'hi {group}']
        if fg:
            parts.append(f"guifg={fg}")
        if bg:
            parts.append(f"guibg={bg}")
        if style:
            parts.append(f"gui={style}")
        return " ".join(parts)

    highlights = [
        hi("Normal", u["foreground"], u["background"]),
        hi("Cursor", u["cursor"], u["background"]),
        hi("Visual", u["foreground"], u["selection"]),
        hi("LineNr", u["muted"], u["background"]),
        hi("CursorLineNr", u["foreground"], u["background"], "bold"),
        hi("CursorLine", None, u["lineHighlight"]),
        hi("Comment", s["comment"], None, italic_comment or "italic"),
        hi("Constant", s["constant"]),
        hi("String", s["string"]),
        hi("Character", s["string"]),
        hi("Number", s["constant"]),
        hi("Boolean", s["constant"]),
        hi("Float", s["constant"]),
        hi("Identifier", s["variable"], None, italic_var),
        hi("Function", s["function"], None, italic_fn),
        hi("Statement", s["keyword"]),
        hi("Conditional", s["keyword"]),
        hi("Repeat", s["keyword"]),
        hi("Keyword", s["keyword"]),
        hi("Label", s["keyword"]),
        hi("Operator", s["punctuation"]),
        hi("Exception", s["error"]),
        hi("PreProc", s["keyword"]),
        hi("Type", s["type"]),
        hi("StorageClass", s["keyword"]),
        hi("Structure", s["type"]),
        hi("Typedef", s["type"]),
        hi("Special", s["support"]),
        hi("SpecialChar", s["string"]),
        hi("Tag", s["tag"]),
        hi("Delimiter", s["punctuation"]),
        hi("SpecialComment", s["comment"], None, italic_comment or "italic"),
        hi("Underlined", s["attribute"], None, "underline"),
        hi("Error", s["error"]),
        hi("Todo", u["accent"], None, "bold"),
        hi("StatusLine", u["foreground"], u["surfaceAlt"]),
        hi("StatusLineNC", u["muted"], u["surface"]),
        hi("TabLine", u["muted"], u["surface"]),
        hi("TabLineFill", u["surfaceAlt"], u["surface"]),
        hi("TabLineSel", u["foreground"], u["background"], "bold"),
        hi("WinSeparator", u["muted"], u["background"]),
        hi("Pmenu", u["foreground"], u["surfaceAlt"]),
        hi("PmenuSel", u["foreground"], u["selection"]),
        hi("Search", u["foreground"], u["selection"]),
        hi("IncSearch", u["background"], u["accent"], "bold"),
        hi("DiffAdd", s["type"], u["background"]),
        hi("DiffChange", u["accent"], u["background"]),
        hi("DiffDelete", s["error"], u["background"]),
        hi("DiffText", s["attribute"], u["background"]),
        hi("@variable", s["variable"], None, italic_var),
        hi("@variable.parameter", s["attribute"]),
        hi("@function", s["function"], None, italic_fn),
        hi("@function.builtin", s["function"], None, italic_fn),
        hi("@keyword", s["keyword"]),
        hi("@type", s["type"]),
        hi("@string", s["string"]),
        hi("@comment", s["comment"], None, italic_comment or "italic"),
        hi("@tag", s["tag"]),
        hi("@tag.attribute", s["attribute"], None, italic_attr),
    ]

    body = "\n".join(f"  vim.cmd('{h}')" for h in highlights)
    return f"""-- {t['name']} for Neovim
vim.cmd('hi clear')
if vim.fn.exists('syntax_on') then
  vim.cmd('syntax reset')
end
vim.o.background = '{bg}'
vim.g.colors_name = 'serendipity-{variant}'

local M = {{}}
function M.setup()
{body}
end

M.setup()
return M
"""


def zed_theme(t: dict, variant: str) -> dict:
    s = t["syntax"]
    u = t["ui"]
    appearance = "light" if t["type"] == "light" else "dark"

    def rgba(hex_color: str, alpha: str = "ff") -> str:
        h = hex_color.lstrip("#")
        if len(h) == 8:
            return f"#{h[:6]}{alpha}"
        return f"#{h}{alpha}"

    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": f"Serendipity {variant.title()}",
        "author": "Micheal Andreuzza",
        "themes": [
            {
                "name": f"Serendipity {variant.title()}",
                "appearance": appearance,
                "style": {
                    "accents": [
                        rgba(s["type"]),
                        rgba(u["accent"]),
                        rgba(s["attribute"]),
                        rgba(s["keyword"]),
                        rgba(s["string"]),
                        rgba(s["error"]),
                        rgba(s["comment"]),
                    ],
                    "background": rgba(u["background"]),
                    "border": rgba(u["border"], "33"),
                    "border.focused": rgba(u["accent"], "77"),
                    "border.selected": rgba(u["accent"], "bb"),
                    "border.transparent": "#00000000",
                    "elevated_surface.background": rgba(u["surfaceAlt"]),
                    "surface.background": rgba(u["surface"], "ee"),
                    "element.background": rgba(u["surfaceAlt"]),
                    "element.hover": rgba(u["selection"]),
                    "element.selected": rgba(u["selection"]),
                    "text": rgba(u["foreground"]),
                    "text.muted": rgba(u["muted"]),
                    "text.accent": rgba(u["accent"]),
                    "icon": rgba(u["foreground"]),
                    "icon.muted": rgba(u["muted"]),
                    "status_bar.background": rgba(u["surface"]),
                    "title_bar.background": rgba(u["background"]),
                    "toolbar.background": rgba(u["surfaceAlt"]),
                    "tab_bar.background": rgba(u["surface"]),
                    "tab.inactive_background": rgba(u["surface"]),
                    "tab.active_background": rgba(u["background"]),
                    "panel.background": rgba(u["surface"]),
                    "editor.foreground": rgba(u["foreground"]),
                    "editor.background": rgba(u["background"]),
                    "editor.gutter.background": rgba(u["background"]),
                    "editor.active_line.background": rgba(u["lineHighlight"]),
                    "editor.line_number": rgba(u["muted"]),
                    "editor.active_line_number": rgba(u["foreground"]),
                    "scrollbar.thumb.background": rgba(u["muted"], "77"),
                    "scrollbar.track.background": rgba(u["surface"]),
                    "terminal.background": rgba(u["background"]),
                    "terminal.foreground": rgba(t["terminal"]["foreground"]),
                    "terminal.ansi.black": rgba(t["terminal"]["ansi0"]),
                    "terminal.ansi.red": rgba(t["terminal"]["ansi1"]),
                    "terminal.ansi.green": rgba(t["terminal"]["ansi2"]),
                    "terminal.ansi.yellow": rgba(t["terminal"]["ansi3"]),
                    "terminal.ansi.blue": rgba(t["terminal"]["ansi4"]),
                    "terminal.ansi.magenta": rgba(t["terminal"]["ansi5"]),
                    "terminal.ansi.cyan": rgba(t["terminal"]["ansi6"]),
                    "terminal.ansi.white": rgba(t["terminal"]["ansi7"]),
                    "terminal.ansi.bright_black": rgba(t["terminal"]["ansi8"]),
                    "terminal.ansi.bright_red": rgba(t["terminal"]["ansi9"]),
                    "terminal.ansi.bright_green": rgba(t["terminal"]["ansi10"]),
                    "terminal.ansi.bright_yellow": rgba(t["terminal"]["ansi11"]),
                    "terminal.ansi.bright_blue": rgba(t["terminal"]["ansi12"]),
                    "terminal.ansi.bright_magenta": rgba(t["terminal"]["ansi13"]),
                    "terminal.ansi.bright_cyan": rgba(t["terminal"]["ansi14"]),
                    "terminal.ansi.bright_white": rgba(t["terminal"]["ansi15"]),
                    "syntax": {
                        "comment": {"color": rgba(s["comment"]), "font_style": "italic"},
                        "keyword": {"color": rgba(s["keyword"])},
                        "string": {"color": rgba(s["string"])},
                        "function": {"color": rgba(s["function"]), "font_style": "italic"},
                        "variable": {"color": rgba(s["variable"]), "font_style": "italic"},
                        "type": {"color": rgba(s["type"])},
                        "constant": {"color": rgba(s["constant"])},
                        "tag": {"color": rgba(s["tag"])},
                        "attribute": {"color": rgba(s["attribute"]), "font_style": "italic"},
                        "punctuation": {"color": rgba(s["punctuation"])},
                    },
                },
            }
        ],
    }


def obsidian_css(t: dict, variant: str) -> str:
    s = t["syntax"]
    u = t["ui"]
    g = t["git"]
    mode = "light" if t["type"] == "light" else "dark"
    selector = ".theme-dark" if mode == "dark" else ".theme-light"

    return f"""/* {t['name']} for Obsidian */
{selector} {{
  --background-primary: {u['background']};
  --background-primary-alt: {u['surface']};
  --background-secondary: {u['surfaceAlt']};
  --background-secondary-alt: {u['surface']};
  --text-normal: {u['foreground']};
  --text-muted: {u['muted']};
  --text-faint: {u['muted']};
  --text-accent: {u['accent']};
  --text-accent-hover: {s['attribute']};
  --text-on-accent: {u['background']};
  --interactive-accent: {u['accent']};
  --interactive-accent-hover: {s['attribute']};
  --text-selection: {u['selection']};
  --text-link: {s['attribute']};
  --text-a: {s['attribute']};
  --text-a-hover: {s['keyword']};
  --text-mark: {s['type']};
  --text-tag: {g['untracked']};
  --markup-code: {s['string']};
  --code-normal: {s['string']};
  --code-comment: {s['comment']};
  --code-function: {s['function']};
  --code-keyword: {s['keyword']};
  --code-important: {s['error']};
  --code-property: {s['type']};
  --code-punctuation: {s['punctuation']};
  --code-string: {s['string']};
  --code-tag: {s['tag']};
  --code-value: {s['constant']};
  --blockquote-border: {s['attribute']};
  --titlebar-background: {u['background']};
  --titlebar-background-focused: {u['surface']};
  --tab-background-active: {u['background']};
  --tab-text-color-focused-active: {u['foreground']};
  --nav-item-background-hover: {u['selection']};
  --nav-item-background-active: {u['selection']};
  --checkbox-color: {u['accent']};
  --checkbox-color-hover: {s['attribute']};
}}
"""


def prism_css(t: dict) -> str:
    s = t["syntax"]
    u = t["ui"]
    return f"""/* {t['name']} for Prism.js */
code[class*="language-"],
pre[class*="language-"] {{
  color: {u['foreground']};
  background: {u['surfaceAlt']};
}}

.token.comment,
.token.prolog,
.token.doctype,
.token.cdata {{
  color: {s['comment']};
  font-style: italic;
}}

.token.punctuation {{
  color: {s['punctuation']};
}}

.token.property,
.token.tag,
.token.constant,
.token.symbol,
.token.deleted {{
  color: {s['tag']};
}}

.token.boolean,
.token.number {{
  color: {s['constant']};
}}

.token.selector,
.token.attr-name,
.token.string,
.token.char,
.token.builtin,
.token.inserted {{
  color: {s['string']};
}}

.token.operator,
.token.entity,
.token.url,
.language-css .token.string,
.style .token.string {{
  color: {s['attribute']};
}}

.token.atrule,
.token.attr-value,
.token.keyword {{
  color: {s['keyword']};
}}

.token.function,
.token.class-name {{
  color: {s['function']};
  font-style: italic;
}}

.token.regex,
.token.important,
.token.variable {{
  color: {s['variable']};
  font-style: italic;
}}

.token.important,
.token.bold {{
  font-weight: bold;
}}

.token.italic {{
  font-style: italic;
}}
"""


def shadcn_globals(t: dict) -> str:
    s = t["syntax"]
    u = t["ui"]
    g = t["git"]
    return f"""/* {t['name']} — shadcn/ui CSS variables */
@layer base {{
  :root {{
    --background: {u['background']};
    --foreground: {u['foreground']};
    --card: {u['surface']};
    --card-foreground: {u['foreground']};
    --popover: {u['surfaceAlt']};
    --popover-foreground: {u['foreground']};
    --primary: {u['accent']};
    --primary-foreground: {u['background']};
    --secondary: {u['surfaceAlt']};
    --secondary-foreground: {u['foreground']};
    --muted: {u['surface']};
    --muted-foreground: {u['muted']};
    --accent: {s['attribute']};
    --accent-foreground: {u['foreground']};
    --destructive: {s['error']};
    --destructive-foreground: {u['foreground']};
    --border: {u['border']};
    --input: {u['border']};
    --ring: {u['accent']};
    --chart-1: {s['keyword']};
    --chart-2: {g['added']};
    --chart-3: {s['string']};
    --chart-4: {s['type']};
    --chart-5: {s['error']};
    --radius: 0.5rem;
  }}
}}
"""


def tailwind_preset(all_tokens: dict) -> str:
    colors = {}
    for variant, t in all_tokens.items():
        colors[variant] = {
            "background": t["ui"]["background"],
            "foreground": t["ui"]["foreground"],
            "surface": t["ui"]["surface"],
            "accent": t["ui"]["accent"],
            "muted": t["ui"]["muted"],
            "keyword": t["syntax"]["keyword"],
            "string": t["syntax"]["string"],
            "error": t["syntax"]["error"],
        }
    return f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  theme: {{
    extend: {{
      colors: {json.dumps(colors, indent=6)}
    }},
  }},
}};
"""


def main():
    all_tokens = {v: extract_tokens(v) for v in VARIANTS}

    # color-palette
    cp = PROJECTS / "color-palette"
    write(cp / "tokens.json", json.dumps(all_tokens, indent=2) + "\n")
    write(cp / "LICENSE", LICENSE)
    write(
        cp / "README.md",
        f"""![Midnight]({HEADER})

# Serendipity Color Palette

Colors for all theme variants in many different formats.

## Files

- **`tokens.json`** — canonical UI, terminal, syntax, and git tokens for **Midnight**, **Sunset**, and **Morning**
- `palette.css`, `palettes.scss`, `tailwind.config.js` — raw color values for CSS and Tailwind

Use `tokens.json` for app ports, or the CSS/SCSS/Tailwind files for web projects.

If you need the colors in a different format, open an issue on GitHub.

## Regenerate tokens

From the [vs-code](https://github.com/Serendipity-Theme/vs-code) repository:

```bash
python3 scripts/generate-ports.py
```

## Check out the palette

![Serendipity Palette](https://user-images.githubusercontent.com/18015147/150700800-0f991263-ad9f-4246-9575-ba74dd95d9ff.png)

See all available interfaces at the [official website]({SITE}).
""",
    )

    # template-for-repositories
    tpl = PROJECTS / "template-for-repositories"
    write(tpl / "LICENSE", LICENSE)
    write(
        tpl / "README.md",
        f"""![Midnight]({HEADER})

# Serendipity for {{APP_NAME}}

Elegant, minimal, and clean color palette to give your eyes rest.

See other interfaces at the [official website]({SITE}).

## Available themes

- **Midnight** — dark
- **Sunset** — dark
- **Morning** — light

## Installation

{{INSTALL_INSTRUCTIONS}}

## Created by

{CREDIT}

---

## Repository layout

```
{{app}}/
├── LICENSE
├── README.md
├── serendipity-midnight.{{ext}}
├── serendipity-sunset.{{ext}}
└── serendipity-morning.{{ext}}
```

Colors are sourced from [color-palette/tokens.json](https://github.com/Serendipity-Theme/color-palette/blob/main/tokens.json).
""",
    )

    # ghostty
    gt = PROJECTS / "ghostty"
    write(gt / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(gt / f"serendipity-{v}", ghostty_config(t))
    write(
        gt / "README.md",
        readme(
            "Ghostty",
            """1. Clone or download this repository.
2. Copy the variant you want into your Ghostty config directory, or add an include to `~/.config/ghostty/config`:

```
config-file = ~/.config/ghostty/serendipity-midnight
```

3. Restart Ghostty and select the theme.

Available files: `serendipity-midnight`, `serendipity-sunset`, `serendipity-morning`.""",
        ),
    )

    # starship
    ss = PROJECTS / "starship"
    write(ss / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(ss / f"starship-{v}.toml", starship_config(t, v))
    write(
        ss / "README.md",
        readme(
            "Starship",
            """1. Copy the desired TOML file to your Starship config:

```bash
cp starship-midnight.toml ~/.config/starship.toml
```

2. Restart your shell.

Files: `starship-midnight.toml`, `starship-sunset.toml`, `starship-morning.toml`.""",
        ),
    )

    # lazygit
    lg = PROJECTS / "lazygit"
    write(lg / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(lg / f"lazygit-{v}.yml", lazygit_config(t))
    write(
        lg / "README.md",
        readme(
            "Lazygit",
            """1. Copy the desired YAML file to your Lazygit config:

```bash
mkdir -p ~/.config/lazygit
cp lazygit-midnight.yml ~/.config/lazygit/config.yml
```

2. Restart Lazygit.

Files: `lazygit-midnight.yml`, `lazygit-sunset.yml`, `lazygit-morning.yml`.""",
        ),
    )

    # neovim
    nv = PROJECTS / "neovim" / "colors"
    write(PROJECTS / "neovim" / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(nv / f"serendipity-{v}.lua", neovim_colorscheme(t, v))
    write(
        PROJECTS / "neovim" / "README.md",
        readme(
            "Neovim",
            """**Manual install**

```bash
git clone https://github.com/Serendipity-Theme/neovim.git ~/.config/nvim/colors/serendipity-src
cp ~/.config/nvim/colors/serendipity-src/colors/*.lua ~/.config/nvim/colors/
```

**Lazy.nvim**

```lua
{ "Serendipity-Theme/neovim", lazy = false }
```

Then set your colorscheme:

```lua
vim.cmd("colorscheme serendipity-midnight")
```

Variants: `serendipity-midnight`, `serendipity-sunset`, `serendipity-morning`.""",
        ),
    )

    # zed
    zd = PROJECTS / "zed"
    write(zd / "LICENSE", LICENSE)
    write(
        zd / "extension.toml",
        """id = "serendipity"
name = "Serendipity"
version = "1.0.0"
schema_version = 1
authors = ["Micheal Andreuzza <michael@andreuzza.com>"]
description = "Serendipity theme for Zed — Morning, Midnight, and Sunset"
repository = "https://github.com/Serendipity-Theme/zed"
""",
    )
    for v, t in all_tokens.items():
        write(
            zd / "themes" / f"serendipity-{v}.json",
            json.dumps(zed_theme(t, v), indent=2) + "\n",
        )
    write(
        zd / "README.md",
        readme(
            "Zed",
            """1. Clone this repository into your Zed extensions directory:

```bash
git clone https://github.com/Serendipity-Theme/zed.git ~/.config/zed/extensions/serendipity
```

2. Open Zed → Settings → Theme and select **Serendipity Midnight**, **Serendipity Sunset**, or **Serendipity Morning**.""",
        ),
    )

    # obsidian
    ob = PROJECTS / "obsidian"
    write(ob / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(ob / f"serendipity-{v}.css", obsidian_css(t, v))
    write(
        ob / "README.md",
        readme(
            "Obsidian",
            """1. Copy the desired CSS file to your Obsidian snippets folder:

```bash
cp serendipity-midnight.css "/path/to/vault/.obsidian/snippets/"
```

2. Open Obsidian → Settings → Appearance → CSS snippets → Enable the snippet.

Files: `serendipity-midnight.css`, `serendipity-sunset.css`, `serendipity-morning.css`.""",
        ),
    )

    # prism
    pr = PROJECTS / "prism"
    write(pr / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(pr / f"serendipity-{v}.css", prism_css(t))
    write(
        pr / "README.md",
        readme(
            "Prism.js",
            """**CDN / HTML**

```html
<link rel="stylesheet" href="serendipity-midnight.css">
```

**npm project**

Copy the desired file into your assets folder and import it in your layout.

Files: `serendipity-midnight.css`, `serendipity-sunset.css`, `serendipity-morning.css`.""",
        ),
    )

    # shadcn-ui
    sc = PROJECTS / "shadcn-ui"
    write(sc / "LICENSE", LICENSE)
    for v, t in all_tokens.items():
        write(sc / v / "globals.css", shadcn_globals(t))
    write(sc / "tailwind.preset.js", tailwind_preset(all_tokens))
    write(
        sc / "README.md",
        readme(
            "shadcn/ui",
            """1. Copy the variant folder's `globals.css` into your shadcn project (merge with existing `:root` variables).

```bash
cp morning/globals.css src/app/globals.css
```

2. Extend Tailwind with the preset:

```js
// tailwind.config.js
const serendipity = require('./tailwind.preset.js');
module.exports = {
  presets: [serendipity],
  // ...
};
```

Folders: `midnight/`, `sunset/`, `morning/` — each contains `globals.css`.""",
        ),
    )

    print("Generated repos:")
    for name in [
        "color-palette",
        "template-for-repositories",
        "ghostty",
        "starship",
        "lazygit",
        "neovim",
        "zed",
        "obsidian",
        "prism",
        "shadcn-ui",
    ]:
        print(f"  {PROJECTS / name}")


if __name__ == "__main__":
    main()
