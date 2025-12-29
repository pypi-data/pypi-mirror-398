"""Rendering utilities package (formatting, models, steps, debug).

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from datetime import datetime
from typing import Any

from rich.console import Console

from glaip_sdk.models.agent_runs import RunWithOutput
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event, render_debug_event_stream


def _parse_event_received_timestamp(event: dict[str, Any]) -> datetime | None:
    """Parse received_at timestamp from SSE event.

    Args:
        event: SSE event dictionary

    Returns:
        Parsed datetime or None if not available
    """
    received_at = event.get("received_at")
    if not received_at:
        return None

    if isinstance(received_at, datetime):
        return received_at

    if isinstance(received_at, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(received_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try common formats
                return datetime.strptime(received_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                return None

    return None


def render_remote_sse_transcript(
    run: RunWithOutput,
    console: Console,
    *,
    show_metadata: bool = True,
) -> None:
    """Render remote SSE transcript events for a RunWithOutput.

    Args:
        run: RunWithOutput instance containing events
        console: Rich console to render to
        show_metadata: Whether to show run metadata summary
    """
    if show_metadata:
        # Render metadata summary
        console.print(f"[bold]Run: {run.id}[/bold]")
        console.print(f"[dim]Agent: {run.agent_id}[/dim]")
        console.print(f"[dim]Status: {run.status}[/dim]")
        console.print(f"[dim]Type: {run.run_type}[/dim]")
        if run.schedule_id:
            console.print(f"[dim]Schedule ID: {run.schedule_id}[/dim]")
        else:
            console.print("[dim]Schedule: —[/dim]")
        console.print(f"[dim]Started: {run.started_at.isoformat()}[/dim]")
        if run.completed_at:
            console.print(f"[dim]Completed: {run.completed_at.isoformat()}[/dim]")
            console.print(f"[dim]Duration: {run.duration_formatted()}[/dim]")
        console.print()

    # Render events
    if not run.output:
        console.print("[dim]No SSE events available for this run.[/dim]")
        return

    console.print("[bold]SSE Events[/bold]")
    console.print("[dim]────────────────────────────────────────────────────────[/dim]")

    render_debug_event_stream(
        run.output,
        console,
        resolve_timestamp=_parse_event_received_timestamp,
    )
    console.print()


class RemoteSSETranscriptRenderer:
    """Renderer for remote SSE transcripts from RunWithOutput."""

    def __init__(self, console: Console | None = None):
        """Initialize the renderer.

        Args:
            console: Rich console instance (creates default if None)
        """
        self.console = console or Console()

    def render(self, run: RunWithOutput, *, show_metadata: bool = True) -> None:
        """Render a remote run transcript.

        Args:
            run: RunWithOutput instance to render
            show_metadata: Whether to show run metadata summary
        """
        render_remote_sse_transcript(run, self.console, show_metadata=show_metadata)


__all__ = [
    "render_remote_sse_transcript",
    "RemoteSSETranscriptRenderer",
]
