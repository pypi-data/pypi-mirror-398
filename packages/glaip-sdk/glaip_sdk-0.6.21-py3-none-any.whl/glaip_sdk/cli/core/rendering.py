"""CLI rendering utilities: Rich console helpers, viewer launchers, renderer builders.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import os
import sys
from contextlib import AbstractContextManager, contextmanager, nullcontext
from typing import Any

from rich.console import Console

from glaip_sdk.branding import ACCENT_STYLE
from glaip_sdk.cli.context import _get_view, get_ctx_value
from glaip_sdk.utils.rendering.renderer import (
    CapturingConsole,
    RendererFactoryOptions,
    RichStreamRenderer,
    make_default_renderer,
    make_verbose_renderer,
)

# Export console for backward compatibility
console = Console()


def _can_use_spinner(ctx: Any | None, active_console: Console) -> bool:
    """Check if spinner output is allowed in the current environment."""
    if ctx is not None:
        tty_enabled = bool(get_ctx_value(ctx, "tty", True))
        view = (_get_view(ctx) or "rich").lower()
        if not tty_enabled or view not in {"", "rich"}:
            return False

    if not active_console.is_terminal:
        return False

    return _stream_supports_tty(getattr(active_console, "file", None))


def _stream_supports_tty(stream: Any) -> bool:
    """Return True if the provided stream can safely render a spinner."""
    target = stream if hasattr(stream, "isatty") else sys.stdout
    try:
        return bool(target.isatty())
    except Exception:
        return False


def update_spinner(status_indicator: Any | None, message: str) -> None:
    """Update spinner text when a status indicator is active."""
    if status_indicator is None:
        return

    try:
        status_indicator.update(message)
    except Exception:  # pragma: no cover - defensive update
        pass


def stop_spinner(status_indicator: Any | None) -> None:
    """Stop an active spinner safely."""
    if status_indicator is None:
        return

    try:
        status_indicator.stop()
    except Exception:  # pragma: no cover - defensive stop
        pass


# Backwards compatibility aliases for legacy callers
_spinner_update = update_spinner
_spinner_stop = stop_spinner


def spinner_context(
    ctx: Any | None,
    message: str,
    *,
    console_override: Console | None = None,
    spinner: str = "dots",
    spinner_style: str = ACCENT_STYLE,
) -> AbstractContextManager[Any]:
    """Return a context manager that renders a spinner when appropriate."""
    active_console = console_override or console
    if not _can_use_spinner(ctx, active_console):
        return nullcontext()

    status = active_console.status(
        message,
        spinner=spinner,
        spinner_style=spinner_style,
    )

    if not hasattr(status, "__enter__") or not hasattr(status, "__exit__"):
        return nullcontext()

    return status


def _register_renderer_with_session(ctx: Any, renderer: RichStreamRenderer) -> None:
    """Attach renderer to an active slash session when present."""
    try:
        ctx_obj = getattr(ctx, "obj", None)
        session = ctx_obj.get("_slash_session") if isinstance(ctx_obj, dict) else None
        if session and hasattr(session, "register_active_renderer"):
            session.register_active_renderer(renderer)
    except Exception:
        # Never let session bookkeeping break renderer creation
        pass


def build_renderer(
    _ctx: Any,
    *,
    save_path: str | os.PathLike[str] | None,
    verbose: bool = False,
    _tty_enabled: bool = True,
    live: bool | None = None,
    snapshots: bool | None = None,
) -> tuple[RichStreamRenderer, Console | CapturingConsole]:
    """Build renderer and capturing console for CLI commands.

    Args:
        _ctx: Click context object for CLI operations.
        save_path: Path to save output to (enables capturing console).
        verbose: Whether to enable verbose mode.
        _tty_enabled: Whether TTY is available for interactive features.
        live: Whether to enable live rendering mode (overrides verbose default).
        snapshots: Whether to capture and store snapshots.

    Returns:
        Tuple of (renderer, capturing_console) for streaming output.
    """
    # Use capturing console if saving output
    working_console = CapturingConsole(console, capture=True) if save_path else console

    # Configure renderer based on verbose mode and explicit overrides
    live_enabled = bool(live) if live is not None else not verbose
    cfg_overrides = {
        "live": live_enabled,
        "append_finished_snapshots": bool(snapshots) if snapshots is not None else False,
    }
    renderer_console = (
        working_console.original_console if isinstance(working_console, CapturingConsole) else working_console
    )
    factory = make_verbose_renderer if verbose else make_default_renderer
    factory_options = RendererFactoryOptions(
        console=renderer_console,
        cfg_overrides=cfg_overrides,
        verbose=verbose if factory is make_default_renderer else None,
    )
    renderer = factory_options.build(factory)

    # Link the renderer back to the slash session when running from the palette.
    _register_renderer_with_session(_ctx, renderer)

    return renderer, working_console


@contextmanager
def with_client_and_spinner(
    ctx: Any,
    spinner_message: str,
    *,
    console_override: Console | None = None,
) -> Any:
    """Context manager for commands that need client and spinner.

    Args:
        ctx: Click context.
        spinner_message: Message to display in spinner.
        console_override: Optional console override.

    Yields:
        Client instance.
    """
    from glaip_sdk.cli.core.context import get_client  # noqa: PLC0415

    client = get_client(ctx)
    with spinner_context(ctx, spinner_message, console_override=console_override):
        yield client
