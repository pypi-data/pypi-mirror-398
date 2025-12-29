"""Utilities for launching the post-run transcript viewer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from rich.console import Console

from glaip_sdk.cli.context import get_ctx_value
from glaip_sdk.cli.transcript.cache import (
    export_transcript as export_cached_transcript,
)
from glaip_sdk.cli.transcript.capture import StoredTranscriptContext
from glaip_sdk.cli.transcript.viewer import ViewerContext, run_viewer_session


def should_launch_post_run_viewer(ctx: Any, console: Console, *, slash_mode: bool) -> bool:
    """Return True if the viewer should open automatically."""
    if slash_mode:
        return False
    ctx_obj = getattr(ctx, "obj", None)
    if isinstance(ctx_obj, dict) and ctx_obj.get("_slash_session"):
        return False
    if get_ctx_value(ctx, "view", "rich") != "rich":
        return False
    if not bool(get_ctx_value(ctx, "tty", True)):
        return False
    if not console.is_terminal:
        return False
    try:
        if not sys.stdin.isatty():
            return False
    except Exception:
        return False
    return True


def maybe_launch_post_run_viewer(
    ctx: Any,
    transcript_context: StoredTranscriptContext | None,
    *,
    console: Console,
    slash_mode: bool,
) -> None:
    """Launch the post-run viewer when context and settings allow it."""
    if transcript_context is None:
        return
    if not should_launch_post_run_viewer(ctx, console, slash_mode=slash_mode):
        return

    manifest_entry = transcript_context.store_result.manifest_entry
    run_id = manifest_entry.get("run_id")
    if not run_id:
        return

    viewer_ctx = ViewerContext(
        manifest_entry=manifest_entry,
        events=transcript_context.payload.events,
        default_output=transcript_context.payload.default_output,
        final_output=transcript_context.payload.final_output,
        stream_started_at=None,
        meta=transcript_context.payload.meta,
    )

    def _export(destination: Path) -> Path:
        return export_cached_transcript(destination=destination, run_id=run_id)

    run_viewer_session(console, viewer_ctx, _export)


__all__ = ["should_launch_post_run_viewer", "maybe_launch_post_run_viewer"]
