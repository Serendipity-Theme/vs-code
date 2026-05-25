#!/usr/bin/env python3
"""Prepare Warp, iTerm2-Color-Schemes, and Helix submission files."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECTS = Path("/Users/michelandreuzza/Desktop/projects")
OUT = Path("/tmp/theme-submissions")

SERENDIPITY_VARIANTS = ["midnight", "morning", "sunset"]
SEQUOIA_VARIANTS = [
    ("moonlight-dark", "Sequoia Moonlight Dark"),
    ("moonlight-light", "Sequoia Moonlight Light"),
    ("monochrome-dark", "Sequoia Monochrome Dark"),
    ("monochrome-light", "Sequoia Monochrome Light"),
    ("retro-dark", "Sequoia Retro Dark"),
    ("retro-light", "Sequoia Retro Light"),
]


def gh_cat(repo: str, path: str) -> bytes:
    out = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
        text=True,
    )
    import base64

    return base64.b64decode(out)


def warp_yaml(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    if lines and lines[0].strip() == "":
        lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def helix_theme(path: Path, slug: str) -> str:
    body = path.read_text(encoding="utf-8")
    body = re.sub(r"^# Serendipity Serendipity ", "# ", body, count=1)
    body = re.sub(r"^# Sequoia Sequoia ", "# ", body, count=1)
    header = (
        "# Author : Micheal Andreuzza <michael@andreuzza.com>\n"
        "# License: MIT\n\n"
    )
    if "Author :" not in body:
        body = header + body
    return body


def windowsterminal_from_scheme(scheme: dict) -> dict:
    return {k: v for k, v in scheme.items()}


def parse_serendipity_schemes() -> list[dict]:
    raw = gh_cat("Serendipity-Theme/windows-terminal", "schemes.jsonc").decode()
    raw = re.sub(r"//.*", "", raw)
    data = json.loads(raw)
    return data["schemes"]


def prepare_warp() -> None:
    dest = OUT / "warp/standard"
    dest.mkdir(parents=True, exist_ok=True)

    for vid in SERENDIPITY_VARIANTS:
        src = PROJECTS / "warp" / f"serendipity-{vid}.yaml"
        (dest / f"serendipity_{vid}.yaml").write_text(warp_yaml(src), encoding="utf-8")

    seq_warp = PROJECTS / "sequoia-ports" / "warp"
    for slug, _name in SEQUOIA_VARIANTS:
        src = seq_warp / f"sequoia-{slug}.yaml"
        if src.exists():
            (dest / f"sequoia_{slug.replace('-', '_')}.yaml").write_text(
                warp_yaml(src), encoding="utf-8"
            )


def prepare_iterm2() -> None:
    schemes = OUT / "iterm2/schemes"
    wt = OUT / "iterm2/windowsterminal"
    schemes.mkdir(parents=True, exist_ok=True)
    wt.mkdir(parents=True, exist_ok=True)

    ser_iterm = {
        "SerendipityMidnight.itermcolors": "Serendipity Midnight.itermcolors",
        "SerendipitySunset.itermcolors": "Serendipity Sunset.itermcolors",
        "serendipityMorning.itermcolors": "Serendipity Morning.itermcolors",
    }
    for remote, local in ser_iterm.items():
        (schemes / local).write_bytes(gh_cat("Serendipity-Theme/iterm", remote))

    for scheme in parse_serendipity_schemes():
        name = scheme["name"]
        fname = name.replace(" ", " ") + ".json"
        (wt / fname).write_text(json.dumps(scheme, indent=2) + "\n", encoding="utf-8")

    seq_map = [
        ("SequoiaMoonlight - iTerm.itermcolors", "Sequoia Moonlight Dark.itermcolors"),
        ("SequoiaMonochomre - iTerm.itermcolors", "Sequoia Monochrome Dark.itermcolors"),
    ]
    for remote, local in seq_map:
        try:
            (schemes / local).write_bytes(gh_cat("Sequoia-Theme/iterm", remote))
        except subprocess.CalledProcessError:
            pass

    for slug, display in SEQUOIA_VARIANTS:
        src = PROJECTS / "sequoia-ports" / "warp" / f"sequoia-{slug}.yaml"
        if not src.exists():
            continue
        yaml_text = warp_yaml(src)
        colors: dict[str, str] = {}
        section = None
        for line in yaml_text.splitlines():
            if line.startswith("terminal_colors:"):
                continue
            if line.strip() in ("normal:", "bright:"):
                section = line.strip().rstrip(":")
                continue
            m = re.match(r"\s+(\w+):\s+'([^']+)'", line)
            if not m or section is None:
                if m := re.match(r"(\w+):\s+'([^']+)'", line):
                    colors[m.group(1)] = m.group(2)
                continue
            key = m.group(1)
            val = m.group(2)
            if section == "normal":
                mapping = {
                    "black": "black",
                    "red": "red",
                    "green": "green",
                    "yellow": "yellow",
                    "blue": "blue",
                    "magenta": "purple",
                    "cyan": "cyan",
                    "white": "white",
                }
            else:
                mapping = {
                    "black": "brightBlack",
                    "red": "brightRed",
                    "green": "brightGreen",
                    "yellow": "brightYellow",
                    "blue": "brightBlue",
                    "magenta": "brightPurple",
                    "cyan": "brightCyan",
                    "white": "brightWhite",
                }
            if key in mapping:
                colors[mapping[key]] = val
        scheme = {
            "name": display,
            "background": colors.get("background", "#000000"),
            "foreground": colors.get("foreground", "#ffffff"),
            "cursorColor": colors.get("accent", colors.get("foreground", "#ffffff")),
            "selectionBackground": colors.get("background", "#000000"),
            **{k: v for k, v in colors.items() if k not in {"background", "foreground", "accent"}},
        }
        (wt / f"{display}.json").write_text(json.dumps(scheme, indent=2) + "\n", encoding="utf-8")


def prepare_helix() -> None:
    themes = OUT / "helix/runtime/themes"
    licenses = OUT / "helix/runtime/themes/licenses"
    themes.mkdir(parents=True, exist_ok=True)
    licenses.mkdir(parents=True, exist_ok=True)

    for vid in SERENDIPITY_VARIANTS:
        slug = f"serendipity-{vid}"
        src = PROJECTS / "helix" / "themes" / f"{slug}.toml"
        (themes / f"{slug}.toml").write_text(helix_theme(src, slug), encoding="utf-8")
        (licenses / f"{slug}.license").write_text("MIT\n", encoding="utf-8")

    seq_helix = PROJECTS / "sequoia-ports" / "helix" / "themes"
    if seq_helix.exists():
        for path in sorted(seq_helix.glob("*.toml")):
            slug = path.stem
            (themes / f"{slug}.toml").write_text(helix_theme(path, slug), encoding="utf-8")
            (licenses / f"{slug}.license").write_text("MIT\n", encoding="utf-8")


def kitty_theme(conf: Path, *, name: str, upstream: str, blurb: str) -> str:
    lines = conf.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    body = "\n".join(line for line in lines if line.strip()).strip()
    return (
        "# vim:ft=kitty\n"
        f"## name: {name}\n"
        "## author: Micheal Andreuzza\n"
        "## license: MIT\n"
        f"## upstream: {upstream}\n"
        f"## blurb: {blurb}\n\n"
        f"{body}\n"
    )


def prepare_kitty() -> None:
    dest = OUT / "kitty-themes/themes"
    dest.mkdir(parents=True, exist_ok=True)

    ser_map = [
        ("midnight", "Serendipity Midnight"),
        ("morning", "Serendipity Morning"),
        ("sunset", "Serendipity Sunset"),
    ]
    for vid, name in ser_map:
        src = PROJECTS / "kitty" / f"serendipity-{vid}.conf"
        upstream = f"https://raw.githubusercontent.com/Serendipity-Theme/kitty/main/serendipity-{vid}.conf"
        fname = name.replace(" ", "_") + ".conf"
        (dest / fname).write_text(
            kitty_theme(src, name=name, upstream=upstream, blurb=f"{name} from the Serendipity theme family."),
            encoding="utf-8",
        )

    seq_dir = PROJECTS / "sequoia-ports" / "kitty"
    for slug, display in SEQUOIA_VARIANTS:
        src = seq_dir / f"sequoia-{slug}.conf"
        if not src.exists():
            continue
        upstream = f"https://raw.githubusercontent.com/Sequoia-Theme/kitty/main/sequoia-{slug}.conf"
        fname = display.replace(" ", "_") + ".conf"
        (dest / fname).write_text(
            kitty_theme(
                src,
                name=display,
                upstream=upstream,
                blurb=f"{display} from the Sequoia theme family.",
            ),
            encoding="utf-8",
        )


def prepare_base16() -> None:
    dest = OUT / "base16"
    dest.mkdir(parents=True, exist_ok=True)
    src = PROJECTS / "base16"
    if src.exists():
        for path in sorted(src.glob("*.yaml")):
            shutil.copy2(path, dest / path.name)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    prepare_warp()
    prepare_iterm2()
    prepare_helix()
    prepare_kitty()
    prepare_base16()
    print("Prepared submission files in", OUT)


if __name__ == "__main__":
    main()
