# ASCII Player — Design Doc

Date: 2026-03-09

## Overview

A general-purpose CLI tool that converts any MP4 video to multi-resolution ASCII art and plays it in the terminal. Built as a reusable Python package that can later be embedded in a TUI portfolio or served as a web page.

**CLI pattern:** npm-style subcommands — `build` (extract + pre-render) and `run` (playback).

---

## Architecture

Modular Python package with 5 focused modules:

```
ascii_player/
  __init__.py        # package init
  __main__.py        # CLI entry point (argparse: build/run subcommands)
  build.py           # ffmpeg frame extraction + multi-res pre-rendering
  cache.py           # content-hash cache management
  player.py          # playback engine: frame loop, resize, scroll
  renderer.py        # ascii_magic wrapper: image path → ANSI string
tests/
  test_build.py
  test_cache.py
  test_player.py
  test_renderer.py
```

Existing files (`player.py`, `converter.py`, `frames/`) are kept as reference, untouched.

---

## CLI Interface

```bash
# Build: extract frames from MP4, pre-render 6 resolutions, save cache
python -m ascii_player build sailing.MP4

# Run: load cache, auto-detect best resolution, play
python -m ascii_player run sailing.MP4

# Run at forced resolution
python -m ascii_player run sailing.MP4 -c 120

# Rebuild cache from scratch
python -m ascii_player build sailing.MP4 --rebuild
```

---

## Build Pipeline

### Phase 1 — Frame Extraction (ffmpeg)

```
video.mp4 → ffmpeg → ~/.cache/ascii-player/<hash>/frames/frame_0001.jpg, ...
```

- Shells out to `ffmpeg -i video.mp4 -vf fps=24 <cache_dir>/frames/frame_%04d.jpg`
- Detects source FPS from ffmpeg probe, defaults to 24
- Requires ffmpeg installed on the system
- ffmpeg not found → clear error: `"ffmpeg not found. Install: brew install ffmpeg"`

### Phase 2 — Multi-Resolution Pre-render

```
For each resolution in [60, 80, 120, 160, 200, 250]:
  For each frame JPEG:
    render to ANSI string via renderer.py
  Save as ~/.cache/ascii-player/<hash>/res_<cols>.bin
```

- Uses `multiprocessing.Pool` for parallel rendering across CPU cores
- Each resolution is independent — can render all 6 in parallel batches
- Progress bar for both phases

### Metadata

`~/.cache/ascii-player/<hash>/manifest.json`:

```json
{
  "source_hash": "sha256:abc123...",
  "source_name": "sailing.MP4",
  "fps": 24,
  "frame_count": 328,
  "resolutions": [60, 80, 120, 160, 200, 250],
  "built_at": "2026-03-09T..."
}
```

`--rebuild` deletes the entire `<hash>/` directory and starts fresh.

### Error Handling

- ffmpeg not found → `"ffmpeg not found. Install: brew install ffmpeg"`
- MP4 corrupt / no video stream → error from ffmpeg probe with details
- Disk full mid-render → catch IOError, report which resolution failed, partial cache is usable for completed resolutions

---

## Cache System

Location: `~/.cache/ascii-player/<sha256-of-mp4>/`

### Cache Lookup Flow

1. Hash the MP4 file (SHA-256, read in 8KB chunks for large files)
2. Check `~/.cache/ascii-player/<hash>/manifest.json` exists
3. Cache hit → return manifest; cache miss → return None

### Key Functions

- `get_cache_dir(video_path) → Path | None` — returns cache dir if built
- `get_manifest(video_path) → dict | None` — reads manifest.json
- `load_resolution(video_path, columns) → list[list[str]]` — loads specific `res_<cols>.bin`
- `best_resolution(video_path, terminal_cols) → int` — largest cached resolution that fits
- `invalidate(video_path)` — deletes entire cache dir
- `compute_hash(video_path) → str` — SHA-256 of file contents

### Cache Format

- `res_<cols>.bin` files use **pickle** format with pre-split lines (`list[list[str]]`)
- Pickle is 5-10x faster to deserialize than JSON for large string arrays
- Only one resolution file loaded at a time (lazy-load on resize)

### Missing Cache Error

```
Error: No cache found for "sailing.MP4" (hash: abc123...)

  To build the cache, run:
    python -m ascii_player build sailing.MP4

  This extracts frames and pre-renders at 6 resolutions.
  Typical build time: ~30-60 seconds for a 328-frame video.
```

