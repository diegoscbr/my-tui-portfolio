"""Tests for the asyncssh SSH server."""
import asyncio
import pytest
import pytest_asyncio
import asyncssh


@pytest_asyncio.fixture
async def portfolio_server(tmp_path):
    """Start the portfolio SSH server on a random port for testing."""
    from server import create_server

    server = await create_server(
        port=0, max_sessions=5, host_key_path=tmp_path / "host_key"
    )
    yield server
    server.close()
    await server.wait_closed()


@pytest_asyncio.fixture
async def portfolio_server_full(tmp_path):
    """Start a server with max_sessions=1, then occupy that slot."""
    from server import create_server

    server = await create_server(
        port=0, max_sessions=1, host_key_path=tmp_path / "host_key"
    )
    # Occupy the one slot by opening a full session
    conn = await asyncssh.connect(
        "localhost", port=server.port, known_hosts=None, username="visitor"
    )
    stdin, stdout, stderr = await conn.open_session(term_type="xterm")
    yield server
    conn.close()
    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_server_accepts_connection(portfolio_server):
    """Server should accept an SSH connection without authentication."""
    async with asyncssh.connect(
        "localhost",
        port=portfolio_server.port,
        known_hosts=None,
        username="visitor",
    ) as conn:
        assert conn is not None


@pytest.mark.asyncio
async def test_server_rejects_when_at_capacity(portfolio_server_full):
    """Server should send 'harbor full' message when at max sessions."""
    async with asyncssh.connect(
        "localhost",
        port=portfolio_server_full.port,
        known_hosts=None,
        username="visitor",
    ) as conn:
        stdin, stdout, stderr = await conn.open_session(term_type="xterm")
        output = await asyncio.wait_for(stdout.read(), timeout=5)
        assert "harbor" in output.lower() or "full" in output.lower()


@pytest.mark.asyncio
async def test_rate_limiting():
    """Should reject connections exceeding rate limit."""
    from server import _check_rate_limit, _ip_connections

    _ip_connections.clear()  # reset state
    ip = "192.168.1.100"

    # First 5 should pass
    for _ in range(5):
        assert _check_rate_limit(ip) is True

    # 6th should fail
    assert _check_rate_limit(ip) is False
