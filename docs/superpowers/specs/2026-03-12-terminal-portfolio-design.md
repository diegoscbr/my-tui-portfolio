# Terminal Portfolio — diego.boats Design Doc

Date: 2026-03-12
Status: Draft

---

## Overview

An SSH-accessible terminal portfolio at `diego.boats`. Visitors run `ssh diego.boats` and get a split-panel TUI with a sailing theme and Tokyo Night Dark color palette. Left panel shows ASCII art that changes per section (looping video on home, placeholder art on others — evolving into custom animations and interactive components). Right panel displays markdown-driven content. Five sailing-themed sections with vim-style and arrow key navigation.

Built entirely in Python with Textual for the TUI framework and asyncssh for SSH serving. The SSH server uses asyncssh to accept connections, allocates a PTY per session, and pipes I/O into an isolated Textual app instance. ASCII art is pre-rendered at build time using ascii_magic (the `ascii_player/` package is a prerequisite that must be built first — see Phase 0 in Build Phases).

---

## Architecture

```
Visitor → ssh diego.boats → DNS (A record) → Hetzner VPS (port 22)
  → asyncssh server (server.py)
    → accepts connection, allocates PTY
    → spawns isolated Textual app per session
      → pipes stdin/stdout through SSH channel
      → loads pre-rendered ANSI frames from disk
      → loads markdown content from content/ directory
      → renders split-panel TUI with Tokyo Dark theme
```

Single Python runtime, single process. No Go, no Node.js. Each SSH session creates a new Textual `App` object instance within the same process — a custom `SSHDriver` isolates each session's I/O to its SSH channel (no subprocess spawning).

**Key components:**

| Component | Role |
|-----------|------|
| asyncssh (`server.py`) | SSH connections, PTY allocation, host key management, session isolation |
| Textual app (`app.py`) | Main TUI application with CSS-based layout |
| ASCII pipeline (`ascii_player/`) | Build-time frame pre-rendering (prerequisite — must be built first) |
| Content pipeline | Markdown files with YAML frontmatter in `content/` |
| Tokyo Dark theme (`theme.tcss`) | Textual CSS using Tokyo Night palette |

---

## TUI Layout

```
+----------------------------------+----------------------------------+
|                                  |                                  |
|  LEFT PANEL (~45%)               |  RIGHT PANEL (~55%)              |
|  ASCII art / video               |  Content from markdown           |
|                                  |                                  |
|  Art changes per section:        |  Section-specific content        |
|  - Notice Board: sailing video   |  rendered from .md files         |
|  - Sailing Inst.: [art]          |  with scrolling via j/k          |
|  - R/C Logs: [art]              |                                  |
|  - Contact: [art]               |                                  |
|  - Experience: [art]            |                                  |
|                                  |                                  |
+----------------------------------+----------------------------------+
| Notice Board | Sailing Inst. | R/C Logs | Contact | Experience     |
| [← → h/l navigate]  [j/k scroll]  [q quit]  [? help]             |
+------------------------------------------------------------------+
```

**Layout details:**
- Left panel: ~45% width, displays ASCII art/video for active section
- Right panel: ~55% width, scrollable content area
- Vertical divider: box-drawing character between panels
- Footer bar: tab labels with active tab highlighted, keybinding hints
- Minimum terminal: 80 columns, 24 rows. Smaller terminals get a centered message: "Terminal too small — please resize to at least 80x24" and the app re-renders automatically when the terminal meets the minimum.

**Textual implementation:**
- Main app uses a `Horizontal` container for the two panels
- Left panel is a custom `AsciiArtWidget` (swaps content on tab change)
- Right panel uses Textual's built-in `Markdown` widget inside a `ScrollableContainer` for rendering content. Custom TCSS rules style markdown elements (headers, code blocks, links) to match Tokyo Night palette.
- Footer is a custom `TabBar` widget with `Static` text labels
- All styling via `theme.tcss` — no inline colors

---

## Sections

| Tab | Left Panel Art | Right Panel Content |
|-----|---------------|-------------------|
| Notice Board | Looping sailing video (24fps, 328 frames) | Bio / introduction |
| Sailing Instructions | Placeholder art (later: animation) | Projects list → detail |
| R/C Logs | Placeholder art (later: animation) | Writing list → detail |
| Contact | Placeholder art (later: animation) | Links, email, socials |
| Experience | Placeholder art (later: animation) | Work history list → detail |

