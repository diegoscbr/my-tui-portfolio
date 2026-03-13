# Hero Title & Transparent Background

**Date:** 2026-03-13
**Status:** Approved

## Summary

Two changes to the terminal portfolio TUI:

1. Add a hand-crafted "DIEGO ESCOBAR" hero title in heavy block lettering to the top of the Notice Board tab's right panel.
2. Make the Textual app background transparent so the visitor's terminal background shows through.

## 1. Hero Title

### Content

Two-line block art title using Heavy Block + Box Shadow style (full-block `█` characters with box-drawing `╔╗╚╝═║` edges, shadow row using `╚═╝` characters):

```
Line 1: DIEGO
Line 2: ESCOBAR
```

Each line includes a shadow row beneath it in muted gray. The exact block art is hand-crafted during implementation — this spec defines the style (Heavy Block + Box Shadow), not the pixel-level layout.

### File

`ascii_art/notice-board/hero.txt` — plain text, no ANSI escape codes. Color is applied at render time.

**Important:** The left-panel `AsciiPanel` loads art via `load_section_art()` which globs `*.txt` from the art directory. To avoid `hero.txt` being picked up by the left panel, store it at a distinct path: `ascii_art/notice-board/hero.txt` with the left-panel art at `ascii_art/notice-board/art.txt` (renamed from `placeholder.txt`). The `load_section_art()` function should load by explicit filename (`art.txt`) rather than globbing, or `hero.txt` should use a non-`.txt` extension (e.g., `.hero`). The implementer should choose the cleanest approach.

### Colors

- Block characters: Tokyo Night purple (`#bb9af7`)
- Shadow row: Muted gray (`#565f89`)

Applied via Rich `Text` styling at render time, not baked into the file.

### Width Constraint

The right panel is 55% of the terminal width. At the minimum supported width of 80 columns, that's ~44 columns. The hero art must fit within 44 columns. This constrains letter width and spacing.

### Layout

- Hero renders at the **top** of the right panel on the Notice Board tab only.
- 1 blank line gap below the hero, then existing Notice Board markdown content flows underneath.
- Other tabs (Sailing Instructions, R/C Logs, Contact, Experience) are unaffected.

### Architecture: ContentPanel Refactor

`ContentPanel` currently extends `Markdown` directly — it is not a container and cannot host child widgets. To support the hero + markdown layout, refactor `ContentPanel` from a `Markdown` subclass into a `Vertical` container that holds:

1. A `Static` widget for the hero title (visible only on Notice Board)
2. A `Markdown` widget for the section content

The `show_content()` method is updated to:
- Accept an optional `show_hero: bool` parameter (or determine it from the section ID)
- Toggle the hero widget's `display` property (`block` for Notice Board, `none` for other tabs)
- Update the inner `Markdown` widget's content

Scroll actions in `app.py` (`scroll_down()`/`scroll_up()`) should target the container rather than the `Markdown` widget directly.

### Widget Details

The hero `Static` widget:
- Loads `hero.txt` at app startup (not on every tab switch)
- Applies purple coloring to block characters and gray to shadow-row characters via Rich `Text` objects
- Toggled via `display` CSS property, not mount/unmount (avoids flicker, matches `#help-overlay` pattern)

## 2. Transparent Background

### TCSS Changes (exact selectors)

| Selector | Current | Target |
|---|---|---|
| `Screen` | `background: #1a1b26` | `background: transparent` |
| `Markdown` | `background: #1a1b26` | `background: transparent` |
| `#size-warning` | `background: #1a1b26` | `background: transparent` |
| `#footer-bar` | `background: #24283b` | `background: transparent` |
| `.keyhint-key` | `background: #3b4261` | Keep as-is (accent highlight, not a panel bg) |

### Keep opaque

- `#help-overlay` (`background: #24283b`) — must remain opaque so help text is readable over content.

### What stays the same

All text colors, borders, and accent colors remain unchanged:
- Purple headers (`#bb9af7`)
- Blue links (`#7dcfff`)
- Green tags (`#9ece6a`)
- Orange dates (`#e0af68`)
- Primary text (`#c0caf5`)

### Trade-off

SSH visitors see their own terminal background. The Tokyo Night text palette is optimized for dark backgrounds and may be hard to read on light terminals. This is acceptable — the target audience is terminal enthusiasts who typically use dark themes.

## Out of Scope

- Phase 4 markdown content pipeline (separate task)
- ASCII art style refinement for other tabs
- `DIEGO.BOATS` domain branding in the title (dropped in favor of full name)
