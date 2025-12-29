"""Shared timing helpers for renderer components.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import Any


def coerce_server_time(value: Any) -> float | None:
    """Convert a raw SSE/server time payload into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_timeline_duration(
    start_server: float | None,
    end_server: float | None,
    start_monotonic: float | None,
    end_monotonic: float | None,
) -> float | None:
    """Return best-effort elapsed time using server or monotonic clocks."""
    if start_server is not None and end_server is not None:
        return max(0.0, float(end_server) - float(start_server))
    if start_monotonic is not None and end_monotonic is not None:
        try:
            return max(0.0, float(end_monotonic) - float(start_monotonic))
        except Exception:
            return None
    return None
