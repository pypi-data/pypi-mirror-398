"""Shared presenter utilities for CLI/offline transcript viewing.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.console import Console

from glaip_sdk.utils.rendering.layout.transcript import (
    DEFAULT_TRANSCRIPT_THEME,
    TranscriptGlyphs,
    TranscriptSnapshot,
    build_transcript_snapshot,
    build_transcript_view,
)
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event_stream
from glaip_sdk.utils.rendering.state import RendererState, coerce_received_at
from glaip_sdk.utils.rendering.steps import StepManager


@dataclass(slots=True)
class ViewerContext:
    """Runtime context passed to transcript presenters."""

    manifest_entry: dict[str, Any]
    events: list[dict[str, Any]]
    default_output: str
    final_output: str
    stream_started_at: float | None
    meta: dict[str, Any]


def render_post_run_view(
    console: Console,
    ctx: ViewerContext,
    *,
    glyphs: TranscriptGlyphs | None = None,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
) -> TranscriptSnapshot:
    """Render the default summary view and return the snapshot used."""
    snapshot, _state = prepare_viewer_snapshot(
        ctx,
        glyphs=glyphs,
        theme=theme,
    )
    render_transcript_view(console, snapshot, theme=theme)
    return snapshot


def render_transcript_view(
    console: Console,
    snapshot: TranscriptSnapshot,
    *,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
) -> None:
    """Render the transcript summary using a prepared snapshot."""
    header, body = build_transcript_view(snapshot, theme=theme)
    _print_renderables(console, header + body)


def render_transcript_events(console: Console, events: list[dict[str, Any]]) -> None:
    """Pretty-print transcript events using shared debug presenter."""
    if not events:
        console.print("[dim]No SSE events were captured for this run.[/dim]")
        console.print()
        return

    console.print("[bold]Transcript Events[/bold]")
    console.print("[dim]────────────────────────────────────────────────────────[/dim]")

    render_debug_event_stream(
        events,
        console,
        resolve_timestamp=lambda event: coerce_received_at(event.get("received_at")),
    )
    console.print()


def prepare_viewer_snapshot(
    ctx: ViewerContext,
    *,
    glyphs: TranscriptGlyphs | None,
    theme: str,
) -> tuple[TranscriptSnapshot, RendererState]:
    """Build a transcript snapshot plus renderer state for reusable viewing."""
    state = _build_renderer_state(ctx)
    manager = _build_steps_from_events(ctx.events)
    query = _extract_query_from_manifest(ctx)
    merged_meta = _merge_meta(ctx)
    snapshot = build_transcript_snapshot(
        state,
        manager,
        glyphs=glyphs,
        query_text=query,
        meta=merged_meta,
        theme=theme,
    )
    return snapshot, state


def _build_renderer_state(ctx: ViewerContext) -> RendererState:
    state = RendererState()
    state.meta = dict(ctx.meta or {})

    final_text = (ctx.final_output or "").strip()
    default_text = (ctx.default_output or "").strip()
    if final_text:
        state.final_text = final_text
    elif default_text:
        state.final_text = default_text
        state.buffer.append(default_text)

    duration = _extract_final_duration(ctx.events)
    if duration:
        state.final_duration_text = duration  # pragma: no cover - exercised indirectly via end-to-end tests
    state.events = list(ctx.events or [])
    return state


def _build_steps_from_events(events: list[dict[str, Any]]) -> StepManager:
    manager = StepManager()
    for event in events or []:
        payload = _coerce_step_event(event)
        if not payload:
            continue
        try:
            manager.apply_event(payload)
        except ValueError:
            continue
    return manager


def _coerce_step_event(event: dict[str, Any]) -> dict[str, Any] | None:
    metadata = event.get("metadata")
    if not isinstance(metadata, dict):
        return None
    if not isinstance(metadata.get("step_id"), str):
        return None
    return {
        "metadata": metadata,
        "status": event.get("status"),
        "task_state": event.get("task_state"),
        "content": event.get("content"),
        "task_id": event.get("task_id"),
        "context_id": event.get("context_id"),
    }


def _extract_final_duration(events: list[dict[str, Any]]) -> str | None:
    for event in events or []:
        metadata = event.get("metadata") or {}
        if metadata.get("kind") != "final_response":
            continue
        time_value = metadata.get("time")
        if isinstance(time_value, (int, float)):
            return f"{float(time_value):.2f}s"
    return None


def _extract_query_from_manifest(ctx: ViewerContext) -> str | None:
    query = ctx.manifest_entry.get("input_message") or ctx.meta.get("input_message") or ctx.meta.get("query")
    if isinstance(query, str) and query.strip():
        return query.strip()
    return None


def _merge_meta(ctx: ViewerContext) -> dict[str, Any]:
    merged = dict(ctx.meta or {})
    manifest = ctx.manifest_entry or {}
    for key in ("agent_name", "agent_id", "model", "run_id", "input_message"):
        if key in manifest and manifest[key] and key not in merged:
            merged[key] = manifest[key]
    return merged


def _print_renderables(console: Console, renderables: list[Any]) -> None:
    for renderable in renderables:
        console.print(renderable)
        console.print()
