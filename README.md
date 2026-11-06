<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/screenshot-slate.png">
    <img src="images/screenshot-daylight.png" alt="OpenClaw Control UI with the Flatcap theme: a chat with a code block, table and composer" width="900">
  </picture>
</p>

# Flatcap for OpenClaw

Flatcap 2.0 as a theme for the OpenClaw Control UI: **Slate** (dark) and **Daylight** (light). Quiet, flat and matte, with one mineral-blue accent, IBM Plex Sans for reading and Cascadia Mono for code. No mascot.

It is a declarative plugin: the theme is data in `themes/flatcap.json`, declared in `openclaw.plugin.json`. The only code is an `index.js` that registers nothing (OpenClaw 2026.10.9 did not discover a manifest-only plugin without an entry point).

## Install

Requires OpenClaw 2026.10.9 or newer (see [Compatibility](#compatibility)).

```sh
# from a local checkout (copy)
openclaw plugins install /path/to/flatcap-openclaw
# or link it while developing
openclaw plugins install -l /path/to/flatcap-openclaw
```

`git:github.com/<owner>/<repo>`, `npm:<package>` and `clawhub:<package>` sources are supported by `openclaw plugins install`, but this package has not been published to any of them yet. Only enabled plugins contribute themes; installing enables the plugin unless you pass `--no-enable`.

## Select it

Open **Settings → Appearance → Theme** and choose **Flatcap**. Its full ID is `flatcap/flatcap`. Color mode follows the Control UI setting (System, Light or Dark): Dark uses Slate, Light uses Daylight.

An agent can do the same through the `theme` tool with the ID `flatcap/flatcap`.

## Fonts

- UI and reading: IBM Plex Sans (bundled with the Control UI).
- Code, logs, IDs: Cascadia Mono, falling back to Cascadia Code, `ui-monospace`, Consolas. Cascadia Mono is **not** bundled; without it installed the fallbacks apply.

## Design decisions

- **Roles, not positions.** Each OpenClaw token is mapped by intent from the Flatcap role palette (table below), never by order.
- **Flat.** Surfaces separate by tone and hairline borders; popovers (`bg.raised`) are the only floating layer.
- **No mascot.** `mascot: "none"`, `lobsterdex: false`, `workingPhrases: []`, `workingIndicator: "dots"`. The community-links entry is left at the host default.
- **Own brand icon.** `brandIcon: "flatcap"` uses `assets/theme-art/flatcap.svg`, derived from the Flatcap symbol. One shadow was dropped to fit OpenClaw's four-element artwork limit. `brandName` is omitted, so the product name stays "OpenClaw".
- **Control outlines are real.** `input` maps to `border.control`, which meets 3:1 against its surfaces; decorative separators use `border.subtle`.
- **One value for two roles.** `secondary` and `muted` both map to `bg.hover`; `primary` and `accent` share the accent family.

## Token mapping

<!-- build:tokens:start -->
| OpenClaw token | Flatcap role | Slate (dark) | Daylight (light) | Used for |
| :--- | :--- | :--- | :--- | :--- |
| `background` | `bg.canvas` | `#191D22` | `#F3F5F7` | App canvas behind everything. |
| `foreground` | `text.primary` | `#D5DBE3` | `#28313B` | Chat text, headings, default ink. |
| `card` | `bg.surface` | `#20252B` | `#FAFBFC` | Panels, message cards, form fields. |
| `card-foreground` | `text.primary` | `#D5DBE3` | `#28313B` | Ink on cards. |
| `popover` | `bg.raised` | `#292F36` | `#FFFFFF` | Menus, dialogs, hover cards: the only floating surfaces. |
| `popover-foreground` | `text.primary` | `#D5DBE3` | `#28313B` | Ink on popovers. |
| `primary` | `accent.fill` | `#9BBFDF` | `#285D85` | Primary action: Send, confirm. |
| `primary-foreground` | `accent.on` | `#101820` | `#FAFBFC` | Label on the primary action; never assumed white. |
| `secondary` | `bg.hover` | `#323A43` | `#E6EBF0` | Quiet neutral fills: avatars, table heads, diff rows. |
| `secondary-foreground` | `text.secondary` | `#AEB8C4` | `#465463` | Secondary ink on those fills. |
| `muted` | `bg.hover` | `#323A43` | `#E6EBF0` | Recessed fills: inline code, code blocks, switches; also the base of hover tints. |
| `muted-foreground` | `text.muted` | `#A7B3C2` | `#536273` | Metadata, timestamps, help text. |
| `accent` | `accent.fg` | `#9BBFDF` | `#285D85` | Links, current item, accent marks and tints. |
| `accent-foreground` | `accent.on` | `#101820` | `#FAFBFC` | Ink on solid accent fills. |
| `destructive` | `danger.fg` | `#E2A0A5` | `#A43F4A` | Destructive actions and error ink. |
| `destructive-foreground` | `danger.bg` | `#382A30` | `#F5E5E7` | Label on a solid destructive fill (the feedback pair, reversed). |
| `border` | `border.subtle` | `#3D4652` | `#D2D9E0` | Separators and panel edges (decorative). |
| `input` | `border.control` | `#8593A5` | `#6C7A89` | Outline that identifies a field or control. |
| `ring` | `focus.ring` | `#B0D2F0` | `#285D85` | Keyboard focus. |
| `font-sans` | `font.ui` | `"IBM Plex Sans", "Segoe UI", system-ui, sans-serif` | same | Interface and reading. |
| `font-mono` | `font.literal` | `"Cascadia Mono", "Cascadia Mono NF", "Cascadia Code", ui-monospace, Consolas, monospace` | same | Code, logs, IDs: one shared literal slot. |
<!-- build:tokens:end -->

## Contrast

Computed from the palette by `scripts/build.py` (WCAG 2.x). The build fails if any pair misses its target.

<!-- build:contrast:start -->
| Foreground | Background | Target | Slate | Daylight |
| :--- | :--- | ---: | ---: | ---: |
| `foreground` | `background` | 7:1 | 12.15:1 | 12.06:1 |
| `foreground` | `card` | 7:1 | 11.07:1 | 12.73:1 |
| `foreground` | `popover` | 7:1 | 9.70:1 | 13.19:1 |
| `foreground` | `muted` | 7:1 | 8.27:1 | 10.99:1 |
| `foreground` | `secondary` | 7:1 | 8.27:1 | 10.99:1 |
| `card-foreground` | `card` | 7:1 | 11.07:1 | 12.73:1 |
| `popover-foreground` | `popover` | 7:1 | 9.70:1 | 13.19:1 |
| `secondary-foreground` | `secondary` | 5:1 | 5.74:1 | 6.46:1 |
| `muted-foreground` | `background` | 5:1 | 7.96:1 | 5.71:1 |
| `muted-foreground` | `card` | 5:1 | 7.25:1 | 6.03:1 |
| `muted-foreground` | `popover` | 5:1 | 6.35:1 | 6.25:1 |
| `muted-foreground` | `muted` | 5:1 | 5.42:1 | 5.21:1 |
| `muted-foreground` | `secondary` | 5:1 | 5.42:1 | 5.21:1 |
| `primary-foreground` | `primary` | 4.5:1 | 9.30:1 | 6.77:1 |
| `accent-foreground` | `accent` | 4.5:1 | 9.30:1 | 6.77:1 |
| `destructive-foreground` | `destructive` | 4.5:1 | 6.36:1 | 5.09:1 |
| `accent` | `background` | 5:1 | 8.80:1 | 6.42:1 |
| `accent` | `card` | 5:1 | 8.02:1 | 6.77:1 |
| `accent` | `popover` | 5:1 | 7.02:1 | 7.01:1 |
| `accent` | `muted` | 5:1 | 5.99:1 | 5.85:1 |
| `accent` | `secondary` | 5:1 | 5.99:1 | 5.85:1 |
| `destructive` | `background` | 5:1 | 7.91:1 | 5.67:1 |
| `destructive` | `card` | 5:1 | 7.20:1 | 5.98:1 |
| `destructive` | `popover` | 5:1 | 6.31:1 | 6.20:1 |
| `primary` | `background` | 3:1 | 8.80:1 | 6.42:1 |
| `primary` | `card` | 3:1 | 8.02:1 | 6.77:1 |
| `primary` | `popover` | 3:1 | 7.02:1 | 7.01:1 |
| `ring` | `background` | 3:1 | 10.74:1 | 6.42:1 |
| `ring` | `card` | 3:1 | 9.79:1 | 6.77:1 |
| `ring` | `popover` | 3:1 | 8.57:1 | 7.01:1 |
| `input` | `background` | 3:1 | 5.41:1 | 4.02:1 |
| `input` | `card` | 3:1 | 4.93:1 | 4.24:1 |
| `input` | `popover` | 3:1 | 4.32:1 | 4.39:1 |
| `text.primary` | `bg.selected` | 7:1 | 7.95:1 | 10.68:1 |
| `text.muted` | `bg.selected` | 5:1 | 5.20:1 | 5.06:1 |
| `accent-foreground` | `accent-hover (host-derived)` | 4.5:1 | 10.61:1 | 8.74:1 |
| `accent-hover (host-derived)` | `background` | 3:1 | 10.04:1 | 8.28:1 |
<!-- build:contrast:end -->

Rendered check (Chromium 1440×1000, isolated Gateway, sampled computed colors over the effective background; indicative, not an audit):

| Sample | Slate | Daylight |
| :--- | ---: | ---: |
| Assistant body text | 12.02:1 | 12.09:1 |
| Sidebar item | 7.96:1 | 5.71:1 |
| Composer placeholder | 12.15:1 | 12.06:1 |
| Link | 10.18:1 | 8.80:1 |
| Inline code | 8.27:1 | 10.99:1 |
| Blockquote | 7.87:1 | 5.73:1 |

All sampled text met AA. Known limit: OpenClaw reuses `--input` as both outline and fill in some controls (for example the session-settings search), so a few control fills are the outline color; those spots were not individually measured.

## Compatibility

- Theme plugins are documented from OpenClaw **2026.9.6** (`docs/releases/2026.9.6.md`).
- The presentation fields (`mascot`, `brandIcon`, `workingIndicator`, `lobsterdex`, `workingPhrases`) are documented in `docs/plugins/manifest/surfaces.md` of the installed 2026.10.9; their first release is not stated, so `package.json` requires `>=2026.10.9`, the only version tested.
- Limits mirrored by the build: 4096 bytes per normalized definition (this one: 1579), 19 colors, 2 font slots, artwork of at most 4 elements.

## Regenerate

Python 3.10+, standard library only.

```sh
python3 scripts/build.py          # regenerate and validate
python3 scripts/build.py --check  # fail if generated files are stale
python3 scripts/build.py --sync   # refresh src/ from ../00-Flatcap, then build
python3 scripts/build.py --contrast
```

`src/theme.json` and `src/logo.svg` are vendored copies of the Flatcap core. Do not edit generated files by hand.

## License and support

Code, configuration and color data: MIT, see [LICENSE](LICENSE). The cap geometry derives from third-party artwork (Vexels, [terms](https://vexels.com/terms-and-conditions/)) and is **not** relicensed by the MIT grant.

If this is useful, you can support the work at <https://buymeacoffee.com/cheycron>.
