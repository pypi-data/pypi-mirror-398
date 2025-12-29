"""Rendering utilities.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any


@dataclass(slots=True)
class Step:
    """Represents a single execution step in a workflow.

    A step tracks the execution of tools, delegates, or agents with
    timing information and metadata.
    """

    step_id: str
    kind: str  # "tool" | "delegate" | "agent"
    name: str
    status: str = "running"
    args: dict = field(default_factory=dict)
    output: str = ""
    parent_id: str | None = None
    task_id: str | None = None
    context_id: str | None = None
    started_at: float = field(default_factory=monotonic)
    duration_ms: int | None = None
    duration_source: str | None = None
    display_label: str | None = None
    status_icon: str | None = None
    failure_reason: str | None = None
    branch_failed: bool = False
    is_parallel: bool = False
    server_started_at: float | None = None
    server_finished_at: float | None = None
    duration_unknown: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self, duration_raw: float | None, *, source: str | None = None) -> None:
        """Mark the step as finished and calculate duration.

        Args:
            duration_raw: Raw duration in seconds, or None to calculate from started_at
            source: Optional duration source tag
        """
        self.duration_unknown = False
        if isinstance(duration_raw, (int, float)) and duration_raw > 0:
            # Use provided duration if it's a positive number (even if very small)
            self.duration_ms = round(float(duration_raw) * 1000)
            self.duration_source = source or self.duration_source or "provided"
        else:
            # Calculate from started_at if duration_raw is None, negative, or zero
            self.duration_ms = int((monotonic() - self.started_at) * 1000)
            self.duration_source = source or self.duration_source or "monotonic"
        self.status = "finished"


@dataclass(slots=True)
class RunStats:
    """Statistics for a complete execution run.

    Tracks timing and resource usage information for workflow executions.
    """

    started_at: float = field(default_factory=monotonic)
    finished_at: float | None = None
    usage: dict[str, Any] = field(default_factory=dict)

    def stop(self) -> None:
        """Mark the run as finished and record the end time."""
        self.finished_at = monotonic()

    @property
    def duration_s(self) -> float | None:
        """Get the duration of the run in seconds.

        Returns:
            Duration in seconds if run is finished, None otherwise
        """
        return None if self.finished_at is None else round(self.finished_at - self.started_at, 2)
