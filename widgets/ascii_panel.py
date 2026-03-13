"""Left panel widget — displays ASCII art or video frames."""
from textual.widgets import Static


class AsciiPanel(Static):
    """Displays ASCII art for the active section."""

    DEFAULT_CSS = """
    AsciiPanel {
        width: 100%;
        height: 100%;
        content-align: center middle;
        overflow: hidden;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("  ~ sailing art placeholder ~  ", **kwargs)

    def update_art(self, art_text: str) -> None:
        """Swap displayed ASCII art."""
        self.update(art_text)
