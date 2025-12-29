"""Shared helpers for creating and printing Rich markup content.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markup import MarkupError
from rich.text import Text


def markup_text(message: str, **kwargs: Any) -> Text:
    """Create a Rich Text instance from markup with graceful fallback."""
    try:
        return Text.from_markup(message, **kwargs)
    except MarkupError:
        return Text(message, **kwargs)


def print_markup(message: str, *, console: Console | None = None, **kwargs: Any) -> None:
    """Print markup-aware text to the provided console (default: new Console)."""
    target_console = console or Console()
    target_console.print(markup_text(message, **kwargs))
