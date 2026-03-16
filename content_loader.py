"""
Loads markdown content with YAML frontmatter.

Handles single files (notice-board.md, contact.md) and directories
(sailing-instructions/, experience/) with list/detail navigation.

Error handling:
- Invalid YAML: logs warning, uses filename as title, includes raw text
- Missing title: uses filename stem as fallback
- Missing directory: returns empty list
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import frontmatter

logger = logging.getLogger("diego.boats")


@dataclass(frozen=True)
class ContentItem:
    title: str
    description: str = ""
    body: str = ""
    tags: tuple = ()
    url: str = ""
    date: date | None = None
    order: int = 999


def load_single_content(file_path: Path) -> ContentItem:
    """Load a single markdown file with frontmatter."""
    try:
        post = frontmatter.load(str(file_path))
        meta = post.metadata
    except Exception:
        logger.warning("Invalid frontmatter in %s, using fallback", file_path)
        return ContentItem(
            title=file_path.stem,
            body=file_path.read_text(),
        )

    return ContentItem(
        title=meta.get("title", file_path.stem),
        description=meta.get("description", ""),
        body=post.content,
        tags=tuple(meta.get("tags", [])),
        url=meta.get("url", ""),
        date=meta.get("date"),
        order=meta.get("order", 999),
    )


def load_directory_content(dir_path: Path) -> list[ContentItem]:
    """Load all .md files from a directory, skip _ prefixed, sort by order/date."""
    if not dir_path.exists():
        return []

    items = []
    for md_file in sorted(dir_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        items.append(load_single_content(md_file))

    return sorted(
        items,
        key=lambda item: (
            item.order,
            -(item.date.toordinal() if item.date else 0),
        ),
    )
