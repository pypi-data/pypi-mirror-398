"""Helpers for clamping the steps summary view to a rolling window.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Callable

from rich.text import Text

Node = tuple[str, tuple[bool, ...]]
LabelFn = Callable[[str], str]
ParentFn = Callable[[str], str | None]


def clamp_step_nodes(
    nodes: list[Node],
    *,
    window: int,
    get_label: LabelFn,
    get_parent: ParentFn,
) -> tuple[list[Node], Text | None, Text | None]:
    """Return a windowed slice of nodes plus optional header/footer notices."""
    if window <= 0 or len(nodes) <= window:
        return nodes, None, None

    start_index = len(nodes) - window
    first_visible_step_id = nodes[start_index][0]
    header = _build_header(first_visible_step_id, window, len(nodes), get_label, get_parent)
    footer = _build_footer(len(nodes) - window)
    return nodes[start_index:], header, footer


def _build_header(
    step_id: str,
    window: int,
    total: int,
    get_label: LabelFn,
    get_parent: ParentFn,
) -> Text:
    """Construct the leading notice for a truncated window."""
    parts = [f"… (latest {window} of {total} steps shown"]
    path = _collect_path_labels(step_id, get_label, get_parent)
    if path:
        parts.append("; continuing with ")
        parts.append(" / ".join(path))
    parts.append(")")
    return Text("".join(parts), style="dim")


def _build_footer(hidden_count: int) -> Text:
    """Construct the footer notice indicating hidden steps."""
    noun = "step" if hidden_count == 1 else "steps"
    message = f"{hidden_count} earlier {noun} hidden. Press Ctrl+T to inspect the full transcript."
    return Text(message, style="dim")


def _collect_path_labels(
    step_id: str,
    get_label: LabelFn,
    get_parent: ParentFn,
) -> list[str]:
    """Collect labels for the ancestry of the provided step."""
    labels: list[str] = []
    seen: set[str] = set()
    current = step_id
    while current and current not in seen:
        seen.add(current)
        label = get_label(current)
        if label:
            labels.append(label)
        parent = get_parent(current)
        if not parent:
            break
        current = parent
    labels.reverse()
    return labels
