"""Summary panel helpers shared between renderer and viewer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from glaip_sdk.utils.rendering.layout.transcript import (
    DEFAULT_TRANSCRIPT_THEME,
    build_transcript_snapshot,
    build_transcript_view,
    normalise_meta_payload,
)
from glaip_sdk.utils.rendering.state import RendererState
from glaip_sdk.utils.rendering.steps import StepManager


def render_summary_panels(
    state: RendererState,
    steps: StepManager,
    *,
    theme: str | None = None,
    summary_window: int | None = None,
    include_query_panel: bool = True,
    include_final_panel: bool = True,
    step_status_overrides: dict[str, str] | None = None,
) -> list[Any]:
    """Return shared summary panels for renderer and offline viewer."""
    resolved_theme = theme or DEFAULT_TRANSCRIPT_THEME
    snapshot_source = state.to_snapshot() if hasattr(state, "to_snapshot") else state
    if isinstance(snapshot_source, Mapping):
        raw_meta = snapshot_source.get("meta")
    else:
        raw_meta = getattr(state, "meta", None)
    snapshot_meta = normalise_meta_payload(raw_meta)
    snapshot = build_transcript_snapshot(
        snapshot_source,
        steps,
        meta=snapshot_meta,
        summary_window=summary_window,
        theme=resolved_theme,
        step_status_overrides=step_status_overrides,
    )
    _header, body = build_transcript_view(snapshot, theme=resolved_theme)

    return [
        renderable
        for renderable in body
        if _should_include_summary_panel(
            renderable,
            include_query_panel=include_query_panel,
            include_final_panel=include_final_panel,
        )
    ]


def _should_include_summary_panel(
    renderable: Any,
    *,
    include_query_panel: bool,
    include_final_panel: bool,
) -> bool:
    """Return True when the panel should be included in the summary list."""
    title = getattr(renderable, "title", "")
    normalised = title.lower() if isinstance(title, str) else ""
    if not include_query_panel and normalised == "user request":
        return False
    if not include_final_panel and normalised.startswith("final result"):
        return False
    return True
