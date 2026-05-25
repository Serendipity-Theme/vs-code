#!/usr/bin/env python3
"""Generate Sublime Text, Logseq, Base16, and Shiki ports."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "generate_ports", ROOT / "scripts" / "generate-ports.py"
)
_gp = importlib.util.module_from_spec(_spec)
sys.modules["generate_ports"] = _gp
assert _spec.loader is not None
_spec.loader.exec_module(_gp)

AUTHOR_CREDIT = _gp.AUTHOR_CREDIT
HEADER = _gp.HEADER
LICENSE = _gp.LICENSE
PROJECTS = _gp.PROJECTS
THEMES = _gp.THEMES
VARIANTS = _gp.VARIANTS
WEBSITE = _gp.WEBSITE
PREFIX = _gp.PREFIX
Tokens = _gp.Tokens
bat_tmtheme = _gp.bat_tmtheme
load_tokens = _gp.load_tokens
write = _gp.write
write_port = _gp.write_port
with_alpha = _gp.with_alpha

LOGSEQ_OUT = PROJECTS / "logseq"
SUBLIME_OUT = PROJECTS / "sublime-text"
BASE16_OUT = PROJECTS / "base16"
SHIKI_OUT = PROJECTS / "shiki"


def logseq_css_vars(tokens: Tokens) -> str:
    return f"""  --ls-primary-background-color: {tokens.background};
  --ls-primary-text-color: {tokens.foreground};
  --ls-secondary-background-color: {tokens.surface};
  --ls-secondary-text-color: {tokens.muted};
  --ls-tertiary-background-color: {tokens.background};
  --ls-quaternary-background-color: {tokens.surface};
  --ls-link-text-color: {tokens.function};
  --ls-link-text-hover-color: {tokens.accent};
  --ls-border-color: {with_alpha(tokens.muted, "40")};
  --ls-icon-color: {tokens.muted};
  --ls-selection-background-color: {tokens.selection_bg};
  --ls-block-bullet-color: {tokens.accent};
  --ls-block-bullet-active-color: {tokens.function};
  --ls-page-checkbox-color: {tokens.accent};
  --ls-focus-ring-color: {with_alpha(tokens.accent, "77")};
  --ls-a-chosen-bg: {tokens.selection_bg};
  --ls-menu-hover-color: {tokens.selection_bg};
  --ls-table-tr-even-background-color: {tokens.surface};
  --ls-code-block-background-color: {tokens.surface};
  --ls-page-inline-code-color: {tokens.string};
  --ls-page-inline-code-bg-color: {with_alpha(tokens.surface, "cc")};
  --ls-page-mark-bg-color: {with_alpha(tokens.accent, "33")};
  --ls-page-mark-color: {tokens.foreground};
  --ls-page-properties-background-color: {tokens.surface};
  --ls-page-title-color: {tokens.foreground};
  --ls-h1-color: {tokens.foreground};
  --ls-h2-color: {tokens.type_color};
  --ls-h3-color: {tokens.keyword};
  --ls-tag-text-color: {tokens.type_color};
  --ls-tag-text-hover-color: {tokens.accent};
  --ls-quote-background-color: {tokens.surface};
  --ls-quote-foreground-color: {tokens.muted};
  --ls-guidance-text-color: {tokens.muted};
  --ls-guidance-background-color: {tokens.surface};
  --ls-guidance-warning-text-color: {tokens.error};
  --ls-guidance-warning-background-color: {with_alpha(tokens.error, "22")};
  --ls-guidance-suggestion-text-color: {tokens.string};
  --ls-guidance-suggestion-background-color: {with_alpha(tokens.string, "22")};
  --ct-background: {tokens.background};
  --ct-page-font-color: {tokens.foreground};
"""


def logseq_css(tokens: Tokens, *, brand: str) -> str:
    return f"""/* {brand} {tokens.name} for Logseq */
:root {{
{logseq_css_vars(tokens)}
}}

html, body {{
  background-color: var(--ls-primary-background-color);
  color: var(--ls-primary-text-color);
}}
"""


def base16_yaml(tokens: Tokens, *, brand: str, slug: str) -> str:
    t = tokens.terminal
    return f"""system: "base16"
