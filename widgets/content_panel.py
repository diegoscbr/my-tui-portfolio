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

    parts = raw.split("---ESCOBAR---\n", 1)
    if len(parts) != 2:
        warnings.warn(
            f"hero.txt at {HERO_PATH} is missing '---ESCOBAR---' delimiter. "
            "Re-run: python3 scripts/build_ascii.py"
        )
        return Text()
    top, bottom = parts
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