### Cache Corruption

If manifest exists but a `res_<cols>.bin` is missing or has wrong frame count → clear error naming the specific problem, suggest `--rebuild`.

---

## Player Engine

### State Model

```python
PlayerState:
  frames: list[list[str]]   # current resolution's frames (pre-split lines)
  frame_idx: int             # current frame position
  resolution: int            # active column width (e.g., 120)
  fps: int                   # from manifest
  scroll_y: int              # vertical scroll offset
```

### Playback Loop

```
1. Load best resolution for current terminal size
2. Enter raw terminal mode + alternate screen buffer
3. Every 1/fps seconds:
   a. Check for input (non-blocking)
   b. Check if resolution needs to change (SIGWINCH flag)
   c. Render current frame at scroll_y offset
   d. Advance frame_idx (wrap to 0 at end)
4. On quit: exit alternate screen, restore terminal
```

### SIGWINCH Resize Handling

```
Terminal resize detected (signal)
  → Read new terminal cols/rows
  → Compute best_resolution(new_cols)
  → If different from current:
      → Load new res_<cols>.bin from disk (background thread)
      → On load complete: swap frames buffer atomically
      → Reset scroll_y to 0 (frame geometry changed)
  → If same: just adjust visible line count
```

User triggers resize by Cmd+Plus (fewer cols → lower res) or Cmd+Minus (more cols → higher res). The player always picks the largest cached resolution that fits.

### Scroll Consistency

All frames at a given resolution have identical line counts (same image dimensions → same ASCII height). Scroll stays consistent within a resolution. On resolution change, scroll resets to 0.

```
max_scroll = max(0, frame_line_count - terminal_rows)
scroll_y = min(scroll_y, max_scroll)
```

### Speed Optimizations

- **Load only one resolution at startup** — don't load all 6
- **Pre-split lines in cache** — stored as `list[list[str]]`, no `.split('\n')` at runtime
- **Single stdout write per frame** — build full frame string in memory, one `sys.stdout.write()` call
- **Background thread for resolution swap** — no playback interruption during resize
- **Pickle + lazy-load** — ~50-100ms to load a resolution file, well within resize tolerance

---

## Terminal Emulator Compatibility

### Safe ANSI Subset (used by this tool)

- CSI sequences: `\033[2J` (clear), `\033[H` (home), `\033[?25l` (hide cursor)
- SGR 256-color: `\033[38;5;Nm` — this is what ascii_magic outputs via `Modes.TERMINAL`
- Alternate screen buffer: `\033[?1049h` / `\033[?1049l` — clean quit, restores previous terminal
- `SIGWINCH` for resize detection — universal on POSIX

### Compatibility Guarantee

No emulator-specific escape sequences. Stick to ANSI standard subset.

### Test Matrix (manual verification)

- Ghostty
- kitty
- iTerm2
- Alacritty
- Terminal.app

---

## Decisions Summary

| Decision | Choice |
|----------|--------|
| Scope | General-purpose CLI tool |
| Architecture | Modular Python package (5 modules) |
| CLI pattern | `build` / `run` subcommands (npm-style) |
| Resize strategy | Multi-resolution cache, snap to best fit |
| Resolutions | 60, 80, 120, 160, 200, 250 columns |
| Cache location | `~/.cache/ascii-player/<sha256>/` |
| Cache format | Pickle with pre-split lines |
| ffmpeg | Required system dependency |
| Color mode | 256-color (ascii_magic Modes.TERMINAL) |
| Missing cache | Error with helpful message |

---

## Future Considerations (out of scope)

- **Audio**: `--background-music-synth`, `--background-music-bossa`, etc. Independent audio loop library with genre-based playlists, separate from video playback
- **Enhanced playback controls** (add after E2E tests pass): Space (pause/resume), +/- (manual resolution cycle), r (restart), f (FPS/resolution info overlay)
- **True color mode**: `--truecolor` flag for 24-bit `\033[38;2;R;G;Bm` in supporting emulators
- **Web export**: Pre-render to HTML with ANSI-to-HTML conversion
- **TUI embed**: Import player module as a component in an Ink/Textual portfolio TUI
- **Windows support**: Currently POSIX-only (termios/SIGWINCH). Would need msvcrt + win32 console APIs
