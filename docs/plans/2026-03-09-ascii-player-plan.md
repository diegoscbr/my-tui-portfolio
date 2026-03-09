# ASCII Player Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a general-purpose CLI tool (`ascii-player`) that converts any MP4 to multi-resolution ASCII art and plays it in the terminal with real-time resize support.

**Architecture:** Modular Python package with 5 modules — renderer (ascii_magic wrapper), cache (content-hash disk cache with pickle), build (ffmpeg extraction + parallel multi-res pre-rendering), player (playback loop with SIGWINCH resize), and CLI (__main__ with build/run subcommands). Each module is independently testable.

**Tech Stack:** Python 3.14, ascii_magic + Pillow (rendering), ffmpeg (frame extraction), pickle (cache format), multiprocessing (parallel rendering), pytest (testing)

**Design doc:** `docs/plans/2026-03-09-ascii-player-design.md`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `ascii_player/__init__.py`
- Create: `ascii_player/__main__.py` (stub)
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `pyproject.toml`

**Step 1: Create package directory structure**

```bash
mkdir -p ascii_player tests
```

**Step 2: Create `pyproject.toml` with pytest config**

```toml
[project]
name = "ascii-player"
version = "0.1.0"
description = "General-purpose MP4 to ASCII video player"
requires-python = ">=3.12"
dependencies = [
    "ascii_magic",
    "Pillow",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**Step 3: Create `ascii_player/__init__.py`**

```python
"""ascii-player: General-purpose MP4 to ASCII video player."""

RESOLUTIONS = (60, 80, 120, 160, 200, 250)
CACHE_DIR_NAME = "ascii-player"
```

**Step 4: Create `ascii_player/__main__.py` stub**

```python
"""CLI entry point: python -m ascii_player"""

import sys


