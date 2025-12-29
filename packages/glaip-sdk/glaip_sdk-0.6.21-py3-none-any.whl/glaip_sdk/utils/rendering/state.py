"""Renderer state utilities and helpers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from collections.abc import Iterable


def coerce_received_at(value: Any) -> datetime | None:
    """Coerce arbitrary values into timezone-aware datetimes if possible."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, str):
        try:
            normalised = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalised)
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    return None


def truncate_display(text: str | None, limit: int = 160) -> str:
    """Return text capped at the given character limit with ellipsis."""
    if not text:
        return ""
    stripped = str(text).strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 1] + "…"


@dataclass(slots=True)
class TranscriptBuffer:
    """Utility container for streaming transcript text."""

    lines: list[str] = field(default_factory=list)

    def append(self, value: str | None) -> None:
        """Append a chunk of transcript text."""
        if not value:
            return
        self.lines.append(value)

    def extend(self, chunks: Iterable[str]) -> None:
        """Append multiple chunks."""
        for chunk in chunks:
            self.append(chunk)

    def clear(self) -> None:
        """Reset the buffer."""
        self.lines.clear()

    def render(self) -> str:
        """Return the concatenated transcript text."""
        return "".join(self.lines)

    def has_visible_text(self) -> bool:
        """Return True when any chunk contains non-whitespace characters."""
        return any(chunk and chunk.strip() for chunk in self.lines)

    def __bool__(self) -> bool:
        """Allow truthiness checks like a regular list."""
        return bool(self.lines)

    def __len__(self) -> int:
        """Return buffered chunk count."""
        return len(self.lines)

    def __iter__(self):
        """Iterate over buffered chunks."""
        return iter(self.lines)

    def __getitem__(self, index: int) -> str:
        """Return the chunk at the requested index."""
        return self.lines[index]

    def __contains__(self, item: object) -> bool:
        """Membership test for convenience."""
        return item in self.lines


@dataclass
class RendererState:
    """Internal state for the renderer."""

    buffer: TranscriptBuffer = field(default_factory=TranscriptBuffer)
    final_text: str = ""
    streaming_started_at: float | None = None
    printed_final_output: bool = False
    finalizing_ui: bool = False
    final_duration_seconds: float | None = None
    final_duration_text: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    streaming_started_event_ts: datetime | None = None

    def record_event(self, event: dict[str, Any], *, received_at: datetime | None = None) -> None:
        """Capture an event snapshot for transcript replay."""
        try:
            captured = json.loads(json.dumps(event))
        except Exception:
            captured = dict(event)

        if received_at is not None:
            try:
                captured["received_at"] = received_at.isoformat()
            except Exception:
                try:
                    captured["received_at"] = str(received_at)
                except Exception:
                    captured["received_at"] = repr(received_at)

        self.events.append(captured)

    def set_final_output(self, value: str) -> None:
        """Record the final assistant output."""
        self.final_text = value

    def append_transcript_text(self, value: str) -> None:
        """Append streaming text to the transcript buffer."""
        self.buffer.append(value)

    def start_stream_timer(self, now: float | None) -> None:
        """Record start timestamp when streaming begins."""
        if now is None or self.streaming_started_at is not None:
            return
        self.streaming_started_at = now

    def stop_stream_timer(self, now: float | None) -> float | None:
        """Record the total elapsed duration."""
        if now is None or self.streaming_started_at is None:
            return None
        duration = max(0.0, now - self.streaming_started_at)
        self.final_duration_seconds = duration
        return duration

    def mark_final_duration(self, duration: float | None, *, formatted: str | None = None) -> None:
        """Store the final duration metadata."""
        if duration is not None:
            self.final_duration_seconds = duration
        self.final_duration_text = formatted

    def to_snapshot(self) -> dict[str, Any]:
        """Return a serialisable snapshot for presenters."""
        return prepare_transcript_snapshot(self)


@dataclass
class ThinkingScopeState:
    """Runtime bookkeeping for deterministic thinking spans."""

    anchor_id: str
    task_id: str | None
    context_id: str | None
    anchor_started_at: float | None = None
    anchor_finished_at: float | None = None
    idle_started_at: float | None = None
    idle_started_monotonic: float | None = None
    active_thinking_id: str | None = None
    running_children: set[str] = field(default_factory=set)
    closed: bool = False


def accumulate_final_text(*, state: RendererState) -> str:
    """Return the most relevant final text for summary panels."""
    if state.final_text.strip():
        return state.final_text.strip()
    return state.buffer.render().strip()


def prepare_transcript_snapshot(state: RendererState) -> dict[str, Any]:
    """Return a dictionary capturing renderer transcript state."""
    return {
        "final_text": state.final_text,
        "buffer_text": state.buffer.render(),
        "events": list(state.events),
        "meta": dict(state.meta),
        "final_duration_seconds": state.final_duration_seconds,
        "final_duration_text": state.final_duration_text,
    }


__all__ = [
    "RendererState",
    "ThinkingScopeState",
    "TranscriptBuffer",
    "accumulate_final_text",
    "coerce_received_at",
    "prepare_transcript_snapshot",
    "truncate_display",
]
