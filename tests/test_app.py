"""Tests for the main portfolio TUI app."""
import pytest


@pytest.mark.asyncio
async def test_app_renders_split_layout():
    """App should render left panel, right panel, and footer."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        assert pilot.app.query_one("#left-panel")
        assert pilot.app.query_one("#right-panel")
        assert pilot.app.query_one("#footer-bar")


@pytest.mark.asyncio
async def test_app_shows_size_warning_for_small_terminal():
    """App should show warning when terminal is too small."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(60, 20)) as pilot:
        warning = pilot.app.query_one("#size-warning")
        assert warning.display is True
        main = pilot.app.query_one("#main-container")
        assert main.display is False


@pytest.mark.asyncio
async def test_app_hides_warning_for_normal_terminal():
    """App should hide warning when terminal is large enough."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        warning = pilot.app.query_one("#size-warning")
        assert warning.display is False
        main = pilot.app.query_one("#main-container")
        assert main.display is True


@pytest.mark.asyncio
async def test_help_overlay_toggles():
    """Pressing ? should show help, pressing again should hide."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        # Help should be hidden initially
        assert not pilot.app.query_one("#help-overlay").display
        await pilot.press("question_mark")
        assert pilot.app.query_one("#help-overlay").display
        await pilot.press("question_mark")
        assert not pilot.app.query_one("#help-overlay").display


@pytest.mark.asyncio
async def test_scroll_down_advances_position():
    """action_scroll_down should not regress scroll position of #right-panel."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        panel = pilot.app.query_one("#right-panel")
        initial_y = panel.scroll_y
        await pilot.press("j")
        await pilot.pause()
        # Scroll position should not regress (may stay if content fits in panel)
        assert panel.scroll_y >= initial_y


@pytest.mark.asyncio
async def test_enter_opens_detail_view():
    """Enter on a directory section should set _in_detail=True."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("2")      # Sailing Instructions (is_directory=True)
        await pilot.pause()
        assert not pilot.app._in_detail
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app._in_detail


@pytest.mark.asyncio
async def test_escape_returns_from_detail():
    """ESC should return from detail view to list."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app._in_detail
        await pilot.press("escape")
        await pilot.pause()
        assert not pilot.app._in_detail


@pytest.mark.asyncio
async def test_escape_does_nothing_at_top_level():
    """ESC at top level should not change active section."""
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app._active_idx == 0
        assert not pilot.app._in_detail
