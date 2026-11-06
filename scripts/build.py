#!/usr/bin/env python3
"""Generate the Flatcap 2.0 theme plugin for OpenClaw from src/theme.json.

    python3 scripts/build.py            # regenerate and validate
    python3 scripts/build.py --check    # fail if generated files are stale or invalid
    python3 scripts/build.py --sync     # refresh src/theme.json and src/logo.svg from ../00-Flatcap, then build
    python3 scripts/build.py --contrast # print the contrast report and exit

Inputs : src/theme.json  vendored copy of the Flatcap 2.0 core; the only source of colors, fonts and brand colors.
         src/logo.svg    vendored copy of the core symbol; the geometry of the plugin's brand icon.
Outputs: openclaw.plugin.json          plugin manifest (declares the theme)
         themes/flatcap.json           theme definition: Slate as dark, Daylight as light
         assets/theme-art/flatcap.svg  brand icon artwork
         README.md                     the blocks between <!-- build:NAME:start/end --> markers

Python 3.10+, standard library only. Output is deterministic.
OpenClaw limits mirrored here come from the installed Control UI / Gateway 2026.10.9 and
docs/plugins/manifest/surfaces.md (Themes): 4096 UTF-8 bytes per normalized definition, 16 KiB
per source file, 120 characters per value, artwork of at most 4 elements and 8192 path characters.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "src" / "theme.json"
LOGO = ROOT / "src" / "logo.svg"
CORE = (ROOT / ".." / "00-Flatcap").resolve()
README = ROOT / "README.md"
MANIFEST = ROOT / "openclaw.plugin.json"
DEFINITION = ROOT / "themes" / "flatcap.json"
ARTWORK = ROOT / "assets" / "theme-art" / "flatcap.svg"
PACKAGE = ROOT / "package.json"

PLUGIN_ID = "flatcap"
THEME_ID = "flatcap"
ICON_ID = "flatcap"
THEME_NAME = "Flatcap"
THEME_DESCRIPTION = (
    "Quiet precision: matte graphite Slate and soft Daylight surfaces, one mineral-blue accent, "
    "IBM Plex Sans and Cascadia Mono. Calm and flat, with no mascot."
)
PLUGIN_DESCRIPTION = (
    "Flatcap 2.0 appearance theme for the OpenClaw Control UI: Slate (dark) and Daylight (light)."
)

# OpenClaw limits ---------------------------------------------------------
MAX_DEFINITION_BYTES = 4096
MAX_SOURCE_BYTES = 16 * 1024
MAX_VALUE_CHARS = 120
MAX_SVG_BYTES = 32 * 1024
MAX_SVG_ELEMENTS = 4
MAX_SVG_PATH_CHARS = 8192
MAX_SVG_PATH_COMMANDS = 1024
COLOR_KEYS = [
    "background", "foreground", "card", "card-foreground", "popover", "popover-foreground",
    "primary", "primary-foreground", "secondary", "secondary-foreground", "muted",
    "muted-foreground", "accent", "accent-foreground", "destructive", "destructive-foreground",
    "border", "input", "ring",
]
FONT_KEYS = ["font-sans", "font-mono"]

# Presentation decisions (rationale in README, "Presentation") -------------
PRESENTATION = {
    "mascot": "none",
    "brandIcon": ICON_ID,
    "workingIndicator": "dots",
    "lobsterdex": False,
    "workingPhrases": [],
}

# Token mapping: OpenClaw semantic token -> Flatcap role, by intent. -------
# (token, role, what the OpenClaw Control UI uses it for)
TOKEN_MAP: list[tuple[str, str, str]] = [
    ("background", "bg.canvas", "App canvas behind everything."),
    ("foreground", "text.primary", "Chat text, headings, default ink."),
    ("card", "bg.surface", "Panels, message cards, form fields."),
    ("card-foreground", "text.primary", "Ink on cards."),
    ("popover", "bg.raised", "Menus, dialogs, hover cards: the only floating surfaces."),
    ("popover-foreground", "text.primary", "Ink on popovers."),
    ("primary", "accent.fill", "Primary action: Send, confirm."),
    ("primary-foreground", "accent.on", "Label on the primary action; never assumed white."),
    ("secondary", "bg.hover", "Quiet neutral fills: avatars, table heads, diff rows."),
    ("secondary-foreground", "text.secondary", "Secondary ink on those fills."),
    ("muted", "bg.hover", "Recessed fills: inline code, code blocks, switches; also the base of hover tints."),
    ("muted-foreground", "text.muted", "Metadata, timestamps, help text."),
    ("accent", "accent.fg", "Links, current item, accent marks and tints."),
    ("accent-foreground", "accent.on", "Ink on solid accent fills."),
    ("destructive", "danger.fg", "Destructive actions and error ink."),
    ("destructive-foreground", "danger.bg", "Label on a solid destructive fill (the feedback pair, reversed)."),
    ("border", "border.subtle", "Separators and panel edges (decorative)."),
    ("input", "border.control", "Outline that identifies a field or control."),
    ("ring", "focus.ring", "Keyboard focus."),
]
FONT_MAP = {"font-sans": "font.ui", "font-mono": "font.literal"}

# Contrast pairs (foreground token, background token, target) --------------
# Targets are Flatcap's (docs/accessibility.md), all at or above WCAG 2.2 AA:
# 7 primary text, 5 informative text, 4.5 labels on fills, 3 non-text.
SURFACES = ["background", "card", "popover", "muted", "secondary"]
PAIRS: list[tuple[str, str, float]] = (
    [("foreground", s, 7.0) for s in SURFACES]
    + [("card-foreground", "card", 7.0), ("popover-foreground", "popover", 7.0)]
    + [("secondary-foreground", "secondary", 5.0)]
    + [("muted-foreground", s, 5.0) for s in SURFACES]
    + [("primary-foreground", "primary", 4.5), ("accent-foreground", "accent", 4.5),
       ("destructive-foreground", "destructive", 4.5)]
    + [("accent", s, 5.0) for s in SURFACES]
    + [("destructive", s, 5.0) for s in ("background", "card", "popover")]
    + [("primary", s, 3.0) for s in ("background", "card", "popover")]
    + [("ring", s, 3.0) for s in ("background", "card", "popover")]
    + [("input", s, 3.0) for s in ("background", "card", "popover")]
)
# Selected surface is not an OpenClaw token; text on it is checked at the role level.
EXTRA_ROLE_PAIRS: list[tuple[str, str, float]] = [
    ("text.primary", "bg.selected", 7.0),
    ("text.muted", "bg.selected", 5.0),
]
WHITE = "#" + "F" * 6
BLACK = "#" + "0" * 6


def load() -> dict:
    return json.loads(THEME.read_text(encoding="utf-8"))


# color math --------------------------------------------------------------
def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lum(h: str) -> float:
    def ch(v: int) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a: str, b: str, pa: float) -> str:
    """color-mix(in srgb, a pa%, b): what the host does for its derived tokens."""
    ca, cb = rgb(a), rgb(b)
    return "#" + "".join(f"{round(x * pa + y * (1 - pa)):02X}" for x, y in zip(ca, cb))


# resolution --------------------------------------------------------------
def palette(theme: dict, mode: str) -> dict[str, str]:
    """OpenClaw palette for a Flatcap mode, resolved role by role."""
    roles = theme["themes"][mode]
    out = {token: roles[role] for token, role, _ in TOKEN_MAP}
    for key, role in FONT_MAP.items():
        out[key] = theme["typography"][role]
    return out


def definition(theme: dict) -> dict:
    d = {"name": THEME_NAME, "description": THEME_DESCRIPTION}
    d.update(PRESENTATION)
    d["dark"] = palette(theme, "slate")
    d["light"] = palette(theme, "daylight")
    return d


def normalized_size(d: dict) -> int:
    return len(json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def brand_color(theme: dict, role: str) -> str:
    b = theme["branding"]
    own = theme["themes"][b["theme"]]
    if role in own:
        return own[role]
    return b["colors"][role]


# artwork -----------------------------------------------------------------
SVG_NS = "http://www.w3.org/2000/svg"


def artwork(theme: dict) -> str:
    """Brand icon: tile disc, cap band and cap crown. The underside shade is omitted.

    OpenClaw rasterizes theme artwork with at most 4 elements including the root, so the
    4-shape master (disc + 3 cap parts) cannot fit; the darkest, lowest-contrast part goes.
    """
    root = ET.parse(LOGO).getroot()
    roles = theme["branding"]["roles"]
    by_role: dict[str, ET.Element] = {}
    transform = ""
    for el in root.iter():
        r = el.get("data-fc-role")
        if r:
            by_role[r] = el
        if el.tag.endswith("}g") and el.get("transform"):
            transform = el.get("transform")
    tile = by_role["tile"]
    comment = (
        "Flatcap symbol (reduced: the cap-underside shade is omitted to fit OpenClaw's 4-element artwork limit). "
        "Cap geometry carried from the Flatcap core. Designed by Vexels.com - 2021 All Rights Reserved - "
        "https://vexels.com/terms-and-conditions/ . Permission to modify and reuse the artwork was confirmed by the "
        "repository owner; MIT does not relicense it. See docs/branding.md in the Flatcap core."
    )
    view = root.get("viewBox")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f"<!-- {comment} -->",
        f'<svg xmlns="{SVG_NS}" width="256" height="256" viewBox="{view}">',
        f'  <circle cx="{tile.get("cx")}" cy="{tile.get("cy")}" r="{tile.get("r")}" '
        f'fill="{brand_color(theme, roles["tile"])}"/>',
    ]
    for part in ("cap.band", "cap.crown"):
        el = by_role[part]
        lines.append(
            f'  <path fill="{brand_color(theme, roles[part])}" transform="{transform}" d="{el.get("d")}"/>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


# manifest ----------------------------------------------------------------
def manifest(theme: dict) -> dict:
    return {
        "id": PLUGIN_ID,
        "name": THEME_NAME,
        "description": PLUGIN_DESCRIPTION,
        "version": theme["version"],
        "configSchema": {"type": "object", "additionalProperties": False},
        "themes": [
            {
                "id": THEME_ID,
                "name": THEME_NAME,
                "description": THEME_DESCRIPTION,
                "source": "themes/flatcap.json",
                "icons": {ICON_ID: "assets/theme-art/flatcap.svg"},
            }
        ],
    }


def dump(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


# README blocks -----------------------------------------------------------
def tokens_block(theme: dict) -> str:
    s, d = theme["themes"]["slate"], theme["themes"]["daylight"]
    rows = ["| OpenClaw token | Flatcap role | Slate (dark) | Daylight (light) | Used for |",
            "| :--- | :--- | :--- | :--- | :--- |"]
    for token, role, why in TOKEN_MAP:
        rows.append(f"| `{token}` | `{role}` | `{s[role]}` | `{d[role]}` | {why} |")
    for key, role in FONT_MAP.items():
        rows.append(f"| `{key}` | `{role}` | `{theme['typography'][role]}` | same | "
                    f"{'Interface and reading.' if key == 'font-sans' else 'Code, logs, IDs: one shared literal slot.'} |")
    return "\n".join(rows)


def pair_results(theme: dict, mode: str) -> list[tuple[str, str, float, float]]:
    p = palette(theme, mode)
    res = [(f, b, t, ratio(p[f], p[b])) for f, b, t in PAIRS]
    roles = theme["themes"][mode]
    res += [(f, b, t, ratio(roles[f], roles[b])) for f, b, t in EXTRA_ROLE_PAIRS]
    # host-derived: accent-hover = accent 82% + white (dark) or black (light) 18%
    hover = mix(p["accent"], WHITE if mode == "slate" else BLACK, 0.82)
    res.append(("accent-foreground", "accent-hover (host-derived)", 4.5, ratio(p["accent-foreground"], hover)))
    res.append(("accent-hover (host-derived)", "background", 3.0, ratio(hover, p["background"])))
    return res


def contrast_block(theme: dict) -> str:
    slate, day = pair_results(theme, "slate"), pair_results(theme, "daylight")
    rows = ["| Foreground | Background | Target | Slate | Daylight |", "| :--- | :--- | ---: | ---: | ---: |"]
    for (f, bg, t, rs), (_, _, _, rd) in zip(slate, day):
        def mark(r: float) -> str:
            return f"{r:.2f}:1" + ("" if r >= t else " FAIL")
        rows.append(f"| `{f}` | `{bg}` | {t:g}:1 | {mark(rs)} | {mark(rd)} |")
    return "\n".join(rows)


BLOCKS = {"tokens": tokens_block, "contrast": contrast_block}


def render_readme(theme: dict, text: str) -> str:
    for name, fn in BLOCKS.items():
        pat = re.compile(rf"(<!-- build:{name}:start -->\n).*?(\n<!-- build:{name}:end -->)", re.S)
        if not pat.search(text):
            raise SystemExit(f"error: README.md is missing the build:{name} markers")
        body = fn(theme)
        text = pat.sub(lambda m: m.group(1) + body + m.group(2), text)
    return text


# validation --------------------------------------------------------------
HEX = "#" + "[0-9a-fA-F]{6}"
FONT_ID = r"(?:--[a-z0-9_-]*|-?[a-z_][a-z0-9_-]*)"
FONT_FAMILY = rf"(?:\"[a-z0-9 ,'._-]*\"|'[a-z0-9 ,\"._-]*'|{FONT_ID}(?: +{FONT_ID})*)"
FONT_LIST = re.compile(rf"^{FONT_FAMILY}(?: *, *{FONT_FAMILY})*$", re.I)
NUM = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
SVG_ALLOWED_TAGS = {"circle", "desc", "ellipse", "g", "line", "path", "polygon", "polyline", "rect", "svg", "title"}
SVG_ATTR = {
    "xmlns": re.compile(r"^http://www\.w3\.org/2000/svg$"),
    "d": re.compile(r"^[0-9a-zA-Z+.,\s-]+$"),
    "viewBox": re.compile(r"^[0-9eE+.,\s-]+$"),
    "fill": re.compile(r"^(?:none|currentColor|#[0-9a-f]{3,8})$", re.I),
    "transform": re.compile(r"^(?:\s*(?:matrix|rotate|scale|skewX|skewY|translate)\(\s*[0-9eE+.,\s-]+\)\s*)+$"),
    "cx": NUM, "cy": NUM, "r": NUM, "width": NUM, "height": NUM,
}


def theme_hexes(theme: dict) -> set[str]:
    values = set()
    for mode in theme["themes"].values():
        values.update(v.upper() for v in mode.values())
    values.update(v.upper() for v in theme["branding"]["colors"].values())
    return values


def validate(theme: dict) -> list[str]:
    errs: list[str] = []
    if not str(theme.get("version", "")).startswith("2."):
        errs.append(f"expected Flatcap 2.x theme.json, got {theme.get('version')}")
    d = definition(theme)
    allowed = theme_hexes(theme)

    # completeness: every token, both modes, values from the core only
    for mode in ("dark", "light"):
        keys = set(d[mode])
        missing = set(COLOR_KEYS + FONT_KEYS) - keys
        extra = keys - set(COLOR_KEYS + FONT_KEYS)
        if missing:
            errs.append(f"{mode}: missing tokens {sorted(missing)}")
        if extra:
            errs.append(f"{mode}: unsupported tokens {sorted(extra)}")
        for k, v in d[mode].items():
            if len(v) > MAX_VALUE_CHARS:
                errs.append(f"{mode}.{k}: {len(v)} characters exceeds {MAX_VALUE_CHARS}")
            if k in COLOR_KEYS and not re.fullmatch(HEX, v):
                errs.append(f"{mode}.{k}: {v!r} is not a 6-digit hex color")
            if k in COLOR_KEYS and v.upper() not in allowed:
                errs.append(f"{mode}.{k}: {v} is not a value of src/theme.json")
            if k in FONT_KEYS and not FONT_LIST.match(v):
                errs.append(f"{mode}.{k}: not a valid font-family list for OpenClaw")
    if not 1 <= len(d["name"]) <= 80:
        errs.append("name length out of range")
    if not 1 <= len(d["description"]) <= 320:
        errs.append("description length out of range")

    # sizes
    size = normalized_size(d)
    if size >= MAX_DEFINITION_BYTES:
        errs.append(f"definition is {size} bytes, limit {MAX_DEFINITION_BYTES}")
    if len(dump(d).encode()) > MAX_SOURCE_BYTES:
        errs.append("source file exceeds 16 KiB")

    # artwork
    svg = artwork(theme)
    if len(svg.encode()) > MAX_SVG_BYTES:
        errs.append("artwork exceeds 32 KiB")
    if re.search(r"<\s*(?:script|foreignObject|image|use|iframe)\b|\b(?:href|src)\s*=|<!doctype|<!entity", svg, re.I):
        errs.append("artwork is not self-contained")
    root = ET.fromstring(svg.encode("utf-8"))
    elements = list(root.iter())
    if len(elements) > MAX_SVG_ELEMENTS:
        errs.append(f"artwork has {len(elements)} elements, limit {MAX_SVG_ELEMENTS}")
    path_chars = commands = 0
    for el in elements:
        tag = el.tag.split("}")[-1]
        if tag not in SVG_ALLOWED_TAGS:
            errs.append(f"artwork element <{tag}> is not allowed")
        for name, value in el.attrib.items():
            rule = SVG_ATTR.get(name)
            if rule is None or not rule.match(value.strip()):
                errs.append(f"artwork attribute {name!r} on <{tag}> is not allowed")
            if name == "fill" and value.upper() not in allowed:
                errs.append(f"artwork fill {value} is not a value of src/theme.json")
            if name == "d":
                path_chars += len(value)
                commands += len(re.findall(r"[a-zA-Z]", value))
    if path_chars > MAX_SVG_PATH_CHARS or commands > MAX_SVG_PATH_COMMANDS:
        errs.append("artwork path data exceeds OpenClaw limits")

    # contrast of declared pairs
    for mode in ("slate", "daylight"):
        for f, b, t, r in pair_results(theme, mode):
            if r < t:
                errs.append(f"contrast {mode}: {f} on {b} is {r:.2f}:1, target {t:g}:1")

    # hand-written files carry no raw colors
    for path in (Path(__file__), PACKAGE):
        if path.is_file() and re.search(HEX, path.read_text(encoding="utf-8")):
            errs.append(f"{path.relative_to(ROOT)} contains a raw hex color; colors come from src/theme.json")
    return errs


def generated(theme: dict) -> dict[Path, str]:
    out = {
        MANIFEST: dump(manifest(theme)),
        DEFINITION: dump(definition(theme)),
        ARTWORK: artwork(theme),
    }
    if README.is_file():
        out[README] = render_readme(theme, README.read_text(encoding="utf-8"))
    return out


def package_errors(theme: dict) -> list[str]:
    if not PACKAGE.is_file():
        return ["package.json is missing"]
    errs = []
    pkg = json.loads(PACKAGE.read_text(encoding="utf-8"))
    if pkg.get("version") != theme["version"]:
        errs.append(f"package.json version {pkg.get('version')} != theme version {theme['version']}")
    files = set(pkg.get("files", []))
    for needed in ("index.js", "openclaw.plugin.json", "themes", "assets/theme-art"):
        if needed not in files:
            errs.append(f"package.json files must include {needed}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if generated files are stale or invalid")
    ap.add_argument("--contrast", action="store_true", help="print the contrast report and exit")
    ap.add_argument("--sync", nargs="?", const=str(CORE), metavar="PATH",
                    help="copy theme.json and logo.svg from the core checkout (default ../00-Flatcap)")
    args = ap.parse_args()

    if args.sync:
        core = Path(args.sync)
        for rel, dst in (("src/theme.json", THEME), ("src/logo.svg", LOGO)):
            if not (core / rel).is_file():
                print(f"error: {core / rel} not found", file=sys.stderr)
                return 2
            shutil.copyfile(core / rel, dst)
            print(f"synced {core / rel} -> {dst.relative_to(ROOT)}")

    theme = load()
    if args.contrast:
        for mode in ("slate", "daylight"):
            print(f"[{mode}]")
            for f, b, t, r in pair_results(theme, mode):
                print(f"  {f:<28} on {b:<30} {r:6.2f}:1  target {t:g}:1  {'ok' if r >= t else 'FAIL'}")
        return 0

    errs = validate(theme) + package_errors(theme)
    files = generated(theme)
    d = definition(theme)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, text in files.items()
                 if not p.is_file() or p.read_text(encoding="utf-8") != text]
        if stale:
            errs.append("stale: " + ", ".join(stale) + " (run python3 scripts/build.py)")
        if errs:
            print("\n".join("error: " + e for e in errs), file=sys.stderr)
            return 1
        print(f"ok: generated files are up to date; definition {normalized_size(d)}/{MAX_DEFINITION_BYTES} bytes; "
              f"{len(COLOR_KEYS)} colors + {len(FONT_KEYS)} fonts in both modes; contrast targets met")
        return 0
    if errs:
        print("\n".join("error: " + e for e in errs), file=sys.stderr)
        return 1
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(text.encode())} bytes)")
    print(f"definition {normalized_size(d)}/{MAX_DEFINITION_BYTES} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
