#!/usr/bin/env python3
"""Agent runs client for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

import httpx

from glaip_sdk.client.base import BaseClient
from glaip_sdk.exceptions import TimeoutError, ValidationError
from glaip_sdk.models.agent_runs import RunSummary, RunsPage, RunWithOutput


class AgentRunsClient(BaseClient):
    """Client for agent run operations."""

    def list_runs(
        self,
        agent_id: str,
        *,
        limit: int = 20,
        page: int = 1,
    ) -> RunsPage:
        """List agent runs with pagination.

        Args:
            agent_id: UUID of the agent
            limit: Number of runs per page (1-100, default 20)
            page: Page number (1-based, default 1)

        Returns:
            RunsPage containing paginated run summaries

        Raises:
            ValidationError: If pagination parameters are invalid
            NotFoundError: If agent is not found
            AuthenticationError: If authentication fails
            TimeoutError: If request times out (30s default)
        """
        self._validate_pagination_params(limit, page)
        envelope = self._fetch_runs_envelope(agent_id, limit, page)
        normalized_data = self._normalize_runs_payload(envelope.get("data"))
        runs = [RunSummary(**item) for item in normalized_data]
        return self._build_runs_page(envelope, runs, limit, page)

    def _fetch_runs_envelope(self, agent_id: str, limit: int, page: int) -> dict[str, Any]:
        params = {"limit": limit, "page": page}
        try:
            envelope = self._request_with_envelope(
                "GET",
                f"/agents/{agent_id}/runs",
                params=params,
            )
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {self._timeout}s while fetching agent runs") from e

        if isinstance(envelope, dict):
            return envelope
        return {"data": envelope}

    @staticmethod
    def _validate_pagination_params(limit: int, page: int) -> None:
        if limit < 1 or limit > 100:
            raise ValidationError("limit must be between 1 and 100")
        if page < 1:
            raise ValidationError("page must be >= 1")

    @staticmethod
    def _normalize_runs_payload(data_payload: Any) -> list[Any]:
        if not data_payload:
            return []
        normalized_data: list[Any] = []
        for item in data_payload:
            normalized_data.append(AgentRunsClient._normalize_run_item(item))
        return normalized_data

    @staticmethod
    def _normalize_run_item(item: Any) -> Any:
        if isinstance(item, dict):
            if item.get("config") is None:
                item["config"] = {}
            schedule_id = item.get("schedule_id")
            if schedule_id == "None" or schedule_id == "":
                item["schedule_id"] = None
        return item

    @staticmethod
    def _build_runs_page(
        envelope: dict[str, Any],
        runs: list[RunSummary],
        limit: int,
        page: int,
    ) -> RunsPage:
        return RunsPage(
            data=runs,
            total=envelope.get("total", 0),
            page=envelope.get("page", page),
            limit=envelope.get("limit", limit),
            has_next=envelope.get("has_next", False),
            has_prev=envelope.get("has_prev", False),
        )

    def get_run(
        self,
        agent_id: str,
        run_id: str,
    ) -> RunWithOutput:
        """Get detailed run information including SSE event stream.

        Args:
            agent_id: UUID of the agent
            run_id: UUID of the run

        Returns:
            RunWithOutput containing complete run details and event stream

        Raises:
            NotFoundError: If run or agent is not found
            AuthenticationError: If authentication fails
            TimeoutError: If request times out (30s default)
        """
        try:
            envelope = self._request_with_envelope(
                "GET",
                f"/agents/{agent_id}/runs/{run_id}",
            )
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {self._timeout}s while fetching run detail") from e

        if not isinstance(envelope, dict):
            envelope = {"data": envelope}

        data = envelope.get("data") or {}
        # Normalize config, output, and schedule_id fields
        if data.get("config") is None:
            data["config"] = {}
        if data.get("output") is None:
            data["output"] = []
        # Normalize schedule_id: convert string "None" to None
        schedule_id = data.get("schedule_id")
        if schedule_id == "None" or schedule_id == "":
            data["schedule_id"] = None

        return RunWithOutput(**data)
