"""Import/export utilities for schema transforms and data merging.

This module provides functions for converting between export and import formats,
merging imported data with CLI arguments, and handling relationship flattening.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

from glaip_sdk.utils.resource_refs import _extract_id_from_item


def extract_ids_from_export(items: list[Any]) -> list[str]:
    """Extract IDs from export format (list of dicts with id/name fields).

    This function is similar to `extract_ids` in `resource_refs.py` but differs in behavior:
    - This function SKIPS items without IDs (doesn't convert to string)
    - `extract_ids` converts items without IDs to strings as fallback

    This difference is intentional: export format should only include actual IDs,
    while general resource reference extraction may need fallback string conversion.

    Args:
        items: List of items (dicts with id/name or strings)

    Returns:
        List of extracted IDs (only items with actual IDs)

    Examples:
        extract_ids_from_export([{"id": "123", "name": "tool"}]) -> ["123"]
        extract_ids_from_export(["123", "456"]) -> ["123", "456"]
        extract_ids_from_export([{"name": "tool"}, "123"]) -> ["123"]  # Skip items without ID
    """
    if not items:
        return []

    ids = []
    for item in items:
        extracted = _extract_id_from_item(item, skip_missing=True)
        if extracted is not None:
            ids.append(extracted)

    return ids


def convert_export_to_import_format(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Convert export format to import-compatible format (extract IDs from objects).

    Args:
        data: Export format data with full objects

    Returns:
        Import format data with extracted IDs

    Notes:
        - Converts tools/agents from dict objects to ID lists
        - Preserves all other data unchanged
    """
    import_data = data.copy()

    for key in ["tools", "agents", "mcps"]:
        if key in import_data and isinstance(import_data[key], list):
            import_data[key] = extract_ids_from_export(import_data[key])

    return import_data


def _get_default_array_fields() -> list[str]:
    """Get default array fields that should be merged."""
    return ["tools", "agents", "mcps"]


def _should_use_cli_value(cli_value: Any) -> bool:
    """Check if CLI value should be used."""
    return cli_value is not None and (not isinstance(cli_value, (list, tuple)) or len(cli_value) > 0)


def _handle_array_field_merge(key: str, cli_value: Any, import_data: dict[str, Any]) -> Any:
    """Handle merging of array fields."""
    import_value = import_data[key]
    if isinstance(import_value, list):
        return list(cli_value) + import_value
    else:
        return cli_value


def _merge_cli_values_with_import(
    merged: dict[str, Any],
    cli_args: dict[str, Any],
    import_data: dict[str, Any],
    array_fields: list[str],
) -> None:
    """Merge CLI values into merged dict."""
    for key, cli_value in cli_args.items():
        if _should_use_cli_value(cli_value):
            # CLI value takes precedence (for non-empty values)
            if key in array_fields and key in import_data:
                # For array fields, combine CLI and imported values
                merged[key] = _handle_array_field_merge(key, cli_value, import_data)
            else:
                merged[key] = cli_value
        elif key in import_data:
            # Use imported value if no CLI value
            merged[key] = import_data[key]


def _add_import_only_fields(merged: dict[str, Any], import_data: dict[str, Any]) -> None:
    """Add fields that exist only in import data."""
    for key, import_value in import_data.items():
        if key not in merged:
            merged[key] = import_value


def merge_import_with_cli_args(
    import_data: dict[str, Any],
    cli_args: dict[str, Any],
    array_fields: list[str] = None,
) -> dict[str, Any]:
    """Merge imported data with CLI arguments, preferring CLI args.

    Args:
        import_data: Data loaded from import file
        cli_args: Arguments passed via CLI
        array_fields: Fields that should be combined (merged) rather than replaced

    Returns:
        Merged data dictionary

    Notes:
        - CLI arguments take precedence over imported data
        - Array fields (tools, agents, mcps) are combined rather than replaced
        - Empty arrays/lists are treated as None (no override)
    """
    if array_fields is None:
        array_fields = _get_default_array_fields()

    merged = {}
    _merge_cli_values_with_import(merged, cli_args, import_data, array_fields)
    _add_import_only_fields(merged, import_data)

    return merged


def flatten_relationships_for_import(
    data: dict[str, Any], fields: tuple[str, ...] = ("tools", "agents")
) -> dict[str, Any]:
    """Flatten relationship fields for import format.

    This is an alias for convert_export_to_import_format with configurable fields.

    Args:
        data: Export format data with full objects
        fields: Tuple of field names to flatten to IDs

    Returns:
        Import format data with specified fields flattened to IDs
    """
    import_data = data.copy()

    for field in fields:
        if field in import_data and isinstance(import_data[field], list):
            import_data[field] = extract_ids_from_export(import_data[field])

    return import_data
