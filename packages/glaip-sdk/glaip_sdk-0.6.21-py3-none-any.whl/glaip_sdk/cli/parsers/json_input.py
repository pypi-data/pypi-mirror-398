"""JSON input parser for CLI options.

Handles both inline JSON strings and @file references.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import json
import os
from pathlib import Path
from typing import Any

import click
import yaml


def _looks_like_file_path(value: str) -> bool:
    """Check if string looks like a file reference.

    Args:
        value: String to check for file-like patterns

    Returns:
        True if the string appears to be a file path
    """
    return (
        value.lower().endswith((".json", ".yaml", ".yml"))
        or "/" in value
        or "\\" in value  # Path separators
        or value.startswith(("./", "../"))  # Relative paths
        or value.count(".") > 1  # Likely a filename with extension
    )


def _format_file_error(prefix: str, file_path_str: str, resolved_path: Path, *, detail: str | None = None) -> str:
    r"""Format a file-related error message with path context.

    Args:
        prefix: Main error message
        file_path_str: Original file path string provided by user
        resolved_path: Resolved absolute path
        detail: Optional additional detail to append

    Returns:
        Formatted error message string with file path context

    Examples:
        >>> from pathlib import Path
        >>> _format_file_error("File not found", "config.json", Path("/abs/config.json"))
        'File not found: config.json\nResolved path: /abs/config.json'
    """
    parts = [f"{prefix}: {file_path_str}", f"Resolved path: {resolved_path}"]
    if detail:
        parts.append(detail)
    return "\n".join(parts)


def _parse_json_from_file(file_path_str: str) -> Any:
    """Parse JSON or YAML from a file path.

    Args:
        file_path_str: Path to the JSON or YAML file (without @ prefix).

    Returns:
        Parsed dictionary from file.

    Raises:
        click.ClickException: If file not found, not readable, empty, or invalid format.
    """
    # Resolve relative paths against CWD
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    # Check if file exists and is a regular file
    if not file_path.is_file():
        raise click.ClickException(_format_file_error("File not found or not a file", file_path_str, file_path))

    # Check if file is readable
    if not os.access(file_path, os.R_OK):
        raise click.ClickException(
            _format_file_error("File not readable (permission denied)", file_path_str, file_path)
        )

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise click.ClickException(
            _format_file_error("Error reading file", file_path_str, file_path, detail=f"Error: {e}")
        ) from e

    # Check for empty content
    if not content.strip():
        raise click.ClickException(_format_file_error("File is empty", file_path_str, file_path))

    # Determine file format and parse accordingly
    file_ext = file_path.suffix.lower()

    if file_ext in [".yaml", ".yml"]:
        # Parse YAML from file content
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise click.ClickException(
                _format_file_error(
                    "Invalid YAML in file",
                    file_path_str,
                    file_path,
                    detail=f"Error: {e}",
                )
            ) from e
    else:
        # Default to JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise click.ClickException(
                _format_file_error(
                    "Invalid JSON in file",
                    file_path_str,
                    file_path,
                    detail=f"Error: {e.msg} at line {e.lineno}, column {e.colno}",
                )
            ) from e


def parse_json_input(value: str | None) -> Any:
    """Parse JSON input from inline string or file reference.

    Args:
        value: JSON string or @file reference. If None, returns None.

    Returns:
        Parsed JSON value (dict, list, str, int, float, bool, None) or None if value is None.

    Raises:
        click.ClickException: If file not found, not readable, empty, or invalid JSON.

    Examples:
        >>> parse_json_input('{"key": "value"}')
        {'key': 'value'}

        >>> parse_json_input('@/path/to/config.json')
        # Returns content of config.json parsed as JSON

        >>> parse_json_input('/path/to/config.json')
        # Fallback: treats as file path if JSON parsing fails

        >>> parse_json_input(None)
        None
    """
    if value is None:
        return None

    # Check if value is a file reference (strip whitespace first)
    trimmed = value.strip()
    if trimmed.startswith("@"):
        return _parse_json_from_file(trimmed[1:])

    # Parse inline JSON
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        # Check if the value looks like a file path and provide helpful hint
        if _looks_like_file_path(trimmed):
            raise click.ClickException(
                f"Invalid JSON in inline value\n"
                f"Error: {e.msg} at line {e.lineno}, column {e.colno}\n"
                f"\n💡 Did you mean to load this from a file? "
                f"File-based config values should start with @ (e.g., @{trimmed})"
            ) from e

        raise click.ClickException(
            f"Invalid JSON in inline value\nError: {e.msg} at line {e.lineno}, column {e.colno}"
        ) from e
