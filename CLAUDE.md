# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An SSH-accessible terminal portfolio at `diego.boats`. Visitors SSH in and get a full sailing-themed TUI with a looping ASCII video and five navigable sections.

Architecture: `ssh2` Node.js server → renders an Ink (React for CLIs) TUI per connection. Python pre-renders 328 sailing video frames to ANSI text once at build time; the TUI loads them from disk instantly.

## Two Runtimes

**Build-time (Python)** — runs once on the machine with ascii_magic installed:
```bash
source .venv/bin/activate
python prerender.py         # converts frames/*.jpg → frames.bin
python player.py            # standalone ASCII player (reference/dev tool)
python converter.py         # single-image converter (reference only)
```

**Runtime (Node.js)** — runs on the VPS, never needs Python:
```bash
npm start                   # tsx src/server.js (SSH server on port 2222 locally, 22 on VPS)
npm test                    # jest
npm test -- tests/Foo.test.jsx  # single test file
```

## Project Structure

```
prerender.py              # build-time: frames/*.jpg → frames.bin (JSON)
frames.bin                # generated, gitignored — load on VPS, re-run if video changes
frames/                   # 328 JPEG frames from sailing.MP4
player.py                 # standalone terminal player (dev reference, not used at runtime)
converter.py              # single-image ASCII converter (reference only)
src/
  server.js               # ssh2 SSH server entry point
  App.jsx                 # root Ink component; handles keyboard input and section routing
  frames.js               # reads frames.bin and exports { frames, fps, columns }
  sections.js             # SECTIONS constant shared across TabBar and App
  components/
    Layout.jsx            # split-panel: video left (45%), divider, content right (55%), footer
    VideoPlayer.jsx       # loops ANSI frames from frames.js at 24fps
    TabBar.jsx            # bottom bar: section tabs + key hint line
  sections/
    NoticeBoard.jsx       # home: bio text (video is in the left panel, not here)
    SailingInstructions.jsx
    RCLogs.jsx
    Contact.jsx
    Experience.jsx
tests/
  Layout.test.jsx
  VideoPlayer.test.jsx
  TabBar.test.jsx
docs/plans/               # design doc and implementation plan
provision.sh              # VPS setup script (Hetzner Ubuntu 22.04)
.ssh/                     # gitignored — host_key + host_key.pub (generate once per machine)
```

## TUI Layout

```
+---------------------------+-----------------------------+
|                           |                             |
|  sailing ASCII video      |  active section content     |
|  (looping, 45% width)     |  (55% width)                |
|                           |                             |
+------------------------------------------------------------------+
|  Notice Board   Sailing Instructions   R/C Logs   Contact   Experience  |
|  [<- -> to navigate  enter to open  q to quit]                          |
+-------------------------------------------------------------------------+
```

## Key Architectural Notes

- **frames.bin** is JSON: `{ fps: 24, columns: 80, frames: ["<ansi string>", ...] }`. The `columns` value is the left panel width and must stay consistent between `prerender.py` and `VideoPlayer.jsx`.
- Each SSH connection gets its own isolated Ink render context — no shared state between visitors.
- SSH host keys live in `.ssh/host_key` (gitignored). Generate once per machine: `ssh-keygen -t ed25519 -f .ssh/host_key -N ""`
- `src/App.jsx` uses `useInput` for keyboard handling; `q`/ESC exits, `←`/`→` navigate sections.
- Tests use `@inkjs/testing` and mock `src/frames.js` to avoid needing `frames.bin` at test time.

## Environment Setup

Python (build machine only):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ascii_magic pillow
```

Node.js (runtime + dev):
```bash
npm install
```