---

## Navigation

Both vim-style and arrow key bindings work interchangeably:

| Action | Keys |
|--------|------|
| Switch tabs | `←/→` or `h/l` (only at top-level, not inside detail view) |
| Scroll content | `↑/↓` or `j/k` |
| Jump to section | `1-5` |
| Open list item | `Enter` |
| Go back from detail | `ESC` or `h` (returns to list, never disconnects) |
| Help overlay | `?` |
| Quit / disconnect | `q` (only key that disconnects — requires top-level context) |

**Navigation state machine:** The app tracks whether the user is at the top level (section list) or in a detail view. `h/l` switch tabs only at the top level. Inside a detail view, `h` goes back to the list. `q` always disconnects regardless of context. `ESC` goes back one level — from detail to list, from list it does nothing (prevents accidental disconnect).

---

## Content Pipeline

### Directory Structure

```
content/
  TEMPLATE.md               # Schema reference + examples for all section types
  notice-board.md            # Bio text
  contact.md                 # Links, email, socials
  sailing-instructions/      # One .md per project
    _example.md              # Copy-paste starter (ignored by content loader)
    project-one.md
  rc-logs/                   # One .md per writing piece
    _example.md
    reflection-one.md
  experience/                # One .md per role
    _example.md
    role-one.md
```

### Frontmatter Format

```yaml
---
title: "Cool Project"
description: "A brief summary"
tags: ["Python", "Textual", "SSH"]
url: "https://github.com/diego/cool-project"
date: 2026-01-15
order: 1
---

Full markdown content here...
```

### Content Loading

- On startup, the app scans `content/` and parses frontmatter with `python-frontmatter`
- Single-file sections (`notice-board.md`, `contact.md`) render directly
- Directory sections (`sailing-instructions/`, `experience/`) show a list view
- Selecting a list item drills into the full content
- List items sorted by `order` field (fallback to `date`)
- Files starting with `_` are ignored (used for templates/examples)
- Content changes require a server restart (no hot-reload in v1)
- **Error handling:** Invalid YAML frontmatter logs a warning and skips the file. Missing required fields (`title`) use the filename as fallback. Empty `content/` directory renders a "no content yet" placeholder per section.

---

## Tokyo Night Dark Theme

Exact Tokyo Night Dark palette applied via Textual CSS (`theme.tcss`).

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#1a1b26` | Main background |
| Surface | `#24283b` | Footer, cards, panels |
| Foreground | `#c0caf5` | Body text |
| Blue | `#7aa2f7` | Active tab, ASCII art tint |
| Cyan | `#7dcfff` | Taglines, secondary highlights |
| Purple | `#bb9af7` | Headings, names, decorative |
| Green | `#9ece6a` | Tags, tech stack labels |
| Yellow | `#e0af68` | Dates, metadata |
| Red | `#f7768e` | Linkable text (future) |
| Muted | `#565f89` | Inactive tabs, help text, dividers |
| Border | `#3b4261` | Panel dividers, box-drawing |

### Application

- Background: `#1a1b26` everywhere
- Panel divider: `#3b4261` box-drawing characters
- Active tab: `#7aa2f7` bold, inactive tabs: `#565f89`
- Section headers: `#bb9af7`
- Body text: `#c0caf5`
- Tags/tech stack: `#9ece6a`
- URLs/links: `#7dcfff`
- Dates: `#e0af68`
- Help text/keybinding hints: `#565f89`
- Future linkable text: `#f7768e`

---

## ASCII Art Pipeline

### Build Time

Pre-rendered ANSI text files organized per section in `ascii_art/`:

```
ascii_art/
  notice-board/         # 328 sailing video frames (pre-rendered ANSI)
  sailing-instructions/ # Placeholder image(s)
  rc-logs/              # Placeholder image(s)
  contact/              # Placeholder image(s)
  experience/           # Placeholder image(s)
```

- Sailing video frames converted using `ascii_player/` pipeline (must be built as Phase 0 prerequisite — see `docs/plans/2026-03-09-ascii-player-plan.md`)
- Static images converted via `ascii_magic` with `Modes.TERMINAL` (256-color)
- `scripts/build_ascii.py` handles all conversions
- Output stored on disk, loaded at runtime

