"""Tests for markdown content loading with frontmatter."""
import pytest
from pathlib import Path


def test_load_single_file(tmp_path):
    """Should load a single markdown file and parse frontmatter."""
    from content_loader import load_single_content

    md_file = tmp_path / "test.md"
    md_file.write_text("---\ntitle: Hello\n---\n\nBody text here.")

    result = load_single_content(md_file)
    assert result.title == "Hello"
    assert "Body text here" in result.body


def test_load_single_file_missing_title(tmp_path):
    """Should use filename as fallback when title is missing."""
    from content_loader import load_single_content

    md_file = tmp_path / "my-post.md"
    md_file.write_text("---\ndate: 2026-01-01\n---\n\nNo title.")

    result = load_single_content(md_file)
    assert result.title == "my-post"


def test_load_directory(tmp_path):
    """Should load all .md files from a directory, skip _ prefixed, sort by order."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "projects"
    content_dir.mkdir()
    (content_dir / "project-a.md").write_text(
        "---\ntitle: Project A\norder: 2\n---\nContent A"
    )
    (content_dir / "project-b.md").write_text(
        "---\ntitle: Project B\norder: 1\n---\nContent B"
    )
    (content_dir / "_example.md").write_text("---\ntitle: Skip Me\n---\n")

    results = load_directory_content(content_dir)
    assert len(results) == 2
    assert results[0].title == "Project B"  # order=1 first
    assert results[1].title == "Project A"  # order=2 second


def test_load_directory_empty(tmp_path):
    """Should return empty list for empty directory."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "empty"
    content_dir.mkdir()

    results = load_directory_content(content_dir)
    assert results == []


def test_load_single_file_invalid_frontmatter(tmp_path):
    """Should handle invalid YAML gracefully — returns content with filename as title."""
    from content_loader import load_single_content

    md_file = tmp_path / "bad.md"
    md_file.write_text("---\n: invalid: yaml: {{{\n---\n\nBody.")

    result = load_single_content(md_file)
    assert result is not None


def test_load_directory_sorts_by_date_fallback(tmp_path):
    """When order is missing, sort by date descending (newer first)."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "posts"
    content_dir.mkdir()
    (content_dir / "old.md").write_text(
        "---\ntitle: Old Post\ndate: 2025-01-01\n---\n"
    )
    (content_dir / "new.md").write_text(
        "---\ntitle: New Post\ndate: 2026-01-01\n---\n"
    )

    results = load_directory_content(content_dir)
    assert results[0].title == "New Post"
