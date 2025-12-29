"""Shared datetime parsing helpers used across CLI and rendering modules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

__all__ = ["coerce_datetime", "from_numeric_timestamp"]

_Z_SUFFIX = "+00:00"


def from_numeric_timestamp(raw_value: Any) -> datetime | None:
    """Convert unix timestamp-like values to datetime with sanity checks."""
    try:
        candidate = float(raw_value)
    except Exception:
        return None

    if candidate < 1_000_000_000:
        return None

    try:
        return datetime.fromtimestamp(candidate, tz=timezone.utc)
    except Exception:
        return None


def _parse_iso(value: str | None) -> datetime | None:
    """Parse ISO8601 strings while tolerating legacy 'Z' suffixes."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", _Z_SUFFIX))
    except Exception:
        return None


def coerce_datetime(value: Any) -> datetime | None:
    """Best-effort conversion of assorted timestamp inputs to aware UTC datetimes."""
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = from_numeric_timestamp(value)
    elif isinstance(value, str):
        dt = _parse_iso(value) or from_numeric_timestamp(value)
    else:
        return None

    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
