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

from pathlib import Path

from config import SECTIONS
from content_loader import load_single_content, load_directory_content, ContentItem
from widgets.ascii_panel import AsciiPanel, ART_ROOT, load_section_art
from widgets.tab_bar import TabBar
from widgets.content_panel import ContentPanel

CONTENT_ROOT = Path(__file__).parent / "content"

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
        Binding("1", "jump_tab_1", show=False),
        Binding("2", "jump_tab_2", show=False),
        Binding("3", "jump_tab_3", show=False),
        Binding("4", "jump_tab_4", show=False),
        Binding("5", "jump_tab_5", show=False),
    ]

    def __init__(self, ssh_driver: SSHDriver | None = None, **kwargs):
        super().__init__(**kwargs)
        self._ssh_driver = ssh_driver
        self._active_idx = 0
        self._in_detail = False
        self._content: dict = {}

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
        yield Static(
            "Keybindings\n\n"
            "  \u2190 \u2192 h l   Switch sections\n"
            "  \u2191 \u2193 j k   Scroll content\n"
            "  1-5        Jump to section\n"
            "  Enter      Open item\n"
            "  ESC h      Go back\n"
            "  q          Quit\n"
            "  ?          Toggle this help\n",
            id="help-overlay",
        )

    def on_mount(self) -> None:
        """Check terminal size on mount and load content."""
        self._check_size()
        self.query_one("#help-overlay").display = False
        self._load_all_content()
        self._refresh_section()

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

    def action_jump_tab_1(self) -> None: self._jump_to(0)
    def action_jump_tab_2(self) -> None: self._jump_to(1)
    def action_jump_tab_3(self) -> None: self._jump_to(2)
    def action_jump_tab_4(self) -> None: self._jump_to(3)
    def action_jump_tab_5(self) -> None: self._jump_to(4)

    def _jump_to(self, idx: int) -> None:
        """Jump directly to a section by index."""
        if not self._in_detail and 0 <= idx < len(SECTIONS):
            self._active_idx = idx
            self._refresh_section()

    def action_toggle_help(self) -> None:
        """Toggle help overlay."""
        overlay = self.query_one("#help-overlay")
        overlay.display = not overlay.display

    def _load_all_content(self) -> None:
        """Load all section content from disk."""
        for section in SECTIONS:
            path = CONTENT_ROOT / section.content_path
            if section.is_directory:
                self._content[section.id] = load_directory_content(path)
            else:
                if path.exists():
                    self._content[section.id] = load_single_content(path)
                else:
                    self._content[section.id] = ContentItem(
                        title=section.label,
                        body="No content yet.",
                    )

    def _refresh_section(self) -> None:
        """Update panels for the active section."""
        section = SECTIONS[self._active_idx]
        art_text = load_section_art(ART_ROOT / section.art_path)
        self.query_one("#left-panel", AsciiPanel).update_art(art_text)
        self.query_one("#footer-bar", TabBar).set_active(self._active_idx)

        content = self._content.get(section.id)
        panel = self.query_one("#right-panel", ContentPanel)

        if isinstance(content, list):
            if not content:
                panel.show_content(f"# {section.label}\n\nNo content yet.", section_id=section.id)
            else:
                md = f"# {section.label}\n\n"
                for item in content:
                    md += f"**{item.title}**\n"
                    if item.description:
                        md += f"{item.description}\n"
                    if item.tags:
                        md += f"*{', '.join(item.tags)}*\n"
                    md += "\n"
                panel.show_content(md, section_id=section.id)
        else:
            item = content or ContentItem(title=section.label, body="No content yet.")
            panel.show_content(f"# {item.title}\n\n{item.body}", section_id=section.id)


if __name__ == "__main__":
    PortfolioApp().run()
