"""Helpers for capturing and caching agent run transcripts.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import StringIO
from typing import Any

from rich.console import Console

from glaip_sdk.cli.auth import resolve_api_url_from_context
from glaip_sdk.cli.context import get_ctx_value
from glaip_sdk.cli.transcript.cache import (
    TranscriptPayload,
    TranscriptStoreResult,
    store_transcript,
)
from glaip_sdk.cli.transcript.cache import (
    build_payload as build_transcript_payload,
)
from glaip_sdk.utils.rendering.layout.progress import format_tool_title


@dataclass(slots=True)
class StoredTranscriptContext:
    """Simple container linking payload and manifest data."""

    payload: TranscriptPayload
    store_result: TranscriptStoreResult


def coerce_events(value: Any) -> list[dict[str, Any]]:
    """Normalise renderer events into a list of dictionaries."""
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    try:
        return [item for item in value if isinstance(item, dict)]
    except Exception:
        return []


def coerce_result_text(result: Any) -> str:
    """Serialise renderer output to a string for transcript payloads."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        return str(result)


def compute_finished_at(renderer: Any) -> float | None:
    """Best-effort end-time calculation based on renderer state."""
    state = getattr(renderer, "state", None)
    if state is not None:
        started_at = getattr(state, "streaming_started_at", None)
        duration = getattr(state, "final_duration_seconds", None)
    else:
        started_at = None
        duration = None

    if started_at is None:
        stream_processor = getattr(renderer, "stream_processor", None)
        started_at = getattr(stream_processor, "streaming_started_at", None) if stream_processor is not None else None
    if started_at is None or duration is None:
        return None
    try:
        return float(started_at) + float(duration)
    except Exception:
        return None


def extract_server_run_id(meta: dict[str, Any], events: list[dict[str, Any]]) -> str | None:
    """Derive a server-side run identifier from renderer metadata."""
    run_id = meta.get("run_id") or meta.get("id")
    if run_id:
        return str(run_id)
    for event in events:
        metadata = event.get("metadata") or {}
        candidate = metadata.get("run_id") or metadata.get("request_id")
        if candidate:
            return str(candidate)
    return None


def _coerce_meta(meta: Any) -> dict[str, Any]:
    """Ensure renderer metadata is recorded as a plain dictionary."""
    if meta is None:
        return {}
    if isinstance(meta, dict):
        return meta
    if hasattr(meta, "items"):
        try:
            return {str(key): value for key, value in meta.items()}
        except Exception:
            pass
    return {"value": coerce_result_text(meta)}


def register_last_transcript(ctx: Any, payload: TranscriptPayload, store_result: TranscriptStoreResult) -> None:
    """Persist last-run transcript references onto the Click context."""
    ctx_obj = getattr(ctx, "obj", None)
    if not isinstance(ctx_obj, dict):
        return
    ctx_obj["_last_transcript_payload"] = payload
    ctx_obj["_last_transcript_manifest"] = store_result.manifest_entry
    ctx_obj["_last_transcript_path"] = str(store_result.path)


def _resolve_api_url(ctx: Any) -> str | None:
    """Resolve API URL from context or account store (CLI/palette ignores env creds)."""
    return resolve_api_url_from_context(
        ctx,
        get_api_url=lambda c: get_ctx_value(c, "api_url"),
        get_account_name=lambda c: get_ctx_value(c, "account_name"),
    )


def _extract_step_summaries(renderer: Any) -> list[dict[str, Any]]:
    """Return lightweight step summaries for the transcript viewer."""
    steps = getattr(renderer, "steps", None)
    if steps is None:
        return []

    order = getattr(steps, "order", []) or []
    by_id = getattr(steps, "by_id", {}) or {}

    return [
        _build_step_summary(by_id.get(step_id), index)
        for index, step_id in enumerate(order)
        if by_id.get(step_id) is not None
    ]


def _build_step_summary(step: Any, index: int) -> dict[str, Any]:
    """Construct a single step summary entry."""
    kind = getattr(step, "kind", "") or ""
    name = getattr(step, "name", "") or ""
    status = getattr(step, "status", "") or ""
    duration_ms = _coerce_duration_ms(getattr(step, "duration_ms", None))
    display_name = _format_step_display_name(name)

    return {
        "index": index,
        "step_id": getattr(step, "step_id", f"step-{index}"),
        "kind": kind,
        "name": name,
        "display_name": display_name,
        "status": status,
        "duration_ms": duration_ms,
    }


def _coerce_duration_ms(value: Any) -> int | None:
    """Return duration in milliseconds if numeric, otherwise None."""
    try:
        if isinstance(value, (int, float)):
            return int(value)
    except Exception:
        return None
    return None


