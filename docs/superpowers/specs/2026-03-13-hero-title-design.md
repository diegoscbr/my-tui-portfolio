# Hero Title Design

**Date:** 2026-03-13
**Status:** Approved

## Summary

Add a two-part "DIEGO ESCOBAR" hero title to the top of the Notice Board tab's right panel. The hero is pre-rendered ASCII art using two figlet fonts, colored at runtime via Rich `Text` styling.

## Hero Art

### Fonts

| Word | Font | Color |
|------|------|-------|
| DIEGO | Terrace | Tokyo Night purple `#bb9af7` |
| ESCOBAR | RubiFont | Tokyo Night gray `#565f89` |

Terrace uses Unicode shade characters (`░`, `█`). RubiFont uses Unicode quarter-block characters (`▗`, `▄`, `▖`, `▌`, `▐`, `▀`). Both render correctly in any UTF-8 terminal. Terrace renders DIEGO at ~54 chars wide (fits at 100+ col terminals); RubiFont renders ESCOBAR at ~35 chars wide (fits at 80 col minimum).

### File

`ascii_art/notice-board/hero.txt` — plain text, no ANSI escape codes. Color applied at render time by `ContentPanel` via Rich `Text` styling. `hero.txt` is committed to the repository as a build artifact.

The file format uses a delimiter line to mark the boundary between fonts:

```
<terrace output lines>
---ESCOBAR---
<rubifont output lines>
```

The delimiter is stripped at render time and never displayed. `load_section_art()` loads `art.txt` explicitly after this change — `hero.txt` is never picked up by the left panel. This explicit-load behavior permanently insulates the left panel from any future `.txt` files in the notice-board art directory.

### Font Files

Both `.flf` font files are committed to `scripts/fonts/`:
- `scripts/fonts/Terrace.flf` — source: `https://raw.githubusercontent.com/patorjk/figlet.js/main/fonts/Terrace.flf`
- `scripts/fonts/RubiFont.flf` — source: `https://raw.githubusercontent.com/patorjk/figlet.js/main/fonts/RubiFont.flf`

### Build

`scripts/build_ascii.py` gains `build_hero()` and a top-level `import subprocess`. The function uses the `figlet` CLI:

```python
def build_hero() -> None:
    """Render DIEGO (Terrace) + ESCOBAR (RubiFont) and write hero.txt."""
    fonts_dir = PROJECT_ROOT / "scripts" / "fonts"
    output_path = ART_ROOT / "notice-board" / "hero.txt"
    diego = subprocess.check_output(
        ["figlet", "-f", str(fonts_dir / "Terrace.flf"), "DIEGO"], text=True,
    )
    escobar = subprocess.check_output(
        ["figlet", "-f", str(fonts_dir / "RubiFont.flf"), "ESCOBAR"], text=True,
    )
    output_path.write_text(diego + "---ESCOBAR---\n" + escobar)
    print("  Built notice-board/hero.txt")
```

**Wiring into `main()`:** `build_hero()` runs as part of the default build alongside image builds. With `--section notice-board`, both `build_notice_board()` (image art) and `build_hero()` run. Updated dispatch:

```python
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
```

**System dependency:** `figlet` must be installed on the build machine (`brew install figlet` on macOS, `apt install figlet` on Linux). Add this to the "Environment Setup" section of `CLAUDE.md` alongside the existing `ffmpeg` note. `figlet` is not required at runtime on the SSH server.

**`pyproject.toml`** gains a `build` extras group (also fixes the pre-existing omission of `ascii_magic` and `pillow`):

```toml
[project.optional-dependencies]
build = [
    "ascii_magic>=2.3.0",
    "pillow>=10.0.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "textual-dev>=1.0.0",
]
```

### Coloring at Runtime

`ContentPanel.on_mount` loads `hero.txt`, splits on the delimiter, and builds a Rich `Text` object. If `hero.txt` is missing (e.g., fresh clone before running the build script), log a warning and leave `#hero-title` empty rather than crashing:

```python
HERO_PATH = Path(__file__).parent.parent / "ascii_art" / "notice-board" / "hero.txt"

# inside ContentPanel:
def on_mount(self) -> None:
    try:
        hero_text = HERO_PATH.read_text()
    except FileNotFoundError:
        import warnings
        warnings.warn(f"hero.txt not found at {HERO_PATH}. Run scripts/build_ascii.py.")
        return
    top, bottom = hero_text.split("---ESCOBAR---\n", 1)
    text = Text(no_wrap=True, overflow="crop")
    for line in top.splitlines(keepends=True):
        text.append(line, style="#bb9af7")
    for line in bottom.splitlines(keepends=True):
        text.append(line, style="#565f89")
    self.query_one("#hero-title", Static).update(text)
```

## Layout

- Hero at top of right panel, Notice Board tab only
- `margin-bottom: 1` on `#hero-title` provides blank line gap before markdown
- Other tabs: hero hidden via `display: none`

## Architecture: ContentPanel Refactor

`ContentPanel` refactored from `Markdown` subclass to a `Vertical` container holding:
1. `Static` (`#hero-title`) — hero art, hidden by default
2. `Markdown` (`#section-content`) — section markdown

### Padding Migration

Padding currently exists in two places and must be removed from both:
- `ContentPanel.DEFAULT_CSS` — `padding: 1 2` (lines 9–14 of `content_panel.py`)
- `#right-panel` in `theme.tcss` — `padding: 1 2` (line 26)

Both are removed. Padding is added only to `#section-content` in `theme.tcss` so the hero art renders flush to the panel edge and only the markdown is indented.

### TCSS Changes in `theme.tcss`

```css
/* Hero title — flush to panel edge */
#hero-title {
    width: 100%;
    margin-bottom: 1;
    display: none;
}

/* Markdown content — indented (replaces padding formerly on #right-panel) */
#section-content {
    padding: 1 2;
}
```

Also remove `padding: 1 2` from the existing `#right-panel` rule.

### show_content() — Signature Change (must land with app.py update in same commit)

**`widgets/content_panel.py`:**
```python
def show_content(self, markdown_text: str, section_id: str) -> None:
    """Update displayed markdown content and toggle hero visibility."""
    self.query_one("#section-content", Markdown).update(markdown_text)
    self.query_one("#hero-title").display = (section_id == "notice-board")
```

**`app.py` — the one call site in `_refresh_section()` (~line 163):**
```python
self.query_one("#right-panel", ContentPanel).show_content(
    f"# {section.label}\n\nPlaceholder content for {section.label}.",
    section_id=section.id,
)
```

### Scroll Behavior

`app.py` scroll actions (`action_scroll_down` / `action_scroll_up`) target `#right-panel` unchanged. All Textual `Widget`s have `scroll_down()` / `scroll_up()` — actual scrolling is enabled by `overflow-y: auto` on `#right-panel` in `theme.tcss`, which is already set (line 27) and remains unchanged after the refactor. An async integration test should assert that `action_scroll_down` advances the scroll position of `#right-panel`.

## Art File Conflict Fix

Four changes in one atomic commit:
1. `load_section_art()` in `widgets/ascii_panel.py` — load `art.txt` explicitly instead of globbing
2. Rename all `placeholder.txt` → `art.txt` in every section art directory
3. `build_ascii.py` lines 70 and 83 — `"placeholder.txt"` → `"art.txt"`
4. `tests/test_ascii_panel.py` and `tests/conftest.py` — `"placeholder.txt"` → `"art.txt"`

## Out of Scope

- Transparent background (dropped — terminal configs already vary the appearance)
- Phase 4 markdown content pipeline
- ASCII video animation (Phase 5)
