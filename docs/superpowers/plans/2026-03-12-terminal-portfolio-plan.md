# Terminal Portfolio (diego.boats) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an SSH-accessible terminal portfolio at diego.boats — a split-panel TUI with sailing theme, Tokyo Night Dark palette, ASCII art per section, and markdown-driven content.

**Architecture:** Single Python process using asyncssh for SSH + a custom Textual SSHDriver for per-session I/O isolation. Textual handles layout, styling (via TCSS), and widgets. Content loaded from markdown files with YAML frontmatter. ASCII art pre-rendered at build time.

**Tech Stack:** Python 3.12+, Textual, asyncssh, python-frontmatter, ascii_magic, pytest

**Spec:** `docs/superpowers/specs/2026-03-12-terminal-portfolio-design.md`

**Critical path risk:** The custom SSHDriver (subclassing Textual's internal driver to route I/O through SSH channels) is the highest-risk piece. Phase 1 begins with a spike to validate this approach before building anything on top of it.

---

## Prerequisites

- Phase 0 (`ascii_player/` package) must be complete — see `docs/plans/2026-03-09-ascii-player-plan.md`
- Python 3.12+ with virtualenv active (`.venv/`)
- `pip install textual asyncssh python-frontmatter pytest pytest-asyncio`

---

## File Structure

```
my-tui-portfolio/
  app.py                     # Main Textual app — layout, navigation state machine, key bindings
  server.py                  # asyncssh SSH server — host key, session management, SSHDriver
  ssh_driver.py              # Custom Textual driver — routes I/O through SSH channel
  theme.tcss                 # Tokyo Night Dark theme (all styling)
  config.py                  # Section registry — maps section IDs to content paths, art paths, labels
  widgets/
    __init__.py
    ascii_panel.py           # Left panel widget — displays ANSI art, handles frame animation
    tab_bar.py               # Bottom navigation bar — renders tabs with active highlight
    content_panel.py         # Right panel widget — wraps Textual Markdown + scrolling
  content_loader.py          # Loads and parses markdown files with frontmatter
  content/
    TEMPLATE.md              # Schema reference + examples for all section types
    notice-board.md          # Bio text
    contact.md               # Links, email, socials
    sailing-instructions/
      _example.md            # Copy-paste starter (ignored by loader)
    rc-logs/
      _example.md
    experience/
      _example.md
  ascii_art/
    notice-board/            # 328 sailing video frames (Phase 3)
    sailing-instructions/    # Placeholder art
    rc-logs/                 # Placeholder art
    contact/                 # Placeholder art
    experience/              # Placeholder art
  scripts/
    build_ascii.py           # Build-time: convert images/video → ANSI text files
    provision.sh             # VPS setup script
  tests/
    __init__.py
    test_ssh_driver.py       # SSHDriver spike validation
    test_app.py              # App navigation, key bindings, state machine
    test_tab_bar.py          # TabBar rendering
    test_ascii_panel.py      # AsciiPanel art loading and swapping
    test_content_loader.py   # Frontmatter parsing, error handling, sorting
    test_content_panel.py    # Markdown rendering
    test_server.py           # Session limits, rate limiting, connection flow
  requirements.txt           # Pinned dependencies (pip freeze)
  pyproject.toml
```

**Design notes:**
- `ssh_driver.py` is separate from `server.py` because the driver subclasses Textual internals (unstable API) — isolating it makes it easy to update if Textual's driver interface changes.
- `config.py` maps section IDs to their content paths and art paths. This avoids per-section Python modules in v1 — the section-specific logic is just configuration. The `sections/` directory from the spec is deferred to future phases when interactive components need per-section code.
- `content_loader.py` is separate from `app.py` because content parsing is independently testable.
- Dependencies are pinned via `requirements.txt` (`pip freeze`) to prevent accidental breakage on deploy.

---

## Chunk 1: Phase 1 — SSH Server + Bare Layout

### Task 1: Project Setup + Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "diego-boats"
version = "0.1.0"
description = "SSH-accessible terminal portfolio at diego.boats"
requires-python = ">=3.12"
dependencies = [
    "textual>=0.47.0",
    "asyncssh>=2.14.0",
    "python-frontmatter>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "textual-dev>=1.0.0",
]
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: All packages install successfully

- [ ] **Step 3: Freeze pinned dependencies**

Run: `pip freeze > requirements.txt`
Expected: `requirements.txt` created with exact versions

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "chore: add project config with textual, asyncssh, frontmatter deps"
```

---

### Task 2: SSHDriver Spike (Critical Path — Validate Before Proceeding)

**Purpose:** Validate that Textual's driver can be subclassed to route I/O through an asyncssh channel. This is the highest-risk integration point. If this doesn't work, the entire architecture needs revisiting.

**Files:**
- Create: `ssh_driver.py`
- Create: `tests/test_ssh_driver.py`
- Create: `tests/__init__.py`

**Research first:** Before writing code, check:
1. Textual's current driver API — inspect `textual.drivers.linux_driver.LinuxDriver` in the installed version. Identify `write()`, `flush()`, and input-reading methods.
2. The xthulu project (github.com/haliphax/xthulu) for their SSH driver implementation.
3. Textual discussion #3493 for community approaches.

- [ ] **Step 1: Create test directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write spike test — validate driver can be instantiated with custom I/O**

```python
# tests/test_ssh_driver.py
"""
Spike test: validate that we can create a Textual driver that writes
to a custom stream instead of sys.stdout.

This test uses a StringIO buffer as a stand-in for an SSH channel.
If this fails, the SSHDriver approach needs rethinking.
"""
import io
import pytest


def test_ssh_driver_writes_to_custom_stream():
    """SSHDriver should write output to the provided stream, not sys.stdout."""
    from ssh_driver import SSHDriver

    buffer = io.BytesIO()
    driver = SSHDriver.create_for_test(output_stream=buffer)
    driver.write(b"\x1b[2J")  # ANSI clear screen
    driver.flush()
    assert buffer.getvalue() == b"\x1b[2J"


def test_ssh_driver_reports_terminal_size():
    """SSHDriver should report the terminal size from SSH PTY dimensions."""
    from ssh_driver import SSHDriver

    buffer = io.BytesIO()
    driver = SSHDriver.create_for_test(output_stream=buffer, size=(120, 40))
    width, height = driver.get_size()
    assert width == 120
    assert height == 40
```

- [ ] **Step 3: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_ssh_driver.py -v`
Expected: FAIL — `ssh_driver` module does not exist

- [ ] **Step 4: Implement SSHDriver**

After researching Textual's current driver internals, implement `ssh_driver.py`. The implementation will depend on what the driver API looks like in the installed Textual version. The key requirements are:

1. Output goes to a provided stream (SSH channel), not `sys.stdout`
2. Input is read from a provided stream, not `sys.stdin`
3. Terminal size is configurable (from SSH PTY dimensions)
4. Resize events can be triggered externally (from asyncssh window-change callback)

```python
# ssh_driver.py
"""
Custom Textual driver for SSH sessions.

Routes all I/O through an SSH channel instead of the process's
stdin/stdout. This is the critical integration piece between
asyncssh and Textual.

WARNING: This subclasses Textual's internal driver API, which is
not a stable public interface. Pin your Textual version and test
after any Textual upgrade.

Prior art: github.com/haliphax/xthulu, Textual discussion #3493
"""
# Implementation depends on Textual driver internals at time of coding.
# The spike test validates the approach works before we build on it.
# See research notes in Step 2 above.
```

**Important:** The actual implementation must be written after inspecting the installed Textual version's driver API. The spike test validates the approach. If the test cannot be made to pass, STOP and reassess — consider alternative approaches:
- Running Textual in a subprocess with stdin/stdout piped to the SSH channel
- Using `textual-web` as a reference for non-standard I/O
- Switching to Bubbletea (Go) as fallback

- [ ] **Step 5: Run test — expect PASS**

Run: `python3 -m pytest tests/test_ssh_driver.py -v`
Expected: PASS — driver writes to custom stream and reports correct size

- [ ] **Step 6: Integration smoke test — Textual app with SSHDriver**

Write a minimal integration test that runs a Textual app with the SSHDriver:

```python
# tests/test_ssh_driver.py (append)

@pytest.mark.asyncio
async def test_textual_app_renders_through_driver():
    """A minimal Textual app should produce output through the SSHDriver."""
    from textual.app import App
    from textual.widgets import Static
    from ssh_driver import SSHDriver

    class TestApp(App):
        def compose(self):
            yield Static("Hello SSH")

    buffer = io.BytesIO()
    app = TestApp()
    # Run app briefly with custom driver, verify output appeared in buffer
    # Exact API depends on Textual version — may need app.run() with driver param
    # or manual driver injection
    assert buffer.getvalue()  # Some output was written
```

- [ ] **Step 7: Run integration test — expect PASS**

Run: `python3 -m pytest tests/test_ssh_driver.py -v`
Expected: PASS — Textual app output goes through custom driver

**GATE: If the spike fails, do not proceed. Reassess architecture.**

- [ ] **Step 8: Commit**

```bash
git add ssh_driver.py tests/
git commit -m "feat: add SSHDriver spike — validates Textual I/O through SSH channel"
```

---

### Task 3: asyncssh Server Skeleton

**Files:**
- Create: `server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write test for server startup and connection acceptance**

```python
# tests/test_server.py
"""Tests for the asyncssh SSH server."""
import asyncio
import pytest
import asyncssh
from time import time


@pytest.fixture
async def portfolio_server(tmp_path):
    """Start the portfolio SSH server on a random port for testing."""
    from server import create_server

    server = await create_server(
        port=0, max_sessions=5, host_key_path=tmp_path / "host_key"
    )
    yield server
    server.close()
    await server.wait_closed()


@pytest.fixture
async def portfolio_server_full(tmp_path):
    """Start a server with max_sessions=1, then occupy that slot."""
    from server import create_server

    server = await create_server(
        port=0, max_sessions=1, host_key_path=tmp_path / "host_key"
    )
    # Occupy the one slot
    conn = await asyncssh.connect(
        "localhost", port=server.port, known_hosts=None, username="visitor"
    )
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
    # The one slot is occupied by the fixture — this connection should
    # receive the "harbor's full" message and be disconnected
    async with asyncssh.connect(
        "localhost",
        port=portfolio_server_full.port,
        known_hosts=None,
        username="visitor",
    ) as conn:
        chan = await conn.open_session(term_type="xterm")
        output = await asyncio.wait_for(chan.read(), timeout=5)
        assert "harbor" in output.lower() or "full" in output.lower()


@pytest.mark.asyncio
async def test_rate_limiting(tmp_path):
    """Should reject connections exceeding rate limit."""
    from server import _check_rate_limit, _ip_connections

    _ip_connections.clear()  # reset state
    ip = "192.168.1.100"

    # First 5 should pass
    for _ in range(5):
        assert _check_rate_limit(ip) is True

    # 6th should fail
    assert _check_rate_limit(ip) is False
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_server.py::test_server_accepts_connection -v`
Expected: FAIL — `server` module does not exist

- [ ] **Step 3: Implement server.py**

```python
# server.py
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
import sys
from pathlib import Path
from time import time
from collections import defaultdict

import asyncssh

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

        # TODO: Phase 1 Task 6 — wire up Textual app with SSHDriver here
        # For now, send placeholder text
        process.stdout.write("\x1b[2J\x1b[H")  # clear screen
        process.stdout.write("Welcome to diego.boats!\r\n")
        process.stdout.write("Portfolio coming soon...\r\n")
        process.stdout.write("Press q to quit.\r\n")

        # Idle timeout: disconnect after IDLE_TIMEOUT_SECONDS of no input
        # Note: rate-limit dict is in-memory only — resets on server restart,
        # so a burst of reconnects during restart could exceed limits briefly.
        while True:
            try:
                data = await asyncio.wait_for(
                    process.stdin.read(1024),
                    timeout=IDLE_TIMEOUT_SECONDS,
                )
                if not data or "q" in data:
                    break
            except asyncio.TimeoutError:
                process.stdout.write(
                    "\r\n  Idle too long — disconnecting in 30 seconds...\r\n"
                )
                try:
                    data = await asyncio.wait_for(
                        process.stdin.read(1024), timeout=30
                    )
                    if data:
                        continue  # User woke up, reset timeout
                except asyncio.TimeoutError:
                    break  # Final timeout — disconnect
    finally:
        _session_semaphore.release()
        process.exit(0)
```


def _ensure_host_key():
    """Generate ed25519 host key on first run, persist for TOFU."""
    HOST_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HOST_KEY_PATH.exists():
        key = asyncssh.generate_private_key("ssh-ed25519")
        HOST_KEY_PATH.write_bytes(key.export_private_key())
        HOST_KEY_PATH.chmod(0o600)
        logger.info("Generated new host key at %s", HOST_KEY_PATH)


async def create_server(
    port: int = 22,
    max_sessions: int = MAX_SESSIONS,
    host_key_path: Path = HOST_KEY_PATH,
):
    """Create and start the SSH server."""
    global MAX_SESSIONS, _session_semaphore, HOST_KEY_PATH
    MAX_SESSIONS = max_sessions
    HOST_KEY_PATH = host_key_path
    _session_semaphore = asyncio.Semaphore(max_sessions)

    _ensure_host_key()

    server = await asyncssh.create_server(
        PortfolioSSHServer,
        "",
        port,
        server_host_keys=[str(HOST_KEY_PATH)],
        process_factory=_handle_client,
    )
    actual_port = server.sockets[0].getsockname()[1]
    logger.info("SSH server listening on port %d (max %d sessions)", actual_port, MAX_SESSIONS)

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
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_server.py::test_server_accepts_connection -v`
Expected: PASS — server accepts SSH connection

- [ ] **Step 5: Manual smoke test**

```bash
# Terminal 1:
python3 server.py --port 2222

# Terminal 2:
ssh -p 2222 -o StrictHostKeyChecking=no localhost
# Expected: "Welcome to diego.boats!" message, q to quit
```

- [ ] **Step 6: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add asyncssh server with session limits and rate limiting"
```

---

### Task 4: Tokyo Night Dark Theme

**Files:**
- Create: `theme.tcss`

- [ ] **Step 1: Write the Textual CSS theme**

```css
/* theme.tcss — Tokyo Night Dark palette for diego.boats */

/* === Base === */
Screen {
    background: #1a1b26;
    color: #c0caf5;
}

/* === Layout containers === */
#main-container {
    layout: horizontal;
    height: 1fr;
}