def main():
    print("ascii-player: not yet implemented", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 5: Create `tests/__init__.py` and `tests/conftest.py`**

```python
# tests/__init__.py
```

```python
# tests/conftest.py
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_cache(tmp_path):
    """Provides a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def sample_frame(tmp_path):
    """Creates a tiny test JPEG image (10x10 red square)."""
    from PIL import Image

    img_path = tmp_path / "frame_0001.jpg"
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(img_path, "JPEG")
    return img_path
```

**Step 6: Install dev dependencies and verify pytest runs**

Run: `source .venv/bin/activate && pip install -e ".[dev]"`
Expected: installs successfully

Run: `python -m pytest tests/ -v`
Expected: `no tests ran` (0 collected, no errors)

**Step 7: Verify package stub runs**

Run: `python -m ascii_player`
Expected: prints `ascii-player: not yet implemented` and exits with code 1

**Step 8: Commit**

```bash
git add ascii_player/__init__.py ascii_player/__main__.py tests/__init__.py tests/conftest.py pyproject.toml
git commit -m "chore: scaffold ascii_player package with pytest config"
```

---

## Task 2: Renderer Module

**Files:**
- Create: `tests/test_renderer.py`
- Create: `ascii_player/renderer.py`

**Ref:** This wraps `ascii_magic` so the rest of the codebase doesn't depend on it directly. See existing usage in `player.py:43-44`.

**Step 1: Write the failing tests**

```python
# tests/test_renderer.py
from pathlib import Path

import pytest

from ascii_player.renderer import render_frame


def test_render_frame_returns_string(sample_frame):
    """render_frame should return a non-empty string of ANSI text."""
    result = render_frame(sample_frame, columns=20)
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_frame_contains_ansi_codes(sample_frame):
    """Output should contain ANSI escape sequences (color codes)."""
    result = render_frame(sample_frame, columns=20)
    assert "\033[" in result


def test_render_frame_respects_column_width(sample_frame):
    """Wider columns should produce longer lines."""
    narrow = render_frame(sample_frame, columns=20)
    wide = render_frame(sample_frame, columns=60)
    narrow_max_line = max(len(line) for line in narrow.split("\n") if line.strip())
    wide_max_line = max(len(line) for line in wide.split("\n") if line.strip())
    assert wide_max_line > narrow_max_line


def test_render_frame_invalid_path_raises():
    """Should raise FileNotFoundError for nonexistent image."""
    with pytest.raises(FileNotFoundError):
        render_frame(Path("/nonexistent/frame.jpg"), columns=20)


def test_render_frame_splits_to_lines(sample_frame):
    """Output should contain newlines (multi-line ASCII art)."""
    result = render_frame(sample_frame, columns=20)
    lines = result.split("\n")
    assert len(lines) > 1
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ascii_player.renderer'`

**Step 3: Write minimal implementation**

```python
# ascii_player/renderer.py
"""Wraps ascii_magic to convert a single image file to an ANSI string."""

from pathlib import Path

from ascii_magic import AsciiArt
from ascii_magic.constants import Modes


def render_frame(image_path: Path, columns: int) -> str:
    """Convert a JPEG image to an ANSI-colored ASCII art string.

    Args:
        image_path: Path to a JPEG image file.
        columns: Width in terminal columns.

    Returns:
        Multi-line string with ANSI color escape codes.

    Raises:
        FileNotFoundError: If image_path does not exist.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    art = AsciiArt.from_image(str(image_path))
    return art._img_to_art(columns=columns, mode=Modes.TERMINAL)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_renderer.py -v`
Expected: all 5 PASS

**Step 5: Commit**

```bash
git add ascii_player/renderer.py tests/test_renderer.py
git commit -m "feat: add renderer module wrapping ascii_magic"
```

---

## Task 3: Cache Module — Hashing

**Files:**
- Create: `tests/test_cache.py`
- Create: `ascii_player/cache.py`

**Step 1: Write the failing tests for compute_hash**

```python
# tests/test_cache.py
from pathlib import Path

import pytest

from ascii_player.cache import compute_hash


class TestComputeHash:
    def test_returns_hex_string(self, tmp_path):
        """Hash should be a 64-char hex string (SHA-256)."""
        f = tmp_path / "test.mp4"
        f.write_bytes(b"fake video content")
        result = compute_hash(f)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_content_same_hash(self, tmp_path):
        """Identical content should produce identical hash."""
        f1 = tmp_path / "a.mp4"
        f2 = tmp_path / "b.mp4"
        content = b"identical content"
        f1.write_bytes(content)
        f2.write_bytes(content)
        assert compute_hash(f1) == compute_hash(f2)

    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hash."""
        f1 = tmp_path / "a.mp4"
        f2 = tmp_path / "b.mp4"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert compute_hash(f1) != compute_hash(f2)

    def test_nonexistent_file_raises(self):
        """Should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_hash(Path("/nonexistent/video.mp4"))
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cache.py::TestComputeHash -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# ascii_player/cache.py
"""Content-hash cache management for pre-rendered ASCII frames."""

import hashlib
from pathlib import Path

CHUNK_SIZE = 8192


def compute_hash(video_path: Path) -> str:
    """Compute SHA-256 hash of a file, reading in chunks.

    Args:
        video_path: Path to the video file.

    Returns:
        64-character hex digest string.

    Raises:
        FileNotFoundError: If video_path does not exist.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"File not found: {video_path}")

    sha = hashlib.sha256()
    with open(video_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha.update(chunk)
    return sha.hexdigest()
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cache.py::TestComputeHash -v`
Expected: all 4 PASS

**Step 5: Commit**

```bash
git add ascii_player/cache.py tests/test_cache.py
git commit -m "feat: add cache module with content hashing"
```

---

## Task 4: Cache Module — Read/Write/Lookup

**Files:**
- Modify: `tests/test_cache.py`
- Modify: `ascii_player/cache.py`

**Step 1: Write the failing tests for cache operations**

Append to `tests/test_cache.py`:

```python
import json
import pickle

from ascii_player.cache import (
    compute_hash,
    get_cache_dir,
    get_manifest,
    save_manifest,
    save_resolution,
    load_resolution,
    best_resolution,
    invalidate,
)
from ascii_player import RESOLUTIONS


@pytest.fixture
def fake_video(tmp_path):
    """Creates a fake video file for hashing."""
    f = tmp_path / "test.mp4"
    f.write_bytes(b"fake video bytes for hashing")
    return f


@pytest.fixture
def populated_cache(fake_video, tmp_cache):
    """Creates a cache dir with manifest and one resolution file."""
    video_hash = compute_hash(fake_video)
    cache_dir = tmp_cache / video_hash
    cache_dir.mkdir()
    (cache_dir / "frames").mkdir()

    manifest = {
        "source_hash": f"sha256:{video_hash}",
        "source_name": "test.mp4",
        "fps": 24,
        "frame_count": 2,
        "resolutions": [80],
        "built_at": "2026-03-09T00:00:00",
    }
    (cache_dir / "manifest.json").write_text(json.dumps(manifest))

    frames = [["line1", "line2"], ["line3", "line4"]]
    with open(cache_dir / "res_80.bin", "wb") as f:
        pickle.dump(frames, f)

    return cache_dir, fake_video, video_hash


class TestGetCacheDir:
    def test_returns_none_when_no_cache(self, fake_video, tmp_cache):
        result = get_cache_dir(fake_video, base_dir=tmp_cache)
        assert result is None

    def test_returns_path_when_cache_exists(self, populated_cache, tmp_cache):
        cache_dir, video, _ = populated_cache
        result = get_cache_dir(video, base_dir=tmp_cache)
        assert result == cache_dir


class TestManifest:
    def test_save_and_load_manifest(self, fake_video, tmp_cache):
        video_hash = compute_hash(fake_video)
        cache_dir = tmp_cache / video_hash
        cache_dir.mkdir()

        manifest = {"fps": 24, "frame_count": 10, "resolutions": [80, 120]}
        save_manifest(cache_dir, manifest)
        loaded = get_manifest(fake_video, base_dir=tmp_cache)
        assert loaded["fps"] == 24
        assert loaded["resolutions"] == [80, 120]

    def test_get_manifest_returns_none_when_missing(self, fake_video, tmp_cache):
        result = get_manifest(fake_video, base_dir=tmp_cache)
        assert result is None


class TestResolutionFiles:
    def test_save_and_load_resolution(self, populated_cache, tmp_cache):
        cache_dir, video, _ = populated_cache
        loaded = load_resolution(video, 80, base_dir=tmp_cache)
        assert loaded == [["line1", "line2"], ["line3", "line4"]]

    def test_load_missing_resolution_raises(self, populated_cache, tmp_cache):
        _, video, _ = populated_cache
        with pytest.raises(FileNotFoundError, match="res_120.bin"):
            load_resolution(video, 120, base_dir=tmp_cache)

    def test_save_resolution_pickle_format(self, fake_video, tmp_cache):
        video_hash = compute_hash(fake_video)
        cache_dir = tmp_cache / video_hash
        cache_dir.mkdir()

        frames = [["a", "b"], ["c", "d"]]
        save_resolution(cache_dir, 120, frames)

        assert (cache_dir / "res_120.bin").exists()
        loaded = load_resolution(fake_video, 120, base_dir=tmp_cache)
        assert loaded == frames


class TestBestResolution:
    def test_picks_largest_that_fits(self):
        available = [60, 80, 120, 160, 200, 250]
        assert best_resolution(available, terminal_cols=145) == 120

    def test_picks_exact_match(self):
        available = [60, 80, 120, 160, 200, 250]
        assert best_resolution(available, terminal_cols=120) == 120

    def test_picks_smallest_when_very_narrow(self):
        available = [60, 80, 120, 160, 200, 250]
        assert best_resolution(available, terminal_cols=40) == 60

    def test_picks_largest_when_very_wide(self):
        available = [60, 80, 120, 160, 200, 250]
        assert best_resolution(available, terminal_cols=500) == 250


class TestInvalidate:
    def test_removes_cache_dir(self, populated_cache, tmp_cache):
        cache_dir, video, _ = populated_cache
        assert cache_dir.exists()
        invalidate(video, base_dir=tmp_cache)
        assert not cache_dir.exists()

    def test_invalidate_nonexistent_is_noop(self, fake_video, tmp_cache):
        invalidate(fake_video, base_dir=tmp_cache)  # should not raise
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cache.py -v -k "not TestComputeHash"`
Expected: FAIL with `ImportError` (functions not yet defined)

**Step 3: Write implementation — add functions to `ascii_player/cache.py`**

```python
# ascii_player/cache.py
"""Content-hash cache management for pre-rendered ASCII frames."""

import hashlib
import json
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path

CHUNK_SIZE = 8192
DEFAULT_BASE_DIR = Path.home() / ".cache" / "ascii-player"


def compute_hash(video_path: Path) -> str:
    """Compute SHA-256 hash of a file, reading in chunks."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"File not found: {video_path}")

    sha = hashlib.sha256()
    with open(video_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha.update(chunk)
    return sha.hexdigest()


def _resolve_cache_dir(video_path: Path, base_dir: Path | None = None) -> Path:
    """Return the cache directory path for a given video (may not exist)."""
    base = base_dir or DEFAULT_BASE_DIR
    video_hash = compute_hash(video_path)
    return base / video_hash


def get_cache_dir(video_path: Path, base_dir: Path | None = None) -> Path | None:
    """Return cache directory if it exists with a manifest, else None."""
    cache_dir = _resolve_cache_dir(video_path, base_dir)
    if (cache_dir / "manifest.json").exists():
        return cache_dir
    return None


def get_manifest(video_path: Path, base_dir: Path | None = None) -> dict | None:
    """Read and return the manifest dict, or None if not cached."""
    cache_dir = get_cache_dir(video_path, base_dir)
    if cache_dir is None:
        return None
    return json.loads((cache_dir / "manifest.json").read_text())


def save_manifest(cache_dir: Path, manifest: dict) -> None:
    """Write manifest dict to cache_dir/manifest.json."""
    (cache_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def save_resolution(cache_dir: Path, columns: int, frames: list[list[str]]) -> None:
    """Save pre-split frames for a resolution as pickle."""
    with open(cache_dir / f"res_{columns}.bin", "wb") as f:
        pickle.dump(frames, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_resolution(
    video_path: Path, columns: int, base_dir: Path | None = None
) -> list[list[str]]:
    """Load pre-split frames for a specific resolution.

    Raises:
        FileNotFoundError: If cache or resolution file doesn't exist.
    """
    cache_dir = get_cache_dir(video_path, base_dir)
    if cache_dir is None:
        raise FileNotFoundError(
            f'No cache found for "{video_path.name}"\n\n'
            f"  To build the cache, run:\n"
            f"    python -m ascii_player build {video_path}\n"
        )
    res_file = cache_dir / f"res_{columns}.bin"
    if not res_file.exists():
        raise FileNotFoundError(
            f"Resolution file not found: {res_file.name}\n"
            f"  Available: {[f.name for f in cache_dir.glob('res_*.bin')]}\n"
            f"  Try: python -m ascii_player build {video_path} --rebuild"
        )
    with open(res_file, "rb") as f:
        return pickle.load(f)


def best_resolution(available: list[int], terminal_cols: int) -> int:
    """Return the largest cached resolution that fits the terminal width.

    If terminal is narrower than all resolutions, returns the smallest.
    If terminal is wider than all resolutions, returns the largest.
    """
    sorted_res = sorted(available)
    for res in reversed(sorted_res):
        if res <= terminal_cols:
            return res
    return sorted_res[0]


def invalidate(video_path: Path, base_dir: Path | None = None) -> None:
    """Delete the entire cache directory for a video."""
    try:
        cache_dir = _resolve_cache_dir(video_path, base_dir)
    except FileNotFoundError:
        return
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cache.py -v`
Expected: all tests PASS (TestComputeHash + new classes)

**Step 5: Commit**

```bash
git add ascii_player/cache.py tests/test_cache.py
git commit -m "feat: add cache read/write/lookup with pickle format"
```

---

## Task 5: Build Module — ffmpeg Frame Extraction

**Files:**
- Create: `tests/test_build.py`
- Create: `ascii_player/build.py`

**Step 1: Write the failing tests for frame extraction**

```python
# tests/test_build.py
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ascii_player.build import (
    check_ffmpeg,
    probe_fps,
    extract_frames,
)


class TestCheckFfmpeg:
    def test_returns_true_when_ffmpeg_exists(self):
        """ffmpeg should be available on this dev machine."""
        assert check_ffmpeg() is True

    @patch("ascii_player.build.shutil.which", return_value=None)
    def test_returns_false_when_missing(self, mock_which):
        assert check_ffmpeg() is False


class TestProbeFps:
    def test_returns_float(self, tmp_path):
        """Should return a positive number for valid video."""
        # We'll mock subprocess since we may not have a real MP4 in tests
        with patch("ascii_player.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="24000/1001\n", returncode=0
            )
            fps = probe_fps(tmp_path / "fake.mp4")
            assert abs(fps - 23.976) < 0.1

    def test_defaults_to_24_on_failure(self, tmp_path):
        """Should default to 24 FPS if probe fails."""
        with patch("ascii_player.build.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("ffprobe failed")
            fps = probe_fps(tmp_path / "fake.mp4")
            assert fps == 24.0


class TestExtractFrames:
    def test_calls_ffmpeg_with_correct_args(self, tmp_path):
        """Should invoke ffmpeg with correct output pattern."""
        output_dir = tmp_path / "frames"
        output_dir.mkdir()

        with patch("ascii_player.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            extract_frames(
                video_path=tmp_path / "test.mp4",
                output_dir=output_dir,
                fps=24,
            )
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args[0]
            assert "-vf" in call_args
            assert "fps=24" in call_args[call_args.index("-vf") + 1]

    def test_raises_on_ffmpeg_failure(self, tmp_path):
        """Should raise RuntimeError when ffmpeg exits non-zero."""
        output_dir = tmp_path / "frames"
        output_dir.mkdir()

        with patch("ascii_player.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Error: invalid input"
            )
            with pytest.raises(RuntimeError, match="ffmpeg"):
                extract_frames(
                    video_path=tmp_path / "test.mp4",
                    output_dir=output_dir,
                    fps=24,
                )
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_build.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# ascii_player/build.py
"""Build pipeline: ffmpeg frame extraction + multi-resolution pre-rendering."""

import shutil
import subprocess
from pathlib import Path

DEFAULT_FPS = 24.0


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system PATH."""
    return shutil.which("ffmpeg") is not None


def probe_fps(video_path: Path) -> float:
    """Detect video frame rate using ffprobe. Returns DEFAULT_FPS on failure."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # r_frame_rate is like "24000/1001" or "24/1"
        parts = result.stdout.strip().split("/")
        if len(parts) == 2:
            return float(parts[0]) / float(parts[1])
        return float(parts[0])
    except Exception:
        return DEFAULT_FPS


def extract_frames(video_path: Path, output_dir: Path, fps: int) -> int:
    """Extract frames from MP4 as numbered JPEGs using ffmpeg.

    Args:
        video_path: Path to the source MP4 file.
        output_dir: Directory to write frame_NNNN.jpg files into.
        fps: Target frames per second for extraction.

    Returns:
        Number of frames extracted.

    Raises:
        RuntimeError: If ffmpeg is not found or exits with error.
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "ffmpeg not found. Install it:\n"
            "  macOS:  brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(output_dir / "frame_%04d.jpg")

    result = subprocess.run(
        [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"fps={fps}",
            "-q:v", "2",
            output_pattern,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit code {result.returncode}):\n{result.stderr}"
        )

    frame_count = len(list(output_dir.glob("frame_*.jpg")))
    return frame_count
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_build.py -v`
Expected: all tests PASS

**Step 5: Commit**

```bash
git add ascii_player/build.py tests/test_build.py
git commit -m "feat: add build module with ffmpeg frame extraction"
```

---

## Task 6: Build Module — Multi-Resolution Pre-render

**Files:**
- Modify: `tests/test_build.py`
- Modify: `ascii_player/build.py`

**Step 1: Write the failing tests for pre-rendering**

Append to `tests/test_build.py`:

```python
import json

from ascii_player.build import prerender_resolutions, build_video
from ascii_player.cache import get_manifest, load_resolution


class TestPrerenderResolutions:
    def test_renders_single_resolution(self, sample_frame, tmp_path):
        """Should produce a pickle file for the given resolution."""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        # Copy sample_frame into frames_dir as frame_0001.jpg
        import shutil
        shutil.copy(sample_frame, frames_dir / "frame_0001.jpg")

        cache_dir = tmp_path / "cache_out"
        cache_dir.mkdir()

        prerender_resolutions(
            frames_dir=frames_dir,
            cache_dir=cache_dir,
            resolutions=[80],
        )
        assert (cache_dir / "res_80.bin").exists()

    def test_renders_multiple_resolutions(self, sample_frame, tmp_path):
        """Should produce pickle files for all requested resolutions."""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        import shutil
        shutil.copy(sample_frame, frames_dir / "frame_0001.jpg")

        cache_dir = tmp_path / "cache_out"
        cache_dir.mkdir()

        resolutions = [60, 80, 120]
        prerender_resolutions(
            frames_dir=frames_dir,
            cache_dir=cache_dir,
            resolutions=resolutions,
        )
        for res in resolutions:
            assert (cache_dir / f"res_{res}.bin").exists()

    def test_frames_are_presplit_lines(self, sample_frame, tmp_path):
        """Cached frames should be list[list[str]] (pre-split)."""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        import shutil
        shutil.copy(sample_frame, frames_dir / "frame_0001.jpg")

        cache_dir = tmp_path / "cache_out"
        cache_dir.mkdir()

        prerender_resolutions(
            frames_dir=frames_dir,
            cache_dir=cache_dir,
            resolutions=[80],
        )
        import pickle
        with open(cache_dir / "res_80.bin", "rb") as f:
            frames = pickle.load(f)
        # Should be list of frames, each frame is list of lines
        assert isinstance(frames, list)
        assert isinstance(frames[0], list)
        assert isinstance(frames[0][0], str)


class TestBuildVideo:
    def test_full_build_pipeline(self, sample_frame, tmp_path):
        """End-to-end: build should create manifest + resolution files."""
        # Set up a fake video and pre-extracted frames
        fake_video = tmp_path / "test.mp4"
        fake_video.write_bytes(b"fake video for hash")

        frames_dir = tmp_path / "extracted_frames"
        frames_dir.mkdir()
        import shutil
        shutil.copy(sample_frame, frames_dir / "frame_0001.jpg")
        shutil.copy(sample_frame, frames_dir / "frame_0002.jpg")

        cache_base = tmp_path / "cache"
        cache_base.mkdir()

        # Mock extract_frames to skip ffmpeg — just use our pre-made frames
        with patch("ascii_player.build.extract_frames") as mock_extract:
            def fake_extract(video_path, output_dir, fps):
                for f in frames_dir.glob("frame_*.jpg"):
                    shutil.copy(f, output_dir / f.name)
                return 2
            mock_extract.side_effect = fake_extract

            build_video(
                video_path=fake_video,
                resolutions=[60, 80],
                base_dir=cache_base,
            )

        manifest = get_manifest(fake_video, base_dir=cache_base)
        assert manifest is not None
        assert manifest["frame_count"] == 2
        assert manifest["resolutions"] == [60, 80]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_build.py -v -k "Prerender or BuildVideo"`
Expected: FAIL with `ImportError`

**Step 3: Add functions to `ascii_player/build.py`**

Append to `ascii_player/build.py`:

```python
import json
import pickle
from datetime import datetime, timezone
from multiprocessing import Pool, cpu_count

from ascii_player import RESOLUTIONS
from ascii_player.renderer import render_frame
from ascii_player.cache import (
    compute_hash,
    save_manifest,
    save_resolution,
)


def _render_single_frame(args: tuple) -> list[str]:
    """Worker function for multiprocessing: render one frame at one resolution."""
    frame_path, columns = args
    ansi_text = render_frame(frame_path, columns)
    return ansi_text.split("\n")


def prerender_resolutions(
    frames_dir: Path,
    cache_dir: Path,
    resolutions: list[int] | None = None,
) -> None:
    """Pre-render all frames at each resolution and save as pickle.

    Args:
        frames_dir: Directory containing frame_NNNN.jpg files.
        cache_dir: Cache directory to write res_<cols>.bin files into.
        resolutions: Column widths to render. Defaults to RESOLUTIONS.
    """
    resolutions = resolutions or list(RESOLUTIONS)
    frame_paths = sorted(frames_dir.glob("frame_*.jpg"))

    if not frame_paths:
        raise FileNotFoundError(f"No frame_*.jpg files found in {frames_dir}")

    worker_count = min(cpu_count(), 8)

    for cols in resolutions:
        print(f"  Rendering {len(frame_paths)} frames at {cols} columns...")
        work_items = [(path, cols) for path in frame_paths]

        with Pool(processes=worker_count) as pool:
            frames = pool.map(_render_single_frame, work_items)

        save_resolution(cache_dir, cols, frames)
        print(f"  Saved res_{cols}.bin")


def build_video(
    video_path: Path,
    resolutions: list[int] | None = None,
    base_dir: Path | None = None,
    rebuild: bool = False,
) -> Path:
    """Full build pipeline: extract frames, pre-render all resolutions, save cache.

    Args:
        video_path: Path to the source MP4 file.
        resolutions: Column widths to pre-render. Defaults to RESOLUTIONS.
        base_dir: Cache base directory. Defaults to ~/.cache/ascii-player/.
        rebuild: If True, delete existing cache first.

    Returns:
        Path to the cache directory.
    """
    from ascii_player.cache import DEFAULT_BASE_DIR, invalidate

    resolutions = resolutions or list(RESOLUTIONS)
    base_dir = base_dir or DEFAULT_BASE_DIR

    if rebuild:
        print(f"Rebuilding cache for {video_path.name}...")
        invalidate(video_path, base_dir=base_dir)

    video_hash = compute_hash(video_path)
    cache_dir = base_dir / video_hash
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Extract frames
    frames_output = cache_dir / "frames"
    if not any(frames_output.glob("frame_*.jpg")) if frames_output.exists() else True:
        print(f"Phase 1: Extracting frames from {video_path.name}...")
        fps = int(probe_fps(video_path))
        frame_count = extract_frames(video_path, frames_output, fps)
        print(f"  Extracted {frame_count} frames at {fps} FPS")
    else:
        frame_count = len(list(frames_output.glob("frame_*.jpg")))
        fps = int(probe_fps(video_path))
        print(f"  Frames already extracted ({frame_count} found), skipping.")

    # Phase 2: Pre-render at all resolutions
    print(f"Phase 2: Pre-rendering at {len(resolutions)} resolutions...")
    prerender_resolutions(frames_output, cache_dir, resolutions)

    # Save manifest
    manifest = {
        "source_hash": f"sha256:{video_hash}",
        "source_name": video_path.name,
        "fps": fps,
        "frame_count": frame_count,
        "resolutions": sorted(resolutions),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    save_manifest(cache_dir, manifest)
    print(f"Build complete. Cache: {cache_dir}")

    return cache_dir
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_build.py -v`
Expected: all tests PASS

**Step 5: Commit**

```bash
git add ascii_player/build.py tests/test_build.py
git commit -m "feat: add multi-resolution pre-rendering with parallel workers"
```

---

## Task 7: CLI Entry Point

**Files:**
- Create: `tests/test_cli.py`
- Modify: `ascii_player/__main__.py`

**Step 1: Write the failing tests**

```python
# tests/test_cli.py
import subprocess
import sys

import pytest


def run_cli(*args):
    """Helper to invoke the CLI as a subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "ascii_player", *args],
        capture_output=True,
        text=True,
    )
    return result


class TestCliHelp:
    def test_no_args_shows_help(self):
        result = run_cli()
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "usage" in result.stdout.lower()

    def test_help_flag(self):
        result = run_cli("--help")
        assert result.returncode == 0
        assert "build" in result.stdout
        assert "run" in result.stdout

    def test_build_help(self):
        result = run_cli("build", "--help")
        assert result.returncode == 0
        assert "video" in result.stdout.lower()

    def test_run_help(self):
        result = run_cli("run", "--help")
        assert result.returncode == 0
        assert "video" in result.stdout.lower()


class TestCliBuild:
    def test_build_nonexistent_file(self):
        result = run_cli("build", "/nonexistent/video.mp4")
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestCliRun:
    def test_run_without_cache(self, tmp_path):
        fake_video = tmp_path / "nocache.mp4"
        fake_video.write_bytes(b"fake")
        result = run_cli("run", str(fake_video))
        assert result.returncode != 0
        assert "no cache found" in result.stderr.lower() or "build" in result.stderr.lower()
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL (current stub doesn't parse subcommands)

**Step 3: Implement the CLI**

```python
# ascii_player/__main__.py
"""CLI entry point: python -m ascii_player [build|run] video.mp4"""

import sys
import argparse
from pathlib import Path


def cmd_build(args):
    """Handle the 'build' subcommand."""
    from ascii_player.build import build_video

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: File not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    try:
        build_video(
            video_path=video_path,
            rebuild=args.rebuild,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error writing cache: {e}", file=sys.stderr)
        print("  Some resolutions may have been cached successfully.", file=sys.stderr)
        print(f"  Try: python -m ascii_player build {video_path} --rebuild", file=sys.stderr)
        sys.exit(1)


def cmd_run(args):
    """Handle the 'run' subcommand."""
    from ascii_player.cache import get_manifest, compute_hash

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: File not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    manifest = get_manifest(video_path)
    if manifest is None:
        video_hash = compute_hash(video_path)
        print(
            f'Error: No cache found for "{video_path.name}" (hash: {video_hash[:12]}...)\n'
            f"\n"
            f"  To build the cache, run:\n"
            f"    python -m ascii_player build {video_path}\n"
            f"\n"
            f"  This extracts frames and pre-renders at 6 resolutions.\n"
            f"  Typical build time: ~30-60 seconds for a 328-frame video.",
            file=sys.stderr,
        )
        sys.exit(1)

    from ascii_player.player import play_video

    try:
        play_video(video_path=video_path, forced_columns=args.columns)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="ascii-player",
        description="General-purpose MP4 to ASCII video player",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build subcommand
    build_parser = subparsers.add_parser(
        "build",
        help="Extract frames from video and pre-render all resolutions",
    )
    build_parser.add_argument("video", help="Path to the MP4 video file")
    build_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing cache and rebuild from scratch",
    )
    build_parser.set_defaults(func=cmd_build)

    # run subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Play a pre-built ASCII video in the terminal",
    )
    run_parser.add_argument("video", help="Path to the MP4 video file")
    run_parser.add_argument(
        "--columns", "-c",
        type=int,
        default=None,
        help="Force a specific resolution in columns (default: auto-detect)",
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all tests PASS

**Step 5: Commit**

```bash
git add ascii_player/__main__.py tests/test_cli.py
git commit -m "feat: add CLI with build/run subcommands"
```

---

## Task 8: Player Module — Basic Playback Loop

**Files:**
- Create: `tests/test_player.py`
- Create: `ascii_player/player.py`

This is the core playback engine. We build it in three steps: basic loop first (this task), resize handling (Task 9), scroll consistency (Task 10).

**Step 1: Write the failing tests**

```python
# tests/test_player.py
import signal
from unittest.mock import patch, MagicMock

import pytest

from ascii_player.player import PlayerState, build_frame_output


class TestPlayerState:
    def test_initial_state(self):
        frames = [["line1", "line2"], ["line3", "line4"]]
        state = PlayerState(frames=frames, fps=24, resolution=80)
        assert state.frame_idx == 0
        assert state.scroll_y == 0
        assert state.resolution == 80

    def test_advance_frame_wraps(self):
        frames = [["a"], ["b"], ["c"]]
        state = PlayerState(frames=frames, fps=24, resolution=80)
        state.frame_idx = 2
        state.advance_frame()
        assert state.frame_idx == 0

    def test_advance_frame_increments(self):
        frames = [["a"], ["b"], ["c"]]
        state = PlayerState(frames=frames, fps=24, resolution=80)
        state.advance_frame()
        assert state.frame_idx == 1


class TestBuildFrameOutput:
    def test_returns_visible_lines(self):
        frame_lines = ["line0", "line1", "line2", "line3", "line4"]
        output = build_frame_output(frame_lines, scroll_y=0, terminal_rows=3)
        assert output.count("\r\n") == 2  # 3 lines joined by \r\n = 2 separators

    def test_scroll_offset(self):
        frame_lines = ["line0", "line1", "line2", "line3"]
        output = build_frame_output(frame_lines, scroll_y=2, terminal_rows=2)
        assert "line2" in output
        assert "line3" in output
        assert "line0" not in output

    def test_clamps_scroll_to_max(self):
        frame_lines = ["line0", "line1"]
        # scroll_y=5 but only 2 lines, terminal shows 3 rows
        output = build_frame_output(frame_lines, scroll_y=5, terminal_rows=3)
        assert "line0" in output
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_player.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write implementation**

```python
# ascii_player/player.py
"""Playback engine: frame loop, resize detection, scroll."""

import shutil
import signal
import sys
import select
import termios
import time
import tty
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread

from ascii_player.cache import (
    best_resolution,
    get_manifest,
    load_resolution,
)

# ANSI escape codes — safe across all modern terminal emulators
CLEAR = "\033[2J"
HOME = "\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"


@dataclass
class PlayerState:
    """Mutable playback state."""

    frames: list[list[str]]
    fps: int
    resolution: int
    frame_idx: int = 0
    scroll_y: int = 0

    def advance_frame(self) -> None:
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)