### Runtime

- Notice Board: loads all frames into memory, loops at 24fps via Textual timer. At ~5-15KB per frame x 328 frames ≈ 2-5MB per session. Frames are loaded once into a shared read-only list; all concurrent sessions reference the same frame data (no duplication).
- Other sections: loads single ANSI text file, displays statically
- Art swaps instantly on tab change (pre-loaded in shared memory at startup)

### Future Evolution

1. Static placeholder images (Phase 3)
2. Looping ASCII animations per section (custom video clips)
3. Interactive game-like ASCII components

---

## SSH Server & Session Management

### asyncssh Server (`server.py`)

The SSH server uses `asyncssh` to handle inbound connections. Each session creates a new Textual `App` object instance within the same Python process (no subprocesses) — isolation comes from a custom driver that routes I/O to the SSH channel.

**Custom SSHDriver (critical integration piece):**

Textual's default drivers read from the process's own stdin/stdout. For SSH serving, a custom `SSHDriver` is required that subclasses `textual.drivers.linux_driver.LinuxDriver` and:
- Overrides `write()` and `flush()` to write to the SSH channel instead of `sys.stdout`
- Reads input from the SSH channel's stdin instead of `sys.stdin`
- Forwards terminal resize events from asyncssh's window-change callback to Textual's resize handler

**Prior art:** The `xthulu` project (github.com/haliphax/xthulu) implements this pattern. Textual discussion #3493 also covers SSH driver integration.

**Connection flow:**

1. asyncssh accepts connection (no authentication — public portfolio)
2. Client requests a PTY — server records terminal dimensions
3. Client requests a shell — server creates a new `App` instance with the custom `SSHDriver`
4. `SSHDriver` pipes all I/O through the SSH channel
5. Window-change events forwarded to Textual's resize handler
6. On disconnect — Textual app instance is cleaned up

```python
# Conceptual structure (not final implementation)
class PortfolioSSHServer(asyncssh.SSHServer):
    def begin_auth(self, username): return False  # no auth required

class SSHDriver(LinuxDriver):
    """Custom Textual driver that routes I/O through an SSH channel."""
    def write(self, data): self._ssh_channel.write(data)
    # Input read from SSH channel stdin, not sys.stdin

class PortfolioProcess(asyncssh.SSHServerProcess):
    def shell_requested(self):
        app = PortfolioApp()
        app.run(driver=SSHDriver, channel=self._chan)
```

- Host key: ed25519, generated on first run via `asyncssh.generate_private_key('ssh-ed25519')`, persisted at `.ssh/host_key`
- Listens on port 22

### Session Limits (implemented in `server.py`)

- **Max sessions**: 20-50 concurrent (configurable via `MAX_SESSIONS` env var). Tracked via an atomic counter incremented on connect, decremented on disconnect.
- **Over capacity**: friendly ASCII art "harbor's full" message sent to the SSH channel, then graceful disconnect.
- **Idle timeout**: 10 minutes of no input → warning message, then disconnect after 30 more seconds. Implemented via asyncio timer reset on each input event.
- **Rate limiting**: max 5 connections per IP per minute. Tracked via an in-memory dict of `{ip: [timestamps]}`, cleaned up via an asyncio background task every 60 seconds that prunes entries older than 1 minute.

### Security

- No shell access — the SSH server only serves the TUI, never a login shell
- Read-only experience — visitors cannot write to the filesystem
- System SSH daemon on port 2222 for admin access
- Fail2ban configured for both port 22 (TUI) and port 2222 (admin)

### Logging

- Connection events: IP, connect/disconnect time, session duration
- Errors: SSH handshake failures, Textual app crashes
- Logged to stdout (captured by systemd journal)
- No visitor PII stored beyond IP addresses

---

## Deployment

### Hetzner VPS

- Provider: Hetzner (CAX11 ARM, ~€3.29/mo)
- OS: Ubuntu
- Python 3.12+ (minimum version — local dev may use 3.14, VPS uses system package)
- systemd service for auto-restart and persistence
- UFW firewall: allow port 22 (TUI SSH), allow port 2222 (admin SSH), deny rest
- System sshd reconfigured to listen on port 2222

### DNS

- `diego.boats` A record pointing to VPS IP via Vercel DNS
- TTL: 300 seconds during setup, 3600 once stable

