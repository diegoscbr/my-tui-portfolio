#!/usr/bin/env python3
"""
Build-time script: convert source images to ANSI text files.

Converts images in ascii_art/<section>/source.* or a specified frame
from frames/ into ANSI art for the TUI left panel.

Usage:
    python3 scripts/build_ascii.py                    # build all
    python3 scripts/build_ascii.py --section contact  # build one section
"""
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from ascii_magic import AsciiArt
    from ascii_magic.constants import Modes
except ImportError:
    print("ascii_magic not installed. Run: pip install ascii_magic pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
ART_ROOT = PROJECT_ROOT / "ascii_art"
FRAMES_DIR = PROJECT_ROOT / "frames"
COLUMNS = 50  # left panel is 45% of ~120-col terminal ≈ 54 usable chars

# Braille characters ordered by visual density (number of dots lit).
# Used instead of ASCII letters/symbols for a cleaner look in the TUI.
BRAILLE_DENSITY = (
    " ⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏"
    "⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟"
    "⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯"
    "⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿"
    "⡀⡁⡂⡃⡄⡅⡆⡇⡈⡉⡊⡋⡌⡍⡎⡏"
    "⡐⡑⡒⡓⡔⡕⡖⡗⡘⡙⡚⡛⡜⡝⡞⡟"
    "⡠⡡⡢⡣⡤⡥⡦⡧⡨⡩⡪⡫⡬⡭⡮⡯"
    "⡰⡱⡲⡳⡴⡵⡶⡷⡸⡹⡺⡻⡼⡽⡾⡿"
    "⢀⢁⢂⢃⢄⢅⢆⢇⢈⢉⢊⢋⢌⢍⢎⢏"
    "⢐⢑⢒⢓⢔⢕⢖⢗⢘⢙⢚⢛⢜⢝⢞⢟"
    "⢠⢡⢢⢣⢤⢥⢦⢧⢨⢩⢪⢫⢬⢭⢮⢯"
    "⢰⢱⢲⢳⢴⢵⢶⢷⢸⢹⢺⢻⢼⢽⢾⢿"
    "⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏"
    "⣐⣑⣒⣓⣔⣕⣖⣗⣘⣙⣚⣛⣜⣝⣞⣟"
    "⣠⣡⣢⣣⣤⣥⣦⣧⣨⣩⣪⣫⣬⣭⣮⣯"
    "⣰⣱⣲⣳⣴⣵⣶⣷⣸⣹⣺⣻⣼⣽⣾⣿"
)


def build_from_image(image_path: Path, output_path: Path) -> None:
    """Convert a single image to ANSI text using braille characters."""
    art = AsciiArt.from_image(str(image_path))
    ansi_text = art._img_to_art(
        columns=COLUMNS, mode=Modes.TERMINAL, char=" ░▒▓█", width_ratio=2.2
    )
    output_path.write_text(ansi_text)
    print(f"  Built {output_path.relative_to(ART_ROOT)}")


def build_notice_board() -> None:
    """Build notice-board art from a sailing video frame."""
    output_dir = ART_ROOT / "notice-board"
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = PROJECT_ROOT / "diego_fixed.png"
    if not frame.exists():
        print(f"  Skipping notice-board: {frame} not found")
        return

    build_from_image(frame, output_dir / "art.txt")


def build_hero() -> None:
    """Render DIEGO (Terrace) + ESCOBAR (RubiFont) and write hero.txt."""
    fonts_dir = PROJECT_ROOT / "scripts" / "fonts"
    output_path = ART_ROOT / "notice-board" / "hero.txt"

    diego = subprocess.check_output(
        ["figlet", "-f", str(fonts_dir / "Terrace.flf"), "DIEGO"],
        text=True,
    )
    escobar = subprocess.check_output(
        ["figlet", "-f", str(fonts_dir / "RubiFont.flf"), "ESCOBAR"],
        text=True,
    )
    output_path.write_text(diego.rstrip("\n") + "\n---ESCOBAR---\n" + escobar)
    print("  Built notice-board/hero.txt")


def build_section(section: str) -> None:
    """Build art for a single section from its source image."""
    section_dir = ART_ROOT / section
    section_dir.mkdir(parents=True, exist_ok=True)

    source_files = list(section_dir.glob("source.*"))
    if not source_files:
        print(f"  Skipping {section}: no source.* image found")
        return

    build_from_image(source_files[0], section_dir / "art.txt")


def main():
    parser = argparse.ArgumentParser(description="Build ASCII art assets")
    parser.add_argument("--section", help="Build only this section")
    args = parser.parse_args()

    print("Build ASCII art assets")
    print("=" * 40)
    print(f"Output: {ART_ROOT}")
    print()

    if args.section:
        if args.section == "notice-board":
            build_notice_board()
            build_hero()
        else:
            build_section(args.section)
    else:
        build_notice_board()
        build_hero()
        for section in ["sailing-instructions", "rc-logs", "contact", "experience"]:
            build_section(section)


if __name__ == "__main__":
    main()