#left-panel {
    width: 45%;
    height: 100%;
    border-right: solid #3b4261;
    overflow: hidden;
}

#right-panel {
    width: 55%;
    height: 100%;
    padding: 1 2;
    overflow-y: auto;
}

#footer-bar {
    dock: bottom;
    height: 3;
    background: #24283b;
    border-top: solid #3b4261;
    padding: 0 1;
}

/* === Tab bar === */
.tab {
    color: #565f89;
    padding: 0 1;
}

.tab--active {
    color: #7aa2f7;
    text-style: bold;
}

/* === Content typography === */
.section-header {
    color: #bb9af7;
    text-style: bold;
}

.tagline {
    color: #7dcfff;
}

.tag {
    color: #9ece6a;
}

.date {
    color: #e0af68;
}

.muted {
    color: #565f89;
}

.link {
    color: #7dcfff;
    text-style: underline;
}

.link-future {
    color: #f7768e;
}

/* === Key hints === */
.keyhint {
    color: #565f89;
}

.keyhint-key {
    color: #7dcfff;
    background: #3b4261;
}

/* === Markdown widget overrides === */
MarkdownH1 {
    color: #bb9af7;
    text-style: bold;
}

MarkdownH2 {
    color: #bb9af7;
}

MarkdownH3 {
    color: #7aa2f7;
}

