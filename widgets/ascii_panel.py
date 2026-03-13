"""Left panel widget — displays ASCII art or video frames."""
from pathlib import Path

from rich.text import Text
from textual.widgets import Static

ART_ROOT = Path(__file__).parent.parent / "ascii_art"


def load_section_art(art_dir: Path) -> str:
    """Load art.txt from an art directory. Returns fallback if missing."""
    art_file = art_dir / "art.txt"
    if not art_file.exists():
        return "  ~ no art available ~  "
    return art_file.read_text()


class AsciiPanel(Static):
    """Displays ASCII art for the active section.

    Converts raw ANSI text to Rich Text objects so Textual can
    properly measure and clip the content within the panel.
    """

    DEFAULT_CSS = """
    AsciiPanel {
        width: 100%;
        height: 100%;
        overflow: hidden auto;
        content-align: center middle;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("  ~ sailing art placeholder ~  ", markup=False, **kwargs)

    def update_art(self, art_text: str) -> None:
        """Swap displayed ASCII art, converting ANSI escapes to Rich Text."""
        rich_text = Text.from_ansi(art_text, no_wrap=True, overflow="crop")
        self.update(rich_text)
