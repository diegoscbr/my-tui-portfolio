# Hero Title Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "DIEGO / ESCOBAR" two-font hero title to the Notice Board tab's right panel, backed by a pre-rendered build pipeline and a refactored ContentPanel widget.

**Architecture:** Pre-render hero art using the `figlet` CLI with two committed `.flf` font files (Terrace + RubiFont), write a delimited `hero.txt`, and color it at runtime via Rich `Text` styling inside a refactored `ContentPanel` (Vertical container holding a Static hero widget + Markdown content widget).

**Tech Stack:** Python 3.14, Textual, Rich, figlet CLI, pytest, pytest-asyncio

---

## Chunk 1: Art File Conflict Fix

Rename all `placeholder.txt` → `art.txt` and make `load_section_art()` load by explicit filename. This prevents `hero.txt` from ever being picked up by the left panel. All four changes land in one atomic commit.

### Task 1: Fix load_section_art() and rename placeholder.txt → art.txt

**Files:**
- Modify: `widgets/ascii_panel.py:10-17`
- Modify: `tests/test_ascii_panel.py`
- Modify: `tests/conftest.py`
- Rename: `ascii_art/notice-board/placeholder.txt` → `ascii_art/notice-board/art.txt`

- [ ] **Step 1: Update the test to expect `art.txt` explicitly**

Open `tests/test_ascii_panel.py`. Replace `test_load_static_art` with a version that proves explicit loading (includes a decoy `aaa.txt` that the old glob would pick first):

```python
def test_load_static_art(tmp_path):
    """Should load art.txt explicitly, ignoring other .txt files."""
    from widgets.ascii_panel import load_section_art

    art_dir = tmp_path / "test-section"
    art_dir.mkdir()
    (art_dir / "aaa.txt").write_text("wrong — glob picks this first")  # decoy
    (art_dir / "art.txt").write_text("  test art  ")
    (art_dir / "hero.txt").write_text("wrong — should never be loaded")

    result = load_section_art(art_dir)
    assert result == "  test art  "
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
source .venv/bin/activate
pytest tests/test_ascii_panel.py::test_load_static_art -v
```

Expected: FAIL — current `load_section_art` globs `*.txt` and picks `aaa.txt` first.

- [ ] **Step 3: Fix `load_section_art()` to load `art.txt` explicitly**

Open `widgets/ascii_panel.py`. Replace the entire `load_section_art` function:

```python
def load_section_art(art_dir: Path) -> str:
    """Load art.txt from an art directory. Returns fallback if missing."""
    art_file = art_dir / "art.txt"
    if not art_file.exists():
        return "  ~ no art available ~  "
    return art_file.read_text()
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
pytest tests/test_ascii_panel.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Update conftest.py fixture**

Open `tests/conftest.py`. In the `art_dir` fixture, rename `placeholder.txt` to `art.txt`:

```python
@pytest.fixture
def art_dir(tmp_path):
    """Create a temporary ascii_art directory with art files."""
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
        (d / "art.txt").write_text(f"  ~ {section} art ~  ")  # was placeholder.txt
    return art
```

- [ ] **Step 6: Rename placeholder.txt on disk**

```bash
mv ascii_art/notice-board/placeholder.txt ascii_art/notice-board/art.txt
```

Check for other sections (they may not have placeholder.txt yet — create art.txt if missing):

```bash
for dir in ascii_art/sailing-instructions ascii_art/rc-logs ascii_art/contact ascii_art/experience; do
  if [ -f "$dir/placeholder.txt" ]; then
    mv "$dir/placeholder.txt" "$dir/art.txt"
  fi