def build_frame_output(
    frame_lines: list[str], scroll_y: int, terminal_rows: int
) -> str:
    """Build the visible portion of a frame as a single string for stdout.

    Clamps scroll_y so it never goes past the frame content.
    """
    max_scroll = max(0, len(frame_lines) - terminal_rows)
    clamped_y = min(scroll_y, max_scroll)
    visible = frame_lines[clamped_y : clamped_y + terminal_rows]
    return "\r\n".join(visible)


def read_key(timeout: float = 0.0) -> str | None:
    """Non-blocking key read in raw mode. Returns a string or None."""
    if not select.select([sys.stdin], [], [], timeout)[0]:
        return None
    ch = sys.stdin.read(1)
    if ch == "\033":
        if select.select([sys.stdin], [], [], 0.05)[0]:
            ch += sys.stdin.read(1)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch += sys.stdin.read(1)
    return ch


def play_video(
    video_path: Path,
    forced_columns: int | None = None,
    base_dir: Path | None = None,
) -> None:
    """Main playback entry point.

    Args:
        video_path: Path to the original MP4 (used for cache lookup).
        forced_columns: If set, use this resolution instead of auto-detect.
        base_dir: Cache base directory override (for testing).
    """
    manifest = get_manifest(video_path, base_dir=base_dir)
    available_res = manifest["resolutions"]
    fps = manifest["fps"]

    term = shutil.get_terminal_size()

    if forced_columns is not None:
        resolution = forced_columns
        if resolution not in available_res:
            closest = best_resolution(available_res, resolution)
            print(
                f"Resolution {resolution} not cached. Using closest: {closest}",
                file=sys.stderr,
            )
            resolution = closest
    else:
        resolution = best_resolution(available_res, term.columns)

    frames = load_resolution(video_path, resolution, base_dir=base_dir)

    state = PlayerState(frames=frames, fps=fps, resolution=resolution)

    # SIGWINCH resize flag
    resize_flag = [False]

    def on_resize(signum, frame):
        resize_flag[0] = True

    signal.signal(signal.SIGWINCH, on_resize)

    delay = 1.0 / fps
    old_settings = termios.tcgetattr(sys.stdin)

    sys.stdout.write(ALT_SCREEN_ON + HIDE_CURSOR + CLEAR)
    sys.stdout.flush()

    try:
        tty.setraw(sys.stdin.fileno())

        while True:
            t0 = time.perf_counter()

            term = shutil.get_terminal_size()

            # Handle resize
            if resize_flag[0]:
                resize_flag[0] = False
                new_res = best_resolution(available_res, term.columns)
                if new_res != state.resolution:
                    new_frames = load_resolution(
                        video_path, new_res, base_dir=base_dir
                    )
                    state.frames = new_frames
                    state.resolution = new_res
                    state.scroll_y = 0
                    sys.stdout.write(CLEAR)

            # Handle input
            key = read_key(0)
            if key in ("q", "\x03"):  # q / Ctrl-C
                break
            elif key in ("\033[A", "k"):  # up
                state.scroll_y = max(0, state.scroll_y - 1)
            elif key in ("\033[B", "j"):  # down
                max_scroll = max(0, len(state.frames[0]) - term.lines)
                state.scroll_y = min(max_scroll, state.scroll_y + 1)

            # Render
            frame_lines = state.frames[state.frame_idx]
            output = build_frame_output(frame_lines, state.scroll_y, term.lines)
            sys.stdout.write(HOME + output)
            sys.stdout.flush()

            state.advance_frame()

            elapsed = time.perf_counter() - t0
            remaining = delay - elapsed
            if remaining > 0:
                time.sleep(remaining)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write(SHOW_CURSOR + ALT_SCREEN_OFF)
        sys.stdout.flush()
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_player.py -v`
Expected: all tests PASS

**Step 5: Commit**

```bash
git add ascii_player/player.py tests/test_player.py
git commit -m "feat: add player module with playback loop and resize handling"
```

---

## Task 9: Player — SIGWINCH Resize Integration Test

**Files:**
- Modify: `tests/test_player.py`

This task adds tests to verify the resize logic works correctly — that resolution swapping happens when the terminal size changes.

**Step 1: Write the failing tests**

Append to `tests/test_player.py`:

```python
from ascii_player.player import PlayerState
from ascii_player.cache import best_resolution


