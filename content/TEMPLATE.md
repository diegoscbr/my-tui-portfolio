# Content Template Reference

This file documents the frontmatter schema for each section type.
The content loader reads .md files with YAML frontmatter.

## Rules
- Files starting with `_` are ignored (use for templates/examples)
- `title` is required (filename stem used as fallback if missing)
- `order` controls sort order (lower = first, default 999)
- `date` is used as secondary sort (newer first) when order is equal

## Single-file sections (notice-board.md, contact.md)

```yaml
---
title: "Section Title"
---
```

Markdown content here...

## Directory sections (sailing-instructions/, rc-logs/, experience/)

```yaml
---
title: "Item Title"
description: "Short description shown in list view"
tags: ["Tag1", "Tag2"]
url: "https://example.com"
date: 2026-01-15
order: 1
---
```

Full markdown content shown in detail view...
