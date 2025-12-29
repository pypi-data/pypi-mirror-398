"""Context-related helpers for the glaip CLI.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

__all__ = [
    "get_ctx_value",
    "_get_view",
    "_set_view",
    "_set_json",
    "output_flags",
    "detect_export_format",
]


def get_ctx_value(ctx: Any, key: str, default: Any = None) -> Any:
    """Safely resolve a value from a click context object.

    Args:
        ctx: Click context object to extract value from
        key: Key to retrieve from the context
        default: Default value if key is not found

    Returns:
        The value associated with the key, or the default if not found
    """
    if ctx is None:
        return default

    obj = getattr(ctx, "obj", None)
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            return default

    return getattr(obj, key, default) if hasattr(obj, key) else default


def _get_view(ctx: Any) -> str:
    """Resolve the active view preference from context.

    Args:
        ctx: Click context object containing view preferences

    Returns:
        The view format string (rich, plain, json, md), defaults to 'rich'
    """
    view = get_ctx_value(ctx, "view")
    if view:
        return view

    fallback = get_ctx_value(ctx, "format")
    return fallback or "rich"


def _set_view(ctx: Any, _param: Any, value: str) -> None:
    """Click callback to persist the `--view/--output` option.

    Args:
        ctx: Click context object to store the view preference
        _param: Click parameter object (unused)
        value: The view format string to store
    """
    if not value:
        return
    ctx.ensure_object(dict)
    ctx.obj["view"] = value


def _set_json(ctx: Any, _param: Any, value: bool) -> None:
    """Click callback for the `--json` shorthand flag.

    Args:
        ctx: Click context object to store the view preference
        _param: Click parameter object (unused)
        value: Boolean flag indicating json mode
    """
    if not value:
        return
    ctx.ensure_object(dict)
    ctx.obj["view"] = "json"


def output_flags() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add shared output flags (`--view`, `--json`) to commands.

    Returns:
        A decorator function that adds output format options to click commands
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        """Apply output flags to a click command.

        Args:
            f: Click command function to decorate.

        Returns:
            Decorated command function.
        """
        f = click.option(
            "--json",
            "json_mode",
            is_flag=True,
            expose_value=False,
            help="Shortcut for --view json",
            callback=_set_json,
        )(f)
        f = click.option(
            "-o",
            "--output",
            "--view",
            "view_opt",
            type=click.Choice(["rich", "plain", "json", "md"]),
            expose_value=False,
            help="Output format",
            callback=_set_view,
        )(f)
        return f

    return decorator


def detect_export_format(file_path: str | Path) -> str:
    """Detect the export format from the file extension.

    Args:
        file_path: Path to the file to analyze

    Returns:
        The format string ('yaml' or 'json') based on file extension
    """
    path = Path(file_path)
    return "yaml" if path.suffix.lower() in {".yaml", ".yml"} else "json"
