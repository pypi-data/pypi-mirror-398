"""Presentation helpers for rendering steps.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from glaip_sdk.icons import ICON_AGENT_STEP, ICON_DELEGATE, ICON_TOOL_STEP
from glaip_sdk.utils.rendering.formatting import glyph_for_status, normalise_display_label, pretty_args
from glaip_sdk.utils.rendering.models import Step

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from glaip_sdk.utils.rendering.layout.transcript import TranscriptGlyphs

UNKNOWN_STEP_DETAIL = "Unknown step detail"
STATUS_ICON_STYLES = {
    "success": "green",
    "failed": "red",
    "warning": "yellow",
}
CONNECTOR_VERTICAL = "│   "
CONNECTOR_EMPTY = "    "
CONNECTOR_BRANCH = "├─ "
CONNECTOR_LAST = "└─ "
ROOT_MARKER = ""


@dataclass(slots=True)
class StepPresentation:
    """Lightweight view model for formatted steps."""

    step_id: str
    title: str
    glyph: str | None
    status_style: str | None
    args_text: str | None = None
    failure_reason: str | None = None
    duration_ms: int | None = None
    status_text: str | None = None


def humanize_tool_name(raw_name: str | None) -> str:
    """Return a user-facing name for a tool or agent identifier."""
    if not raw_name:
        return UNKNOWN_STEP_DETAIL
    name = raw_name
    if name.startswith("delegate_to_"):
        name = name.removeprefix("delegate_to_")
    elif name.startswith("delegate_"):
        name = name.removeprefix("delegate_")
    cleaned = name.replace("_", " ").replace("-", " ").strip()
    if not cleaned:
        return UNKNOWN_STEP_DETAIL
    lowered = cleaned.lower()
    return lowered[0].upper() + lowered[1:] if lowered else UNKNOWN_STEP_DETAIL


def step_icon_for_kind(step_kind: str) -> str:
    """Return the icon prefix for a step kind."""
    if step_kind == "agent":
        return ICON_AGENT_STEP
    if step_kind == "delegate":
        return ICON_DELEGATE
    if step_kind == "thinking":
        return "💭"
    return ICON_TOOL_STEP


def resolve_label_body(step_kind: str, tool_name: str | None, metadata: dict[str, Any]) -> str:
    """Resolve the textual body for a step label."""
    if step_kind == "thinking":
        thinking_text = metadata.get("thinking_and_activity_info")
        if isinstance(thinking_text, str) and thinking_text.strip():
            return thinking_text.strip()
        return "Thinking…"

    if step_kind == "delegate":
        return humanize_tool_name(tool_name)

    if step_kind == "agent":
        agent_name = metadata.get("agent_name")
        if isinstance(agent_name, str) and agent_name.strip():
            return agent_name.strip()

    return humanize_tool_name(tool_name)


def compose_display_label(
    step_kind: str,
    tool_name: str | None,
    args: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    """Compose the display label for a step using tool metadata."""
    icon = step_icon_for_kind(step_kind)
    body = resolve_label_body(step_kind, tool_name, metadata)
    label = f"{icon} {body}".strip()
    if isinstance(args, dict) and args:
        label = f"{label} —"
    return label or UNKNOWN_STEP_DETAIL


def status_icon_for_step(step: Step) -> str:
    """Return the canonical status icon key for a step."""
    if step.status == "failed":
        return "failed"
    if step.branch_failed:
        return "warning"
    if step.status == "finished":
        return "success"
    if step.status == "stopped":
        return "warning"
    return "spinner"


def format_step_label(step: Step) -> str:
    """Return the normalized display label for a step."""
    label = normalise_display_label(getattr(step, "display_label", None))
    if label and label != UNKNOWN_STEP_DETAIL:
        return label
    metadata = getattr(step, "metadata", {}) or {}
    computed = compose_display_label(step.kind, getattr(step, "name", None), getattr(step, "args", {}), metadata)
    return normalise_display_label(computed)


def format_tool_args(step: Step, max_len: int = 160) -> str | None:
    """Return a pretty-printed args summary for a step."""
    if not step.args:
        return None
    try:
        return pretty_args(step.args, max_len=max_len)
    except Exception:
        return None


def format_step(
    step: Step,
    *,
    glyphs: TranscriptGlyphs | None = None,
    label: str | None = None,
) -> StepPresentation:
    """Return a StepPresentation for downstream transcript rendering."""
    del glyphs  # Reserved for future glyph customisation hooks
    if label:
        resolved_label = normalise_display_label(label)
    else:
        resolved_label = format_step_label(step)
    glyph_key = status_icon_for_step(step)
    glyph = glyph_for_status(glyph_key)
    style = STATUS_ICON_STYLES.get(glyph_key)
    failure_reason = (step.failure_reason or "").strip() or None
    return StepPresentation(
        step_id=step.step_id,
        title=resolved_label,
        glyph=glyph,
        status_style=style,
        args_text=format_tool_args(step),
        failure_reason=failure_reason,
        duration_ms=getattr(step, "duration_ms", None),
    )


def build_connector_prefix(branch_state: tuple[bool, ...]) -> str:
    """Build connector prefix for a tree line based on ancestry state."""
    if not branch_state:
        return ROOT_MARKER

    parts: list[str] = []
    for ancestor_is_last in branch_state[:-1]:
        parts.append(CONNECTOR_EMPTY if ancestor_is_last else CONNECTOR_VERTICAL)
    parts.append(CONNECTOR_LAST if branch_state[-1] else CONNECTOR_BRANCH)
    return "".join(parts)
