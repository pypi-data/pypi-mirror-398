"""Configuration types for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RendererConfig:
    """Configuration for the RichStreamRenderer."""

    # Performance
    refresh_debounce: float = 0.25
    render_thinking: bool = True
    live: bool = True
    persist_live: bool = True
    summary_display_window: int = 20

    # Scrollback/append options
    summary_max_steps: int = 0
    append_finished_snapshots: bool = False
    snapshot_max_chars: int = 0
    snapshot_max_lines: int = 0
