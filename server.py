"""
asyncssh SSH server for diego.boats terminal portfolio.

Accepts SSH connections on port 22 (configurable), spawns an isolated
Textual app per session using the custom SSHDriver.

Uses SSHServerSession (not process_factory) for raw keystroke access
and window-change notifications — required for a TUI over SSH.

Usage:
    python3 server.py                    # port 22
    python3 server.py --port 2222        # custom port
    MAX_SESSIONS=30 python3 server.py    # custom session limit
"""
import asyncio
import logging
import os
from pathlib import Path
from time import time
from collections import defaultdict

import asyncssh

from app import PortfolioApp
from ssh_driver import SSHDriver

logger = logging.getLogger("diego.boats")

MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "50"))
RATE_LIMIT_PER_IP = 5  # connections per minute
HOST_KEY_PATH = Path(".ssh/host_key")

# Shared state — asyncio.Semaphore is safe for concurrent coroutines
_session_semaphore: asyncio.Semaphore | None = None  # initialized in create_server
_ip_connections: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    """Return True if the IP is within rate limits."""
    now = time()
    _ip_connections[ip] = [t for t in _ip_connections[ip] if now - t < 60]
    if len(_ip_connections[ip]) >= RATE_LIMIT_PER_IP:
        return False
    _ip_connections[ip].append(now)
    return True


async def _cleanup_rate_limits():
    """Background task: prune stale rate-limit entries every 60 seconds."""
    while True:
        await asyncio.sleep(60)
        now = time()
        stale_ips = [
            ip for ip, times in _ip_connections.items()
            if all(now - t >= 60 for t in times)
        ]
        for ip in stale_ips:
            del _ip_connections[ip]


class PortfolioSession(asyncssh.SSHServerSession):
    """One session = one Textual app instance.

    Uses SSHServerSession instead of process_factory so we get:
    - data_received() for raw keystrokes (no line-editor buffering)
    - window_change_received() for terminal resize
    """

    def __init__(self):
        self._chan = None
        self._app = None
        self._driver = None
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._width = 80
        self._height = 24
        self._app_task = None

    def connection_made(self, chan):
        self._chan = chan

    def pty_requested(self, term_type, term_size, term_modes):
        w, h = term_size[0], term_size[1]
        self._width = w if w > 0 else 80
        self._height = h if h > 0 else 24
        return True

    def shell_requested(self):
        return True

    def session_started(self):
        self._app_task = asyncio.create_task(self._run_app())

    def data_received(self, data, datatype):
        """Feed raw input to the Textual input queue."""
        if data:
            text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
            self._input_queue.put_nowait(text)

    def window_change_received(self, width, height, pixwidth, pixheight):
        """Handle terminal resize — update driver and post Resize event."""
        w = width if width > 0 else 80
        h = height if height > 0 else 24
        if self._driver:
            self._driver.set_size(w, h)

    def eof_received(self):
        self._input_queue.put_nowait(None)
        return False

    def connection_lost(self, exc):
        self._input_queue.put_nowait(None)
        if self._app_task and not self._app_task.done():
            self._app_task.cancel()

    async def _run_app(self):
        """Launch the Textual app for this session."""
        if _session_semaphore.locked():
            self._chan.write(
                b"\r\n  Harbor's full! Too many sailors aboard.\r\n"
                b"  Try again in a moment.\r\n\r\n"
            )
            self._chan.exit(1)
            return

        await _session_semaphore.acquire()
        try:
            self._app = PortfolioApp()
            self._driver = SSHDriver(
                self._app,
                output_stream=self._chan,
                input_queue=self._input_queue,
                size=(self._width, self._height),
                mouse=False,
            )
            self._app._ssh_driver = self._driver
            await self._app.run_async()
        finally:
            _session_semaphore.release()
            self._chan.exit(0)


class PortfolioSSHServer(asyncssh.SSHServer):
    """SSH server — no auth required (public portfolio)."""

    def connection_made(self, conn):
        self._conn = conn
        ip = conn.get_extra_info("peername")[0]
        logger.info("Connection from %s", ip)

    def begin_auth(self, username):
        return False  # No auth required — public portfolio

    def session_requested(self):
        ip = self._conn.get_extra_info("peername")[0]
        if not _check_rate_limit(ip):
            logger.warning("Rate limit exceeded for %s", ip)
            return False
        return PortfolioSession()


def _ensure_host_key(host_key_path: Path) -> None:
    """Generate ed25519 host key on first run, persist for TOFU."""
    host_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not host_key_path.exists():
        key = asyncssh.generate_private_key("ssh-ed25519")
        host_key_path.write_bytes(key.export_private_key())
        host_key_path.chmod(0o600)
        logger.info("Generated new host key at %s", host_key_path)


async def create_server(
    port: int = 22,
    max_sessions: int = MAX_SESSIONS,
    host_key_path: Path = HOST_KEY_PATH,
):
    """Create and start the SSH server."""
    global _session_semaphore
    _session_semaphore = asyncio.Semaphore(max_sessions)

    _ensure_host_key(host_key_path)

    server = await asyncssh.create_server(
        PortfolioSSHServer,
        "",
        port,
        server_host_keys=[str(host_key_path)],
        encoding=None,  # Binary mode — PortfolioSession handles encoding
    )
    actual_port = server.sockets[0].getsockname()[1]
    logger.info(
        "SSH server listening on port %d (max %d sessions)",
        actual_port, max_sessions,
    )

    # Store port for test fixtures
    server.port = actual_port

    # Start rate-limit cleanup task
    asyncio.create_task(_cleanup_rate_limits())

    return server


async def main():
    """Entry point — start server and run forever."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    parser = argparse.ArgumentParser(description="diego.boats SSH portfolio")
    parser.add_argument("--port", type=int, default=22)
    args = parser.parse_args()

    server = await create_server(port=args.port)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
