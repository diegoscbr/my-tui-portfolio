"""Right panel widget — renders markdown content with scrolling."""
from textual.widgets import Markdown


class ContentPanel(Markdown):
    """Displays markdown content for the active section."""

    DEFAULT_CSS = """
    ContentPanel {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("# Welcome\n\nContent loading...", **kwargs)

    def show_content(self, markdown_text: str) -> None:
        """Update displayed markdown content."""
        self.update(markdown_text)
