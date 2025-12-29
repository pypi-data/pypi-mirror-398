"""CLI I/O utilities for file import/export orchestration.

This module handles file operations and network requests for CLI commands,
wrapping core serialization utilities with Click-friendly error handling.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from glaip_sdk.branding import WARNING_STYLE
from glaip_sdk.utils.serialization import (
    collect_attributes_for_export,
    load_resource_from_file,
    write_resource_export,
)

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from rich.console import Console


def _create_console() -> "Console":
    """Return a Console instance (lazy import for easier testing)."""
    try:
        console_module = import_module("rich.console")
    except ImportError as exc:  # pragma: no cover - optional dependency missing
        raise RuntimeError("Rich Console is not available") from exc
    return console_module.Console()


def load_resource_from_file_with_validation(file_path: Path, resource_type: str) -> dict[str, Any]:
    """Load resource data from JSON or YAML file with CLI-friendly error handling.

    Args:
        file_path: Path to the file
        resource_type: Type of resource (for error messages)

    Returns:
        Dictionary with resource data

    Raises:
        click.ClickException: If file operations fail
    """
    try:
        return load_resource_from_file(file_path)
    except FileNotFoundError as err:
        raise click.ClickException(f"File not found: {file_path}") from err
    except ValueError as e:
        raise click.ClickException(f"Invalid {resource_type.lower()} file format: {e}") from e
    except Exception as e:
        raise click.ClickException(f"Failed to load {resource_type.lower()} file: {e}") from e


def export_resource_to_file_with_validation(resource: Any, file_path: Path, format: str = "json") -> None:
    """Export resource to file with CLI-friendly error handling.

    Args:
        resource: Resource object to export
        file_path: Path to export file
        format: Export format ("json" or "yaml")

    Raises:
        click.ClickException: If export operations fail
    """
    try:
        # Get all available resource attributes dynamically
        export_data = collect_attributes_for_export(resource)
        write_resource_export(file_path, export_data, format)
    except Exception as e:
        raise click.ClickException(f"Failed to export resource: {e}") from e


def fetch_raw_resource_details(client: Any, resource: Any, resource_type: str) -> Any:
    """Fetch raw resource details directly from API to preserve ALL fields.

    Args:
        client: API client
        resource: Resource object
        resource_type: Type of resource ("agents", "tools", "mcps")

    Returns:
        Raw API response data or None if failed

    Notes:
        This is CLI-specific functionality for displaying comprehensive resource details.
    """
    console = _create_console()

    try:
        resource_id = str(getattr(resource, "id", "")).strip()
        if resource_id:
            # Make direct API call to get raw response
            response = client.http_client.get(f"/{resource_type}/{resource_id}")
            response.raise_for_status()
            raw_response = response.json()

            # If it's a wrapped response (success/data/message), extract the data
            if isinstance(raw_response, dict) and "data" in raw_response:
                return raw_response["data"]
            else:
                # Direct response
                return raw_response
    except Exception as e:
        console.print(f"[{WARNING_STYLE}]Failed to fetch raw {resource_type} details: {e}[/]")
        # Fall back to regular method
        return None
    return None