Markdown {
    color: #c0caf5;
    background: #1a1b26;
}

/* === Help overlay === */
#help-overlay {
    background: #24283b;
    border: solid #3b4261;
    padding: 2 4;
    layer: overlay;
    width: 60;
    height: auto;
    offset-x: 50%;
    offset-y: 50%;
    margin: -15 -30;
}

/* === Small terminal warning === */
#size-warning {
    width: 100%;
    height: 100%;
    content-align: center middle;
    color: #e0af68;
    background: #1a1b26;
}
```

- [ ] **Step 2: Commit**

```bash
git add theme.tcss
git commit -m "feat: add Tokyo Night Dark theme (Textual CSS)"
```

---

### Task 5: Bare Split-Panel Layout + App Shell

**Files:**
- Create: `app.py`
- Create: `config.py`
- Create: `widgets/__init__.py`
- Create: `widgets/ascii_panel.py`
- Create: `widgets/tab_bar.py`
- Create: `widgets/content_panel.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write config.py — section registry**

```python
# config.py
"""
Section registry — maps section IDs to labels, content paths, and art paths.
Central configuration for the portfolio sections.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SectionConfig:
    id: str
    label: str
    short_label: str
    content_path: str  # relative to content/ dir
    art_path: str      # relative to ascii_art/ dir
    is_directory: bool  # True = list/detail, False = single file


SECTIONS: tuple[SectionConfig, ...] = (
    SectionConfig(
        id="notice-board",
        label="Notice Board",
        short_label="Notice Board",
        content_path="notice-board.md",
        art_path="notice-board",
        is_directory=False,
    ),
    SectionConfig(
        id="sailing-instructions",
        label="Sailing Instructions",
        short_label="Sailing Inst.",
        content_path="sailing-instructions",
        art_path="sailing-instructions",
        is_directory=True,
    ),
    SectionConfig(
        id="rc-logs",
        label="R/C Logs",
        short_label="R/C Logs",
        content_path="rc-logs",
        art_path="rc-logs",
        is_directory=True,
    ),
    SectionConfig(
        id="contact",
        label="Contact",
        short_label="Contact",
        content_path="contact.md",
        art_path="contact",
        is_directory=False,
    ),
    SectionConfig(
        id="experience",
        label="Experience",
        short_label="Experience",
        content_path="experience",
        art_path="experience",
        is_directory=True,
    ),
)
```

- [ ] **Step 2: Write failing test for App shell**

```python
# tests/test_app.py
"""Tests for the main portfolio TUI app."""
import pytest
from textual.testing import AppTest


@pytest.mark.asyncio
async def test_app_renders_split_layout():
    """App should render left panel, right panel, and footer."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        app = pilot.app
        assert app.query_one("#left-panel")
        assert app.query_one("#right-panel")
        assert app.query_one("#footer-bar")


@pytest.mark.asyncio
async def test_app_shows_size_warning_for_small_terminal():
    """App should show warning when terminal is too small."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp(), size=(60, 20)) as pilot:
        assert pilot.app.query_one("#size-warning")
```

- [ ] **Step 3: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: FAIL — `app` module does not exist

- [ ] **Step 4: Create widget stubs**

```bash
mkdir -p widgets
touch widgets/__init__.py
```

```python
# widgets/ascii_panel.py
"""Left panel widget — displays ASCII art or video frames."""
from textual.widgets import Static


class AsciiPanel(Static):
    """Displays ASCII art for the active section."""

    DEFAULT_CSS = """
    AsciiPanel {
        width: 100%;
        height: 100%;
        content-align: center middle;
        overflow: hidden;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("  ~ sailing art placeholder ~  ", **kwargs)

    def update_art(self, art_text: str) -> None:
        """Swap displayed ASCII art."""
        self.update(art_text)
```

```python
# widgets/tab_bar.py
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
            " [#7dcfff]←→[/] [#7dcfff]h/l[/] navigate  "
            "[#7dcfff]j/k[/] scroll  "
            "[#7dcfff]q[/] quit  "
            "[#7dcfff]?[/] help",
            classes="keyhint",
        )

    def watch_active_idx(self) -> None:
        """Reactive watcher — recompose when active tab changes."""
        self.recompose()

    def set_active(self, idx: int) -> None:
        """Update the active tab index (triggers recompose via reactive)."""
        self.active_idx = idx
```

```python
# widgets/content_panel.py
"""Right panel widget — renders markdown content with scrolling."""
from textual.widgets import Markdown


class ContentPanel(Markdown):
    """Displays markdown content for the active section."""

    DEFAULT_CSS = """
    ContentPanel {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("# Welcome\n\nContent loading...", **kwargs)

    def show_content(self, markdown_text: str) -> None:
        """Update displayed markdown content."""
        self.update(markdown_text)
```

- [ ] **Step 5: Implement app.py**