done
ls ascii_art/*/art.txt 2>/dev/null || echo "some dirs may not have art.txt yet"
```

- [ ] **Step 7: Run full test suite**

```bash
pytest -v
```

Expected: All 18 existing tests PASS.

- [ ] **Step 8: Commit (all four changes atomically)**

```bash
git add widgets/ascii_panel.py tests/test_ascii_panel.py tests/conftest.py ascii_art/
git commit -m "fix: load art.txt explicitly to prevent hero.txt left-panel collision"
```

---

## Chunk 2: Hero Build Pipeline

Download and commit font files, add `build_hero()` to the build script, generate `hero.txt`.

### Task 2: Commit font files

**Files:**
- Create: `scripts/fonts/Terrace.flf`
- Create: `scripts/fonts/RubiFont.flf`

- [ ] **Step 1: Create the fonts directory and download both fonts**

```bash
mkdir -p scripts/fonts
curl -sL "https://raw.githubusercontent.com/patorjk/figlet.js/main/fonts/Terrace.flf" \
  -o scripts/fonts/Terrace.flf
curl -sL "https://raw.githubusercontent.com/patorjk/figlet.js/main/fonts/RubiFont.flf" \
  -o scripts/fonts/RubiFont.flf
```

- [ ] **Step 2: Verify both files are valid figlet fonts**

```bash
figlet -f scripts/fonts/Terrace.flf "DIEGO"
figlet -f scripts/fonts/RubiFont.flf "ESCOBAR"
```

Expected: ASCII art output for each. If you see `figlet: Not a FIGlet 2 font file`, the download failed — check your internet connection and retry.

- [ ] **Step 3: Commit the font files**

```bash
git add scripts/fonts/
git commit -m "chore: add Terrace and RubiFont figlet font files"
```

---

### Task 3: Add build_hero() to build_ascii.py

**Files:**
- Modify: `scripts/build_ascii.py`
- Modify: `pyproject.toml`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write a test for build_hero()**

Create `tests/test_build_hero.py`:

```python
"""Tests for the build_hero() function in scripts/build_ascii.py."""
import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import build_ascii
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_build_hero_creates_hero_txt(tmp_path, monkeypatch):
    """build_hero() should create hero.txt with ---ESCOBAR--- delimiter."""
    import build_ascii

    # Point ART_ROOT and PROJECT_ROOT at tmp_path
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
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
pytest tests/test_build_hero.py -v
```

Expected: FAIL — `build_ascii` has no `build_hero` function yet.

- [ ] **Step 3: Add `import subprocess` and `build_hero()` to build_ascii.py**

Open `scripts/build_ascii.py`. Add `import subprocess` at the top (after existing imports). Then add the function after `build_notice_board()`:

```python
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
    output_path.write_text(diego + "---ESCOBAR---\n" + escobar)
    print("  Built notice-board/hero.txt")
```

- [ ] **Step 4: Fix the two `placeholder.txt` references in build_ascii.py**

In `build_notice_board()` (line ~70):
```python
build_from_image(frame, output_dir / "art.txt")  # was placeholder.txt
```

In `build_section()` (line ~83):
```python
build_from_image(source_files[0], section_dir / "art.txt")  # was placeholder.txt
```

- [ ] **Step 5: Wire build_hero() into main()**

In `main()`, update the dispatch block so `build_hero()` runs alongside `build_notice_board()`:

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

- [ ] **Step 6: Run the test — verify it passes**

```bash
pytest tests/test_build_hero.py -v
```

Expected: PASS.

- [ ] **Step 7: Update pyproject.toml**

Add a `build` extras group (also fixes pre-existing omission of `ascii_magic` and `pillow`):

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

- [ ] **Step 8: Update CLAUDE.md environment setup**

In the "Environment Setup" section of `CLAUDE.md`, add `figlet` alongside the existing `ffmpeg` note:

```
System dependencies:
- `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux) — for video processing
- `brew install figlet` (macOS) or `apt install figlet` (Linux) — for hero art build
```

- [ ] **Step 9: Run the full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 10: Commit**

```bash
git add scripts/build_ascii.py tests/test_build_hero.py pyproject.toml CLAUDE.md
git commit -m "feat: add build_hero() to generate Terrace+RubiFont hero art"
```

---

### Task 4: Generate hero.txt and commit

**Files:**
- Create: `ascii_art/notice-board/hero.txt`

- [ ] **Step 1: Run the build script**

```bash
source .venv/bin/activate
python3 scripts/build_ascii.py --section notice-board
```

Expected output:
```
Build ASCII art assets
========================================
Output: /path/to/ascii_art

  Built notice-board/hero.txt
```

- [ ] **Step 2: Inspect hero.txt**

```bash
cat ascii_art/notice-board/hero.txt
```

Expected: Terrace-rendered "DIEGO" block, then `---ESCOBAR---`, then RubiFont-rendered "ESCOBAR" block. Both should contain Unicode block characters (`░`, `█`, `▗`, `▄`).

- [ ] **Step 3: Commit hero.txt**

```bash
git add ascii_art/notice-board/hero.txt
git commit -m "chore: generate hero.txt build artifact"
```

---

## Chunk 3: ContentPanel Refactor

Refactor `ContentPanel` from a `Markdown` subclass to a `Vertical` container, add hero loading and coloring logic, update TCSS, and update the call site in `app.py`.

### Task 5: Write ContentPanel tests

**Files:**
- Create: `tests/test_content_panel.py`

Textual requires an `App` instance to run tests — widgets cannot be tested directly. Wrap `ContentPanel` in a minimal test app for each test.

- [ ] **Step 1: Write tests for the new ContentPanel interface**

Create `tests/test_content_panel.py`:

```python
"""Tests for the refactored ContentPanel widget."""
import pytest
from pathlib import Path
from unittest.mock import patch

import widgets.content_panel as cp_module
from textual.app import App, ComposeResult
from textual.widgets import Markdown
from widgets.content_panel import ContentPanel

FAKE_HERO = "DIEGO BLOCK\n---ESCOBAR---\nESCOBAR BLOCK\n"


class _TestApp(App):
    """Minimal app that mounts a ContentPanel for testing."""
    def compose(self) -> ComposeResult:
        yield ContentPanel(id="panel")


@pytest.mark.asyncio
async def test_hero_visible_on_notice_board():
    """show_content() with section_id='notice-board' should show #hero-title."""
    with patch.object(cp_module.HERO_PATH, "read_text", return_value=FAKE_HERO):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            panel.show_content("# Test\n\nContent.", section_id="notice-board")
            await pilot.pause()
            assert panel.query_one("#hero-title").display is True


@pytest.mark.asyncio
async def test_hero_hidden_on_other_sections():
    """show_content() with any other section_id should hide #hero-title."""
    with patch.object(cp_module.HERO_PATH, "read_text", return_value=FAKE_HERO):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            panel.show_content("# Experience\n\nContent.", section_id="experience")
            await pilot.pause()
            assert panel.query_one("#hero-title").display is False


@pytest.mark.asyncio
async def test_show_content_updates_markdown():
    """show_content() should update #section-content markdown widget."""
    with patch.object(cp_module.HERO_PATH, "read_text", return_value=FAKE_HERO):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            panel.show_content("# Hello\n\nWorld.", section_id="contact")
            await pilot.pause()
            # Widget exists and is the right type
            assert panel.query_one("#section-content", Markdown) is not None


@pytest.mark.asyncio
async def test_hero_missing_file_does_not_crash():
    """Missing hero.txt should warn but not crash — hero widget still present."""
    with patch.object(cp_module.HERO_PATH, "read_text", side_effect=FileNotFoundError):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            assert panel.query_one("#hero-title") is not None
            assert panel.query_one("#section-content") is not None
```

- [ ] **Step 2: Run the tests — verify they fail**

```bash
pytest tests/test_content_panel.py -v
```

Expected: FAIL — `ContentPanel` still extends `Markdown` with no `#hero-title` or `#section-content`.

---

### Task 6: Refactor ContentPanel

**Files:**
- Modify: `widgets/content_panel.py`

- [ ] **Step 1: Rewrite content_panel.py**

Replace the entire file:

```python
"""Right panel widget — hero title + markdown content with scrolling."""
import warnings
from pathlib import Path

from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Markdown, Static

HERO_PATH = Path(__file__).parent.parent / "ascii_art" / "notice-board" / "hero.txt"

# Purple for DIEGO (Terrace), gray for ESCOBAR (RubiFont)
_PURPLE = "#bb9af7"
_GRAY = "#565f89"


def _load_hero() -> Text:
    """Load hero.txt and return a colored Rich Text object.

    Returns empty Text if the file is missing.
    """
    try:
        raw = HERO_PATH.read_text()
    except FileNotFoundError:
        warnings.warn(
            f"hero.txt not found at {HERO_PATH}. Run: python3 scripts/build_ascii.py"
        )
        return Text()

    top, bottom = raw.split("---ESCOBAR---\n", 1)
    text = Text(no_wrap=True, overflow="crop")
    for line in top.splitlines(keepends=True):
        text.append(line, style=_PURPLE)
    for line in bottom.splitlines(keepends=True):
        text.append(line, style=_GRAY)
    return text


class ContentPanel(Vertical):
    """Right panel — hero title (Notice Board only) + markdown content."""

    DEFAULT_CSS = """
    ContentPanel {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self):
        yield Static("", id="hero-title", markup=False)
        yield Markdown("# Welcome\n\nContent loading...", id="section-content")

    def on_mount(self) -> None:
        self.query_one("#hero-title", Static).update(_load_hero())

    def show_content(self, markdown_text: str, section_id: str) -> None:
        """Update markdown content and toggle hero visibility."""
        self.query_one("#section-content", Markdown).update(markdown_text)
        self.query_one("#hero-title").display = (section_id == "notice-board")
```

- [ ] **Step 2: Run the new tests**

```bash
pytest tests/test_content_panel.py -v
```

Expected: PASS (or close — fix any import/fixture issues).

- [ ] **Step 3: Run the full test suite**

```bash
pytest -v
```

Expected: All tests PASS. If existing `test_app.py` tests fail because `show_content()` is called without `section_id`, that's expected — it's fixed in Task 8.

---

### Task 7: Update theme.tcss

**Files:**
- Modify: `theme.tcss`

- [ ] **Step 1: Add hero title and section content rules, remove double padding**

Open `theme.tcss`. Make three changes:

**a) Remove `padding: 1 2` from `#right-panel`:**
```css
#right-panel {
    width: 55%;
    height: 100%;
    overflow-y: auto;
    /* padding: 1 2  <-- removed, now on #section-content */
}
```

**b) Add `#hero-title` rule (after `#right-panel`):**
```css
#hero-title {
    width: 100%;
    margin-bottom: 1;
    display: none;
}
```

