"""Keyboard-driven transcript toggling support for the live renderer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any

try:  # pragma: no cover - Windows-specific dependencies
    import msvcrt  # type: ignore[import]
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None  # type: ignore[assignment]

if os.name != "nt":  # pragma: no cover - POSIX-only imports
    import select
    import termios
    import tty


CTRL_T = "\x14"


class TranscriptToggleController:
    """Manage mid-run transcript toggling for RichStreamRenderer instances."""

    def __init__(self, *, enabled: bool) -> None:
        """Initialise controller.

        Args:
            enabled: Whether toggling should be active (usually gated by TTY checks).
        """
        self._enabled = enabled and bool(sys.stdin) and sys.stdin.isatty()
        self._lock = threading.Lock()
        self._posix_fd: int | None = None
        self._posix_attrs: list[int] | None = None
        self._active = False
        self._stop_event = threading.Event()
        self._poll_thread: threading.Thread | None = None

    @property
    def enabled(self) -> bool:
        """Return True when controller is able to process keypresses."""
        return self._enabled

    def on_stream_start(self, renderer: Any) -> None:
        """Prepare terminal state before streaming begins."""
        if not self._enabled:
            return

        if os.name == "nt":  # pragma: no cover - Windows behaviour not in CI
            self._active = True
            self._start_polling_thread(renderer)
            return

        fd = sys.stdin.fileno()
        try:
            attrs = termios.tcgetattr(fd)
        except Exception:
            self._enabled = False
            return

        try:
            tty.setcbreak(fd)
        except Exception:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, attrs)
            except Exception:
                pass
            self._enabled = False
            return

        with self._lock:
            self._posix_fd = fd
            self._posix_attrs = attrs
            self._active = True

        self._start_polling_thread(renderer)

    def on_stream_complete(self) -> None:
        """Restore terminal state when streaming ends."""
        if not self._active:
            return

        self._stop_polling_thread()

        if os.name == "nt":  # pragma: no cover - Windows behaviour not in CI
            self._active = False
            return

        with self._lock:
            fd = self._posix_fd
            attrs = self._posix_attrs
            self._posix_fd = None
            self._posix_attrs = None
            self._active = False

        if fd is None or attrs is None:
            return

        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, attrs)
        except Exception:
            pass

    def poll(self, renderer: Any) -> None:
        """Poll for toggle keypresses and update renderer if needed."""
        if not self._active:
            return

        if os.name == "nt":  # pragma: no cover - Windows behaviour not in CI
            self._poll_windows(renderer)
        else:
            self._poll_posix(renderer)

    # ------------------------------------------------------------------
    # Platform-specific polling
    # ------------------------------------------------------------------
    def _poll_windows(self, renderer: Any) -> None:
        if not msvcrt:  # pragma: no cover - safety guard
            return

        while msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == CTRL_T:
                renderer.toggle_transcript_mode()

    def _poll_posix(self, renderer: Any) -> None:  # pragma: no cover - requires TTY
        fd = self._posix_fd
        if fd is None:
            return

        while True:
            readable, _, _ = select.select([fd], [], [], 0)
            if not readable:
                return

            try:
                data = os.read(fd, 1)
            except Exception:
                return

            if not data:
                return

            ch = data.decode(errors="ignore")
            if ch == CTRL_T:
                renderer.toggle_transcript_mode()

    def _start_polling_thread(self, renderer: Any) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        if not self._active:
            return

        self._stop_event.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, args=(renderer,), daemon=True)
        self._poll_thread.start()

    def _stop_polling_thread(self) -> None:
        self._stop_event.set()
        thread = self._poll_thread
        if thread and thread.is_alive():
            thread.join(timeout=0.2)
        self._poll_thread = None

    def _poll_loop(self, renderer: Any) -> None:
        while self._active and not self._stop_event.is_set():
            try:
                if os.name == "nt":
                    self._poll_windows(renderer)
                else:
                    self._poll_posix(renderer)
            except Exception:
                # Never let background polling disrupt the main stream
                pass
            time.sleep(0.05)
