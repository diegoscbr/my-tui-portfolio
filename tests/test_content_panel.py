"""Tests for the refactored ContentPanel widget."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    with patch.object(cp_module, "_load_hero", return_value=cp_module.Text(FAKE_HERO)):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            panel.show_content("# Test\n\nContent.", section_id="notice-board")
            await pilot.pause()
            assert panel.query_one("#hero-title").display is True


@pytest.mark.asyncio
async def test_hero_hidden_on_other_sections():
    """show_content() with any other section_id should hide #hero-title."""
    with patch.object(cp_module, "_load_hero", return_value=cp_module.Text(FAKE_HERO)):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            panel.show_content("# Experience\n\nContent.", section_id="experience")
            await pilot.pause()
            assert panel.query_one("#hero-title").display is False


@pytest.mark.asyncio
async def test_show_content_updates_markdown():
    """show_content() should update #section-content markdown widget — no exception raised."""
    with patch.object(cp_module, "_load_hero", return_value=cp_module.Text(FAKE_HERO)):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            # show_content() must not raise; #section-content must be queryable after call
            panel.show_content("# Hello\n\nWorld.", section_id="contact")
            await pilot.pause()
            md = panel.query_one("#section-content", Markdown)
            assert md is not None  # query_one raises NoMatches if missing, so this is proof of existence


@pytest.mark.asyncio
async def test_hero_missing_file_does_not_crash():
    """Missing hero.txt should warn but not crash — hero widget still present."""
    with patch.object(cp_module, "_load_hero", return_value=cp_module.Text()):
        async with _TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#panel", ContentPanel)
            assert panel.query_one("#hero-title") is not None
            assert panel.query_one("#section-content") is not None