```python
# app.py
"""
Main Textual app for diego.boats terminal portfolio.

Split-panel layout: ASCII art on the left, markdown content on the right,
tab navigation along the bottom. Tokyo Night Dark theme.
"""
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from textual.binding import Binding

from config import SECTIONS
from widgets.ascii_panel import AsciiPanel
from widgets.tab_bar import TabBar
from widgets.content_panel import ContentPanel

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

    def action_scroll_down(self) -> None:
        """Scroll the right panel content down."""
        self.query_one("#right-panel").scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll the right panel content up."""
        self.query_one("#right-panel").scroll_up()

    def action_request_quit(self) -> None:
        """Quit only from top level. In detail view, go back instead."""
        if self._in_detail:
            self.action_go_back()
        else:
            self.exit()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_idx = 0
        self._in_detail = False

    def compose(self) -> ComposeResult:
        # Size warning (hidden when terminal is large enough)
        yield Static(
            "Terminal too small — please resize to at least 80x24",
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
```

- [ ] **Step 6: Run test — expect PASS**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: PASS

- [ ] **Step 7: Manual smoke test — run locally**

```bash
python3 app.py
# Expected: split-panel layout with Tokyo Dark theme
# Left panel: placeholder art text
# Right panel: "Notice Board" placeholder
# Footer: tab bar with Notice Board highlighted
# Press q to quit
```

- [ ] **Step 8: Commit**

```bash
git add app.py config.py widgets/ tests/test_app.py
git commit -m "feat: add split-panel layout with Tokyo Dark theme and placeholder content"
```

---

### Task 6: Wire SSH Server to Textual App

**Files:**
- Modify: `server.py` — replace placeholder text with Textual app

- [ ] **Step 1: Update server.py _handle_client to use SSHDriver + PortfolioApp**

Replace the placeholder section in `_handle_client` with:

```python
from app import PortfolioApp
from ssh_driver import SSHDriver

# In _handle_client, replace the placeholder block:
width = process.get_terminal_size()[0] or 80
height = process.get_terminal_size()[1] or 24

# Handle edge case: mosh or weird clients reporting 0x0
if width == 0:
    width = 80
if height == 0:
    height = 24

app = PortfolioApp()
driver = SSHDriver(
    app=app,
    output_stream=process.stdout,
    input_stream=process.stdin,
    size=(width, height),
)
await app.run_async(driver=driver)
```

- [ ] **Step 2: SSH smoke test**

```bash
# Terminal 1:
python3 server.py --port 2222

# Terminal 2:
ssh -p 2222 -o StrictHostKeyChecking=no localhost
# Expected: Full Textual TUI with split-panel layout and Tokyo Dark theme
# Press q to quit
```

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat: wire asyncssh server to Textual app via SSHDriver"
```

**Phase 1 validation complete:** `ssh -p 2222 localhost` shows themed split layout.

---

## Chunk 2: Phase 2 — Navigation + Tab Switching

### Task 7: Tab Navigation with Vim + Arrow Keys

**Files:**
- Modify: `app.py` — add number key bindings (1-5)
- Modify: `widgets/tab_bar.py` — proper re-rendering on tab change
- Create: `tests/test_tab_bar.py`

- [ ] **Step 1: Write failing test for tab switching**

```python
# tests/test_tab_bar.py
"""Tests for tab navigation."""
import pytest
from textual.testing import AppTest


@pytest.mark.asyncio
async def test_right_arrow_switches_to_next_tab():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        assert pilot.app._active_idx == 0
        await pilot.press("right")
        assert pilot.app._active_idx == 1


@pytest.mark.asyncio
async def test_left_arrow_switches_to_prev_tab():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("right")
        await pilot.press("right")
        assert pilot.app._active_idx == 2
        await pilot.press("left")
        assert pilot.app._active_idx == 1


@pytest.mark.asyncio
async def test_h_l_keys_switch_tabs():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("l")
        assert pilot.app._active_idx == 1
        await pilot.press("h")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_number_keys_jump_to_section():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("3")
        assert pilot.app._active_idx == 2
        await pilot.press("1")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_j_k_scroll_content():
    """j/k should scroll the right panel content."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        # Scrolling relies on Textual's built-in ScrollableContainer behavior
        # j/k are bound to scroll_down/scroll_up actions
        right_panel = pilot.app.query_one("#right-panel")
        await pilot.press("j")  # scroll down
        # Verify scroll position changed (exact API depends on Textual version)
        await pilot.press("k")  # scroll up


@pytest.mark.asyncio
async def test_q_in_detail_goes_back_not_quit():
    """Pressing q in detail view should go back, not disconnect."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("2")  # Sailing Instructions
        await pilot.press("enter")  # enter detail
        assert pilot.app._in_detail
        await pilot.press("q")
        assert not pilot.app._in_detail  # went back, didn't quit


@pytest.mark.asyncio
async def test_left_arrow_does_not_go_below_zero():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("left")
        assert pilot.app._active_idx == 0


@pytest.mark.asyncio
async def test_right_arrow_does_not_exceed_max():
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        for _ in range(10):
            await pilot.press("right")
        assert pilot.app._active_idx == 4  # 5 sections, max index 4
```

- [ ] **Step 2: Run test — expect FAIL** (number keys not bound yet)

Run: `python3 -m pytest tests/test_tab_bar.py -v`
Expected: Some tests FAIL — number key bindings missing

- [ ] **Step 3: Add number key bindings to app.py**

Add to `BINDINGS`:
```python
Binding("1", "jump_tab_1", show=False),
Binding("2", "jump_tab_2", show=False),
Binding("3", "jump_tab_3", show=False),
Binding("4", "jump_tab_4", show=False),
Binding("5", "jump_tab_5", show=False),
```

Add methods:
```python
def action_jump_tab_1(self) -> None: self._jump_to(0)
def action_jump_tab_2(self) -> None: self._jump_to(1)
def action_jump_tab_3(self) -> None: self._jump_to(2)
def action_jump_tab_4(self) -> None: self._jump_to(3)
def action_jump_tab_5(self) -> None: self._jump_to(4)

def _jump_to(self, idx: int) -> None:
    if not self._in_detail and 0 <= idx < len(SECTIONS):
        self._active_idx = idx
        self._refresh_section()
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_tab_bar.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_tab_bar.py
git commit -m "feat: add tab navigation with vim keys, arrow keys, and number jumps"
```

---

### Task 8: Help Overlay

**Files:**
- Modify: `app.py` — implement help overlay toggle
- Modify: `theme.tcss` — help overlay is already styled

- [ ] **Step 1: Write failing test**

```python
# tests/test_app.py (append)

