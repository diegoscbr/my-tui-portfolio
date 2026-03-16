#!/usr/bin/env python3
import sys
import time
import shutil
import select
import termios
import tty
import argparse
from pathlib import Path
from PIL import Image
from ascii_magic import AsciiArt
from ascii_magic.constants import Modes

FRAMES_DIR = Path(__file__).parent / "frames"
FPS = 24

# ANSI escape codes
CLEAR      = "\033[2J"
HOME       = "\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def compute_columns(sample_path, term_cols, term_rows, width_ratio=2.2):
    """Return the column count that makes the ASCII frame fit the terminal."""
    with Image.open(sample_path) as img:
        img_w, img_h = img.size
    aspect = img_w / img_h
    max_cols_by_height = int((term_rows - 1) * width_ratio * aspect)
    return min(term_cols, max_cols_by_height)


def load_frames(columns):
    frame_paths = sorted(FRAMES_DIR.glob("frame_*.jpg"))
    if not frame_paths:
        print(f"No frames found in {FRAMES_DIR}")
        sys.exit(1)

    frames = []
    total = len(frame_paths)
    for i, path in enumerate(frame_paths):
        print(f"\rConverting frames: {i + 1}/{total}", end="", flush=True)
        art = AsciiArt.from_image(str(path))
        frames.append(art._img_to_art(columns=columns, mode=Modes.TERMINAL, char=" ░▒▓█", width_ratio=2.2))

    print(f"\nDone — {total} frames ready.")
    return frames


def read_key(timeout=0.0):
    """Non-blocking key read in raw mode. Returns a string or None."""
    if not select.select([sys.stdin], [], [], timeout)[0]:
        return None
    ch = sys.stdin.read(1)
    # Escape sequence (arrow keys)
    if ch == "\033":
        if select.select([sys.stdin], [], [], 0.05)[0]:
            ch += sys.stdin.read(1)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch += sys.stdin.read(1)
    return ch


def play(frames, fps):
    delay = 1.0 / fps
    frame_idx = 0
    scroll_y = 0

    frame_lines = [f.split("\n") for f in frames]
    max_height = max(len(lines) for lines in frame_lines)

    term = shutil.get_terminal_size()
    term_rows = term.lines

    sys.stdout.write(HIDE_CURSOR + CLEAR)
    sys.stdout.flush()

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            t0 = time.perf_counter()

            # Refresh terminal size each frame
            term = shutil.get_terminal_size()
            term_rows = term.lines

            # Handle input
            key = read_key(0)
            if key in ("q", "\x1b", "\x03"):   # q / ESC / Ctrl-C
                break
            elif key in ("\033[A", "k"):        # up arrow / k
                scroll_y = max(0, scroll_y - 1)
            elif key in ("\033[B", "j"):        # down arrow / j
                scroll_y = min(max(0, max_height - term_rows), scroll_y + 1)

            # Build and write the visible slice of the current frame
            lines = frame_lines[frame_idx]
            visible = lines[scroll_y: scroll_y + term_rows]
            sys.stdout.write(HOME + "\r\n".join(visible))
            sys.stdout.flush()

            frame_idx = (frame_idx + 1) % len(frames)

            elapsed = time.perf_counter() - t0
            remaining = delay - elapsed
            if remaining > 0:
                time.sleep(remaining)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write(SHOW_CURSOR + CLEAR + HOME)
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="ASCII video player")
    parser.add_argument(
        "--columns", "-c",
        type=int,
        default=None,
        help="ASCII resolution in columns (default: auto-fit terminal)",
    )
    args = parser.parse_args()

    term = shutil.get_terminal_size()
    sample = sorted(FRAMES_DIR.glob("frame_*.jpg"))[0]

    columns = args.columns if args.columns else compute_columns(sample, term.columns, term.lines)

    print(f"Terminal: {term.columns}x{term.lines} — rendering at {columns} columns")
    print("Pre-converting all frames to ASCII (one-time cost)...")
    frames = load_frames(columns)
    print("Starting playback... (↑↓ or j/k to scroll · q/ESC to quit)")
    time.sleep(1)
    play(frames, FPS)


if __name__ == "__main__":
    main()
