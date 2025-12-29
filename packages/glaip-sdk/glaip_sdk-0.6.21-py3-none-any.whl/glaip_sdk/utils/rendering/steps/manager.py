"""Rendering utilities.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Iterator

from glaip_sdk.utils.rendering.models import Step
from glaip_sdk.utils.rendering.step_tree_state import StepTreeState
from glaip_sdk.utils.rendering.steps.event_processor import StepEventMixin


class StepManagerError(Exception):
    """Raised when invalid operations are attempted on the step tree."""


class StepManager(StepEventMixin):
    """Manages the lifecycle and organization of execution steps.

    Tracks step creation, parent-child relationships, and execution state
    with automatic pruning of old steps when limits are reached.
    """

    def __init__(self, max_steps: int = 200) -> None:
        """Initialize the step manager.

        Args:
            max_steps: Maximum number of steps to retain before pruning
        """
        normalised_max = int(max_steps) if isinstance(max_steps, (int, float)) else 0
        self.state = StepTreeState(max_steps=normalised_max)
        self.by_id: dict[str, Step] = self.state.step_index
        self.key_index: dict[tuple, str] = {}
        self.slot_counter: dict[tuple, int] = {}
        self.max_steps = normalised_max
        self._last_running: dict[tuple, str] = {}
        self._step_aliases: dict[str, str] = {}
        self.root_agent_id: str | None = None
        self._scope_anchors: dict[str, list[str]] = {}
        self._step_scope_map: dict[str, str] = {}

    def set_root_agent(self, agent_id: str | None) -> None:
        """Record the root agent identifier for scope-aware parenting."""
        if isinstance(agent_id, str) and agent_id.strip():
            self.root_agent_id = agent_id.strip()

    def _alloc_slot(
        self,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
    ) -> int:
        k = (task_id, context_id, kind, name)
        self.slot_counter[k] = self.slot_counter.get(k, 0) + 1
        return self.slot_counter[k]

    def _key(
        self,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
        slot: int,
    ) -> tuple[str | None, str | None, str, str, int]:
        return (task_id, context_id, kind, name, slot)

    def _make_id(
        self,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
        slot: int,
    ) -> str:
        return f"{task_id or 't'}::{context_id or 'c'}::{kind}::{name}::{slot}"

    def start_or_get(
        self,
        *,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
        parent_id: str | None = None,
        args: dict[str, object] | None = None,
    ) -> Step:
        """Start a new step or return existing running step with same parameters.

        Args:
            task_id: Task identifier
            context_id: Context identifier
            kind: Step kind (tool, delegate, agent)
            name: Step name
            parent_id: Parent step ID if this is a child step
            args: Step arguments

        Returns:
            The Step instance (new or existing)
        """
        existing = self.find_running(task_id=task_id, context_id=context_id, kind=kind, name=name)
        if existing:
            if args and existing.args != args:
                existing.args = args
            return existing
        slot = self._alloc_slot(task_id, context_id, kind, name)
        key = self._key(task_id, context_id, kind, name, slot)
        step_id = self._make_id(task_id, context_id, kind, name, slot)
        st = Step(
            step_id=step_id,
            kind=kind,
            name=name,
            parent_id=parent_id,
            task_id=task_id,
            context_id=context_id,
            args=args or {},
        )
        self.by_id[step_id] = st
        if parent_id:
            self.children.setdefault(parent_id, []).append(step_id)
        else:
            self.order.append(step_id)
        self.key_index[key] = step_id
        self.state.retained_ids.add(step_id)
        self._prune_steps()
        self._last_running[(task_id, context_id, kind, name)] = step_id
        return st

    def _calculate_total_steps(self) -> int:
        """Calculate total number of steps."""
        return len(self.order) + sum(len(v) for v in self.children.values())

    def _get_subtree_size(self, root_id: str) -> int:
        """Get the size of a subtree (including root)."""
        subtree = [root_id]
        stack = list(self.children.get(root_id, []))
        while stack:
            x = stack.pop()
            subtree.append(x)
            stack.extend(self.children.get(x, []))
        return len(subtree)

    def _remove_subtree(self, root_id: str) -> None:
        """Remove a complete subtree from all data structures."""
        for step_id in self._collect_subtree_ids(root_id):
            self._purge_step_references(step_id)

    def _collect_subtree_ids(self, root_id: str) -> list[str]:
        """Return a flat list of step ids contained within a subtree."""
        stack = [root_id]
        collected: list[str] = []
        while stack:
            sid = stack.pop()
            collected.append(sid)
            stack.extend(self.children.pop(sid, []))
        return collected

    def _purge_step_references(self, step_id: str) -> None:
        """Remove a single step id from all indexes and helper structures."""
        st = self.by_id.pop(step_id, None)
        if st:
            key = (st.task_id, st.context_id, st.kind, st.name)
            self._last_running.pop(key, None)
            self.state.retained_ids.discard(step_id)
            self.state.discard_running(step_id)
        self._remove_parent_links(step_id)
        if step_id in self.order:
            self.order.remove(step_id)
        self.state.buffered_children.pop(step_id, None)
        self.state.pending_branch_failures.discard(step_id)

    def _remove_parent_links(self, child_id: str) -> None:
        """Detach a child id from any parent lists."""
        for parent, kids in self.children.copy().items():
            if child_id not in kids:
                continue
            kids.remove(child_id)
            if not kids:
                self.children.pop(parent, None)

    def _should_prune_steps(self, total: int) -> bool:
        """Check if steps should be pruned."""
        if self.max_steps <= 0:
            return False
        return total > self.max_steps

    def _get_oldest_step_id(self) -> str | None:
        """Get the oldest step ID for pruning."""
        return self.order[0] if self.order else None

    def _prune_steps(self) -> None:
        """Prune steps when total exceeds maximum."""
        total = self._calculate_total_steps()
        if not self._should_prune_steps(total):
            return

        while self._should_prune_steps(total) and self.order:
            sid = self._get_oldest_step_id()
            if not sid:
                break

            subtree_size = self._get_subtree_size(sid)
            self._remove_subtree(sid)
            total -= subtree_size

    def remove_step(self, step_id: str) -> None:
        """Remove a single step from the tree and cached indexes."""
        step = self.by_id.pop(step_id, None)
        if not step:
            return

        if step.parent_id:
            self.state.unlink_child(step.parent_id, step_id)
        else:
            self.state.unlink_root(step_id)

        self.children.pop(step_id, None)
        self.state.buffered_children.pop(step_id, None)
        self.state.retained_ids.discard(step_id)
        self.state.pending_branch_failures.discard(step_id)
        self.state.discard_running(step_id)

        self.key_index = {key: sid for key, sid in self.key_index.items() if sid != step_id}
        for key, last_sid in self._last_running.copy().items():
            if last_sid == step_id:
                self._last_running.pop(key, None)

        aliases = [alias for alias, target in self._step_aliases.items() if alias == step_id or target == step_id]
        for alias in aliases:
            self._step_aliases.pop(alias, None)

    def get_child_count(self, step_id: str) -> int:
        """Get the number of child steps for a given step.

        Args:
            step_id: The parent step ID

        Returns:
            Number of child steps
        """
        return len(self.children.get(step_id, []))

    def find_running(
        self,
        *,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
    ) -> Step | None:
        """Find a currently running step with the given parameters.

        Args:
            task_id: Task identifier
            context_id: Context identifier
            kind: Step kind (tool, delegate, agent)
            name: Step name

        Returns:
            The running Step if found, None otherwise
        """
        key = (task_id, context_id, kind, name)
        step_id = self._last_running.get(key)
        if step_id:
            st = self.by_id.get(step_id)
            if st and st.status != "finished":
                return st
        for sid in reversed(list(self._iter_all_steps())):
            st = self.by_id.get(sid)
            if (
                st
                and (st.task_id, st.context_id, st.kind, st.name)
                == (
                    task_id,
                    context_id,
                    kind,
                    name,
                )
                and st.status != "finished"
            ):
                return st
        return None

    def list_ordered(self) -> list[Step]:
        """Return a depth-first list of steps currently tracked."""
        ordered: list[Step] = []
        for step_id, _branch_state in self.iter_tree():
            step = self.by_id.get(step_id)
            if step:
                ordered.append(step)
        return ordered

    def prune_for_summary(self, limit: int) -> list[tuple[str, tuple[bool, ...]]]:
        """Return the most recent ``limit`` nodes for compact summaries."""
        if limit < 0:
            raise StepManagerError("limit must be non-negative")
        nodes = list(self.iter_tree())
        if limit == 0 or len(nodes) <= limit:
            return nodes
        return nodes[-limit:]

    def finish(
        self,
        *,
        task_id: str | None,
        context_id: str | None,
        kind: str,
        name: str,
        output: object | None = None,
        duration_raw: float | None = None,
    ) -> Step:
        """Finish a step with the given parameters.

        Args:
            task_id: Task identifier
            context_id: Context identifier
            kind: Step kind (tool, delegate, agent)
            name: Step name
            output: Step output data
            duration_raw: Raw duration in seconds

        Returns:
            The finished Step instance

        Raises:
            RuntimeError: If no matching step is found
        """
        st = self.find_running(task_id=task_id, context_id=context_id, kind=kind, name=name)
        if not st:
            # Try to find any existing step with matching parameters, even if not running
            for sid in reversed(list(self._iter_all_steps())):
                st_check = self.by_id.get(sid)
                if (
                    st_check
                    and st_check.task_id == task_id
                    and st_check.context_id == context_id
                    and st_check.kind == kind
                    and st_check.name == name
                ):
                    st = st_check
                    break

            # If still no step found, create a new one
            if not st:
                st = self.start_or_get(task_id=task_id, context_id=context_id, kind=kind, name=name)

        if output:
            st.output = output
        st.finish(duration_raw)
        key = (task_id, context_id, kind, name)
        if self._last_running.get(key) == st.step_id:
            self._last_running.pop(key, None)
        return st

    def _iter_all_steps(self) -> Iterator[str]:
        for root in self.order:
            yield root
            stack = list(self.children.get(root, []))
            while stack:
                sid = stack.pop()
                yield sid
                stack.extend(self.children.get(sid, []))

    def iter_tree(self) -> Iterator[tuple[str, tuple[bool, ...]]]:
        """Expose depth-first traversal info for rendering."""
        yield from self.state.iter_visible_tree()

    @property
    def order(self) -> list[str]:
        """Root step ordering accessor backed by StepTreeState."""
        return self.state.root_order

    @order.setter
    def order(self, value: list[str]) -> None:
        self.state.root_order = list(value)

    @property
    def children(self) -> dict[str, list[str]]:
        """Child mapping accessor backed by StepTreeState."""
        return self.state.child_map

    @children.setter
    def children(self, value: dict[str, list[str]]) -> None:
        self.state.child_map = value
