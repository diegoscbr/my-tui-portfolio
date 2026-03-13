"""Tests for the build_hero() function in scripts/build_ascii.py."""
import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import build_ascii
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_build_hero_creates_hero_txt(tmp_path, monkeypatch):
    """build_hero() should create hero.txt with ---ESCOBAR--- delimiter."""
    import build_ascii

    # Point ART_ROOT at tmp_path but keep PROJECT_ROOT at real project dir
    # so figlet can find scripts/fonts/
    notice_board_dir = tmp_path / "ascii_art" / "notice-board"
    notice_board_dir.mkdir(parents=True)
    monkeypatch.setattr(build_ascii, "ART_ROOT", tmp_path / "ascii_art")
    monkeypatch.setattr(build_ascii, "PROJECT_ROOT", Path(__file__).parent.parent)

    build_ascii.build_hero()

    hero_path = notice_board_dir / "hero.txt"
    assert hero_path.exists(), "hero.txt should be created"
    content = hero_path.read_text()
    assert "---ESCOBAR---" in content, "hero.txt must contain the delimiter"
    top, bottom = content.split("---ESCOBAR---\n", 1)
    assert len(top.strip()) > 0, "DIEGO block should not be empty"
    assert len(bottom.strip()) > 0, "ESCOBAR block should not be empty"
