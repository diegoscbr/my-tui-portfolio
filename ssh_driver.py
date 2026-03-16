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
from __future__ import annotations

import asyncio
import io
import threading
from typing import IO, Any

from textual import events
from textual.app import App
from textual.driver import Driver
from textual.drivers._writer_thread import WriterThread
from textual._xterm_parser import XTermParser
from textual.geometry import Size


class ChannelFileWrapper:
    """File-like wrapper around an SSH channel or any writable stream.

    Presents the interface Textual's WriterThread expects:
    .write(str), .flush(), .fileno(), .isatty().
    """

    def __init__(self, stream: IO[str]) -> None:
        self._stream = stream

    def write(self, data: str) -> int:
        try:
            encoded: str | bytes = data.encode("utf-8") if isinstance(data, str) else data
            try:
                self._stream.write(encoded)
            except TypeError:
                # Stream is text-mode (e.g. StringIO in tests) — write as str
                self._stream.write(encoded.decode("utf-8") if isinstance(encoded, bytes) else encoded)
        except (BrokenPipeError, OSError):
            return 0
        return len(data)

    def flush(self) -> None:
        if hasattr(self._stream, "flush"):
            self._stream.flush()

    def fileno(self) -> int:
        if hasattr(self._stream, "fileno"):
            return self._stream.fileno()
        return -1

    def isatty(self) -> bool:
        return True


class SSHDriver(Driver):
    """Textual driver that routes I/O through an SSH channel.

    Output goes to the provided output_stream instead of sys.stdout.
    Input is fed via feed_input() from the asyncssh session handler.
    Terminal size is set from SSH PTY dimensions.
    """

    def __init__(
        self,
        app: App[Any],
        *,
        output_stream: IO[str],
        input_queue: asyncio.Queue[str] | None = None,
        debug: bool = False,
        mouse: bool = True,
        size: tuple[int, int] | None = None,
    ) -> None:
        super().__init__(app, debug=debug, mouse=mouse, size=size)
        self._output_stream = output_stream
        self._file_wrapper = ChannelFileWrapper(output_stream)
        self._input_queue = input_queue
        self._size = size or (80, 24)
        self._writer_thread: WriterThread | None = None
        self._input_thread: threading.Thread | None = None
        self._exit_event = threading.Event()

    def get_size(self) -> tuple[int, int]:
        """Return terminal size from SSH PTY dimensions."""
        return self._size

    def set_size(self, width: int, height: int) -> None:
        """Update terminal size (called on SSH window-change event)."""
        self._size = (width, height)
        size = Size(width, height)
        self._app.post_message(events.Resize(size, size))

    def write(self, data: str) -> None:
        """Write output data to the SSH channel via writer thread."""
        if self._writer_thread is not None:
            self._writer_thread.write(data)
        else:
            self._file_wrapper.write(data)
            self._file_wrapper.flush()

    def flush(self) -> None:
        """Flush buffered output."""
        self._file_wrapper.flush()

    def start_application_mode(self) -> None:
        """Initialize the driver — start writer thread and send initial size."""
        self._writer_thread = WriterThread(self._file_wrapper)
        self._writer_thread.start()

        self.write("\x1b[?1049h")  # alt screen
        self.write("\x1b[?25l")  # hide cursor
        if self._mouse:
            self.write("\x1b[?1003h")  # mouse tracking

        size = Size(self._size[0], self._size[1])
        self._app.post_message(events.Resize(size, size))

        if self._input_queue is not None:
            self._input_thread = threading.Thread(
                target=self._run_input_thread, daemon=True
            )
            self._input_thread.start()

    def _run_input_thread(self) -> None:
        """Read input from the asyncio queue and feed to Textual's XTermParser."""
        parser = XTermParser(self._debug)
        loop = asyncio.new_event_loop()
        try:
            while not self._exit_event.is_set():
                try:
                    data = loop.run_until_complete(
                        asyncio.wait_for(
                            self._input_queue.get(), timeout=0.1
                        )
                    )
                    if data is None:
                        break
                    for event in parser.feed(data):
                        self.process_message(event)
                except asyncio.TimeoutError:
                    for event in parser.tick():
                        self.process_message(event)
        finally:
            loop.close()

    def disable_input(self) -> None:
        """Stop accepting input."""
        self._exit_event.set()

    def stop_application_mode(self) -> None:
        """Restore terminal state and clean up threads."""
        self._exit_event.set()

        if self._mouse:
            self.write("\x1b[?1003l")  # disable mouse tracking
        self.write("\x1b[?25h")  # show cursor
        self.write("\x1b[?1049l")  # exit alt screen

        if self._writer_thread is not None:
            self._writer_thread.stop()
            self._writer_thread = None

        if self._input_thread is not None:
            self._input_thread.join(timeout=2)
            self._input_thread = None

    @classmethod
    def create_for_test(
        cls,
        output_stream: IO[str] | None = None,
        size: tuple[int, int] = (80, 24),
    ) -> SSHDriver:
        """Create an SSHDriver for unit testing without a full App."""
        stream = output_stream or io.StringIO()
        app = App()
        return cls(
            app,
            output_stream=stream,
            size=size,
        )
