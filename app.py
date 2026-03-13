"""
Main Textual app for diego.boats terminal portfolio.

Split-panel layout: ASCII art on the left, markdown content on the right,
tab navigation along the bottom. Tokyo Night Dark theme.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.driver import Driver
from textual.widgets import Static
from textual.binding import Binding

from config import SECTIONS
from widgets.ascii_panel import AsciiPanel
from widgets.tab_bar import TabBar
from widgets.content_panel import ContentPanel

if TYPE_CHECKING:
    from ssh_driver import SSHDriver

MIN_WIDTH = 80
MIN_HEIGHT = 24


class PortfolioApp(App):
    """SSH-accessible terminal portfolio."""

    CSS_PATH = "theme.tcss"

    BINDINGS = [
        Binding("q", "request_quit", "Quit", show=False),
        Binding("question_mark", "toggle_help", "Help", show=False),
        Binding("left,h", "prev_tab", "Previous tab", show=False),
        Binding("right,l", "next_tab", "Next tab", show=False),
        Binding("j,down", "scroll_down", "Scroll down", show=False),
        Binding("k,up", "scroll_up", "Scroll up", show=False),
    ]

    def __init__(self, ssh_driver: SSHDriver | None = None, **kwargs):
        super().__init__(**kwargs)
        self._ssh_driver = ssh_driver
        self._active_idx = 0
        self._in_detail = False

    def _build_driver(
        self,
        headless: bool,
        inline: bool,
        mouse: bool,
        size: tuple[int, int] | None,
    ) -> Driver:
        """Use injected SSH driver if available, otherwise default."""
        if self._ssh_driver is not None:
            self._driver = self._ssh_driver
            return self._ssh_driver
        return super()._build_driver(headless, inline, mouse, size)

    def compose(self) -> ComposeResult:
        # Size warning (hidden when terminal is large enough)
        yield Static(
            "Terminal too small \u2014 please resize to at least 80x24",
            id="size-warning",
        )
        # Main layout
        with Horizontal(id="main-container"):
            yield AsciiPanel(id="left-panel")
            yield ContentPanel(id="right-panel")
        yield TabBar(active_idx=0, id="footer-bar")

    def on_mount(self) -> None:
        """Check terminal size on mount."""
        self._check_size()

    def on_resize(self) -> None:
        """Re-check terminal size on resize."""
        self._check_size()

    def _check_size(self) -> None:
        """Show/hide size warning based on terminal dimensions."""
        too_small = self.size.width < MIN_WIDTH or self.size.height < MIN_HEIGHT
        self.query_one("#size-warning").display = too_small
        self.query_one("#main-container").display = not too_small
        self.query_one("#footer-bar").display = not too_small

    def action_scroll_down(self) -> None:
        """Scroll the right panel content down."""
        self.query_one("#right-panel").scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll the right panel content up."""
        self.query_one("#right-panel").scroll_up()

    def action_request_quit(self) -> None:
        """Quit only from top level. In detail view, go back instead."""
        if self._in_detail:
            self._in_detail = False
            self._refresh_section()
        else:
            self.exit()

    def action_prev_tab(self) -> None:
        """Switch to previous tab (only at top level)."""
        if self._in_detail:
            self._in_detail = False
            self._refresh_section()
            return
        if self._active_idx > 0:
            self._active_idx -= 1
            self._refresh_section()

    def action_next_tab(self) -> None:
        """Switch to next tab (only at top level)."""
        if self._in_detail:
            return
        if self._active_idx < len(SECTIONS) - 1:
            self._active_idx += 1
            self._refresh_section()

    def action_toggle_help(self) -> None:
        """Toggle help overlay."""
        # TODO: Phase 2 — implement help overlay
        pass

    def _refresh_section(self) -> None:
        """Update panels for the active section."""
        section = SECTIONS[self._active_idx]
        self.query_one("#left-panel", AsciiPanel).update_art(
            f"  ~ {section.label} art ~  "
        )
        self.query_one("#right-panel", ContentPanel).show_content(
            f"# {section.label}\n\nPlaceholder content for {section.label}."
        )
        self.query_one("#footer-bar", TabBar).set_active(self._active_idx)


if __name__ == "__main__":
    PortfolioApp().run()
