"""
asyncssh SSH server for diego.boats terminal portfolio.

Accepts SSH connections on port 22 (configurable), spawns an isolated
Textual app per session using the custom SSHDriver.

Relies on asyncssh for all SSH protocol handling, including malformed
input, unsupported features, and binary garbage — asyncssh's defaults
handle these gracefully.

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
IDLE_TIMEOUT_SECONDS = 600  # 10 minutes
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


class PortfolioSSHServer(asyncssh.SSHServer):
    """SSH server that accepts all connections (no auth)."""

    def connection_made(self, conn):
        self._conn = conn
        ip = conn.get_extra_info("peername")[0]
        logger.info("Connection from %s", ip)

    def begin_auth(self, username):
        return False  # No auth required — public portfolio

    def session_requested(self):
        return True


async def _handle_client(process: asyncssh.SSHServerProcess):
    """Handle a single SSH session — spawn Textual app with SSHDriver."""
    if _session_semaphore.locked():
        process.stdout.write(
            "\r\n  Harbor's full! Too many sailors aboard.\r\n"
            "  Try again in a moment.\r\n\r\n"
        )
        process.exit(1)
        return
    await _session_semaphore.acquire()

    try:
        # Get terminal dimensions from PTY (handle 0x0 edge case from mosh etc.)
        width = process.get_terminal_size()[0] or 80
        height = process.get_terminal_size()[1] or 24
        if width == 0:
            width = 80
        if height == 0:
            height = 24

        # Create input queue for feeding SSH input to Textual
        input_queue: asyncio.Queue[str | None] = asyncio.Queue()

        app = PortfolioApp()
        driver = SSHDriver(
            app,
            output_stream=process.stdout,
            input_queue=input_queue,
            size=(width, height),
        )
        app._ssh_driver = driver

        # Feed SSH stdin to the input queue in a background task
        async def _feed_input():
            try:
                while True:
                    data = await asyncio.wait_for(
                        process.stdin.read(1024),
                        timeout=IDLE_TIMEOUT_SECONDS,
                    )
                    if not data:
                        break
                    await input_queue.put(data)
            except (asyncio.TimeoutError, asyncssh.BreakReceived):
                pass
            finally:
                await input_queue.put(None)  # Signal EOF

        input_task = asyncio.create_task(_feed_input())

        try:
            await app.run_async()
        finally:
            input_task.cancel()
            try:
                await input_task
            except asyncio.CancelledError:
                pass
    finally:
        _session_semaphore.release()
        process.exit(0)


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
        process_factory=_handle_client,
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
