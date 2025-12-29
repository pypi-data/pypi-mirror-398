"""Serialization utilities for JSON/YAML read/write and resource attribute collection.

This module provides pure functions for file I/O operations and data serialization
that can be used by both CLI and SDK layers without coupling to Click or Rich.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import importlib
import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:  # pragma: no cover - type-only imports
    from rich.console import Console

    from glaip_sdk.models import MCP


def read_json(file_path: Path) -> dict[str, Any]:
    """Read data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid JSON
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path: Path, data: dict[str, Any], indent: int = 2) -> None:
    """Write data to JSON file.

    Args:
        file_path: Path to write JSON file
        data: Data to write
        indent: JSON indentation level (default: 2)
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def read_yaml(file_path: Path) -> dict[str, Any]:
    """Read data from YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid YAML
    """
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Handle instruction_lines array format for user-friendly YAML
    if isinstance(data, dict) and "instruction_lines" in data and isinstance(data["instruction_lines"], list):
        data["instruction"] = "\n\n".join(data["instruction_lines"])
        del data["instruction_lines"]

    # Handle instruction as list from YAML export (convert back to string)
    if isinstance(data, dict) and "instruction" in data and isinstance(data["instruction"], list):
        data["instruction"] = "\n\n".join(data["instruction"])

    return data


def write_yaml(file_path: Path, data: dict[str, Any]) -> None:
    """Write data to YAML file with user-friendly formatting.

    Args:
        file_path: Path to write YAML file
        data: Data to write
    """

    # Custom YAML dumper for user-friendly instruction formatting
    class LiteralString(str):
        """String subclass for YAML literal block scalar formatting."""

        pass

    def literal_string_representer(dumper: yaml.Dumper, data: "LiteralString") -> yaml.nodes.Node:
        """YAML representer for LiteralString to use literal block scalar style.

        Args:
            dumper: YAML dumper instance.
            data: LiteralString instance to represent.

        Returns:
            YAML node with literal block scalar style for multiline strings.
        """
        # Use literal block scalar (|) for multiline strings to preserve formatting
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    # Add custom representer to the YAML dumper
    yaml.add_representer(LiteralString, literal_string_representer)

    # Convert instruction to LiteralString for proper formatting
    if isinstance(data, dict) and "instruction" in data and data["instruction"]:
        data = data.copy()  # Don't modify original
        data["instruction"] = LiteralString(data["instruction"])

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_resource_from_file(file_path: Path) -> dict[str, Any]:
    """Load resource data from JSON or YAML file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with resource data

    Raises:
        ValueError: If file format is not supported
    """
    if file_path.suffix.lower() in [".yaml", ".yml"]:
        return read_yaml(file_path)
    elif file_path.suffix.lower() == ".json":
        return read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}. Only JSON and YAML files are supported.")


def write_resource_export(file_path: Path, data: dict[str, Any], format: str = "json") -> None:
    """Write resource export data to file.

    Args:
        file_path: Path to export file
        data: Resource data to export
        format: Export format ("json" or "yaml")
    """
    if format.lower() == "yaml" or file_path.suffix.lower() in [".yaml", ".yml"]:
        write_yaml(file_path, data)
    else:
        write_json(file_path, data)


_EXCLUDED_ATTRS = {
    "id",
    "created_at",
    "updated_at",
    "_client",
    "_raw_data",
}
_EXCLUDED_NAMES = {
    "model_dump",
    "dict",
    "json",
    "get",
    "post",
    "put",
    "delete",
    "save",
    "refresh",
    "update",
}
_PREFERRED_MAPPERS: tuple[str, ...] = ("model_dump", "dict", "to_dict")


def collect_attributes_for_export(resource: Any) -> dict[str, Any]:
    """Collect resource attributes suitable for export.

    The helper prefers structured dump methods when available and gracefully
    falls back to the object's attribute space. Internal fields, identifiers,
    and callables are filtered out so the result only contains user-configurable
    data.
    """
    mapping = _coerce_resource_to_mapping(resource)
    if mapping is None:  # pragma: no cover - defensive fallback when attribute introspection fails
        items = ((name, _safe_getattr(resource, name)) for name in _iter_public_attribute_names(resource))
    else:
        items = mapping.items()

    export: dict[str, Any] = {}
    for key, value in items:
        if _should_include_attribute(key, value):
            export[key] = value

    # Post-process agent exports to clean up unwanted transformations
    if hasattr(resource, "__class__") and resource.__class__.__name__ == "Agent":
        export = _clean_agent_export_data(export)

    return export


def _clean_agent_export_data(agent_data: dict[str, Any]) -> dict[str, Any]:
    """Clean up agent export data to remove unwanted transformations.

    This function addresses the issue where the backend API transforms
    the 'timeout' field into 'execution_timeout' in an 'agent_config' section
    during export, which is not desired for clean agent configuration exports.
    """
    cleaned = agent_data.copy()

    # Remove execution_timeout from agent_config if it exists
    if "agent_config" in cleaned and isinstance(cleaned["agent_config"], dict):
        agent_config = cleaned["agent_config"]
        if "execution_timeout" in agent_config:
            # Move execution_timeout back to root level as timeout
            cleaned["timeout"] = agent_config.pop("execution_timeout")

    return cleaned


def _coerce_resource_to_mapping(resource: Any) -> dict[str, Any] | None:
    """Return a mapping representation of ``resource`` when possible."""
    for attr in _PREFERRED_MAPPERS:
        method = getattr(resource, attr, None)
        if callable(method):
            try:
                data = method()
            except Exception:
                continue
            if isinstance(data, dict):
                return data

    if isinstance(resource, dict):
        return resource

    try:
        if hasattr(resource, "__dict__"):
            return dict(resource.__dict__)
    except Exception:  # pragma: no cover - pathological objects can still defeat coercion
        return None

    return None


def _iter_public_attribute_names(resource: Any) -> Iterable[str]:
    """Yield attribute names we should inspect on ``resource``."""
    seen: set[str] = set()
    names: list[str] = []

    def _collect(candidates: Iterable[str] | None) -> None:
        """Collect unique candidate attribute names.

        Args:
            candidates: Iterable of candidate attribute names.
        """
        for candidate in candidates or ():
            if candidate not in seen:
                seen.add(candidate)
                names.append(candidate)

    # Collect from __dict__
    _collect_from_dict(resource, _collect)

    # Collect from __annotations__
    _collect_from_annotations(resource, _collect)

    # Collect from __slots__
    _collect(getattr(resource, "__slots__", ()))

    # Fallback to dir() if no names found
    if not names:
        _collect_from_dir(resource, _collect)

    return iter(names)


def _collect_from_dict(resource: Any, collect_func: Callable[[Iterable[str]], None]) -> None:
    """Safely collect attribute names from __dict__."""
    try:
        if hasattr(resource, "__dict__"):
            dict_keys = getattr(resource, "__dict__", {})
            if dict_keys:
                collect_func(dict_keys.keys())
    except Exception:  # pragma: no cover - defensive programming
        pass


def _collect_from_annotations(resource: Any, collect_func: Callable[[Iterable[str]], None]) -> None:
    """Safely collect attribute names from __annotations__."""
    annotations = getattr(resource, "__annotations__", {})
    if annotations:
        collect_func(annotations.keys())


def _collect_from_dir(resource: Any, collect_func: Callable[[Iterable[str]], None]) -> None:
    """Safely collect attribute names from dir()."""
    try:
        collect_func(name for name in dir(resource) if not name.startswith("__"))
    except Exception:  # pragma: no cover - defensive programming
        pass


def _safe_getattr(resource: Any, name: str) -> Any:
    """Return getattr(resource, name) but swallow any exception and return None."""
    try:
        return getattr(resource, name)
    except Exception:
        return None


def _should_include_attribute(key: str, value: Any) -> bool:
    """Return True when an attribute should be serialized."""
    if key in _EXCLUDED_ATTRS or key in _EXCLUDED_NAMES:
        return False
    if key.startswith("_"):
        return False
    if callable(value):
        return False
    return True


def strip_empty_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove None values and empty dictionaries from a dictionary.

    Args:
        data: Dictionary to clean

    Returns:
        Cleaned dictionary with None values and empty dicts removed
    """
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            nested = strip_empty_fields(value)
            if nested:  # Only include non-empty dicts
                cleaned[key] = nested
        else:
            cleaned[key] = value

    return cleaned