@pytest.mark.asyncio
async def test_help_overlay_toggles():
    """Pressing ? should show help, pressing again should hide."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        # Help should be hidden initially
        assert not pilot.app.query_one("#help-overlay").display
        await pilot.press("question_mark")
        assert pilot.app.query_one("#help-overlay").display
        await pilot.press("question_mark")
        assert not pilot.app.query_one("#help-overlay").display
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_app.py::test_help_overlay_toggles -v`
Expected: FAIL — help overlay not in DOM yet

- [ ] **Step 3: Add help overlay to app.py compose()**

Add to `compose()`:
```python
yield Static(
    "# Keybindings\n\n"
    "  ← → h l   Switch sections\n"
    "  ↑ ↓ j k   Scroll content\n"
    "  1-5        Jump to section\n"
    "  Enter      Open item\n"
    "  ESC h      Go back\n"
    "  q          Quit\n"
    "  ?          Toggle this help\n",
    id="help-overlay",
)
```

Set `display = False` in `on_mount()`. Implement `action_toggle_help`:
```python
def action_toggle_help(self) -> None:
    overlay = self.query_one("#help-overlay")
    overlay.display = not overlay.display
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_app.py::test_help_overlay_toggles -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: add help overlay with keybinding reference"
```

**Phase 2 validation complete:** Can navigate all 5 sections with arrows/vim keys/numbers, help overlay toggles with ?.

---

## Chunk 3: Phase 3 — ASCII Art

### Task 8.5: Build ASCII Script + Shared Test Fixtures

**Files:**
- Create: `scripts/build_ascii.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create tests/conftest.py for shared fixtures**

```python
# tests/conftest.py
"""Shared test fixtures for the portfolio test suite."""
import pytest
from pathlib import Path


@pytest.fixture
def content_dir(tmp_path):
    """Create a temporary content directory with sample files."""
    content = tmp_path / "content"
    content.mkdir()
    (content / "notice-board.md").write_text("---\ntitle: Test Bio\n---\nHello")
    (content / "contact.md").write_text("---\ntitle: Contact\n---\nemail@test.com")

    projects = content / "sailing-instructions"
    projects.mkdir()
    (projects / "_example.md").write_text("---\ntitle: Skip\n---\n")
    (projects / "proj.md").write_text("---\ntitle: Proj\norder: 1\n---\nDetails")

    return content


@pytest.fixture
def art_dir(tmp_path):
    """Create a temporary ascii_art directory with placeholder files."""
    art = tmp_path / "ascii_art"
    for section in ["notice-board", "sailing-instructions", "rc-logs", "contact", "experience"]:
        d = art / section
        d.mkdir(parents=True)
        (d / "placeholder.txt").write_text(f"  ~ {section} art ~  ")
    return art
```

- [ ] **Step 2: Create scripts/build_ascii.py**

```python
#!/usr/bin/env python3
"""
Build-time script: convert source images/video to ANSI text files.

For video (Notice Board):
  Requires ascii_player to be built first. Copies pre-rendered frames
  from ascii_player cache to ascii_art/notice-board/.

For static images (other sections):
  Converts source images to ANSI text via ascii_magic.

Usage:
    python3 scripts/build_ascii.py                    # build all
    python3 scripts/build_ascii.py --section contact  # build one section