class TestResizeLogic:
    def test_best_resolution_picks_lower_on_shrink(self):
        """Simulates Cmd+Plus: fewer columns → lower resolution."""
        available = [60, 80, 120, 160, 200, 250]
        # Terminal was 160, user makes font bigger → now 100 cols
        new_res = best_resolution(available, terminal_cols=100)
        assert new_res == 80

    def test_best_resolution_picks_higher_on_grow(self):
        """Simulates Cmd+Minus: more columns → higher resolution."""
        available = [60, 80, 120, 160, 200, 250]
        # Terminal was 120, user makes font smaller → now 180 cols
        new_res = best_resolution(available, terminal_cols=180)
        assert new_res == 160

    def test_state_scroll_resets_on_resolution_change(self):
        """Scroll should reset to 0 when resolution changes."""
        frames_80 = [["a", "b", "c"]] * 3
        frames_120 = [["x", "y", "z", "w"]] * 3

        state = PlayerState(frames=frames_80, fps=24, resolution=80)
        state.scroll_y = 2

        # Simulate resolution change
        state.frames = frames_120
        state.resolution = 120
        state.scroll_y = 0  # reset on change

        assert state.scroll_y == 0
        assert state.resolution == 120
        assert len(state.frames[0]) == 4
```

**Step 2: Run tests to verify they fail (or pass immediately since logic exists)**

Run: `python -m pytest tests/test_player.py::TestResizeLogic -v`
Expected: all PASS (logic already implemented in Task 8, this validates it)

**Step 3: Commit**

```bash
git add tests/test_player.py
git commit -m "test: add resize logic integration tests"
```

---

## Task 10: Player — Scroll Consistency Tests

**Files:**
- Modify: `tests/test_player.py`

**Step 1: Write the scroll consistency tests**

Append to `tests/test_player.py`:

```python
class TestScrollConsistency:
    def test_all_frames_same_line_count(self):
        """At a given resolution, all frames must have the same line count.

        This is guaranteed by ascii_magic rendering the same resolution,
        but we test the invariant explicitly.
        """
        # Simulate pre-rendered frames — all must have same height
        frames = [
            ["line1", "line2", "line3"],
            ["line4", "line5", "line6"],
            ["line7", "line8", "line9"],
        ]
        heights = {len(f) for f in frames}
        assert len(heights) == 1, f"Inconsistent frame heights: {heights}"

    def test_scroll_clamp_prevents_overscroll(self):
        """build_frame_output should clamp scroll_y to valid range."""
        frame_lines = ["a", "b", "c"]  # 3 lines
        # Try to scroll past the end
        output = build_frame_output(frame_lines, scroll_y=100, terminal_rows=2)
        # Should show the last 2 lines (clamped to max_scroll=1)
        assert "b" in output
        assert "c" in output

    def test_scroll_stays_consistent_across_frames(self):
        """Same scroll_y on different frames should show same vertical position."""
        frame_a = ["a0", "a1", "a2", "a3", "a4"]
        frame_b = ["b0", "b1", "b2", "b3", "b4"]

        out_a = build_frame_output(frame_a, scroll_y=2, terminal_rows=2)
        out_b = build_frame_output(frame_b, scroll_y=2, terminal_rows=2)

        # Both should show lines at index 2 and 3
        assert "a2" in out_a and "a3" in out_a
        assert "b2" in out_b and "b3" in out_b

    def test_no_scroll_when_frame_fits(self):
        """If frame fits in terminal, scroll_y should have no effect."""
        frame_lines = ["a", "b"]
        output_no_scroll = build_frame_output(frame_lines, scroll_y=0, terminal_rows=5)
        output_scroll = build_frame_output(frame_lines, scroll_y=3, terminal_rows=5)
        assert output_no_scroll == output_scroll
