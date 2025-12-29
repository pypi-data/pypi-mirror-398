"""State container for hierarchical renderer steps.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from glaip_sdk.utils.rendering.models import Step


@dataclass(slots=True)
class StepTreeState:
    """Track hierarchical ordering, buffers, and pruning metadata."""

    max_steps: int = 200
    root_order: list[str] = field(default_factory=list)
    child_map: dict[str, list[str]] = field(default_factory=dict)
    buffered_children: dict[str, list[str]] = field(default_factory=dict)
    running_by_context: dict[tuple[str | None, str | None], set[str]] = field(default_factory=dict)
    retained_ids: set[str] = field(default_factory=set)
    step_index: dict[str, Step] = field(default_factory=dict)
    pending_branch_failures: set[str] = field(default_factory=set)

    def link_root(self, step_id: str) -> None:
        """Ensure a step id is present in the root ordering."""
        if step_id not in self.root_order:
            self.root_order.append(step_id)

    def unlink_root(self, step_id: str) -> None:
        """Remove a step id from the root ordering if present."""
        if step_id in self.root_order:
            self.root_order.remove(step_id)

    def link_child(self, parent_id: str, child_id: str) -> None:
        """Attach a child step to a parent."""
        children = self.child_map.setdefault(parent_id, [])
        if child_id not in children:
            children.append(child_id)

    def unlink_child(self, parent_id: str, child_id: str) -> None:
        """Detach a child from a parent."""
        children = self.child_map.get(parent_id)
        if not children:
            return

        if child_id in children:
            children.remove(child_id)
        # Clean up if the list is now empty
        if len(children) == 0:
            self.child_map.pop(parent_id, None)

    def buffer_child(self, parent_id: str, child_id: str) -> None:
        """Track a child that is waiting for its parent to appear."""
        queue = self.buffered_children.setdefault(parent_id, [])
        if child_id not in queue:
            queue.append(child_id)

    def pop_buffered_children(self, parent_id: str) -> list[str]:
        """Return any buffered children for a parent."""
        return self.buffered_children.pop(parent_id, [])

    def discard_running(self, step_id: str) -> None:
        """Remove a step from running context tracking."""
        for key, running in tuple(self.running_by_context.items()):
            if step_id in running:
                running.discard(step_id)
                if not running:
                    self.running_by_context.pop(key, None)

    def iter_visible_tree(self) -> Iterator[tuple[str, tuple[bool, ...]]]:
        """Yield step ids in depth-first order alongside branch metadata.

        Returns:
            Iterator of (step_id, branch_state) tuples where branch_state
            captures whether each ancestor was the last child. This data
            is later used by rendering helpers to draw connectors such as
            `│`, `├─`, and `└─` consistently.
        """
        roots = tuple(self.root_order)
        total_roots = len(roots)
        for index, root_id in enumerate(roots):
            yield root_id, ()
            ancestor_state = (index == total_roots - 1,)
            yield from self._walk_children(root_id, ancestor_state)

    def _walk_children(
        self, parent_id: str, ancestor_state: tuple[bool, ...]
    ) -> Iterator[tuple[str, tuple[bool, ...]]]:
        """Depth-first traversal helper yielding children with ancestry info."""
        children = self.child_map.get(parent_id, [])
        total_children = len(children)
        for idx, child_id in enumerate(children):
            is_last = idx == total_children - 1
            branch_state = ancestor_state + (is_last,)
            yield child_id, branch_state
            yield from self._walk_children(child_id, branch_state)