name: "{tokens.name}"
author: "Micheal Andreuzza (https://michaelandreuzza.com/)"
description: "{brand} {tokens.name} from the {brand} theme family"
variant: "{tokens.appearance}"
palette:
  base00: "{tokens.background}"
  base01: "{tokens.surface}"
  base02: "{tokens.surface}"
  base03: "{tokens.comment}"
  base04: "{tokens.muted}"
  base05: "{tokens.foreground}"
  base06: "{tokens.foreground}"
  base07: "{tokens.accent_fg}"
  base08: "{t['red']}"
  base09: "{tokens.function}"
  base0A: "{t['yellow']}"
  base0B: "{t['green']}"
  base0C: "{t['cyan']}"
  base0D: "{tokens.type_color}"
  base0E: "{tokens.string}"
  base0F: "{tokens.constant}"
"""


def shiki_theme(vid: str, fname: str) -> str:
    raw = json.loads((THEMES / fname).read_text(encoding="utf-8"))
    name = raw.get("name", f"Serendipity {vid.title()}")
    return json.dumps(
        {
            "name": name,
            "type": raw.get("type", "dark"),
            "colors": raw.get("colors", {}),
            "tokenColors": raw.get("tokenColors", []),
        },
        indent=2,
    ) + "\n"


def logseq_marketplace_md(*, brand: str, github: str) -> str:
    return f"""# Publish {brand} to Logseq Marketplace

1. Fork [logseq/marketplace](https://github.com/logseq/marketplace).
2. Add `packages/{brand.lower()}/manifest.json`:

```json
{{
  "title": "{brand}",
  "description": "{brand} theme family for Logseq.",
  "author": "Micheal Andreuzza",
  "repo": "{github.replace('https://github.com/', '')}",
  "theme": true
}}
```

3. Open a pull request.
"""


def generate() -> None:
    all_tokens = {vid: load_tokens(vid, fname) for vid, fname in VARIANTS}

    sublime_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.tmTheme"
        sublime_files.append(f)
        write(SUBLIME_OUT / f, bat_tmtheme(tok))
    write_port(
        "sublime-text",
        "Copy `.tmTheme` files to `Packages/User/` or install via Package Control. "
        "Set **Preferences → Color Scheme** to Serendipity Midnight / Morning / Sunset.",
        "Serendipity for Sublime Text",
        sublime_files,
    )

    logseq_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.css"
        logseq_files.append(f)
        write(LOGSEQ_OUT / f, logseq_css(tok, brand="Serendipity"))
    write(
        LOGSEQ_OUT / "MARKETPLACE.md",
        logseq_marketplace_md(
            brand="Serendipity",
            github="https://github.com/Serendipity-Theme/logseq",
        ),
    )
    logseq_files.append("MARKETPLACE.md")
    write_port(
        "logseq",
        "Import a CSS file into Logseq **Settings → Custom CSS**, or use `@import` in `logseq/custom.css`. "
        "See `MARKETPLACE.md` to list in the Logseq Marketplace.",
        "Serendipity for Logseq",
        logseq_files,
    )

    base16_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.yaml"
        base16_files.append(f)
        write(BASE16_OUT / f, base16_yaml(tok, brand="Serendipity", slug=vid))
    write_port(
        "base16",
        "Submit YAML files to [tinted-theming/schemes](https://github.com/tinted-theming/schemes) under `base16/`. "
        "Use with Base16-compatible tools (Alacritty, Kitty, Vim, etc.).",
        "Serendipity for Base16",
        base16_files,
    )

    shiki_files: list[str] = []
    for vid, fname in VARIANTS:
        f = f"{PREFIX}-{vid}.json"
        shiki_files.append(f)
        write(SHIKI_OUT / f, shiki_theme(vid, fname))
    write_port(
        "shiki",
        "Import JSON themes into [Shiki](https://shiki.style/) for docs sites, Astro, and MDX.",
        "Serendipity for Shiki",
        shiki_files,
    )

    print("Generated extra Serendipity ports:")
    for d in (SUBLIME_OUT, LOGSEQ_OUT, BASE16_OUT, SHIKI_OUT):
        print(" ", d)


if __name__ == "__main__":
    generate()
