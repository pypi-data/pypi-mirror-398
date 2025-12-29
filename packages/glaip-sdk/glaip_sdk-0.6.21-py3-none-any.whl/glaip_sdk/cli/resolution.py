"""CLI resource resolution utilities for handling ID/name references.

This module provides CLI-specific resource resolution functionality,
including interactive pickers and ambiguity handling.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Callable
from typing import Any

import click

from glaip_sdk.branding import ACCENT_STYLE
from glaip_sdk.cli.utils import resolve_resource, spinner_context


def resolve_resource_reference(
    ctx: Any,
    _client: Any,
    reference: str,
    resource_type: str,
    get_by_id_func: Callable,
    find_by_name_func: Callable,
    label: str,
    select: int | None = None,
    interface_preference: str | None = None,
    spinner_message: str | None = None,
) -> Any | None:
    """Resolve resource reference (ID or name) with ambiguity handling.

    This is a common pattern used across all resource types.

    Args:
        ctx: Click context for CLI operations.
        _client: API client instance for backend operations.
        reference: Resource ID or name to resolve.
        resource_type: Type of resource being resolved.
        get_by_id_func: Function to get resource by ID.
        find_by_name_func: Function to find resources by name.
        label: Label for error messages and user feedback.
        select: Selection index for ambiguous matches in non-interactive mode.
        interface_preference: Interface preference for user interaction ("fuzzy" or "questionary").
        spinner_message: Custom message to show during resolution process.

    Returns:
        Resolved resource object or None if not found.

    Raises:
        click.ClickException: If resolution fails.
    """
    try:
        message = spinner_message if spinner_message is not None else f"[bold blue]Fetching {label}…[/bold blue]"
        with spinner_context(ctx, message, spinner_style=ACCENT_STYLE) as status_indicator:
            return resolve_resource(
                ctx,
                reference,
                get_by_id=get_by_id_func,
                find_by_name=find_by_name_func,
                label=label,
                select=select,
                interface_preference=interface_preference,
                status_indicator=status_indicator,
            )
    except Exception as e:
        raise click.ClickException(f"Failed to resolve {resource_type.lower()}: {e}") from e
