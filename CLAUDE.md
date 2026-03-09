# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An SSH-accessible terminal portfolio at `diego.boats` with a sailing regatta theme. Visitors `ssh diego.boats` and get a split-panel TUI: looping ASCII sailing video on the left, bio/content sections on the right, tab navigation along the bottom.

**Architecture**: Hetzner VPS → Wish (Go SSH server) → spawns per-connection Node.js Ink TUI process. Python is build-time only (pre-renders video frames to ANSI text).

The project is currently in **pre-implementation** — only the Python frame tools, design doc, and implementation plan exist. The Node.js/Ink TUI and SSH server have not been built yet.

## Environment Setup

Python 3.14 virtualenv (`.venv/`):

```bash
source .venv/bin/activate
pip install ascii_magic pillow
```

## Running

```bash
# Static image → ASCII (outputs to terminal + ascii_img.html)
python converter.py

# Play 328-frame ASCII video in terminal (24 FPS, auto-fits terminal)
python player.py              # auto-detect columns
python player.py -c 120      # force 120 columns
```

`player.py` pre-converts all frames on startup (takes a few seconds), then loops playback. Controls: `↑/k` scroll up, `↓/j` scroll down, `q/ESC` quit.

## Key Dependencies

- `ascii_magic` — converts images to ASCII/ANSI art via `AsciiArt.from_image()`. Uses `Modes.TERMINAL` for ANSI color output. Internal method `_img_to_art()` used directly in `player.py` for raw string output.
- `Pillow` — image processing, required by ascii_magic.

## Planned Architecture (from docs/plans/)

The implementation plan (`docs/plans/2026-03-08-terminal-portfolio-plan.md`) has 11 tasks:

1. **prerender.py** — batch-convert `frames/*.jpg` → `frames.bin` (serialized ANSI strings)
2. **Node.js project** — Ink 5, ink-big-text, ssh2 dependencies
3. **SSH server** — Wish-based, auto host key management, port 22
4. **Layout component** — split-panel Ink TUI
5. **VideoPlayer** — loads `frames.bin`, loops ANSI frames
6. **TabBar** — section navigation (←/→, enter, q)
7. **Section components** — NoticeBoard, SailingInstructions, RCLogs, Contact, Experience
8. **App.jsx** — wire everything together
9. **VPS provisioning** — Hetzner Ubuntu setup script
10. **DNS** — `diego.boats` A record via Vercel DNS
11. **GitHub repo** — push and configure

## File Roles

- `converter.py` — simple one-off: converts `sailing.jpg` → terminal + HTML output
- `player.py` — full TUI ASCII video player with scrolling, raw terminal mode, ANSI escape codes
- `frames/` — 328 sequential JPEGs extracted from `sailing.MP4`
- `docs/plans/` — design doc and implementation plan
