"""Tests for AsciiPanel widget — art loading and swapping."""
import pytest
from pathlib import Path


def test_load_static_art(tmp_path):
    """Should load a .txt file as ANSI art string."""
    from widgets.ascii_panel import load_section_art

    art_dir = tmp_path / "test-section"
    art_dir.mkdir()
    (art_dir / "placeholder.txt").write_text("  test art  ")

    result = load_section_art(art_dir)
    assert result == "  test art  "


def test_load_static_art_missing_dir(tmp_path):
    """Should return fallback text for missing art directory."""
    from widgets.ascii_panel import load_section_art

    result = load_section_art(tmp_path / "nonexistent")
    assert "no art" in result.lower()