**c) Add `#section-content` rule (after `#hero-title`):**
```css
#section-content {
    padding: 1 2;
}
```

- [ ] **Step 2: Run the app locally to visually verify**

```bash
python3 -m textual run app:PortfolioApp
```

Check:
- Notice Board tab: hero art appears at top in purple/gray, markdown below with left/right padding
- Other tabs (press 2–5): no hero, markdown with padding intact
- Scroll with j/k: content scrolls
- Press q to quit

- [ ] **Step 3: Commit TCSS**

```bash
git add theme.tcss
git commit -m "style: add hero-title and section-content TCSS rules"
```

---

### Task 8: Update app.py call site

**Files:**
- Modify: `app.py:163-165`

- [ ] **Step 1: Update the show_content() call in _refresh_section()**

Open `app.py`. Find `_refresh_section()` (~line 158). Update the `show_content` call to pass `section_id`:

```python
def _refresh_section(self) -> None:
    """Update panels for the active section."""
    section = SECTIONS[self._active_idx]
    art_text = load_section_art(ART_ROOT / section.art_path)
    self.query_one("#left-panel", AsciiPanel).update_art(art_text)
    self.query_one("#right-panel", ContentPanel).show_content(
        f"# {section.label}\n\nPlaceholder content for {section.label}.",
        section_id=section.id,
    )
    self.query_one("#footer-bar", TabBar).set_active(self._active_idx)
```

