# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python project for converting images and video frames to ASCII art. The `frames/` directory contains 328 JPEG frames extracted from `sailing.MP4`. The current script (`converter.py`) converts a PNG profile image to ASCII art using the `ascii_magic` library.

## Environment Setup

Python 3.12 with a local virtualenv:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies (if setting up fresh)
pip install ascii_magic pillow
```

## Running the Script

```bash
source .venv/bin/activate
python converter.py
```

## Key Files

- `converter.py` — main script; converts `diego_profile.png` to ASCII art, outputs to terminal and `profile_out.png`
- `frames/frame_XXXX.jpg` — 328 sequential video frames (extracted from `sailing.MP4`) for potential ASCII animation use
- `sailing.MP4` — source video for the frames
- `diego_profile.png` — source profile image (~40MB PNG)

## Architecture Notes

The project is early-stage with a single script. The natural next step is processing the `frames/` directory sequentially to produce ASCII animations. The `ascii_magic` library wraps Pillow and accepts file paths, PIL Image objects, or URLs via `AsciiArt.from_image()`.