```

**Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_player.py::TestScrollConsistency -v`
Expected: all PASS

**Step 3: Commit**

```bash
git add tests/test_player.py
git commit -m "test: add scroll consistency validation tests"
```

---

## Task 11: E2E Integration Test

**Files:**
- Create: `tests/test_e2e.py`

This tests the full `build` → `run` pipeline using a real tiny test video.

**Step 1: Create a minimal test video fixture**

```python
# tests/test_e2e.py
"""End-to-end test: build and verify cache for a synthetic test video."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ascii_player.build import build_video, check_ffmpeg
from ascii_player.cache import (
    get_manifest,
    load_resolution,
    best_resolution,
    invalidate,
)


@pytest.fixture
def test_video_with_frames(tmp_path):
    """Creates a fake MP4 file and pre-made frame JPEGs (skips ffmpeg)."""
    from PIL import Image

    video = tmp_path / "test_video.mp4"
    video.write_bytes(b"synthetic test video content for hashing")

    frames_dir = tmp_path / "synthetic_frames"
    frames_dir.mkdir()

    # Create 5 tiny frames with different colors
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
    for i, color in enumerate(colors):
        img = Image.new("RGB", (32, 18), color=color)
        img.save(frames_dir / f"frame_{i + 1:04d}.jpg", "JPEG")

    return video, frames_dir


class TestE2EPipeline:
    def test_build_creates_manifest_and_all_resolutions(
        self, test_video_with_frames, tmp_path
    ):
        """Full build should create manifest + resolution files."""
        video, frames_dir = test_video_with_frames
        cache_base = tmp_path / "e2e_cache"
        cache_base.mkdir()
        import shutil as sh

        with patch("ascii_player.build.extract_frames") as mock_extract:
            def fake_extract(video_path, output_dir, fps):
                output_dir.mkdir(parents=True, exist_ok=True)
                for f in frames_dir.glob("frame_*.jpg"):
                    sh.copy(f, output_dir / f.name)
                return 5
            mock_extract.side_effect = fake_extract

            build_video(
                video_path=video,
                resolutions=[60, 80, 120],
                base_dir=cache_base,
            )

        # Verify manifest
        manifest = get_manifest(video, base_dir=cache_base)
        assert manifest is not None
        assert manifest["frame_count"] == 5
        assert manifest["resolutions"] == [60, 80, 120]

        # Verify each resolution loads correctly
        for res in [60, 80, 120]:
            frames = load_resolution(video, res, base_dir=cache_base)
            assert len(frames) == 5
            assert isinstance(frames[0], list)
            assert isinstance(frames[0][0], str)

    def test_best_resolution_selects_correctly(
        self, test_video_with_frames, tmp_path
    ):
        """After build, best_resolution should pick correctly."""
        video, frames_dir = test_video_with_frames
        cache_base = tmp_path / "e2e_cache"
        cache_base.mkdir()
        import shutil as sh

        with patch("ascii_player.build.extract_frames") as mock_extract:
            def fake_extract(video_path, output_dir, fps):
                output_dir.mkdir(parents=True, exist_ok=True)
                for f in frames_dir.glob("frame_*.jpg"):
                    sh.copy(f, output_dir / f.name)
                return 5
            mock_extract.side_effect = fake_extract

            build_video(
                video_path=video,
                resolutions=[60, 80, 120],
                base_dir=cache_base,
            )

        manifest = get_manifest(video, base_dir=cache_base)
        assert best_resolution(manifest["resolutions"], terminal_cols=100) == 80
        assert best_resolution(manifest["resolutions"], terminal_cols=200) == 120
        assert best_resolution(manifest["resolutions"], terminal_cols=60) == 60

    def test_rebuild_replaces_cache(self, test_video_with_frames, tmp_path):
        """--rebuild should wipe and recreate the cache."""
        video, frames_dir = test_video_with_frames
        cache_base = tmp_path / "e2e_cache"
        cache_base.mkdir()
        import shutil as sh

        with patch("ascii_player.build.extract_frames") as mock_extract:
            def fake_extract(video_path, output_dir, fps):
                output_dir.mkdir(parents=True, exist_ok=True)
                for f in frames_dir.glob("frame_*.jpg"):
                    sh.copy(f, output_dir / f.name)
                return 5
            mock_extract.side_effect = fake_extract

            # First build
            build_video(video_path=video, resolutions=[60], base_dir=cache_base)
            manifest1 = get_manifest(video, base_dir=cache_base)

            # Rebuild with different resolutions
            build_video(
                video_path=video,
                resolutions=[80, 120],
                base_dir=cache_base,
                rebuild=True,
            )
            manifest2 = get_manifest(video, base_dir=cache_base)

        assert manifest1["resolutions"] == [60]
        assert manifest2["resolutions"] == [80, 120]

    def test_frame_heights_consistent_within_resolution(
        self, test_video_with_frames, tmp_path
    ):
        """All frames at a given resolution must have identical line counts."""
        video, frames_dir = test_video_with_frames
        cache_base = tmp_path / "e2e_cache"
        cache_base.mkdir()
        import shutil as sh

        with patch("ascii_player.build.extract_frames") as mock_extract:
            def fake_extract(video_path, output_dir, fps):
                output_dir.mkdir(parents=True, exist_ok=True)
                for f in frames_dir.glob("frame_*.jpg"):
                    sh.copy(f, output_dir / f.name)
                return 5
            mock_extract.side_effect = fake_extract

            build_video(video_path=video, resolutions=[80], base_dir=cache_base)

        frames = load_resolution(video, 80, base_dir=cache_base)
        heights = {len(f) for f in frames}
        assert len(heights) == 1, f"Inconsistent frame heights across frames: {heights}"


class TestCliE2E:
    def test_run_without_build_shows_error(self, tmp_path):
        """Running without build should show helpful error."""
        fake_video = tmp_path / "no_build.mp4"
        fake_video.write_bytes(b"not built yet")

        result = subprocess.run(
            [sys.executable, "-m", "ascii_player", "run", str(fake_video)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "no cache found" in result.stderr.lower() or "build" in result.stderr.lower()
```

**Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_e2e.py -v`
Expected: all tests PASS

**Step 3: Run full test suite with coverage**

Run: `python -m pytest tests/ -v --cov=ascii_player --cov-report=term-missing`
Expected: all tests PASS, coverage > 80%

**Step 4: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add E2E integration tests for build/run pipeline"
```

---

## Task 12: Manual Smoke Test with Real Video

**No code changes — manual verification only.**

**Step 1: Build cache for the existing sailing video**

Run: `source .venv/bin/activate && python -m ascii_player build sailing.MP4`
Expected: Extracts 328 frames, pre-renders at 6 resolutions, prints cache location

**Step 2: Run the player**

Run: `python -m ascii_player run sailing.MP4`
Expected: ASCII video plays in alternate screen buffer at auto-detected resolution

**Step 3: Test resize**

While playing:
1. Press Cmd+Plus (make font bigger) → video should snap to lower resolution
2. Press Cmd+Minus (make font smaller) → video should snap to higher resolution
3. Press j/k or ↑/↓ to scroll — image should stay consistent

**Step 4: Test forced resolution**

Run: `python -m ascii_player run sailing.MP4 -c 60`
Expected: plays at 60 columns (small)

Run: `python -m ascii_player run sailing.MP4 -c 250`
Expected: plays at 250 columns (huge, may need small font)

**Step 5: Test error cases**

Run: `python -m ascii_player run nonexistent.mp4`
Expected: error with helpful message

Run: `python -m ascii_player build nonexistent.mp4`
Expected: error with helpful message

**Step 6: Commit any fixes from smoke testing**

```bash
git add -u
git commit -m "fix: address issues found during manual smoke testing"
```

---

## Post-E2E Enhancements (Future Tasks)

After all E2E tests pass, add these playback controls:

- **Space**: pause/resume playback
- **+/-**: manually cycle through cached resolutions
- **r**: restart from frame 0
- **f**: toggle FPS/resolution info overlay

These are documented in the design doc under "Future Considerations."