"""
import sys
from pathlib import Path

try:
    from ascii_magic import AsciiArt
    from ascii_magic.constants import Modes
except ImportError:
    print("ascii_magic not installed. Run: pip install ascii_magic pillow")
    sys.exit(1)

ART_ROOT = Path(__file__).parent.parent / "ascii_art"
COLUMNS = 60  # left panel width for static art


def build_static_art(section: str, image_path: Path) -> None:
    """Convert a single image to ANSI text."""
    output_dir = ART_ROOT / section
    output_dir.mkdir(parents=True, exist_ok=True)

    art = AsciiArt.from_image(str(image_path))
    ansi_text = art._img_to_art(columns=COLUMNS, mode=Modes.TERMINAL)
    (output_dir / "placeholder.txt").write_text(ansi_text)
    print(f"  Built {section}/placeholder.txt")


def main():
    print("Build ASCII art assets")
    print("=" * 40)
    print(f"Output: {ART_ROOT}")
    print()
    print("Note: For notice-board video frames, run:")
    print("  python3 -m ascii_player build sailing.MP4")
    print("  Then copy frames from cache to ascii_art/notice-board/")
    print()
    print("For static sections, place source images in ascii_art/<section>/source.jpg")
    print("and re-run this script.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add scripts/build_ascii.py tests/conftest.py
git commit -m "chore: add build_ascii script and shared test fixtures"
```

---

### Task 9: AsciiPanel — Load and Display Static Art

**Files:**
- Modify: `widgets/ascii_panel.py` — load ANSI text files from disk
- Create: `tests/test_ascii_panel.py`
- Create: `ascii_art/` placeholder files

- [ ] **Step 1: Create placeholder ASCII art files**

```bash
mkdir -p ascii_art/{notice-board,sailing-instructions,rc-logs,contact,experience}
```

For each non-video section, create a simple placeholder `.txt` file:

```python
# scripts/create_placeholders.py — run once
sections = ["sailing-instructions", "rc-logs", "contact", "experience"]
art = {
    "sailing-instructions": "  ⚓  COMPASS  ⚓  \n  ~ projects ~  ",
    "rc-logs":              "  📜  LOGBOOK  📜  \n  ~ writing ~  ",
    "contact":              "  🏴  FLAGS  🏴  \n  ~ signals ~  ",
    "experience":           "  ⛵  VOYAGE  ⛵  \n  ~ journey ~  ",
}
for name in sections:
    with open(f"ascii_art/{name}/placeholder.txt", "w") as f:
        f.write(art[name])
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_ascii_panel.py
"""Tests for AsciiPanel widget — art loading and swapping."""
import pytest
from pathlib import Path


def test_load_static_art(tmp_path):
    """Should load a .txt file as ANSI art string."""
    from widgets.ascii_panel import load_section_art

    art_dir = tmp_path / "test-section"
    art_dir.mkdir()
    (art_dir / "placeholder.txt").write_text("  test art  ")

    result = load_section_art(art_dir)
    assert result == "  test art  "


def test_load_static_art_missing_dir(tmp_path):
    """Should return fallback text for missing art directory."""
    from widgets.ascii_panel import load_section_art

    result = load_section_art(tmp_path / "nonexistent")
    assert "no art" in result.lower() or result.strip() != ""
```

- [ ] **Step 3: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_ascii_panel.py -v`
Expected: FAIL — `load_section_art` does not exist

- [ ] **Step 4: Implement art loading in ascii_panel.py**

Add to `widgets/ascii_panel.py`:
```python
from pathlib import Path

ART_ROOT = Path(__file__).parent.parent / "ascii_art"


def load_section_art(art_dir: Path) -> str:
    """Load the first .txt file from an art directory."""
    if not art_dir.exists():
        return "  ~ no art available ~  "
    txt_files = sorted(art_dir.glob("*.txt"))
    if not txt_files:
        return "  ~ no art available ~  "
    return txt_files[0].read_text()
```

- [ ] **Step 5: Run test — expect PASS**

Run: `python3 -m pytest tests/test_ascii_panel.py -v`
Expected: PASS

- [ ] **Step 6: Wire art loading into app.py _refresh_section**

Update `_refresh_section` to load real art:
```python
from widgets.ascii_panel import load_section_art, ART_ROOT

def _refresh_section(self) -> None:
    section = SECTIONS[self._active_idx]
    art_text = load_section_art(ART_ROOT / section.art_path)
    self.query_one("#left-panel", AsciiPanel).update_art(art_text)
    # ... rest of refresh
```

- [ ] **Step 7: Commit**

```bash
git add widgets/ascii_panel.py tests/test_ascii_panel.py ascii_art/ scripts/create_placeholders.py
git commit -m "feat: add ASCII art loading with placeholder art per section"
```

---

### Task 10: Video Frame Animation on Notice Board

**Files:**
- Modify: `widgets/ascii_panel.py` — add frame animation via Textual timer
- Modify: `tests/test_ascii_panel.py`

**Prerequisite:** `ascii_player/` must have built frames into `ascii_art/notice-board/`. For testing, use small mock frames.

- [ ] **Step 1: Write failing test for frame animation**

```python
# tests/test_ascii_panel.py (append)

def test_load_video_frames(tmp_path):
    """Should load multiple .txt frame files sorted numerically."""
    from widgets.ascii_panel import load_video_frames

    frames_dir = tmp_path / "video-section"
    frames_dir.mkdir()
    for i in range(5):
        (frames_dir / f"frame_{i:04d}.txt").write_text(f"frame {i}")

    frames = load_video_frames(frames_dir)
    assert len(frames) == 5
    assert frames[0] == "frame 0"
    assert frames[4] == "frame 4"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_ascii_panel.py::test_load_video_frames -v`
Expected: FAIL — `load_video_frames` does not exist

- [ ] **Step 3: Implement frame loading and animation**

Add to `widgets/ascii_panel.py`:
```python
def load_video_frames(frames_dir: Path) -> list[str]:
    """Load all .txt frame files from a directory, sorted by name."""
    if not frames_dir.exists():
        return []
    frame_files = sorted(frames_dir.glob("frame_*.txt"))
    return [f.read_text() for f in frame_files]
```

Update `AsciiPanel` class to support animation:
```python
class AsciiPanel(Static):
    DEFAULT_CSS = """..."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._frames: list[str] = []
        self._frame_idx: int = 0
        self._timer = None

    def start_animation(self, frames: list[str], fps: int = 24) -> None:
        """Start looping through video frames."""
        self.stop_animation()
        self._frames = frames
        self._frame_idx = 0
        if frames:
            self.update(frames[0])
            self._timer = self.set_interval(1.0 / fps, self._advance_frame)

    def stop_animation(self) -> None:
        """Stop frame animation."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._frames = []

    def _advance_frame(self) -> None:
        """Show next frame in the loop."""
        if self._frames:
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)
            self.update(self._frames[self._frame_idx])

    def update_art(self, art_text: str) -> None:
        """Show static art (stops any animation)."""
        self.stop_animation()
        self.update(art_text)
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_ascii_panel.py -v`
Expected: PASS

- [ ] **Step 5: Wire animation into app.py for Notice Board**

In `_refresh_section`, detect Notice Board and start animation:
```python
if section.id == "notice-board":
    frames = load_video_frames(ART_ROOT / section.art_path)
    if frames:
        panel.start_animation(frames, fps=24)
    else:
        panel.update_art("  ~ video frames not built yet ~  ")
else:
    art_text = load_section_art(ART_ROOT / section.art_path)
    panel.update_art(art_text)
```

- [ ] **Step 6: Manual smoke test**

```bash
python3 app.py
# Notice Board: video should loop (if frames exist)
# Switch tabs: art should change to static placeholders
# Switch back to Notice Board: video resumes
```

- [ ] **Step 7: Commit**

```bash
git add widgets/ascii_panel.py tests/test_ascii_panel.py app.py
git commit -m "feat: add video frame animation on Notice Board, static art on other sections"
```

**Phase 3 validation complete:** Video loops on Notice Board, static art shows on other sections, art swaps on tab change.

---

## Chunk 4: Phase 4 — Markdown Content Pipeline

### Task 11: Content Loader

**Files:**
- Create: `content_loader.py`
- Create: `tests/test_content_loader.py`

- [ ] **Step 1: Write failing tests for content loading**

```python
# tests/test_content_loader.py
"""Tests for markdown content loading with frontmatter."""
import pytest
from pathlib import Path


def test_load_single_file(tmp_path):
    """Should load a single markdown file and parse frontmatter."""
    from content_loader import load_single_content

    md_file = tmp_path / "test.md"
    md_file.write_text("---\ntitle: Hello\n---\n\nBody text here.")

    result = load_single_content(md_file)
    assert result.title == "Hello"
    assert "Body text here" in result.body


def test_load_single_file_missing_title(tmp_path):
    """Should use filename as fallback when title is missing."""
    from content_loader import load_single_content

    md_file = tmp_path / "my-post.md"
    md_file.write_text("---\ndate: 2026-01-01\n---\n\nNo title.")

    result = load_single_content(md_file)
    assert result.title == "my-post"


def test_load_directory(tmp_path):
    """Should load all .md files from a directory, skip _ prefixed."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "projects"
    content_dir.mkdir()
    (content_dir / "project-a.md").write_text(
        "---\ntitle: Project A\norder: 2\n---\nContent A"
    )
    (content_dir / "project-b.md").write_text(
        "---\ntitle: Project B\norder: 1\n---\nContent B"
    )
    (content_dir / "_example.md").write_text("---\ntitle: Skip Me\n---\n")

    results = load_directory_content(content_dir)
    assert len(results) == 2
    assert results[0].title == "Project B"  # order=1 first
    assert results[1].title == "Project A"  # order=2 second


def test_load_directory_empty(tmp_path):
    """Should return empty list for empty directory."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "empty"
    content_dir.mkdir()

    results = load_directory_content(content_dir)
    assert results == []


def test_load_single_file_invalid_frontmatter(tmp_path):
    """Should handle invalid YAML gracefully."""
    from content_loader import load_single_content

    md_file = tmp_path / "bad.md"
    md_file.write_text("---\n: invalid: yaml: {{{\n---\n\nBody.")

    # Should not raise — returns content with filename as title
    result = load_single_content(md_file)
    assert result is not None


def test_load_directory_sorts_by_date_fallback(tmp_path):
    """When order is missing, sort by date descending."""
    from content_loader import load_directory_content

    content_dir = tmp_path / "posts"
    content_dir.mkdir()
    (content_dir / "old.md").write_text(
        "---\ntitle: Old Post\ndate: 2025-01-01\n---\n"
    )
    (content_dir / "new.md").write_text(
        "---\ntitle: New Post\ndate: 2026-01-01\n---\n"
    )

    results = load_directory_content(content_dir)
    assert results[0].title == "New Post"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_content_loader.py -v`
Expected: FAIL — `content_loader` does not exist

- [ ] **Step 3: Implement content_loader.py**

```python
# content_loader.py
"""
Loads markdown content with YAML frontmatter.

Handles single files (notice-board.md, contact.md) and directories
(sailing-instructions/, experience/) with list/detail navigation.

Error handling:
- Invalid YAML: logs warning, uses filename as title, includes body
- Missing title: uses filename (without extension) as fallback
- Missing directory: returns empty list
- Broken markdown: passed through to Textual's Markdown widget as-is
  (Textual handles malformed markdown gracefully)
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import frontmatter

logger = logging.getLogger("diego.boats")


@dataclass(frozen=True)
class ContentItem:
    title: str
    description: str = ""
    body: str = ""
    tags: tuple[str, ...] = ()
    url: str = ""
    date: date | None = None
    order: int = 999


