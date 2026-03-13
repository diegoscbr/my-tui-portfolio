# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An SSH-accessible terminal portfolio at `diego.boats` with a sailing regatta theme. Visitors `ssh diego.boats` and get a split-panel TUI: ASCII art on the left, bio/content sections on the right, tab navigation along the bottom. Tokyo Night Dark color palette throughout.

**Architecture**: Single Python process — `asyncssh` for the SSH server + a custom `SSHDriver` (subclasses Textual's `LinuxDriver`) for per-session I/O isolation. Textual handles layout, styling (TCSS), and widgets. Content will be loaded from markdown files with YAML frontmatter. ASCII art is pre-rendered at build time via `ascii_magic`.

**Tech Stack**: Python 3.14, Textual, asyncssh, python-frontmatter, ascii_magic, Pillow, pytest

## Environment Setup

Python 3.14 virtualenv (`.venv/`). The system `python` command may not exist — always use `python3`:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

System dependency for video processing: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).

## Running

```bash
# Run the Textual app locally (no SSH, direct terminal)
python3 -m textual run app:PortfolioApp

# Run the SSH server (listens on port 8022 by default)
python3 server.py

# Run tests
pytest

# Build ASCII art from images
python3 scripts/build_ascii.py

# Legacy: standalone ASCII video player (reference implementation)
python3 player.py
```

## Implementation Status

### Done (Phases 1-3) — All merged to main

**Phase 1 — SSH Server + Bare Layout (Tasks 1-6)**
- `pyproject.toml` / `requirements.txt` — project config and pinned deps
- `ssh_driver.py` — custom Textual driver routing I/O through asyncssh channels
- `server.py` — asyncssh SSH server with session limits and rate limiting
- `theme.tcss` — full Tokyo Night Dark theme (Textual CSS)
- `app.py` — main app: split-panel layout, key bindings, navigation state machine, size warning overlay
- `config.py` — section registry mapping IDs → content paths, art paths, labels
- `widgets/ascii_panel.py` — left panel displaying ANSI art via `Text.from_ansi()`
- `widgets/tab_bar.py` — bottom navigation bar with active tab highlight
- `widgets/content_panel.py` — right panel wrapping Textual `Markdown` widget

**Phase 2 — Navigation + Tab Switching (Tasks 7-8)**
- Tab switching with number keys (1-5), vim keys (h/l), arrow keys
- Help overlay toggled with `?`

**Phase 3 — ASCII Art (Tasks 8.5-9)**
- `scripts/build_ascii.py` — renders images via ascii_magic with configurable `char` param
- Block element charset `" ░▒▓█"` with `diego_fixed.png` — retro pixel style
- `ascii_art/<section>/placeholder.txt` — per-section placeholder art files
- `AsciiPanel` converts ANSI → Rich `Text.from_ansi()` for Textual containment

**Tests**: 18 passing across `tests/test_app.py`, `test_tab_bar.py`, `test_ascii_panel.py`, `test_ssh_driver.py`, `test_server.py`

### Spec'd But Not Implemented

**Hero Title + Transparent Background**
- Spec: `docs/superpowers/specs/2026-03-13-hero-title-transparent-bg-design.md`
- "DIEGO ESCOBAR" two-line heavy block lettering at top of Notice Board right panel
- `ascii_art/notice-board/hero.txt` — plain text, colored at render time (purple `#bb9af7`, gray shadow `#565f89`)
- Requires `ContentPanel` refactor: from `Markdown` subclass → `Vertical` container holding `Static` (hero) + `Markdown`
- Make app backgrounds transparent (Screen, Markdown, footer, size-warning); keep help-overlay opaque
- Brainstorm artifacts: `.superpowers/brainstorm/43458-1773413199/lettering-styles.html`

### Not Started

