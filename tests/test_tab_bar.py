"""Tests for tab navigation."""
import pytest


@pytest.mark.asyncio
async def test_right_arrow_switches_to_next_tab():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        assert pilot.app._active_idx == 0
        await pilot.press("right")
        assert pilot.app._active_idx == 1


@pytest.mark.asyncio
async def test_left_arrow_switches_to_prev_tab():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        await pilot.press("right")
        await pilot.press("right")
        assert pilot.app._active_idx == 2
        await pilot.press("left")
        assert pilot.app._active_idx == 1


@pytest.mark.asyncio
async def test_h_l_keys_switch_tabs():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        await pilot.press("l")
        assert pilot.app._active_idx == 1
        await pilot.press("h")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_number_keys_jump_to_section():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert pilot.app._active_idx == 2
        await pilot.press("1")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_left_arrow_does_not_go_below_zero():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        await pilot.press("left")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_right_arrow_does_not_exceed_max():
    from app import PortfolioApp

    app = PortfolioApp()
    async with app.run_test() as pilot:
        for _ in range(10):
            await pilot.press("right")
        assert pilot.app._active_idx == 4  # 5 sections, max index 4