def load_single_content(file_path: Path) -> ContentItem:
    """Load a single markdown file with frontmatter."""
    try:
        post = frontmatter.load(str(file_path))
        meta = post.metadata
    except Exception:
        logger.warning("Invalid frontmatter in %s, using fallback", file_path)
        text = file_path.read_text()
        return ContentItem(
            title=file_path.stem,
            body=text,
        )

    return ContentItem(
        title=meta.get("title", file_path.stem),
        description=meta.get("description", ""),
        body=post.content,
        tags=tuple(meta.get("tags", [])),
        url=meta.get("url", ""),
        date=meta.get("date"),
        order=meta.get("order", 999),
    )


def load_directory_content(dir_path: Path) -> list[ContentItem]:
    """Load all .md files from a directory, skip _ prefixed, sort by order/date."""
    if not dir_path.exists():
        return []

    items = []
    for md_file in sorted(dir_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        items.append(load_single_content(md_file))

    # Sort by order first, then by date descending
    return sorted(
        items,
        key=lambda item: (
            item.order,
            -(item.date.toordinal() if item.date else 0),
        ),
    )
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_content_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add content_loader.py tests/test_content_loader.py
git commit -m "feat: add content loader with frontmatter parsing and error handling"
```

---

### Task 12: Content Templates + Sample Content

**Files:**
- Create: `content/TEMPLATE.md`
- Create: `content/notice-board.md`
- Create: `content/contact.md`
- Create: `content/sailing-instructions/_example.md`
- Create: `content/rc-logs/_example.md`
- Create: `content/experience/_example.md`

- [ ] **Step 1: Create content directory structure**

```bash
mkdir -p content/{sailing-instructions,rc-logs,experience}
```

- [ ] **Step 2: Write TEMPLATE.md**

```markdown
# Content Template Reference

This file documents the frontmatter schema for each section type.
The content loader reads .md files with YAML frontmatter.

## Rules
- Files starting with `_` are ignored (use for templates)
- `title` is required (filename used as fallback if missing)
- `order` controls sort order (lower = first, default 999)
- `date` is used as secondary sort (newer first) when order is equal

## Single-file sections (notice-board.md, contact.md)

---
title: "Section Title"
---

Markdown content here...

## Directory sections (sailing-instructions/, rc-logs/, experience/)

---
title: "Item Title"
description: "Short description shown in list view"
tags: ["Tag1", "Tag2"]
url: "https://example.com"
date: 2026-01-15
order: 1
---

Full markdown content shown in detail view...
```

- [ ] **Step 3: Write notice-board.md**

```markdown
---
title: "Diego Escobar"
---

## builder · sailor · maker

A developer who builds cool things and sails when the wind is right.

This portfolio is itself a project — an SSH-accessible TUI built with
Python and Textual, themed after the open water.
```

- [ ] **Step 4: Write contact.md**

```markdown
---
title: "Contact"
---

## Signal Flags

- **GitHub**: github.com/diego
- **Email**: hello@diego.boats
- **LinkedIn**: linkedin.com/in/diego
```

- [ ] **Step 5: Write _example.md files for each directory section**

```markdown
# content/sailing-instructions/_example.md
---
title: "Project Name"
description: "One-line description"
tags: ["Python", "Textual"]
url: "https://github.com/diego/project"
date: 2026-01-15
order: 1
---

Full project writeup here.
```

```markdown
# content/rc-logs/_example.md
---
title: "Post Title"
description: "Short preview"
date: 2026-01-15
order: 1
---

Full writing here.
```

```markdown
# content/experience/_example.md
---
title: "Role Title — Company"
description: "Brief role summary"
date: 2026-01-15
order: 1
---

- Key achievement one
- Key achievement two
```

- [ ] **Step 6: Commit**

```bash
git add content/
git commit -m "feat: add content templates and sample markdown files"
```

---

### Task 13: Wire Content Pipeline into App

**Files:**
- Modify: `app.py` — load real content on section switch
- Modify: `widgets/content_panel.py` — support list view and detail view

- [ ] **Step 1: Write failing test for content display**

```python
# tests/test_app.py (append)

@pytest.mark.asyncio
async def test_app_loads_content_on_tab_switch():
    """Switching tabs should load the section's markdown content."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        # Notice Board should show bio content
        content = pilot.app.query_one("#right-panel")
        # After switching to a section, content should update
        await pilot.press("right")  # Sailing Instructions
        # Content panel should have updated (exact assertion depends on content)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_app.py::test_app_loads_content_on_tab_switch -v`

- [ ] **Step 3: Update app.py to load content**

Add content loading to `on_mount` and `_refresh_section`:

```python
from content_loader import load_single_content, load_directory_content, ContentItem

CONTENT_ROOT = Path(__file__).parent / "content"

def on_mount(self) -> None:
    self._check_size()
    self._load_all_content()
    self._refresh_section()

def _load_all_content(self) -> None:
    """Load all content from disk on startup."""
    self._content: dict[str, ContentItem | list[ContentItem]] = {}
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
    section = SECTIONS[self._active_idx]
    content = self._content.get(section.id)
    panel = self.query_one("#right-panel", ContentPanel)

    if isinstance(content, list):
        # Directory section — show list view
        if not content:
            panel.show_content(f"# {section.label}\n\nNo content yet.")
        else:
            md = f"# {section.label}\n\n"
            for item in content:
                md += f"**{item.title}**\n"
                if item.description:
                    md += f"{item.description}\n"
                if item.tags:
                    md += f"*{', '.join(item.tags)}*\n"
                md += "\n"
            panel.show_content(md)
    else:
        # Single file section
        panel.show_content(f"# {content.title}\n\n{content.body}")

    # Update art panel (existing code)
    # Update tab bar (existing code)
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py widgets/content_panel.py
git commit -m "feat: wire markdown content pipeline into app with list/detail views"
```

---

### Task 14: List → Detail Navigation

**Files:**
- Modify: `app.py` — add Enter/ESC navigation for detail views

- [ ] **Step 1: Write failing test for detail navigation**

```python
# tests/test_app.py (append)

@pytest.mark.asyncio
async def test_enter_opens_detail_view():
    """Enter should open detail view for directory sections."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        # Navigate to a directory section (Sailing Instructions)
        await pilot.press("2")
        assert not pilot.app._in_detail
        await pilot.press("enter")
        assert pilot.app._in_detail


@pytest.mark.asyncio
async def test_escape_returns_from_detail():
    """ESC should return from detail view to list."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("2")
        await pilot.press("enter")
        assert pilot.app._in_detail
        await pilot.press("escape")
        assert not pilot.app._in_detail


@pytest.mark.asyncio
async def test_escape_does_nothing_at_top_level():
    """ESC at top level should not disconnect."""
    from app import PortfolioApp

    async with AppTest.from_app(PortfolioApp()) as pilot:
        await pilot.press("escape")
        # App should still be running
        assert pilot.app._active_idx == 0
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python3 -m pytest tests/test_app.py -v`

- [ ] **Step 3: Implement detail navigation in app.py**

Add bindings and state management:
```python
Binding("enter", "open_item", show=False),
Binding("escape", "go_back", show=False),
```

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._active_idx = 0
    self._in_detail = False
    self._selected_item_idx = 0  # which list item is selected

def action_open_item(self) -> None:
    """Open selected item in detail view (directory sections only)."""
    section = SECTIONS[self._active_idx]
    content = self._content.get(section.id)
    if isinstance(content, list) and content and not self._in_detail:
        self._in_detail = True
        item = content[self._selected_item_idx]
        panel = self.query_one("#right-panel", ContentPanel)
        panel.show_content(f"# {item.title}\n\n{item.body}")

def action_go_back(self) -> None:
    """Go back from detail view to list. Does nothing at top level."""
    if self._in_detail:
        self._in_detail = False
        self._selected_item_idx = 0
        self._refresh_section()
```

Also update `action_prev_tab` to use `action_go_back` when `h` is pressed in detail:
```python
def action_prev_tab(self) -> None:
    if self._in_detail:
        self.action_go_back()
        return
    if self._active_idx > 0:
        self._active_idx -= 1
        self._refresh_section()
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: PASS

- [ ] **Step 5: Manual smoke test**

```bash
python3 app.py
# Navigate to Sailing Instructions (2)
# Press Enter to open first item
# Press ESC to go back to list
# Press q to quit
```

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: add list/detail navigation with Enter and ESC/h"
```

**Phase 4 validation complete:** Content loads from markdown, list → detail works, edit markdown and restart to see changes.

---

## Chunk 5: Phase 5 — Visual Polish + Phase 6 — Deployment

### Task 15: Visual Polish

**Files:**
- Modify: `theme.tcss` — refinements
- Modify: `widgets/tab_bar.py` — box-drawing borders
- Modify: `app.py` — figlet-style banner on Notice Board

- [ ] **Step 1: Add figlet-style banner for Notice Board header**

Install pyfiglet: `pip install pyfiglet` and add to pyproject.toml dependencies.

In `_refresh_section`, when on Notice Board, prepend a figlet banner:
```python
import pyfiglet

def _format_notice_board(self, content: ContentItem) -> str:
    banner = pyfiglet.figlet_format("DIEGO", font="slant")
    return f"```\n{banner}```\n\n{content.body}"
```

- [ ] **Step 2: Refine theme.tcss — adjust padding, borders, spacing**

Review and adjust based on actual terminal rendering. Key tweaks:
- Ensure panel divider is visible
- Adjust footer padding
- Ensure markdown headers render in correct colors

- [ ] **Step 3: Test in multiple terminals**

```bash
# Test in each terminal emulator available:
# Ghostty, iTerm2, Terminal.app, kitty, Alacritty
python3 app.py
# Verify: colors render correctly, layout is clean, no visual artifacts
```

- [ ] **Step 4: Commit**

```bash
git add theme.tcss widgets/ app.py pyproject.toml
git commit -m "feat: visual polish — figlet banner, refined borders and spacing"
```

- [ ] **Step 5: Freeze updated requirements**

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update pinned dependencies"
```

---

### Task 16: VPS Provisioning Script

**Files:**
- Create: `scripts/provision.sh`

- [ ] **Step 1: Write provision script**

```bash
#!/bin/bash
# provision.sh — Run on the Hetzner VPS as root
# Sets up diego.boats terminal portfolio
set -euo pipefail

echo "=== diego.boats VPS provisioning ==="

# Move system SSH to port 2222
sed -i 's/^#Port 22$/Port 2222/' /etc/ssh/sshd_config
sed -i 's/^Port 22$/Port 2222/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall
ufw allow 22/tcp    # TUI SSH
ufw allow 2222/tcp  # Admin SSH
ufw --force enable

# Install Python 3.12+
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# Clone repo
git clone https://github.com/YOUR_USERNAME/my-tui-portfolio.git /app
cd /app

# Create venv and install deps
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Generate host key
mkdir -p .ssh
.venv/bin/python3 -c "
import asyncssh
key = asyncssh.generate_private_key('ssh-ed25519')
open('.ssh/host_key', 'wb').write(key.export_private_key())
import os; os.chmod('.ssh/host_key', 0o600)
print('Host key generated')
"

# Systemd service
cat > /etc/systemd/system/portfolio.service << 'EOF'
[Unit]
Description=diego.boats terminal portfolio
After=network.target

[Service]
WorkingDirectory=/app
ExecStart=/app/.venv/bin/python3 server.py --port 22
Restart=always
RestartSec=5
User=root
Environment=MAX_SESSIONS=50

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable portfolio
systemctl start portfolio

# Fail2ban
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
port = 2222
enabled = true

[portfolio]
port = 22
enabled = true
filter = sshd
EOF
systemctl restart fail2ban

echo "=== Done. Run: systemctl status portfolio ==="
echo "=== Admin SSH on port 2222 ==="
```

- [ ] **Step 2: Commit**

```bash
git add scripts/provision.sh
chmod +x scripts/provision.sh
git commit -m "chore: add VPS provisioning script"
```

---

### Task 17: Deploy + DNS

**Manual steps (not automated):**

- [ ] **Step 1: Create Hetzner VPS**
  - Hetzner Cloud → New Server
  - Ubuntu 22.04, CAX11 (ARM, ~€3.29/mo)
  - Add your SSH public key during setup
  - Note the server IP

- [ ] **Step 2: Run provision script**
```bash
scp scripts/provision.sh root@<VPS_IP>:/root/
ssh root@<VPS_IP> "bash /root/provision.sh"
```

- [ ] **Step 3: Verify service is running**
```bash
ssh -p 2222 root@<VPS_IP> "systemctl status portfolio"
```

- [ ] **Step 4: Test SSH connection to TUI**
```bash
ssh -o StrictHostKeyChecking=no <VPS_IP>
# Expected: full TUI portfolio
```

- [ ] **Step 5: Configure DNS**
  - Vercel DNS → diego.boats
  - Add A record: `@` → `<VPS_IP>`, TTL 300

- [ ] **Step 6: Wait for DNS propagation and test**
```bash
dig diego.boats A +short
# Expected: <VPS_IP>

ssh diego.boats
# Expected: full TUI portfolio
```

- [ ] **Step 7: Increase DNS TTL**
  - Change TTL from 300 to 3600 once stable

**Phase 6 validation complete:** `ssh diego.boats` works end-to-end.

---

## Testing Strategy Summary

| Phase | What's Tested | How |
|-------|--------------|-----|
| 1 | SSHDriver I/O routing, server connection acceptance | pytest unit + integration tests against real asyncssh connection |
| 2 | Tab switching (arrows, vim, numbers), help overlay | Textual AppTest simulated key presses |
| 3 | Art file loading, frame animation start/stop | pytest unit tests with tmp_path fixtures |
| 4 | Frontmatter parsing, content sorting, error handling, list/detail nav | pytest unit tests + AppTest integration |
| 5 | Visual rendering across terminal emulators | Manual verification |
| 6 | End-to-end SSH connection to VPS | Manual `ssh diego.boats` |
