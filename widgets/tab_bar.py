"""Bottom navigation bar — renders tabs with active highlight."""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from config import SECTIONS


class TabBar(Widget):
    """Tab navigation bar with active section highlight and key hints."""

    DEFAULT_CSS = """
    TabBar {
        height: 3;
        layout: vertical;
    }
    """

    # Reactive property — changing this triggers recompose automatically
    active_idx: reactive[int] = reactive(0)

    def __init__(self, active_idx: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.active_idx = active_idx

    def compose(self) -> ComposeResult:
        with Horizontal():
            for i, section in enumerate(SECTIONS):
                classes = "tab tab--active" if i == self.active_idx else "tab"
                yield Static(section.short_label, classes=classes)
        yield Static(
            " [#7dcfff]\u2190\u2192[/] [#7dcfff]h/l[/] navigate  "
            "[#7dcfff]j/k[/] scroll  "
            "[#7dcfff]q[/] quit  "
            "[#7dcfff]?[/] help",
            classes="keyhint",
        )

    async def watch_active_idx(self) -> None:
        """Reactive watcher — recompose when active tab changes."""
        await self.recompose()

    def set_active(self, idx: int) -> None:
        """Update the active tab index (triggers recompose via reactive)."""
        self.active_idx = idx
