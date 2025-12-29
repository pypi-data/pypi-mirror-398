"""Shared helpers for toggling Textual loading indicators.

Note: uses Textual's built-in LoadingIndicator as the MVP; upgrade to the
PulseIndicator from cli-textual-animated-indicators.md when shipped.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

try:  # pragma: no cover - optional dependency
    from textual.widgets import LoadingIndicator
except Exception:  # pragma: no cover - optional dependency
    LoadingIndicator = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - type checking aid
    from textual.widgets import LoadingIndicator as _LoadingIndicatorType

    LoadingIndicator: type[_LoadingIndicatorType] | None


def _set_indicator_display(app: object, selector: str, visible: bool) -> None:
    """Safely toggle a LoadingIndicator's display property."""
    if LoadingIndicator is None:
        return
    try:
        indicator = app.query_one(selector, LoadingIndicator)  # type: ignore[arg-type]
        indicator.display = visible
    except Exception:
        # Ignore lookup/rendering errors to keep UI resilient
        return


def show_loading_indicator(
    app: object,
    selector: str,
    *,
    message: str | None = None,
    set_status: Callable[..., None] | None = None,
    status_style: str = "cyan",
) -> None:
    """Show a loading indicator and optionally set a status message."""
    _set_indicator_display(app, selector, True)
    if message and set_status:
        try:
            set_status(message, status_style)
        except TypeError:
            # Fallback for setters that accept only a single arg or kwargs
            try:
                set_status(message)
            except Exception:
                return


def hide_loading_indicator(app: object, selector: str) -> None:
    """Hide a loading indicator."""
    _set_indicator_display(app, selector, False)
