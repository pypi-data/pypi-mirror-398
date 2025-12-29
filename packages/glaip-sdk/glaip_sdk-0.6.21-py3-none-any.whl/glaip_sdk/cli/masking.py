"""Masking helpers for CLI output.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from typing import Any

from glaip_sdk.cli.constants import MASK_SENSITIVE_FIELDS, MASKING_ENABLED

__all__ = [
    "mask_payload",
    "mask_rows",
    "_mask_value",
    "_mask_any",
    "_maybe_mask_row",
    "_resolve_mask_fields",
    "mask_api_key_display",
]


def _mask_value(raw: Any) -> str:
    """Return a masked representation of the provided value.

    Args:
        raw: The raw value to mask, converted to string.

    Returns:
        str: A masked representation showing first 4 and last 4 characters
             separated by dots, or "••••" for strings ≤ 8 characters.
    """
    text = str(raw)
    if len(text) <= 8:
        return "••••"
    return f"{text[:4]}••••••••{text[-4:]}"


def _mask_any(value: Any, mask_fields: set[str]) -> Any:
    """Recursively mask sensitive fields in mappings and iterables.

    Args:
        value: The value to process - can be dict, list, or any other type.
        mask_fields: Set of field names (lowercase) that should be masked.

    Returns:
        Any: The processed value with sensitive fields masked. Dicts and lists
             are processed recursively, other values are returned unchanged.
    """
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, raw in value.items():
            if isinstance(key, str) and key.lower() in mask_fields and raw is not None:
                masked[key] = _mask_value(raw)
            else:
                masked[key] = _mask_any(raw, mask_fields)
        return masked

    if isinstance(value, list):
        return [_mask_any(item, mask_fields) for item in value]

    return value


def _maybe_mask_row(row: dict[str, Any], mask_fields: set[str]) -> dict[str, Any]:
    """Mask a single row when masking is enabled.

    Args:
        row: A dictionary representing a single row of data.
        mask_fields: Set of field names to mask. If empty, returns row unchanged.

    Returns:
        dict[str, Any]: The row with sensitive fields masked, or the original
                       row if no mask_fields are provided.
    """
    if not mask_fields:
        return row
    return _mask_any(row, mask_fields)


def _resolve_mask_fields() -> set[str]:
    """Return the configured set of fields that should be masked."""
    if not MASKING_ENABLED:
        return set()
    return set(MASK_SENSITIVE_FIELDS)


def mask_payload(payload: Any) -> Any:
    """Mask sensitive values in an arbitrary payload when masking is enabled.

    Args:
        payload: Any data structure (dict, list, or primitive) to mask.

    Returns:
        Any: The payload with sensitive fields masked based on configuration.
    """
    mask_fields = _resolve_mask_fields()
    if not mask_fields:
        return payload
    try:
        return _mask_any(payload, mask_fields)
    except Exception:
        return payload


def mask_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mask sensitive values in row-oriented data when masking is enabled.

    Args:
        rows: List of dictionaries representing rows of tabular data.

    Returns:
        list[dict[str, Any]]: List of rows with sensitive fields masked based
                              on configuration. Returns original rows if
                              masking is disabled or if an error occurs.
    """
    mask_fields = _resolve_mask_fields()
    if not mask_fields:
        return rows
    try:
        return [_maybe_mask_row(row, mask_fields) for row in rows]
    except Exception:
        return rows


def mask_api_key_display(value: str | None) -> str:
    """Mask API keys for CLI display while preserving readability for short keys."""
    if not value:
        return ""
    length = len(value)
    if length <= 4:
        return "***"
    if length <= 8:
        return value[:1] + "••••" + value[-1:]
    return value[:4] + "••••" + value[-4:]