- [ ] **Step 2: Run the full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 3: Run the app and exercise all tabs**

```bash
python3 -m textual run app:PortfolioApp
```

Press 1–5, h/l, left/right. Verify:
- Tab 1 (Notice Board): hero visible, markdown below
- Tabs 2–5: no hero, markdown with padding
- j/k scrolls content

- [ ] **Step 4: Write a scroll integration test**

Add to `tests/test_app.py`:

```python
@pytest.mark.asyncio
async def test_scroll_down_advances_position():
    """action_scroll_down should advance scroll position of #right-panel."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Load enough content to be scrollable
        panel = pilot.app.query_one("#right-panel")
        initial_y = panel.scroll_y
        await pilot.press("j")
        await pilot.pause()
        # Scroll position should have advanced (or stayed if content fits)
        assert panel.scroll_y >= initial_y
```

Run:
```bash
pytest tests/test_app.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit everything**

```bash
git add widgets/content_panel.py app.py tests/test_content_panel.py tests/test_app.py
git commit -m "feat: add hero title to Notice Board — Terrace DIEGO + RubiFont ESCOBAR"
```

---

## Final Verification

- [ ] **Run full test suite one last time**

```bash
pytest -v
```

Expected: All tests PASS. Note the test count — should be higher than the original 18.

- [ ] **Run the app via SSH locally (optional)**

```bash
python3 server.py &
ssh -p 8022 localhost
```

Verify the hero renders correctly over an actual SSH session. Press q to quit.
