"""Console handling utilities for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import io
from typing import Any

from rich.console import Console as RichConsole


class CapturingConsole:
    """Console wrapper that captures all output for saving."""

    def __init__(self, original_console: RichConsole, capture: bool = False) -> None:
        """Initialize the capturing console.

        Args:
            original_console: The original Rich console instance
            capture: Whether to capture output in addition to displaying it
        """
        self.original_console = original_console
        self.capture = capture
        self.captured_output: list[str] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to both original console and capture buffer if capturing."""
        # Always print to original console
        self.original_console.print(*args, **kwargs)

        if self.capture:
            # Capture the output as text
            # Create a temporary console to capture output
            temp_output = io.StringIO()
            temp_console = RichConsole(
                file=temp_output,
                width=self.original_console.size.width,
                legacy_windows=False,
                force_terminal=False,
            )
            temp_console.print(*args, **kwargs)
            self.captured_output.append(temp_output.getvalue())

    def get_captured_output(self) -> str:
        """Get the captured output as plain text."""
        if self.capture:
            return "".join(self.captured_output)
        return ""

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attributes to the original console."""
        return getattr(self.original_console, name)
