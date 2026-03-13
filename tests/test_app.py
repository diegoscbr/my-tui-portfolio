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
