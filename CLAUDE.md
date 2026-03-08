# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An SSH-accessible terminal portfolio at diego.boats with a sailing-themed interactive TUI. Features a color ASCII video loop of sailing footage alongside navigable content sections, built with Node.js (Ink/React for CLIs) and an ssh2 server.

## Environment Setup

### Node.js (main runtime)

```bash
npm install
```

### Python (build-time pre-rendering only)

```bash
source .venv/bin/activate
pip install ascii_magic pillow
```

### Pre-render frames (one-time, generates frames.bin)

```bash
source .venv/bin/activate
python prerender.py
```

## Running

### Start SSH server locally

```bash
# First, generate a host key (one-time):
mkdir -p .ssh
ssh-keygen -t ed25519 -f .ssh/host_key -N ""

# Start the server:
node src/server.js
```

### Run tests

```bash
npm test
```

## Key Files

- `src/server.js` — ssh2 server entry point; renders Ink TUI per SSH connection
- `src/App.jsx` — root Ink component with section navigation
- `src/components/Layout.jsx` — split-panel layout (video left, content right)
- `src/components/VideoPlayer.jsx` — ANSI frame loop from pre-rendered data
- `src/components/TabBar.jsx` — bottom navigation bar
- `src/sections/*.jsx` — content for each tab (NoticeBoard, SailingInstructions, RCLogs, Contact, Experience)
- `src/sections.js` — section definitions shared across components
- `src/frames.js` — loads pre-rendered frames from frames.bin
- `prerender.py` — build-time script converting frames/*.jpg to frames.bin (ANSI text)
- `provision.sh` — VPS provisioning script for deployment
- `converter.py` — legacy script for single-image ASCII conversion

## Architecture

- **SSH layer**: Node.js `ssh2` server accepts all connections (public portfolio), spawns an Ink render context per session
- **TUI**: Ink 5 (React for CLIs) with split-panel layout — ASCII video left, content sections right, tab bar bottom
- **Video**: 328 JPEG frames pre-rendered to ANSI color text at build time (`prerender.py` → `frames.bin`), loaded and looped at runtime
- **Navigation**: Arrow keys switch sections, `q` to quit
