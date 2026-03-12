# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An SSH-accessible terminal portfolio at `diego.boats` with a sailing regatta theme. Visitors `ssh diego.boats` and get a split-panel TUI: looping ASCII sailing video on the left, bio/content sections on the right, tab navigation along the bottom.

**Architecture**: Hetzner VPS → Wish (Go SSH server) → spawns per-connection Node.js Ink TUI process. Python is build-time only (pre-renders video frames to ANSI text).

The project is in **pre-implementation** — only Python frame tools, design docs, and implementation plans exist. The Node.js/Ink TUI and SSH server have not been built yet.

## Environment Setup

Python 3.14 virtualenv (`.venv/`). The system `python` command may not exist — use `python3`:

```bash
source .venv/bin/activate
pip install ascii_magic pillow
```

System dependency for video processing: `brew install ffmpeg`

## Running

```bash
# Static image → ASCII (outputs to terminal + ascii_img.html)
python3 converter.py

# Play 328-frame ASCII video in terminal (24 FPS, auto-fits terminal)
python3 player.py              # auto-detect columns
python3 player.py -c 120      # force 120 columns
```

`player.py` pre-converts all frames on startup (takes a few seconds), then loops playback. Controls: `↑/k` scroll up, `↓/j` scroll down, `q/ESC` quit.

## Key Dependencies

- `ascii_magic` — converts images to ASCII/ANSI art via `AsciiArt.from_image()`. Uses `Modes.TERMINAL` for 256-color ANSI output. Internal method `_img_to_art()` used in `player.py` for raw string output.
- `Pillow` — image processing, required by ascii_magic.
- `ffmpeg` — system dependency for MP4→JPEG frame extraction (used by the ascii-player build pipeline).

## Active Development: ascii-player

The current focus is building a general-purpose CLI tool (`ascii_player/` package) that converts any MP4 to multi-resolution ASCII art and plays it in the terminal. Design and plan docs:

- **Design**: `docs/plans/2026-03-09-ascii-player-design.md`
- **Plan**: `docs/plans/2026-03-09-ascii-player-plan.md` (12 tasks, TDD)

Key concepts:
- CLI subcommands: `python3 -m ascii_player build video.mp4` and `python3 -m ascii_player run video.mp4`
- Multi-resolution cache at `~/.cache/ascii-player/<sha256>/` with resolutions [60, 80, 120, 160, 200, 250]
- Pickle format with pre-split lines for fast deserialization
- SIGWINCH-based terminal resize detection, snaps to best cached resolution
- 5 modules: `__main__.py` (CLI), `build.py` (ffmpeg + pre-render), `cache.py` (hash/lookup), `player.py` (playback), `renderer.py` (ascii_magic wrapper)

## Planned Terminal Portfolio (future)

The older plan (`docs/plans/2026-03-08-terminal-portfolio-plan.md`) covers the full TUI portfolio: SSH server, Ink layout, tab navigation, content sections. This builds on top of the ascii-player once it's complete.

## File Roles

- `converter.py` — one-off: converts `sailing.jpg` → terminal + HTML output
- `profile.py` — one-off: image processing experiments with Pillow/ascii_magic
- `player.py` — TUI ASCII video player (reference implementation for ascii-player package)
- `frames/` — 328 sequential JPEGs extracted from `sailing.MP4`
- `sailing.MP4` — source video for frame extraction
- `docs/plans/` — design docs and implementation plans
