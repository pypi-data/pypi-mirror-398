"""Helpers for formatting CLI/slash command hints.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import click

from glaip_sdk.branding import HINT_COMMAND_STYLE, HINT_DESCRIPTION_COLOR


def in_slash_mode(ctx: click.Context | None = None) -> bool:
    """Return True when running inside the slash command palette."""
    if ctx is None:
        try:
            ctx = click.get_current_context(silent=True)
        except RuntimeError:
            ctx = None

    if ctx is None:
        return False

    obj = getattr(ctx, "obj", None)
    if isinstance(obj, dict):
        return bool(obj.get("_slash_session"))

    return bool(getattr(obj, "_slash_session", False))


def command_hint(
    cli_command: str | None,
    slash_command: str | None = None,
    *,
    ctx: click.Context | None = None,
) -> str | None:
    """Return the appropriate command string for the current mode."""
    if in_slash_mode(ctx):
        if not slash_command:
            return None
        return slash_command if slash_command.startswith("/") else f"/{slash_command}"

    if not cli_command:
        return None
    return f"aip {cli_command}"


def format_command_hint(command: str | None, description: str | None = None) -> str | None:
    """Return a Rich markup string that highlights a command hint."""
    if not command:
        return None

    highlighted = f"[{HINT_COMMAND_STYLE}]{command}[/]"
    if description:
        highlighted += f"  [{HINT_DESCRIPTION_COLOR}]{description}[/{HINT_DESCRIPTION_COLOR}]"
    return highlighted
