# Terminal Portfolio — diego.boats Design Doc

Date: 2026-03-08

## Overview

A terminal-based interactive portfolio accessible by SSHing into `diego.boats`.
Visitors get a full TUI experience with a sailing regatta theme, built on
Wish (Go SSH server) and Ink (React for CLIs).

---

## Architecture

```
Hetzner VPS (Ubuntu, ~€3.29/mo)
  |
  +-- Wish SSH server (port 22)
        |
        +-- spawns per connection --> Node.js Ink TUI process
```

- **Wish** handles SSH host key generation, storage, and connection management automatically.
- Each SSH connection gets its own isolated Ink process — no shared state between visitors.
- **Domain**: `diego.boats` (Vercel DNS) — one A record pointing to the VPS IP.
  `ssh diego.boats` works out of the box.
- Python (`ascii_magic`, `Pillow`) is only needed on the build machine, not the VPS.

---

## TUI Layout

```
+---------------------------+-----------------------------+
|                           |                             |
|  sailing ASCII video      |  DIEGO                      |
|  (looping, left panel)    |  ~~~~~                      |
|                           |  builder · sailor · maker   |
|                           |                             |
|                           |  [bio text]                 |
|                           |                             |
+---------------------------+-----------------------------+
|  Notice Board   Sailing Instructions   R/C Logs   Contact   Experience  |
|  [<- -> to navigate  enter to open  q to quit]                          |
+-------------------------------------------------------------------------+
```

Split-panel layout:
- **Left panel**: sailing ASCII video loop (pre-rendered ANSI frames)
- **Right panel**: content for the active section
- **Bottom bar**: tab navigation + key hints

---

## Sections

| Tab                    | Content                                      |
|------------------------|----------------------------------------------|
| Notice Board           | Home — sailing video left, bio right         |
| Sailing Instructions   | Projects / builds                            |
| R/C Logs               | Reflections / writing                        |
| Contact                | Links, email, socials                        |
| Experience             | Work history                                 |

---

## Video Pre-rendering Pipeline

Pre-conversion runs once at build/deploy time, not per SSH connection.

### Build time (runs once)

```
python prerender.py
  |
  +-- reads frames/*.jpg (328 frames)
  +-- converts each to ANSI color text via ascii_magic (Modes.TERMINAL)
  +-- serializes to frames.bin on disk
```

### Runtime (per SSH connection)

```
Ink TUI starts
  |
  +-- loads frames.bin from disk (near-instant)
  +-- begins looping video immediately on Notice Board
```

`frames.bin` is generated during server provisioning and stored on the VPS.
If the video changes, re-run `prerender.py` and redeploy.

---

## SSH Security

Wish handles all SSH security automatically:
- Host keys are generated on first boot and stored persistently
- No password auth — connections are unauthenticated (public portfolio, read-only)
- Each visitor gets an isolated process; no access to the host filesystem
- Rate limiting configured in Wish to prevent abuse

---

## Tech Stack

| Layer         | Technology                        |
|---------------|-----------------------------------|
| SSH server    | Wish (Go, Charmbracelet)          |
| TUI framework | Ink (React for CLIs, Node.js)     |
| Video frames  | Pre-rendered ANSI text (Python)   |
| Hosting       | Hetzner VPS (Ubuntu)              |
| Domain/DNS    | diego.boats via Vercel DNS        |

---

## Out of Scope

- Web version (browser access) — SSH only
- Auth / login for visitors
- Dynamic content / CMS
