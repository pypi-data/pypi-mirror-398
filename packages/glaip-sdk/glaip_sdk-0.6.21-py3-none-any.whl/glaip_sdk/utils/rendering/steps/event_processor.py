"""SSE event processing mixin for StepManager.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from copy import deepcopy
from time import monotonic
from typing import Any

from glaip_sdk.utils.rendering.models import Step
from glaip_sdk.utils.rendering.timing import coerce_server_time

logger = logging.getLogger(__name__)


COERCION_FAILED_KEY = "_meta_coercion_failed_"


class StepEventMixin:
    """Mixin providing SSE event processing capabilities for StepManager.

    This mixin adds methods to process server-sent events (SSE) and update
    step state accordingly. It handles event parsing, step creation/updates,
    parent-child relationships, and duration tracking.
    """

    def apply_event(self, event: dict[str, Any]) -> Step:
        """Apply an SSE step event and return the updated step."""
        cloned_events = self._split_multi_tool_event(event)
        if cloned_events:
            last_step: Step | None = None
            for cloned in cloned_events:
                last_step = self._apply_single_event(cloned)
            if last_step:
                return last_step
        return self._apply_single_event(event)

    def _split_multi_tool_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Split events that describe multiple tool calls into per-call clones."""
        metadata = event.get("metadata") or {}
        tool_info = metadata.get("tool_info") or {}
        tool_calls = tool_info.get("tool_calls")
        if not self._should_split_tool_calls(tool_calls):
            return []
        if self._all_delegate_calls(tool_calls):
            return []

        base_step_id = metadata.get("step_id") or "step"
        clones: list[dict[str, Any]] = []
        for index, call in enumerate(tool_calls):
            clone = self._clone_tool_call(event, tool_info, call, base_step_id, index)
            if clone is not None:
                clones.append(clone)
        return clones

    @staticmethod
    def _should_split_tool_calls(tool_calls: Any) -> bool:
        """Return True when an event references more than one tool call."""
        return isinstance(tool_calls, list) and len(tool_calls) > 1

    def _all_delegate_calls(self, tool_calls: Any) -> bool:
        """Return True when an event batch only contains delegate tools."""
        if not isinstance(tool_calls, list) or not tool_calls:
            return False
        for call in tool_calls:
            if not isinstance(call, dict):
                return False
            name = (call.get("name") or "").lower()
            if not self._is_delegate_tool(name):
                return False
        return True

    def _clone_tool_call(
        self,
        event: dict[str, Any],
        tool_info: dict[str, Any],
        call: Any,
        base_step_id: str,
        index: int,
    ) -> dict[str, Any] | None:
        """Create a per-call clone of a multi-tool event."""
        if not isinstance(call, dict):
            return None

        cloned = deepcopy(event)
        cloned_meta = cloned.setdefault("metadata", {})
        cloned_tool_info = dict(tool_info)
        cloned_tool_info["tool_calls"] = [dict(call)]
        self._copy_tool_call_field(call, cloned_tool_info, "name")
        self._copy_tool_call_field(call, cloned_tool_info, "args")
        self._copy_tool_call_field(call, cloned_tool_info, "id")
        cloned_meta["tool_info"] = cloned_tool_info
        cloned_meta["step_id"] = self._derive_call_step_id(call, base_step_id, index)
        return cloned

    @staticmethod
    def _copy_tool_call_field(call: dict[str, Any], target: dict[str, Any], field: str) -> None:
        """Copy a field from the tool call when it exists."""
        value = call.get(field)
        if value:
            target[field] = value

    @staticmethod
    def _derive_call_step_id(call: dict[str, Any], base_step_id: str, index: int) -> str:
        """Determine the per-call step identifier."""
        call_id = call.get("id")
        if isinstance(call_id, str):
            stripped = call_id.strip()
            if stripped:
                return stripped
        return f"{base_step_id}#{index}"

    def _apply_single_event(self, event: dict[str, Any]) -> Step:
        metadata, step_id, tool_info, args = self._parse_event_payload(event)
        metadata_failed = bool(metadata.pop(COERCION_FAILED_KEY, False))
        tool_name = self._resolve_tool_name(tool_info, metadata, step_id)
        kind = self._derive_step_kind(tool_name, metadata)
        parent_hint = self._coerce_parent_id(metadata.get("previous_step_ids"))

        step = self._get_or_create_step(
            step_id=step_id,
            kind=kind,
            tool_name=tool_name,
            event=event,
            metadata=metadata,
            args=args,
        )
        parent_id = self._determine_parent_id(step, metadata, parent_hint)
        self._link_step(step, parent_id)

        self.state.retained_ids.add(step.step_id)
        if metadata_failed:
            step.metadata = {}
        else:
            step.metadata = dict(metadata)
        self._flush_buffered_children(step.step_id)
        self._apply_pending_branch_flags(step.step_id)

        status = self._normalise_status(metadata.get("status"), event.get("status"), event.get("task_state"))
        status = self._apply_failure_state(step, status, event)

        server_time = coerce_server_time(metadata.get("time"))
        self._update_server_timestamps(step, server_time, status)

        self._apply_duration(
            step=step,
            status=status,
            tool_info=tool_info,
            args=args,
            server_time=server_time,
        )

        self._update_scope_bindings(
            step=step,
            metadata=metadata,
            tool_name=tool_name,
            status=status,
        )

        self._update_parallel_tracking(step)
        self._update_running_index(step)
        self._prune_steps()
        return step

    def _parse_event_payload(self, event: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, Any]]:
        metadata_raw = event.get("metadata") or {}
        metadata, metadata_reliable = self._coerce_event_metadata(metadata_raw)
        if not metadata:
            raise ValueError("Step event missing metadata payload")
        metadata[COERCION_FAILED_KEY] = not metadata_reliable

        step_id = metadata.get("step_id")
        if not isinstance(step_id, str) or not step_id:
            raise ValueError("Step event missing step_id")

        tool_info = metadata.get("tool_info") or {}
        if not isinstance(tool_info, dict):
            tool_info = {}

        canonical_step_id = self._canonicalize_step_id(step_id, tool_info)
        metadata["step_id"] = canonical_step_id
        step_id = canonical_step_id

        args = self._resolve_tool_args(tool_info)

        return metadata, step_id, tool_info, args

    def _coerce_event_metadata(self, metadata: Any) -> tuple[dict[str, Any], bool]:
        """Return a dict copy of event metadata with graceful fallbacks."""
        if isinstance(metadata, dict):
            return metadata, True
        if isinstance(metadata, Mapping):
            try:
                return dict(metadata), True
            except Exception:
                logger.debug("Failed to coerce mapping metadata; falling back to key-by-key copy", exc_info=True)
                return self._copy_mapping_fields(metadata), False
        # All other payloads are treated as empty
        return {}, False

    @staticmethod
    def _copy_mapping_fields(metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Copy known fields from a mapping without iteration."""
        copied: dict[str, Any] = {}
        for key in (
            "step_id",
            "tool_info",
            "status",
            "kind",
            "previous_step_ids",
            "time",
            "agent_name",
            "task_id",
            "context_id",
        ):
            value = metadata.get(key)  # type: ignore[attr-defined]
            if value is not None:
                copied[key] = value
        return copied

    def _resolve_tool_name(self, tool_info: dict[str, Any], metadata: dict[str, Any], step_id: str) -> str:
        name = tool_info.get("name")
        if not name:
            call = self._first_tool_call(tool_info)
            if call:
                name = call.get("name")
        if isinstance(name, str) and name.strip():
            return name
        if name is not None:
            return str(name)

        agent_name = metadata.get("agent_name")
        if isinstance(agent_name, str) and agent_name.strip():
            return agent_name
        return step_id

    def _resolve_tool_args(self, tool_info: dict[str, Any]) -> dict[str, Any]:
        args = tool_info.get("args")
        if isinstance(args, dict):
            return args
        call = self._first_tool_call(tool_info)
        if call:
            call_args = call.get("args")
            if isinstance(call_args, dict):
                return call_args
        return {}

    def _first_tool_call(self, tool_info: dict[str, Any]) -> dict[str, Any] | None:
        tool_calls = tool_info.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            candidate = tool_calls[0]
            if isinstance(candidate, dict):
                return candidate
        return None

    def _get_or_create_step(
        self,
        step_id: str,
        kind: str,
        tool_name: str,
        event: dict[str, Any],
        metadata: dict[str, Any],
        args: dict[str, Any],
    ) -> Step:
        existing = self.by_id.get(step_id)
        if existing:
            return self._update_existing_step(existing, kind, tool_name, event, metadata, args)
        return self._create_step_from_event(step_id, kind, tool_name, event, metadata, args)

    def _create_step_from_event(
        self,
        step_id: str,
        kind: str,
        tool_name: str,
        event: dict[str, Any],
        metadata: dict[str, Any],
        args: dict[str, Any],
    ) -> Step:
        step = Step(
            step_id=step_id,
            kind=kind,
            name=tool_name or step_id,
            task_id=self._coalesce_metadata_value("task_id", event, metadata, fallback=None),
            context_id=self._coalesce_metadata_value("context_id", event, metadata, fallback=None),
            args=args or {},
        )
        self.by_id[step_id] = step
        self.state.retained_ids.add(step_id)
        return step

    def _update_existing_step(
        self,
        step: Step,
        kind: str,
        tool_name: str,
        event: dict[str, Any],
        metadata: dict[str, Any],
        args: dict[str, Any],
    ) -> Step:
        step.kind = step.kind or kind
        step.name = tool_name or step.name
        if args:
            step.args = args
        step.task_id = self._coalesce_metadata_value("task_id", event, metadata, fallback=step.task_id)
        step.context_id = self._coalesce_metadata_value("context_id", event, metadata, fallback=step.context_id)
        return step

    def _apply_failure_state(self, step: Step, status: str, event: dict[str, Any]) -> str:
        failure_reason = self._extract_failure_reason(status, event.get("task_state"), event.get("content"))
        if not failure_reason:
            step.status = status
            return status

        step.failure_reason = failure_reason
        if status not in {"failed", "stopped"}:
            status = "failed"
        self._set_branch_warning(step.parent_id)
        step.status = status
        return status

    def _apply_duration(
        self,
        step: Step,
        status: str,
        tool_info: dict[str, Any],
        args: dict[str, Any],
        server_time: float | None,
    ) -> None:
        duration_ms, duration_source = self._resolve_duration_from_event(tool_info, args)
        if duration_ms is not None:
            step.duration_ms = duration_ms
            step.duration_source = duration_source
            return

        if status in {"finished", "failed", "stopped"} and step.duration_ms is None:
            timeline_ms = self._calculate_server_duration(step, server_time)
            if timeline_ms is not None:
                step.duration_ms = timeline_ms
                step.duration_source = "timeline"
                return
            try:
                step.duration_ms = int((monotonic() - step.started_at) * 1000)
            except Exception:
                step.duration_ms = 0
            step.duration_source = step.duration_source or "monotonic"

    def _update_running_index(self, step: Step) -> None:
        key = (step.task_id, step.context_id, step.kind, step.name)
        if step.status == "finished":
            if self._last_running.get(key) == step.step_id:
                self._last_running.pop(key, None)
        else:
            self._last_running[key] = step.step_id

    def _coalesce_metadata_value(
        self,
        key: str,
        event: dict[str, Any],
        metadata: dict[str, Any],
        *,
        fallback: Any = None,
    ) -> Any:
        if event.get(key) is not None:
            return event[key]
        if metadata.get(key) is not None:
            return metadata[key]
        return fallback

    def _coerce_parent_id(self, parent_value: Any) -> str | None:
        if isinstance(parent_value, list):
            for candidate in parent_value:
                if isinstance(candidate, str) and candidate.strip():
                    return self._canonical_parent_id(candidate)
        elif isinstance(parent_value, str) and parent_value.strip():
            return self._canonical_parent_id(parent_value)
        return None

    def _canonical_parent_id(self, value: str) -> str:
        return self._step_aliases.get(value, value)

    def _derive_step_kind(self, tool_name: str | None, metadata: dict[str, Any]) -> str:
        metadata_kind = metadata.get("kind")
        kind = self._clean_kind(metadata_kind)
        tool = (tool_name or "").lower()

        if self._is_thinking_step(kind, tool):
            return "thinking"
        if self._is_delegate_tool(tool):
            return "delegate"
        if kind == "agent_thinking_step" and tool:
            return "tool"
        if self._is_top_level_agent(tool_name, metadata, kind):
            return "agent"
        if kind == "agent_step" and tool.startswith("delegate"):
            return "delegate"
        if tool.startswith("agent_"):
            return "agent"
        if kind == "agent_step":
            return "tool" if tool else "agent_step"
        return kind or "tool"

    def _clean_kind(self, metadata_kind: Any) -> str:
        return metadata_kind.lower() if isinstance(metadata_kind, str) else ""

    def _is_thinking_step(self, kind: str, tool: str) -> bool:
        if tool.startswith("agent_thinking"):
            return True
        return kind == "agent_thinking_step" and not tool

    def _is_delegate_tool(self, tool: str) -> bool:
        return tool.startswith(("delegate_to_", "delegate-", "delegate ", "delegate_"))

    def _is_top_level_agent(self, tool_name: str | None, metadata: dict[str, Any], kind: str) -> bool:
        if kind != "agent_step":
            return False
        agent_name = metadata.get("agent_name")
        if isinstance(agent_name, str) and agent_name and tool_name == agent_name:
            return True
        return self._looks_like_uuid(tool_name or "")

    @staticmethod
    def _looks_like_uuid(value: str) -> bool:
        stripped = value.replace("-", "")
        if len(stripped) not in {32, 36}:
            return False
        return all(ch in "0123456789abcdefABCDEF" for ch in stripped)

    def _normalise_status(
        self,
        metadata_status: Any,
        event_status: Any,
        task_state: Any,
    ) -> str:
        for candidate in (metadata_status, event_status, task_state):
            status = (candidate or "").lower() if isinstance(candidate, str) else ""
            if status in {"running", "started", "pending", "working"}:
                return "running"
            if status in {"finished", "success", "succeeded", "completed"}:
                return "finished"
            if status in {"failed", "error"}:
                return "failed"
            if status in {"stopped", "cancelled", "canceled"}:
                return "stopped"
        return "running"

    def _extract_failure_reason(
        self,
        status: str,
        task_state: Any,
        content: Any,
    ) -> str | None:
        failure_states = {"failed", "stopped", "error"}
        task_state_str = (task_state or "").lower() if isinstance(task_state, str) else ""
        if status in failure_states or task_state_str in failure_states:
            if isinstance(content, str) and content.strip():
                return content.strip()
            if task_state_str:
                return task_state_str
        return None

    def _resolve_duration_from_event(
        self,
        tool_info: dict[str, Any],
        args: dict[str, Any],
    ) -> tuple[int | None, str | None]:
        exec_time = tool_info.get("execution_time")
        if isinstance(exec_time, (int, float)):
            return max(0, int(round(float(exec_time) * 1000))), "metadata"

        duration_seconds = tool_info.get("duration_seconds")
        if isinstance(duration_seconds, (int, float)):
            return max(0, int(round(float(duration_seconds) * 1000))), "metadata"

        wait_seconds = args.get("wait_seconds")
        if isinstance(wait_seconds, (int, float)):
            return max(0, int(round(float(wait_seconds) * 1000))), "argument"

        return None, None

    def _determine_parent_id(self, step: Step, metadata: dict[str, Any], parent_hint: str | None) -> str | None:
        scope_parent = self._lookup_scope_parent(metadata, step)
        candidate = scope_parent or parent_hint
        if candidate == step.step_id:
            logger.debug("Step %s cannot parent itself; dropping parent hint", candidate)
            return None
        return candidate

    def _lookup_scope_parent(self, metadata: dict[str, Any], step: Step) -> str | None:
        agent_name = metadata.get("agent_name")
        if not isinstance(agent_name, str) or not agent_name.strip():
            return None
        stack = self._scope_anchors.get(agent_name.strip())
        if not stack:
            return None
        anchor_id = stack[-1]
        if anchor_id == step.step_id:
            return None
        return anchor_id

    def _link_step(self, step: Step, parent_id: str | None) -> None:
        """Attach a step to the resolved parent, buffering when necessary."""
        parent_id = self._sanitize_parent_reference(step, parent_id)
        if self._ensure_existing_link(step, parent_id):
            return

        self._detach_from_current_parent(step)
        self._attach_to_parent(step, parent_id)

    def _sanitize_parent_reference(self, step: Step, parent_id: str | None) -> str | None:
        """Guard against self-referential parent assignments."""
        if parent_id != step.step_id:
            return parent_id

        logger.debug(
            "Ignoring self-referential parent_id %s for step %s",
            parent_id,
            step.step_id,
        )
        return step.parent_id

    def _ensure_existing_link(self, step: Step, parent_id: str | None) -> bool:
        """Keep existing parent/child wiring in sync when the parent is unchanged."""
        if parent_id != step.parent_id:
            return False

        if parent_id is None:
            if step.step_id not in self.state.root_order:
                self.state.link_root(step.step_id)
            return True

        if parent_id not in self.by_id:
            return False

        children = self.children.get(parent_id, [])
        if step.step_id not in children:
            self.state.link_child(parent_id, step.step_id)
        return True

    def _detach_from_current_parent(self, step: Step) -> None:
        """Remove the step from its current parent/root collection."""
        if step.parent_id:
            self.state.unlink_child(step.parent_id, step.step_id)
            return
        self.state.unlink_root(step.step_id)

    def _attach_to_parent(self, step: Step, parent_id: str | None) -> None:
        """Attach the step to the requested parent, buffering when needed."""
        if parent_id is None:
            step.parent_id = None
            self.state.link_root(step.step_id)
            return

        if parent_id not in self.by_id:
            self.state.buffer_child(parent_id, step.step_id)
            step.parent_id = None
            return

        step.parent_id = parent_id
        self.state.link_child(parent_id, step.step_id)
        self.state.unlink_root(step.step_id)

    def _update_scope_bindings(
        self,
        *,
        step: Step,
        metadata: dict[str, Any],
        tool_name: str,
        status: str,
    ) -> None:
        agent_name = metadata.get("agent_name")
        if step.kind == "agent" and isinstance(agent_name, str) and agent_name.strip():
            self._register_scope_anchor(agent_name.strip(), step.step_id)
            return

        if step.kind == "delegate":
            slug = self._derive_delegate_slug(tool_name)
            if not slug:
                return
            # Ensure the delegate anchor exists even if the first event we see is already finished
            if status == "running" or step.step_id not in self._step_scope_map:
                self._register_scope_anchor(slug, step.step_id)
            elif status in {"finished", "failed", "stopped"}:
                self._release_scope_anchor(step.step_id)
            return

        if status in {"finished", "failed", "stopped"}:
            self._release_scope_anchor(step.step_id)

    def _register_scope_anchor(self, scope_key: str, step_id: str) -> None:
        scope = scope_key.strip()
        stack = self._scope_anchors.setdefault(scope, [])
        if step_id not in stack:
            stack.append(step_id)
        self._step_scope_map[step_id] = scope

    def _release_scope_anchor(self, step_id: str) -> None:
        scope = self._step_scope_map.get(step_id)
        if not scope or scope == (self.root_agent_id or "").strip():
            return
        stack = self._scope_anchors.get(scope)
        if stack:
            if stack[-1] == step_id:
                stack.pop()
            elif step_id in stack:
                stack.remove(step_id)
            # Clean up if stack is now empty
            if len(stack) == 0:
                self._scope_anchors.pop(scope, None)
        self._step_scope_map.pop(step_id, None)

    @staticmethod
    def _derive_delegate_slug(tool_name: str | None) -> str | None:
        if not isinstance(tool_name, str):
            return None
        slug = tool_name.strip()
        if slug.startswith("delegate_to_"):
            slug = slug.removeprefix("delegate_to_")
        elif slug.startswith("delegate_"):
            slug = slug.removeprefix("delegate_")
        elif slug.startswith("delegate-"):
            slug = slug.removeprefix("delegate-")
        slug = slug.replace("-", "_").strip()
        return slug or None

    def _update_server_timestamps(self, step: Step, server_time: float | None, status: str) -> None:
        if server_time is None:
            return
        if status == "running" and step.server_started_at is None:
            step.server_started_at = server_time
        elif status in {"finished", "failed", "stopped"}:
            step.server_finished_at = server_time
            if step.server_started_at is None:
                step.server_started_at = server_time

    def _calculate_server_duration(self, step: Step, server_time: float | None) -> int | None:
        start = step.server_started_at
        end = server_time if server_time is not None else step.server_finished_at
        if start is None or end is None:
            return None
        try:
            return max(0, int(round((float(end) - float(start)) * 1000)))
        except Exception:
            return None

    def _flush_buffered_children(self, parent_id: str) -> None:
        for child_id in self.state.pop_buffered_children(parent_id):
            child = self.by_id.get(child_id)
            if not child:
                continue
            child.parent_id = parent_id
            self.state.link_child(parent_id, child_id)
            self.state.unlink_root(child_id)

    def _apply_pending_branch_flags(self, step_id: str) -> None:
        if step_id not in self.state.pending_branch_failures:
            return
        step = self.by_id.get(step_id)
        if step:
            step.branch_failed = True
        self.state.pending_branch_failures.discard(step_id)

    def _set_branch_warning(self, parent_id: str | None) -> None:
        if not parent_id:
            return
        parent = self.by_id.get(parent_id)
        if parent:
            parent.branch_failed = True
        else:
            self.state.pending_branch_failures.add(parent_id)

    def _update_parallel_tracking(self, step: Step) -> None:
        if step.kind != "tool":
            step.is_parallel = False
            return

        key = (step.task_id, step.context_id)
        running = self.state.running_by_context.get(key)

        if step.status == "running":
            if running is None:
                running = set()
                self.state.running_by_context[key] = running
            running.add(step.step_id)
        elif running:
            running.discard(step.step_id)
            step.is_parallel = False

        if not running:
            self.state.running_by_context.pop(key, None)
            step.is_parallel = False
            return

        is_parallel = len(running) > 1
        for sid in running:
            current = self.by_id.get(sid)
            if current:
                current.is_parallel = is_parallel

    def _canonicalize_step_id(self, step_id: str, tool_info: dict[str, Any]) -> str:
        alias = self._lookup_alias(step_id)
        if alias:
            return alias

        candidate_ids = self._collect_instance_ids(tool_info)
        alias = self._find_existing_candidate_alias(candidate_ids)
        if alias:
            self._step_aliases[step_id] = alias
            return alias

        return self._register_new_alias(step_id, candidate_ids)

    def _lookup_alias(self, step_id: str) -> str | None:
        alias = self._step_aliases.get(step_id)
        return alias if alias else None

    def _find_existing_candidate_alias(self, candidate_ids: list[str]) -> str | None:
        for candidate in candidate_ids:
            mapped = self._step_aliases.get(candidate)
            if mapped:
                return mapped
        return None

    def _register_new_alias(self, step_id: str, candidate_ids: list[str]) -> str:
        if candidate_ids:
            canonical = step_id if len(candidate_ids) > 1 else candidate_ids[0]
            self._step_aliases[step_id] = canonical
            for candidate in candidate_ids:
                self._step_aliases.setdefault(candidate, canonical)
            return canonical

        self._step_aliases.setdefault(step_id, step_id)
        return step_id

    def _collect_instance_ids(self, tool_info: dict[str, Any]) -> list[str]:
        """Collect all potential identifiers for a tool invocation."""
        candidates: list[str] = []
        identifier = self._normalise_identifier(tool_info.get("id"))
        if identifier:
            candidates.append(identifier)

        candidates.extend(self._extract_tool_call_ids(tool_info.get("tool_calls")))
        return self._deduplicate_candidates(candidates)

    def _extract_tool_call_ids(self, tool_calls: Any) -> list[str]:
        """Extract unique IDs from tool_calls payloads."""
        if not isinstance(tool_calls, list):
            return []
        collected: list[str] = []
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            identifier = self._normalise_identifier(call.get("id"))
            if identifier:
                collected.append(identifier)
        return collected

    @staticmethod
    def _normalise_identifier(value: Any) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    @staticmethod
    def _deduplicate_candidates(candidates: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            ordered.append(candidate)
        return ordered