**Phase 4 — Markdown Content Pipeline (Tasks 11+)**
- `content_loader.py` — parse markdown files with YAML frontmatter
- `content/` directory — markdown files per section (notice-board.md, contact.md, sailing-instructions/*.md, rc-logs/*.md, experience/*.md)
- `content/TEMPLATE.md` — schema reference and examples
- Wire content loader into `app.py` and `ContentPanel`

**Phase 5 — Video Animation**
- Looping ASCII sailing video on Notice Board left panel (328 frames in `frames/`)
- Integrate the standalone `player.py` approach into `AsciiPanel`

**Phase 6 — Deployment**
- Hetzner VPS (~€3.29/mo), admin SSH on port 2222
- `scripts/provision.sh` — VPS setup script
- systemd service, host key management, firewall

## Key Design Docs

- **Design spec**: `docs/superpowers/specs/2026-03-12-terminal-portfolio-design.md`
- **Implementation plan**: `docs/superpowers/plans/2026-03-12-terminal-portfolio-plan.md` (7 phases, task-level detail with checkboxes)
- **Hero title spec**: `docs/superpowers/specs/2026-03-13-hero-title-transparent-bg-design.md`
- **ASCII player design**: `docs/plans/2026-03-09-ascii-player-design.md`
- **ASCII player plan**: `docs/plans/2026-03-09-ascii-player-plan.md`

## File Structure

```
app.py                  # Main Textual app — layout, navigation, key bindings
server.py               # asyncssh SSH server — session management, SSHDriver wiring
ssh_driver.py           # Custom Textual driver — routes I/O through SSH channel
theme.tcss              # Tokyo Night Dark theme (all Textual CSS styling)
config.py               # Section registry — maps section IDs to paths and labels
widgets/
  ascii_panel.py        # Left panel — ANSI art display, load_section_art()
  tab_bar.py            # Bottom nav bar — tab rendering with active highlight
  content_panel.py      # Right panel — Markdown widget wrapper
scripts/
  build_ascii.py        # Build-time: image → ANSI text via ascii_magic
ascii_art/
  notice-board/         # Art files for Notice Board section
  sailing-instructions/ # Art files for Sailing Instructions section
  rc-logs/              # Art files for R/C Logs section
  contact/              # Art files for Contact section
  experience/           # Art files for Experience section
tests/
  test_app.py           # App navigation, key bindings, state machine
  test_tab_bar.py       # TabBar rendering
  test_ascii_panel.py   # AsciiPanel art loading and swapping
  test_ssh_driver.py    # SSHDriver spike validation
  test_server.py        # Session limits, rate limiting
  conftest.py           # Shared fixtures
frames/                 # 328 sequential JPEGs from sailing.MP4
docs/                   # Design specs and implementation plans
```

## Known Gotchas

- **ANSI in Textual**: Raw ANSI escape strings break Textual's layout engine. Always convert to Rich `Text` objects via `Text.from_ansi()` before passing to widgets.
- **Python command**: Use `python3`, not `python` — the system may not have `python` aliased.
- **ascii_magic internals**: `player.py` uses the internal `_img_to_art()` method for raw string output. This is fragile across ascii_magic versions.
- **SSH driver risk**: `SSHDriver` subclasses Textual's internal `LinuxDriver` (unstable API). Isolated in its own file so it's easy to update if Textual changes.

## ASCII Art Style Notes

The current rendering uses block elements `" ░▒▓█"` which gives a retro pixel/Mario aesthetic. Other options explored:
- `"▄▀█"` half-blocks — 2x vertical resolution, not yet tested in-app
- `char="·"` dot-only — spacing felt off
- Braille density — char spacing was problematic
- Lower COLUMNS = chunkier pixels; `enhance_image=True` = more vibrant colors

## 5 Sailing-Themed Sections

| # | ID | Label | Content Type |
|---|---|---|---|
| 1 | notice-board | Notice Board | Single file (bio) |
| 2 | sailing-instructions | Sailing Instructions | Directory (projects/posts) |
| 3 | rc-logs | R/C Logs | Directory (blog entries) |
| 4 | contact | Contact | Single file (links/socials) |
| 5 | experience | Experience | Directory (resume items) |

## Legacy Files (pre-TUI experiments)

- `converter.py` — one-off: converts `sailing.jpg` → terminal + HTML
- `profile.py` — image processing experiments with Pillow/ascii_magic
- `player.py` — standalone TUI ASCII video player (reference for Phase 5)
- `sailing.MP4` — source video for frame extraction
- `sailing.jpg`, `diego_fixed.png`, `diego_mog.jpeg`, etc. — test images
