"""Thinking scope controller used by the renderer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from time import monotonic
from typing import Any

from glaip_sdk.utils.rendering.formatting import is_step_finished
from glaip_sdk.utils.rendering.models import Step
from glaip_sdk.utils.rendering.state import ThinkingScopeState
from glaip_sdk.utils.rendering.steps import StepManager
from glaip_sdk.utils.rendering.timing import calculate_timeline_duration, coerce_server_time

FINISHED_STATUS_HINTS = {
    "finished",
    "success",
    "succeeded",
    "completed",
    "failed",
    "stopped",
    "error",
}


class ThinkingScopeController:
    """Encapsulates deterministic thinking bookkeeping for the renderer."""

    def __init__(self, steps: StepManager, *, step_server_start_times: dict[str, float]) -> None:
        """Initialize the thinking scope controller.

        Args:
            steps: Step manager instance for tracking steps
            step_server_start_times: Dictionary mapping step IDs to server start times
        """
        self._steps = steps
        self._step_server_start_times = step_server_start_times
        self._scopes: dict[str, ThinkingScopeState] = {}

    def update_timeline(self, step: Step | None, payload: dict[str, Any], *, enabled: bool) -> None:
        """Update thinking spans for a streamed step event."""
        if not enabled or not step:
            return

        now_monotonic = monotonic()
        server_time = coerce_server_time(payload.get("time"))
        status_hint = (payload.get("status") or "").lower()

        if self._is_scope_anchor(step):
            self._update_anchor_thinking(
                step=step,
                server_time=server_time,
                status_hint=status_hint,
                now_monotonic=now_monotonic,
            )
            return

        self._update_child_thinking(
            step=step,
            server_time=server_time,
            status_hint=status_hint,
            now_monotonic=now_monotonic,
        )

    def close_active_scopes(self, server_time: float | None) -> None:
        """Finish any in-flight thinking nodes during finalization."""
        now = monotonic()
        for scope in self._scopes.values():
            if not scope.active_thinking_id:
                continue
            self._finish_scope_thinking(scope, server_time, now)

    # ------------------------------------------------------------------
    # Internal helpers mirroring the previous renderer implementation.
    # ------------------------------------------------------------------
    def _update_anchor_thinking(
        self,
        *,
        step: Step,
        server_time: float | None,
        status_hint: str,
        now_monotonic: float,
    ) -> None:
        scope = self._get_or_create_scope(step)
        if scope.anchor_started_at is None and server_time is not None:
            scope.anchor_started_at = server_time

        if not scope.closed and scope.active_thinking_id is None:
            self._start_scope_thinking(
                scope,
                start_server_time=scope.anchor_started_at or server_time,
                start_monotonic=now_monotonic,
            )

        is_anchor_finished = status_hint in FINISHED_STATUS_HINTS or (not status_hint and is_step_finished(step))
        if is_anchor_finished:
            scope.anchor_finished_at = server_time or scope.anchor_finished_at
            self._finish_scope_thinking(scope, server_time, now_monotonic)
            scope.closed = True

        parent_anchor_id = self._resolve_anchor_id(step)
        if parent_anchor_id:
            self._cascade_anchor_update(
                parent_anchor_id=parent_anchor_id,
                child_step=step,
                server_time=server_time,
                now_monotonic=now_monotonic,
                is_finished=is_anchor_finished,
            )

    def _cascade_anchor_update(
        self,
        *,
        parent_anchor_id: str,
        child_step: Step,
        server_time: float | None,
        now_monotonic: float,
        is_finished: bool,
    ) -> None:
        parent_scope = self._scopes.get(parent_anchor_id)
        if not parent_scope or parent_scope.closed:
            return
        if is_finished:
            self._mark_child_finished(parent_scope, child_step.step_id, server_time, now_monotonic)
        else:
            self._mark_child_running(parent_scope, child_step, server_time, now_monotonic)

    def _update_child_thinking(
        self,
        *,
        step: Step,
        server_time: float | None,
        status_hint: str,
        now_monotonic: float,
    ) -> None:
        anchor_id = self._resolve_anchor_id(step)
        if not anchor_id:
            return

        scope = self._scopes.get(anchor_id)
        if not scope or scope.closed or step.kind == "thinking":
            return

        is_finish_event = status_hint in FINISHED_STATUS_HINTS or (not status_hint and is_step_finished(step))
        if is_finish_event:
            self._mark_child_finished(scope, step.step_id, server_time, now_monotonic)
        else:
            self._mark_child_running(scope, step, server_time, now_monotonic)

    def _resolve_anchor_id(self, step: Step) -> str | None:
        parent_id = step.parent_id
        while parent_id:
            parent = self._steps.by_id.get(parent_id)
            if not parent:
                return None
            if self._is_scope_anchor(parent):
                return parent.step_id
            parent_id = parent.parent_id
        return None

    def _get_or_create_scope(self, step: Step) -> ThinkingScopeState:
        scope = self._scopes.get(step.step_id)
        if scope:
            if scope.task_id is None:
                scope.task_id = step.task_id
            if scope.context_id is None:
                scope.context_id = step.context_id
            return scope
        scope = ThinkingScopeState(
            anchor_id=step.step_id,
            task_id=step.task_id,
            context_id=step.context_id,
        )
        self._scopes[step.step_id] = scope
        return scope

    def _is_scope_anchor(self, step: Step) -> bool:
        if step.kind in {"agent", "delegate"}:
            return True
        name = (step.name or "").lower()
        return name.startswith(("delegate_to_", "delegate_", "delegate "))

    def _start_scope_thinking(
        self,
        scope: ThinkingScopeState,
        *,
        start_server_time: float | None,
        start_monotonic: float,
    ) -> None:
        if scope.closed or scope.active_thinking_id or not scope.anchor_id:
            return
        step = self._steps.start_or_get(
            task_id=scope.task_id,
            context_id=scope.context_id,
            kind="thinking",
            name=f"agent_thinking_step::{scope.anchor_id}",
            parent_id=scope.anchor_id,
            args={"reason": "deterministic_timeline"},
        )
        step.display_label = "💭 Thinking…"
        scope.active_thinking_id = step.step_id
        scope.idle_started_at = start_server_time
        scope.idle_started_monotonic = start_monotonic

    def _finish_scope_thinking(
        self,
        scope: ThinkingScopeState,
        end_server_time: float | None,
        end_monotonic: float,
    ) -> None:
        if not scope.active_thinking_id:
            return
        thinking_step = self._steps.by_id.get(scope.active_thinking_id)
        if not thinking_step:
            scope.active_thinking_id = None
            scope.idle_started_at = None
            scope.idle_started_monotonic = None
            return

        duration = calculate_timeline_duration(
            scope.idle_started_at,
            end_server_time,
            scope.idle_started_monotonic,
            end_monotonic,
        )
        thinking_step.display_label = thinking_step.display_label or "💭 Thinking…"
        if duration is not None:
            thinking_step.finish(duration, source="timeline")
        else:
            thinking_step.finish(None, source="timeline")
        scope.active_thinking_id = None
        scope.idle_started_at = None
        scope.idle_started_monotonic = None

    def _mark_child_running(
        self,
        scope: ThinkingScopeState,
        step: Step,
        server_time: float | None,
        now_monotonic: float,
    ) -> None:
        if step.step_id in scope.running_children:
            return
        scope.running_children.add(step.step_id)
        if not scope.active_thinking_id:
            return

        start_server = self._step_server_start_times.get(step.step_id)
        if start_server is None:
            start_server = server_time
        self._finish_scope_thinking(scope, start_server, now_monotonic)

    def _mark_child_finished(
        self,
        scope: ThinkingScopeState,
        step_id: str,
        server_time: float | None,
        now_monotonic: float,
    ) -> None:
        scope.running_children.discard(step_id)
        if scope.active_thinking_id or scope.closed or scope.running_children:
            return
        self._start_scope_thinking(
            scope,
            start_server_time=server_time,
            start_monotonic=now_monotonic,
        )


__all__ = ["ThinkingScopeController", "FINISHED_STATUS_HINTS"]
