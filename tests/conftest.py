"""Shared test fixtures for the portfolio test suite."""
import pytest
from pathlib import Path


@pytest.fixture
def content_dir(tmp_path):
    """Create a temporary content directory with sample files."""
    content = tmp_path / "content"
    content.mkdir()
    (content / "notice-board.md").write_text("---\ntitle: Test Bio\n---\nHello")
    (content / "contact.md").write_text("---\ntitle: Contact\n---\nemail@test.com")

    projects = content / "sailing-instructions"
    projects.mkdir()
    (projects / "_example.md").write_text("---\ntitle: Skip\n---\n")
    (projects / "proj.md").write_text("---\ntitle: Proj\norder: 1\n---\nDetails")

    return content


@pytest.fixture
def art_dir(tmp_path):
    """Create a temporary ascii_art directory with art.txt files per section."""
    art = tmp_path / "ascii_art"
    for section in [
        "notice-board",
        "sailing-instructions",
        "rc-logs",
        "contact",
        "experience",
    ]:
        d = art / section
        d.mkdir(parents=True)
        (d / "art.txt").write_text(f"  ~ {section} art ~  ")
    return art
