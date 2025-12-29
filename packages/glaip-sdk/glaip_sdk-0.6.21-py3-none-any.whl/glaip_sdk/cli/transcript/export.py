"""Shared helpers for transcript export workflows.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from glaip_sdk.cli.transcript.cache import (
    latest_manifest_entry,
    resolve_manifest_entry,
)


def resolve_manifest_for_export(ctx: Any, run_id: str | None) -> dict[str, Any] | None:
    """Resolve a manifest entry for export based on run id or recent context."""
    if run_id:
        return resolve_manifest_entry(run_id)

    ctx_obj = ctx if isinstance(ctx, dict) else getattr(ctx, "obj", None)
    if isinstance(ctx_obj, dict):
        candidate = ctx_obj.get("_last_transcript_manifest")
        if isinstance(candidate, dict):
            return candidate

    return latest_manifest_entry()


def normalise_export_destination(path: Path) -> Path:
    """Return an absolute path for the export destination."""
    expanded = path.expanduser()
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


__all__ = ["resolve_manifest_for_export", "normalise_export_destination"]
