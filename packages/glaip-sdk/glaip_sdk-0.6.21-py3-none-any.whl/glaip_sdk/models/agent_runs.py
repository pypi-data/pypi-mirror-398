#!/usr/bin/env python3
"""Agent run models for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from datetime import datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# Type alias for SSE event dictionaries
RunOutputChunk = dict[str, Any]


class RunSummary(BaseModel):
    """Represents a single agent run in list/table views with metadata only."""

    id: UUID
    agent_id: UUID
    run_type: Literal["manual", "schedule"]
    schedule_id: UUID | None = None
    status: Literal["started", "success", "failed", "cancelled", "aborted", "unavailable"]
    started_at: datetime
    completed_at: datetime | None = None
    input: str | None = None
    config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("completed_at")
    @classmethod
    def validate_completed_after_started(cls, v: datetime | None, info) -> datetime | None:
        """Validate that completed_at is after started_at if present."""
        if v is not None and "started_at" in info.data:
            started_at = info.data["started_at"]
            if v < started_at:
                raise ValueError("completed_at must be after started_at")
        return v

    def duration(self) -> timedelta | None:
        """Calculate duration from started_at to completed_at.

        Returns:
            Duration as timedelta if completed_at exists, None otherwise
        """
        if self.completed_at is not None:
            return self.completed_at - self.started_at
        return None

    def duration_formatted(self) -> str:
        """Format duration as HH:MM:SS string.

        Returns:
            Formatted duration string or "—" if not completed
        """
        duration = self.duration()
        if duration is None:
            return "—"
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def input_preview(self, max_length: int = 120) -> str:
        """Generate truncated input preview for table display.

        Args:
            max_length: Maximum length of preview string

        Returns:
            Truncated input string or "—" if input is None or empty
        """
        if not self.input:
            return "—"
        # Strip newlines and collapse whitespace
        preview = " ".join(self.input.split())
        if len(preview) > max_length:
            return preview[:max_length] + "…"
        return preview


class RunsPage(BaseModel):
    """Represents a paginated collection of run summaries from the list endpoint."""

    data: list[RunSummary]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)
    has_next: bool
    has_prev: bool

    @model_validator(mode="after")
    def validate_pagination_consistency(self) -> "RunsPage":
        """Validate pagination consistency."""
        # If has_next is True, then page * limit < total
        if self.has_next and self.page * self.limit >= self.total:
            raise ValueError("has_next inconsistency: page * limit must be < total when has_next is True")
        return self


class RunWithOutput(RunSummary):
    """Extends RunSummary with the complete SSE event stream for detailed viewing."""

    output: list[RunOutputChunk] = Field(default_factory=list)

    @field_validator("output", mode="before")
    @classmethod
    def normalize_output(cls, v: Any) -> list[RunOutputChunk]:
        """Normalize output field to empty list when null."""
        if v is None:
            return []
        return v
