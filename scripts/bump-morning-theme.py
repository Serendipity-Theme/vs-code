#!/usr/bin/env python3
"""Apply a slight color bump to Serendipity Morning (richer accents, stronger contrast)."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "themes" / "serendipity-morning.json"

# Longer hex values first so alpha suffixes match correctly.
MORNING_BUMP = [
    # Backgrounds & surfaces
    ("#fdfdfe", "#f6f7fb"),
    ("#f1f1f4", "#eaebee"),
    ("#d8dae4", "#ccd0dc"),
    # Text & muted UI
    ("#4e5377", "#3f4363"),
    ("#5f6488", "#505575"),
    ("#8388ad", "#6d7296"),
    # Accent & syntax
    ("#f19a8e", "#e58678"),
    ("#7397de", "#6288d8"),
    ("#3788be", "#2f7aab"),
    ("#77aab3", "#629aa5"),
    ("#886cdb", "#785fd0"),
    ("#d26a5d", "#c25a4d"),
    # Selection / overlay tints (slightly stronger on light bg)
    ("#6e6a8614", "#5a567018"),
    ("#6e6a8626", "#5a567030"),
    ("#6e6a860d", "#5a567012"),
]


def replace_hex(value: str, replacements: list[tuple[str, str]]) -> str:
    if not isinstance(value, str) or not value.startswith("#"):
        return value
    lower = value.lower()
    for old, new in replacements:
        if lower == old:
            return new
        if lower.startswith(old) and len(lower) > len(old):
            return new + lower[len(old) :]
    return value


def transform_node(node, replacements: list[tuple[str, str]]):
    if isinstance(node, dict):
        return {k: transform_node(v, replacements) for k, v in node.items()}
    if isinstance(node, list):
        return [transform_node(v, replacements) for v in node]
    if isinstance(node, str):
        return replace_hex(node, replacements)
    return node


def main() -> None:
    theme = json.loads(THEME.read_text())
    bumped = transform_node(theme, MORNING_BUMP)
    THEME.write_text(json.dumps(bumped, indent=2) + "\n")
    print(f"Bumped {THEME.name}")


if __name__ == "__main__":
    main()
