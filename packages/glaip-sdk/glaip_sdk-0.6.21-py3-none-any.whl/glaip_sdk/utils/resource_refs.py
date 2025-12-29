"""Resource reference utilities for ID/name extraction and UUID detection.

This module provides normalized helpers for working with resource references
across the SDK, consolidating logic that was previously duplicated between
CLI and SDK layers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import re
from typing import Any
from uuid import UUID


def is_uuid(value: str) -> bool:
    """Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if value is a valid UUID, False otherwise
    """
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def _extract_id_from_item(item: Any, *, skip_missing: bool = False) -> str | None:
    """Extract ID from a single item.

    Args:
        item: Item that may be a string, object with .id, or dict with "id" key.
        skip_missing: If True, return None for items without IDs. If False, convert to string.

    Returns:
        Extracted ID as string, or None if skip_missing=True and no ID found.
    """
    if isinstance(item, str):
        return item
    if hasattr(item, "id"):
        return str(item.id)
    if isinstance(item, dict) and "id" in item:
        return str(item["id"])
    if skip_missing:
        return None
    # Fallback: convert to string
    return str(item)


def extract_ids(items: list[str | Any] | None) -> list[str]:
    """Extract IDs from a list of objects or strings.

    This function unifies the behavior between CLI and SDK layers, always
    returning a list (empty list for None/empty input) rather than None.

    Args:
        items: List of items that may be strings, objects with .id, or other types

    Returns:
        List of extracted IDs (empty list if items is None/empty)

    Examples:
        extract_ids([{"id": "123"}, "456"]) -> ["123", "456"]
        extract_ids(None) -> []
        extract_ids([]) -> []
    """
    if not items:
        return []

    # Extract IDs from all items, converting non-ID items to strings
    extracted_ids = [_extract_id_from_item(item, skip_missing=False) for item in items]
    return [id_val for id_val in extracted_ids if id_val is not None]


def extract_names(items: list[str | Any] | None) -> list[str]:
    """Extract names from a list of objects or strings.

    Args:
        items: List of items that may be strings, objects with .name, or other types

    Returns:
        List of extracted names (empty list if items is None/empty)

    Examples:
        extract_names([{"name": "tool1"}, "tool2"]) -> ["tool1", "tool2"]
        extract_names(None) -> []
    """
    if not items:
        return []

    names = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif hasattr(item, "name"):
            names.append(str(item.name))
        elif isinstance(item, dict) and "name" in item:
            names.append(str(item["name"]))
        else:
            # Fallback: convert to string
            names.append(str(item))

    return names


def find_by_name(items: list[Any], name: str, case_sensitive: bool = False) -> list[Any]:
    """Filter items by name with optional case sensitivity.

    This is a common pattern used across different clients for client-side
    filtering when the backend doesn't support name query parameters.

    Args:
        items: List of items to filter
        name: Name to search for
        case_sensitive: Whether the search should be case sensitive

    Returns:
        Filtered list of items matching the name
    """
    if not name:
        return items

    if case_sensitive:
        return [item for item in items if name in item.name]
    else:
        return [item for item in items if name.lower() in item.name.lower()]


def sanitize_name(name: str) -> str:
    """Sanitize a name for resource creation.

    Args:
        name: Raw name input

    Returns:
        Sanitized name suitable for resource creation
    """
    # Remove special characters and normalize
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "-", name.strip())
    sanitized = re.sub(r"-+", "-", sanitized)  # Collapse multiple dashes
    return sanitized.lower().strip("-")


def validate_name_format(name: str, resource_type: str = "resource") -> str:
    """Validate resource name format and return cleaned version.

    Args:
        name: Name to validate
        resource_type: Type of resource (for error messages)

    Returns:
        Cleaned name

    Raises:
        ValueError: If name format is invalid
    """
    # Map resource types to proper display names
    type_display = {"agent": "Agent", "tool": "Tool", "mcp": "MCP"}
    display_type = type_display.get(resource_type.lower(), resource_type.title())

    if not name or not name.strip():
        raise ValueError(f"{display_type} name cannot be empty")

    cleaned_name = name.strip()

    if len(cleaned_name) < 1:
        raise ValueError(f"{display_type} name cannot be empty")

    if len(cleaned_name) > 100:
        raise ValueError(f"{display_type} name cannot be longer than 100 characters")

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9_-]+$", cleaned_name):
        raise ValueError(f"{display_type} name can only contain letters, numbers, hyphens, and underscores")

    return cleaned_name


def validate_name_uniqueness(name: str, existing_names: list[str], resource_type: str = "resource") -> None:
    """Validate that a resource name is unique.

    Args:
        name: Name to validate
        existing_names: List of existing names to check against
        resource_type: Type of resource (for error messages)

    Raises:
        ValueError: If name is not unique
    """
    if name.lower() in [existing.lower() for existing in existing_names]:
        raise ValueError(f"A {resource_type.lower()} named '{name}' already exists. Please choose a unique name.")