### Deployment Workflow

- Code in GitHub repository
- Deploy via `git pull` + `systemctl restart portfolio` on VPS
- ASCII art pre-generated locally or in CI, committed to repo
- Content updates (markdown) trigger a restart

---

## Project Structure

```
my-tui-portfolio/
  app.py                     # Main Textual app entry point
  server.py                  # asyncssh SSH server — spawns Textual app per connection
  theme.tcss                 # Tokyo Night Dark theme (Textual CSS)
  widgets/
    ascii_panel.py           # Left panel — swaps ASCII art per section
    tab_bar.py               # Bottom navigation bar
    content_panel.py         # Right panel — markdown renderer + scrolling
  sections/
    notice_board.py          # Home screen logic
    sailing_instructions.py  # Projects list/detail
    rc_logs.py               # Writing list/detail
    contact.py               # Links & socials
    experience.py            # Work history list/detail
  content/
    TEMPLATE.md              # Schema reference + examples
    notice-board.md          # Bio text
    contact.md               # Links
    sailing-instructions/    # One .md per project
      _example.md
    rc-logs/                 # One .md per writing piece
      _example.md
    experience/              # One .md per role
      _example.md
  ascii_art/
    notice-board/            # Sailing video frames
    sailing-instructions/    # Placeholder art
    rc-logs/                 # Placeholder art
    contact/                 # Placeholder art
    experience/              # Placeholder art
  ascii_player/              # Existing build pipeline
  scripts/
    build_ascii.py           # Build-time image/video → ANSI conversion
    provision.sh             # VPS setup script
  tests/
    test_app.py
    test_widgets.py
    test_sections.py
    test_content.py
  docs/
    ideas/
    plans/
    superpowers/specs/
  requirements.txt
  pyproject.toml
```

---

## Iterative Build Phases

| Phase | Scope | Validation |
|-------|-------|-----------|
| 0 | Build `ascii_player/` package (prerequisite — see `docs/plans/2026-03-09-ascii-player-plan.md`) | `python3 -m ascii_player build sailing.MP4` produces cached frames |
| 1 | asyncssh server + bare split-panel layout with placeholder text, Tokyo Dark theme | `ssh localhost` shows themed split layout |
| 2 | Tab bar with 5 sections, vim + arrow navigation, `?` help overlay, both panels swap placeholder content | Can navigate all 5 sections, scroll content |
| 3 | Sailing video on Notice Board left panel, static placeholder images on other sections, art swaps on tab change | Video loops smoothly, art changes per section |
| 4 | Markdown content pipeline, frontmatter parsing, list → detail navigation, `TEMPLATE.md` and `_example.md` files | Edit markdown, restart, see changes |
| 5 | Figlet banner text, box-drawing borders, refined spacing, color fine-tuning | Looks production-ready in multiple terminals |
| 6 | Hetzner VPS, systemd service, DNS `diego.boats` A record | `ssh diego.boats` works end-to-end |

---

## Future Enhancements (Out of Scope for v1)

- **Custom ASCII animations**: unique looping video per section (replace placeholder art)
- **Interactive ASCII components**: game-like interactive elements per section
- **Linkable highlighted text**: red-highlighted text that opens URLs in browser on Enter
- **Hot-reload**: file watcher for content changes without restart
- **Analytics**: visitor counts, session duration, navigation paths
- **Mobile SSH clients**: graceful degradation for Termius/Blink on iOS/Android

---

## Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| TUI framework | Textual (Python) | Single language with ASCII pipeline, CSS-like theming, direct ANSI control |
| SSH server | asyncssh | Mature async SSH library, clean integration with Textual's asyncio event loop |
| Theme | Tokyo Night Dark (exact palette) | Clean, modern dark theme that complements nautical sailing theme |
| Layout | Split-panel on all screens | Distinctive look, ASCII art as constant visual element |
| ASCII art | Changes per section | Each section has its own visual identity |
| Navigation | Vim keys + arrow keys | Developer-friendly with universal fallback |
| Content | Markdown with YAML frontmatter | Easy to update, no database, structured metadata |
| Hosting | Hetzner VPS (€3.29/mo) | Reliable, cheap, no home networking hassles |
| Build approach | Iterative (6 phases) | Validate UI/server at each point |
