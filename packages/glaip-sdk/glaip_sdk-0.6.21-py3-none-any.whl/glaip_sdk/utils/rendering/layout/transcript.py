"""Shared transcript presentation helpers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text

from glaip_sdk.icons import ICON_AGENT
from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.rendering.layout.panels import create_final_panel
from glaip_sdk.utils.rendering.renderer.summary_window import clamp_step_nodes
from glaip_sdk.utils.rendering.state import RendererState
from glaip_sdk.utils.rendering.steps import (
    StepManager,
    StepPresentation,
    build_connector_prefix,
    format_step,
    format_step_label,
    humanize_tool_name,
)

DEFAULT_TRANSCRIPT_THEME = "dark"
_NO_STEPS_TEXT = Text("No steps yet", style="dim")


@dataclass(slots=True)
class TranscriptGlyphs:
    """Glyph overrides for transcript presentation."""

    branch_fill: str = "│   "
    branch_empty: str = "    "
    branch_item: str = "├─ "
    branch_last: str = "└─ "
    query_prefix: str = "     "


@dataclass(slots=True)
class TranscriptRow:
    """Renderable row metadata for the transcript/summary tree."""

    prefix: str
    presentation: StepPresentation


@dataclass(slots=True)
class TranscriptSnapshot:
    """Snapshot consumed by presenter/viewer components."""

    rows: list[TranscriptRow]
    final_panel: Any | None
    events: list[dict[str, Any]]
    agent_label: str | None = None
    model_label: str | None = None
    run_id: str | None = None
    query_text: str | None = None
    duration_text: str | None = None
    window_header: Text | None = None
    window_footer: Text | None = None


def format_final_panel_title(state: RendererState | Mapping[str, Any], base_title: str = "Final Result") -> str:
    """Return the final panel title including duration if available."""
    if isinstance(state, RendererState):
        duration_text = state.final_duration_text
    else:
        duration_text = state.get("final_duration_text") if isinstance(state, Mapping) else None
    if duration_text:
        return f"{base_title} · {duration_text}"
    return base_title


def build_final_panel(
    state: RendererState | Mapping[str, Any],
    *,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
    title: str | None = None,
) -> Any | None:
    """Create a Rich panel for the renderer/viewer final output."""
    if isinstance(state, RendererState):
        body = (state.final_text or state.buffer.render() or "").strip()
    else:
        final_text = str(state.get("final_text", "")) if isinstance(state, Mapping) else ""
        buffer_text = str(state.get("buffer_text", "")) if isinstance(state, Mapping) else ""
        body = (final_text or buffer_text).strip()
    if not body:
        return None
    panel_title = title or format_final_panel_title(state)
    return create_final_panel(body, title=panel_title, theme=theme)


def build_transcript_snapshot(
    state: RendererState | Mapping[str, Any],
    steps: StepManager,
    *,
    glyphs: TranscriptGlyphs | None = None,
    query_text: str | None = None,
    meta: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
    summary_window: int | None = None,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
    step_status_overrides: dict[str, str] | None = None,
) -> TranscriptSnapshot:
    """Compose a snapshot consumable by renderers/viewers alike."""
    glyphs = glyphs or TranscriptGlyphs()
    final_text, buffer_text, events, meta_payload, duration_text = _resolve_state_payload(state, meta)
    query_value = query_text or extract_query_from_meta(meta_payload)
    rows, window_header, window_footer = _build_rows(
        steps,
        glyphs,
        meta_payload,
        summary_window,
        query_text=query_value,
        step_status_overrides=step_status_overrides,
    )
    if not rows:
        stored = meta_payload.get("transcript_steps")
        if isinstance(stored, list) and stored:
            rows, window_header, window_footer = _rows_from_stored_steps(stored)
    panel_state: RendererState | Mapping[str, Any]
    if isinstance(state, RendererState):
        panel_state = state
    else:
        panel_state = {
            "final_text": final_text,
            "buffer_text": buffer_text,
            "final_duration_text": duration_text,
        }
    final_panel = build_final_panel(panel_state, theme=theme)

    return TranscriptSnapshot(
        rows=rows,
        final_panel=final_panel,
        events=events,
        agent_label=_friendly_agent_label(meta_payload),
        model_label=meta_payload.get("model"),
        run_id=meta_payload.get("run_id"),
        query_text=query_value,
        duration_text=duration_text,
        window_header=window_header,
        window_footer=window_footer,
    )


def build_transcript_view(
    snapshot: TranscriptSnapshot,
    *,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
) -> tuple[list[Any], list[Any]]:
    """Return header + body renderables for a transcript snapshot."""
    header_renderables: list[Any] = []
    body_renderables: list[Any] = []

    header_text = _compose_header_text(snapshot)
    if header_text is not None:
        if theme != DEFAULT_TRANSCRIPT_THEME:
            header_text.style = "bold black"
        header_renderables.append(header_text)

    if snapshot.query_text:
        body_renderables.append(
            _build_query_panel(snapshot.query_text),
        )

    body_renderables.append(
        _build_steps_panel(
            snapshot.rows,
            window_header=snapshot.window_header,
            window_footer=snapshot.window_footer,
            theme=theme,
        )
    )

    if snapshot.final_panel is not None:
        body_renderables.append(snapshot.final_panel)

    return header_renderables, body_renderables


def render_final_panel(
    console: Any,
    state: RendererState | Mapping[str, Any],
    *,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
    title: str | None = None,
) -> bool:
    """Print the shared final panel, returning True when rendered."""
    panel = build_final_panel(state, theme=theme, title=title)
    if panel is None:
        return False
    console.print(panel)
    console.print()
    return True


__all__ = [
    "DEFAULT_TRANSCRIPT_THEME",
    "TranscriptGlyphs",
    "TranscriptRow",
    "TranscriptSnapshot",
    "build_transcript_snapshot",
    "build_transcript_view",
    "render_final_panel",
    "build_final_panel",
    "format_final_panel_title",
    "extract_query_from_meta",
]


def _resolve_state_payload(
    state: RendererState | Mapping[str, Any],
    meta_override: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
) -> tuple[str, str, list[dict[str, Any]], dict[str, Any], str | None]:
    if isinstance(state, RendererState):
        final_text = state.final_text
        buffer_text = state.buffer.render()
        events = list(state.events)
        meta_payload = normalise_meta_payload(meta_override or getattr(state, "meta", None))
        duration_text = state.final_duration_text
    else:
        mapping_state = dict(state) if isinstance(state, Mapping) else {}
        final_text = str(mapping_state.get("final_text") or "")
        buffer_text = str(mapping_state.get("buffer_text") or "")
        events = list(mapping_state.get("events") or [])
        base_meta = mapping_state.get("meta")
        meta_payload = normalise_meta_payload(meta_override or base_meta)
        duration_text = mapping_state.get("final_duration_text")
    return final_text, buffer_text, events, meta_payload, duration_text


def _build_rows(
    steps: StepManager,
    glyphs: TranscriptGlyphs,
    meta_payload: dict[str, Any],
    summary_window: int | None,
    *,
    query_text: str | None,
    step_status_overrides: dict[str, str] | None = None,
) -> tuple[list[TranscriptRow], Text | None, Text | None]:
    nodes = list(steps.iter_tree())
    header_notice: Text | None = None
    footer_notice: Text | None = None
    if summary_window is not None and summary_window > 0:
        nodes, header_notice, footer_notice = _apply_summary_window(steps, nodes, summary_window)

    rows: list[TranscriptRow] = []
    for index, (step_id, branch_state) in enumerate(nodes):
        row = _create_step_row(
            steps,
            glyphs,
            meta_payload,
            step_id,
            branch_state,
            step_status_overrides=step_status_overrides,
        )
        if row is not None:
            rows.append(row)
            if index == 0:
                query_row = _create_query_hint_row(glyphs, query_text)
                if query_row is not None:
                    rows.append(query_row)

    return rows, header_notice, footer_notice


def _apply_summary_window(
    steps: StepManager,
    nodes: list[tuple[str, tuple[bool, ...]]],
    summary_window: int,
) -> tuple[list[tuple[str, tuple[bool, ...]]], Text | None, Text | None]:
    """Apply summary window clamping to step nodes."""

    def _get_label(step_id: str) -> str:
        step = steps.by_id.get(step_id)
        return format_step_label(step) if step else ""

    def _get_parent(step_id: str) -> str | None:
        step = steps.by_id.get(step_id)
        return step.parent_id if step else None

    return clamp_step_nodes(
        nodes,
        window=summary_window,
        get_label=_get_label,
        get_parent=_get_parent,
    )


def _create_step_row(
    steps: StepManager,
    glyphs: TranscriptGlyphs,
    meta_payload: dict[str, Any],
    step_id: str,
    branch_state: tuple[bool, ...],
    *,
    step_status_overrides: dict[str, str] | None = None,
) -> TranscriptRow | None:
    """Create a transcript row from a step."""
    step = steps.by_id.get(step_id)
    if not step:
        return None
    override = None
    if not branch_state and _should_override_root_label(meta_payload):
        override = _friendly_root_label(meta_payload, step, getattr(step, "display_label", None))
    presentation = format_step(step, glyphs=glyphs, label=override)
    if step_status_overrides:
        status_text = step_status_overrides.get(step_id)
        if status_text:
            presentation.status_text = status_text
    prefix = build_connector_prefix(branch_state)
    return TranscriptRow(prefix=prefix, presentation=presentation)


def _create_query_hint_row(glyphs: TranscriptGlyphs, query_text: str | None) -> TranscriptRow | None:
    """Create a query hint row mirroring the documented transcript output."""
    if not query_text:
        return None
    return TranscriptRow(
        prefix=glyphs.query_prefix,
        presentation=StepPresentation(
            step_id="query",
            title=query_text,
            glyph=None,
            status_style=None,
            args_text=None,
            failure_reason=None,
            duration_ms=None,
        ),
    )


def _rows_from_stored_steps(entries: list[dict[str, Any]]) -> tuple[list[TranscriptRow], Text | None, Text | None]:
    rows: list[TranscriptRow] = []
    for index, entry in enumerate(entries):
        title = entry.get("display_name") or entry.get("name") or "Step"
        finished = entry.get("status") == "finished"
        duration_ms = entry.get("duration_ms")
        presentation = StepPresentation(
            step_id=f"stored-{index}",
            title=str(title),
            glyph="✓" if finished else None,
            status_style="green" if finished else None,
            args_text=None,
            failure_reason=None,
            duration_ms=duration_ms,
        )
        rows.append(TranscriptRow(prefix="  ", presentation=presentation))
    return rows, None, None


def _compose_header_text(snapshot: TranscriptSnapshot) -> Text | None:
    parts: list[str] = []
    if snapshot.agent_label:
        parts.append(snapshot.agent_label)
    if snapshot.model_label:
        parts.append(snapshot.model_label)
    if snapshot.duration_text:
        parts.append(snapshot.duration_text)
    if snapshot.run_id:
        parts.append(snapshot.run_id)
    if not parts:
        return None
    return Text(" · ".join(parts), style="bold")


def _build_query_panel(query_text: str) -> AIPPanel:
    """Build a query panel."""
    return AIPPanel(
        Markdown(f"**Query:** {query_text.strip()}"),
        title="User Request",
        border_style="#d97706",
        padding=(0, 1),
    )


def _build_steps_panel(
    rows: Sequence[TranscriptRow],
    *,
    window_header: Text | None = None,
    window_footer: Text | None = None,
    theme: str = DEFAULT_TRANSCRIPT_THEME,
) -> AIPPanel:
    if not rows:
        steps_body: Text | Group = _NO_STEPS_TEXT.copy()
    else:
        rendered = [_format_row_text(row) for row in rows]
        style = "dim" if theme == DEFAULT_TRANSCRIPT_THEME else "default"
        steps_body = Text("\n".join(rendered), style=style)

    renderables: list[Any] = []
    if window_header is not None:
        renderables.append(window_header)
    renderables.append(steps_body)
    if window_footer is not None:
        renderables.append(window_footer)

    if len(renderables) == 1:
        body: Any = renderables[0]
    else:
        body = Group(*renderables)

    return AIPPanel(body, title="Steps", border_style="blue")


def _format_row_text(row: TranscriptRow) -> str:
    prefix = row.prefix
    title, summary = _split_label(row.presentation.title)
    line = f"{prefix}{title}".rstrip()

    args_lines = _extract_args_lines(row)
    has_args = bool(args_lines)

    if summary:
        line += f" — {_truncate_summary(summary)}"
    elif has_args:
        line += " —"

    badge = _format_duration_badge(row.presentation.duration_ms)
    status_text = row.presentation.status_text
    if status_text:
        line += f" {status_text}"
    elif badge:
        line += f" {badge}"

    if row.presentation.glyph:
        line += f" {row.presentation.glyph}"

    if row.presentation.failure_reason:
        line += f" {row.presentation.failure_reason}"

    if has_args:
        for args_line in args_lines:
            line += f"\n{prefix}     {args_line}"

    return line


def _format_duration_badge(duration_ms: int | None) -> str | None:
    if duration_ms is None:
        return None
    try:
        duration_ms = int(duration_ms)
    except Exception:
        return None
    if duration_ms <= 0:
        value = "<1ms"
    elif duration_ms < 1000:
        value = f"{duration_ms}ms"
    else:
        seconds = duration_ms / 1000
        value = f"{seconds:.2f}s"
    return f"[{value}]"


def _extract_args_lines(row: TranscriptRow) -> list[str]:
    args_text = row.presentation.args_text
    if _should_skip_args_summary(row, args_text):
        return []

    parsed = _parse_args_payload(args_text or "")
    title = row.presentation.title or ""

    if isinstance(parsed, dict) and parsed:
        if title.startswith(ICON_AGENT) and set(parsed.keys()) == {"query"}:
            return [str(parsed["query"])]
        return [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in parsed.items()]

    if isinstance(parsed, list):
        return [json.dumps(parsed, ensure_ascii=False)]

    return [args_text or ""]


def _should_skip_args_summary(row: TranscriptRow, args_text: str | None) -> bool:
    if not args_text or args_text == "{}":
        return True
    title = (row.presentation.title or "").strip()
    if title.startswith("💭 Thinking…"):
        return True
    if not row.prefix.strip():
        return True
    if args_text.strip() == '{"reason":"deterministic_timeline"}':
        return True
    return False


def _parse_args_payload(args_text: str) -> Any | None:
    stripped = args_text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(args_text)
        except Exception:
            return None
    return None


def _split_label(label: Any) -> tuple[str, str | None]:
    if not isinstance(label, str):
        try:
            label = str(label)
        except Exception:
            return "Step", None
    if "—" not in label:
        return label, None
    title, summary = label.split("—", 1)
    return title.strip(), summary.strip()


def _truncate_summary(summary: str, limit: int = 80) -> str:
    if len(summary) <= limit:
        return summary
    return summary[: limit - 1] + "…"


def _friendly_agent_label(meta: Mapping[str, Any]) -> str | None:
    """Return a user-facing agent label for headers."""
    raw_name = _string_or_none(meta.get("agent_name"))
    if raw_name:
        friendly = humanize_tool_name(raw_name)
        if friendly:
            return friendly
    return _string_or_none(meta.get("agent_id"))


def _friendly_root_label(meta: dict[str, Any], step: Any, fallback: str | None) -> str:
    fallback_label = _string_or_none(fallback)
    raw_agent_name = _string_or_none(meta.get("agent_name"))
    agent_name = humanize_tool_name(raw_agent_name) if raw_agent_name else None
    if agent_name:
        agent_name = agent_name.title()
    agent_name = agent_name or fallback_label
    agent_id = _string_or_none(meta.get("agent_id") or getattr(step, "name", ""))

    if not agent_name:
        return fallback_label or agent_id or ICON_AGENT

    parts = [ICON_AGENT, agent_name]
    if agent_id and agent_id != agent_name:
        parts.append(f"({agent_id})")
    return " ".join(parts)


def extract_query_from_meta(meta: Mapping[str, Any] | None) -> str | None:
    """Return the canonical query string embedded in renderer metadata."""
    if not meta:
        return None

    payload = dict(meta)
    nested_meta = payload.get("meta") or {}
    candidate = (
        payload.get("input_message")
        or payload.get("query")
        or payload.get("message")
        or nested_meta.get("input_message")
    )
    if isinstance(candidate, str):
        candidate = candidate.strip()
    return candidate or None


def _should_override_root_label(meta: Mapping[str, Any] | None) -> bool:
    if not meta:
        return False
    if meta.get("agent_name") or meta.get("agent_id"):
        return True
    return False


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def normalise_meta_payload(meta: Any) -> dict[str, Any]:
    """Return a defensive dictionary for arbitrary metadata payloads."""
    if not meta:
        return {}
    if isinstance(meta, dict):
        return dict(meta)
    if isinstance(meta, Mapping):
        try:
            return dict(meta)
        except Exception:
            return {}
    if isinstance(meta, Sequence) and not isinstance(meta, (str, bytes)):
        try:
            return dict(meta)
        except Exception:
            return {}
    try:
        return dict(meta)
    except Exception:
        return {}