def _format_step_display_name(name: str) -> str:
    """Apply tool title formatting with a safe fallback."""
    try:
        return format_tool_title(name)
    except Exception:
        return name


def _extract_step_summary_lines(renderer: Any) -> list[str]:
    """Render the live steps summary to plain text lines."""
    if not hasattr(renderer, "_render_steps_text"):
        return []

    try:
        renderable = renderer._render_steps_text()
    except Exception:
        return []

    buffer = StringIO()
    console = Console(file=buffer, record=True, force_terminal=False, width=120)
    try:
        console.print(renderable)
    except Exception:
        return []

    text = console.export_text() or buffer.getvalue()
    lines = [line.rstrip() for line in text.splitlines()]
    half = len(lines) // 2
    if half and lines[:half] == lines[half : half * 2]:
        return lines[:half]
    start = 0
    prefixes = ("🤖", "🔧", "💭", "├", "└", "│", "•")
    for idx, line in enumerate(lines):
        if line.lstrip().startswith(prefixes):
            start = idx
            break
    trimmed = lines[start:]
    return [line for line in trimmed if line]


def _collect_renderer_outputs(
    renderer: Any, final_result: Any
) -> tuple[
    list[dict[str, Any]],
    str,
    str,
]:
    """Collect events and text outputs from a renderer with safe fallbacks."""
    events_raw = []
    if hasattr(renderer, "get_transcript_events"):
        try:
            events_raw = renderer.get_transcript_events()
        except Exception:
            events_raw = []
    events = coerce_events(events_raw)

    aggregated_raw = ""
    if hasattr(renderer, "get_aggregated_output"):
        try:
            aggregated_raw = renderer.get_aggregated_output()
        except Exception:
            aggregated_raw = ""

    aggregated_output = coerce_result_text(aggregated_raw)
    final_output = coerce_result_text(final_result)
    return events, aggregated_output, final_output


def _derive_transcript_meta(
    renderer: Any, model: str | None
) -> tuple[dict[str, Any], float | None, float | None, str | None]:
    """Build transcript metadata including step summaries and timings."""
    raw_meta = getattr(getattr(renderer, "state", None), "meta", {}) or {}
    meta = _coerce_meta(raw_meta)

    step_summaries = _extract_step_summaries(renderer)
    if step_summaries:
        meta["transcript_steps"] = step_summaries

    step_lines = _extract_step_summary_lines(renderer)
    if step_lines:
        meta["transcript_step_lines"] = step_lines

    stream_processor = getattr(renderer, "stream_processor", None)
    stream_started_at = (
        getattr(stream_processor, "streaming_started_at", None) if stream_processor is not None else None
    )
    finished_at = compute_finished_at(renderer)
    state = getattr(renderer, "state", None)
    if state is not None:
        duration_hint = getattr(state, "final_duration_seconds", None)
        if duration_hint is not None:
            try:
                meta["final_duration_seconds"] = float(duration_hint)
            except Exception:
                pass
    model_name = meta.get("model") or model
    return meta, stream_started_at, finished_at, model_name


def store_transcript_for_session(
    ctx: Any,
    renderer: Any,
    *,
    final_result: Any,
    agent_id: str | None,
    agent_name: str | None,
    model: str | None,
    source: str,
) -> StoredTranscriptContext | None:
    """Capture renderer output and persist the transcript for later reuse."""
    if not hasattr(renderer, "get_transcript_events"):
        return None

    events, aggregated_output, final_output = _collect_renderer_outputs(renderer, final_result)

    if not (events or aggregated_output or final_output):
        return None

    meta, stream_started_at, finished_at, model_name = _derive_transcript_meta(renderer, model)

    try:
        api_url = _resolve_api_url(ctx)
    except Exception:
        api_url = None
    if api_url:
        meta["api_url"] = api_url

    payload: TranscriptPayload = build_transcript_payload(
        events=events,
        renderer_output=aggregated_output,
        final_output=final_output,
        agent_id=agent_id,
        agent_name=agent_name,
        model=model_name,
        server_run_id=extract_server_run_id(meta, events),
        started_at=stream_started_at,
        finished_at=finished_at,
        meta=meta,
        source=source,
    )

    store_result = store_transcript(payload)
    register_last_transcript(ctx, payload, store_result)

    return StoredTranscriptContext(payload=payload, store_result=store_result)


__all__ = [
    "StoredTranscriptContext",
    "coerce_events",
    "coerce_result_text",
    "compute_finished_at",
    "extract_server_run_id",
    "register_last_transcript",
    "store_transcript_for_session",
]
