#!/usr/bin/env python3
"""
Build-time script. Run once on the machine with ascii_magic installed.
Outputs frames.bin (JSON) which the Node TUI reads at runtime.
"""
import json
import sys
from pathlib import Path
from ascii_magic import AsciiArt
from ascii_magic.constants import Modes

FRAMES_DIR = Path(__file__).parent / "frames"
OUTPUT = Path(__file__).parent / "frames.bin"
COLUMNS = 80   # left panel width; ~half a 160-col terminal


def main():
    frame_paths = sorted(FRAMES_DIR.glob("frame_*.jpg"))
    if not frame_paths:
        print(f"No frames found in {FRAMES_DIR}", file=sys.stderr)
        sys.exit(1)

    total = len(frame_paths)
    frames = []
    for i, path in enumerate(frame_paths):
        print(f"\rPre-rendering: {i + 1}/{total}", end="", flush=True)
        art = AsciiArt.from_image(str(path))
        ansi_text = art._img_to_art(columns=COLUMNS, mode=Modes.TERMINAL)
        frames.append(ansi_text)

    OUTPUT.write_text(json.dumps({"fps": 24, "columns": COLUMNS, "frames": frames}))
    print(f"\nWrote {total} frames to {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