def build_mcp_export_payload(
    mcp: "MCP",
    *,
    prompt_for_secrets: bool,
    placeholder: str,
    console: "Console",
) -> dict[str, Any]:
    """Build MCP export payload with authentication secret handling.

    This function prepares an MCP resource for export by:
    1. Starting from model_dump(exclude_none=True) for API alignment
    2. Cleaning internal fields (_client, empty metadata)
    3. Processing authentication with secret capture/placeholder logic
    4. Removing empty fields recursively

    Args:
        mcp: MCP model instance to export
        prompt_for_secrets: Whether to interactively prompt for missing secrets
        placeholder: Placeholder text for missing secrets
        console: Rich Console instance for user interaction

    Returns:
        Dictionary ready for export (JSON/YAML serialization)

    Raises:
        ImportError: If required modules (auth helpers) are not available
    """
    auth_module = importlib.import_module("glaip_sdk.cli.auth")
    prepare_authentication_export = auth_module.prepare_authentication_export

    # Start with model dump (excludes None values automatically)
    payload = mcp.model_dump(exclude_none=True)

    # Remove internal/CLI fields
    payload.pop("_client", None)

    # Remove empty metadata dict
    if "metadata" in payload and not payload["metadata"]:
        payload.pop("metadata")

    # Process authentication section
    if "authentication" in payload:
        processed_auth = prepare_authentication_export(
            payload["authentication"],
            prompt_for_secrets=prompt_for_secrets,
            placeholder=placeholder,
            console=console,
        )
        if processed_auth:
            payload["authentication"] = processed_auth
        else:
            payload.pop("authentication")

    # Apply final cleanup to remove any remaining empty fields
    payload = strip_empty_fields(payload)

    return payload


def validate_json_string(json_str: str) -> dict[str, Any]:
    """Validate JSON string and return parsed data.

    Args:
        json_str: JSON string to validate

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
