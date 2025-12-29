"""Debug rendering utilities for verbose SSE event display.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
from datetime import datetime, timezone
from typing import Any
from collections.abc import Callable, Iterable

from rich.console import Console
from rich.markdown import Markdown

from glaip_sdk.branding import PRIMARY, SUCCESS, WARNING
from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.datetime_helpers import coerce_datetime


def _parse_event_timestamp(event: dict[str, Any], received_ts: datetime | None = None) -> datetime | None:
    """Resolve the most accurate timestamp available for the event."""
    if received_ts is not None:
        return received_ts if received_ts.tzinfo else received_ts.replace(tzinfo=timezone.utc)

    ts_value = event.get("timestamp") or (event.get("metadata") or {}).get("timestamp")
    return coerce_datetime(ts_value)


def _format_timestamp_for_display(dt: datetime) -> str:
    """Format timestamp for panel title, including timezone offset."""
    local_dt = dt.astimezone()
    ts_ms = local_dt.strftime("%H:%M:%S.%f")[:-3]
    offset = local_dt.strftime("%z")
    # offset is always non-empty for timezone-aware datetimes
    offset = f"{offset[:3]}:{offset[3:]}"
    return f"{ts_ms} {offset}"


def _calculate_relative_time(
    event_ts: datetime | None,
    baseline_ts: datetime | None,
) -> tuple[float, str]:
    """Calculate relative time since start and format event timestamp."""
    rel = 0.0

    # Determine display timestamp - use event timestamp when present, otherwise current time
    display_ts: datetime | None = event_ts
    if display_ts is None:
        display_ts = datetime.now(timezone.utc)

    if event_ts is not None and baseline_ts is not None:
        rel = max(0.0, (event_ts - baseline_ts).total_seconds())

    ts_ms = _format_timestamp_for_display(display_ts)

    return rel, ts_ms


def _get_event_metadata(event: dict[str, Any]) -> tuple[str, str | None]:
    """Extract event kind and status."""
    sse_kind = (event.get("metadata") or {}).get("kind") or "event"
    status_str = event.get("status") or (event.get("metadata") or {}).get("status")
    return sse_kind, status_str


def _build_debug_title(sse_kind: str, status_str: str | None, ts_ms: str, rel: float) -> str:
    """Build the debug event title."""
    if status_str:
        return f"SSE: {sse_kind} — {status_str} @ {ts_ms} (+{rel:.2f}s)"
    else:
        return f"SSE: {sse_kind} @ {ts_ms} (+{rel:.2f}s)"


def _dejson_value(obj: Any) -> Any:
    """Deep-parse JSON strings in nested objects."""
    if isinstance(obj, dict):
        return {k: _dejson_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dejson_value(x) for x in obj]
    if isinstance(obj, str):
        s = obj.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return _dejson_value(json.loads(s))
            except Exception:
                return obj
        return obj
    return obj


def _format_event_json(event: dict[str, Any]) -> str:
    """Format event as JSON with deep parsing."""
    try:
        return json.dumps(_dejson_value(event), indent=2, ensure_ascii=False)
    except Exception:
        return str(event)


def _get_border_color(sse_kind: str) -> str:
    """Get border color for event type."""
    border_map = {
        "agent_step": PRIMARY,
        "content": SUCCESS,
        "final_response": SUCCESS,
        "status": WARNING,
        "artifact": "grey42",
    }
    return border_map.get(sse_kind, "grey42")


def _create_debug_panel(title: str, event_json: str, border: str) -> AIPPanel:
    """Create the debug panel."""
    md = Markdown(f"```json\n{event_json}\n```", code_theme="monokai")
    return AIPPanel(md, title=title, border_style=border)


def render_debug_event(
    event: dict[str, Any],
    console: Console,
    *,
    received_ts: datetime | None = None,
    baseline_ts: datetime | None = None,
) -> None:
    """Render a debug panel for an SSE event.

    Args:
        event: The SSE event data
        console: Rich console to print to
        received_ts: Client-side receipt timestamp, if available
        baseline_ts: Baseline event timestamp for elapsed timing
    """
    try:
        # Calculate timing information
        event_ts = _parse_event_timestamp(event, received_ts)
        rel, ts_ms = _calculate_relative_time(event_ts, baseline_ts)

        # Extract event metadata
        sse_kind, status_str = _get_event_metadata(event)

        # Build title
        title = _build_debug_title(sse_kind, status_str, ts_ms, rel)

        # Format event JSON
        event_json = _format_event_json(event)

        # Get border color
        border = _get_border_color(sse_kind)

        # Create and print panel
        panel = _create_debug_panel(title, event_json, border)
        console.print(panel)

    except Exception as e:
        # Debug helpers must not break streaming
        print(f"Debug error: {e}")  # Fallback debug output


def render_debug_event_stream(
    events: Iterable[dict[str, Any]],
    console: Console,
    *,
    resolve_timestamp: Callable[[dict[str, Any]], datetime | None],
) -> None:
    """Render a sequence of SSE events with baseline-aware timestamps."""
    baseline: datetime | None = None
    for event in events:
        try:
            received_ts = resolve_timestamp(event)
            if baseline is None and received_ts is not None:
                baseline = received_ts
            render_debug_event(
                event,
                console,
                received_ts=received_ts,
                baseline_ts=baseline,
            )
        except Exception as exc:  # pragma: no cover - debug stream resilience
            console.print(f"[red]Debug stream error: {exc}[/red]")
