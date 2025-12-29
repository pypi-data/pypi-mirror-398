"""Transcript mode utilities extracted from the renderer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from glaip_sdk.utils.rendering.renderer.debug import render_debug_event
from glaip_sdk.utils.rendering.state import coerce_received_at


class TranscriptModeMixin:
    """Provides transcript-mode toggling, hints, and replay helpers."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize transcript mode mixin.

        Args:
            *args: Positional arguments passed to parent class
            **kwargs: Keyword arguments passed to parent class
        """
        super().__init__(*args, **kwargs)
        self._transcript_mode_enabled: bool = False
        self._transcript_render_cursor: int = 0
        self.transcript_controller: Any | None = None
        self._transcript_hint_message = "[dim]Transcript view · Press Ctrl+T to return to the summary.[/dim]"
        self._summary_hint_message = "[dim]Press Ctrl+T to inspect raw transcript events.[/dim]"
        self._summary_hint_printed_once: bool = False
        self._transcript_hint_printed_once: bool = False
        self._transcript_header_printed: bool = False
        self._transcript_enabled_message_printed: bool = False

    # ------------------------------------------------------------------
    # Public controls
    # ------------------------------------------------------------------
    @property
    def transcript_mode_enabled(self) -> bool:
        """Return True when transcript mode is currently active."""
        return self._transcript_mode_enabled

    def toggle_transcript_mode(self) -> None:
        """Flip transcript mode on/off."""
        self.set_transcript_mode(not self._transcript_mode_enabled)

    def set_transcript_mode(self, enabled: bool) -> None:
        """Set transcript mode explicitly."""
        if enabled == self._transcript_mode_enabled:
            return

        self._transcript_mode_enabled = enabled
        self.apply_verbosity(enabled)

        if enabled:
            self._summary_hint_printed_once = False
            self._transcript_hint_printed_once = False
            self._transcript_header_printed = False
            self._transcript_enabled_message_printed = False
            self._stop_live_display()
            self._clear_console_safe()
            self._print_transcript_enabled_message()
            self._render_transcript_backfill()
        else:
            self._transcript_hint_printed_once = False
            self._transcript_header_printed = False
            self._transcript_enabled_message_printed = False
            self._clear_console_safe()

        self._render_summary_static_sections()
        summary_notice = (
            "[dim]Returning to the summary view. Streaming will continue here.[/dim]"
            if not self.state.finalizing_ui
            else "[dim]Returning to the summary view.[/dim]"
        )
        self.console.print(summary_notice)
        self._render_summary_after_transcript_toggle()
        if not self.state.finalizing_ui:
            self._print_summary_hint(force=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _clear_console_safe(self) -> None:
        try:
            self.console.clear()
        except Exception:
            pass

    def _print_transcript_hint(self) -> None:
        if not self._transcript_mode_enabled:
            return
        try:
            self.console.print(self._transcript_hint_message)
        except Exception:
            pass
        else:
            self._transcript_hint_printed_once = True

    def _print_transcript_enabled_message(self) -> None:
        if self._transcript_enabled_message_printed:
            return
        try:
            self.console.print("[dim]Transcript mode enabled — streaming raw transcript events.[/dim]")
        except Exception:
            pass
        else:
            self._transcript_enabled_message_printed = True

    def _ensure_transcript_header(self) -> None:
        if self._transcript_header_printed:
            return
        try:
            self.console.rule("Transcript Events")
        except Exception:
            self._transcript_header_printed = True
            return
        self._transcript_header_printed = True

    def _print_summary_hint(self, force: bool = False) -> None:
        controller = getattr(self, "transcript_controller", None)
        if controller and not getattr(controller, "enabled", False):
            if not force:
                self._summary_hint_printed_once = True
            return
        if not force and self._summary_hint_printed_once:
            return
        try:
            self.console.print(self._summary_hint_message)
        except Exception:
            return
        self._summary_hint_printed_once = True

    def _render_transcript_backfill(self) -> None:
        pending = self.state.events[self._transcript_render_cursor :]
        self._ensure_transcript_header()
        if not pending:
            self._print_transcript_hint()
            return

        baseline = self.state.streaming_started_event_ts
        for ev in pending:
            received_ts = coerce_received_at(ev.get("received_at"))
            render_debug_event(
                ev,
                self.console,
                received_ts=received_ts,
                baseline_ts=baseline,
            )

        self._transcript_render_cursor = len(self.state.events)
        self._print_transcript_hint()

    def _capture_event(self, ev: dict[str, Any], received_at: datetime | None = None) -> None:
        self.state.record_event(ev, received_at=received_at)
        if self._transcript_mode_enabled:
            self._transcript_render_cursor = len(self.state.events)


__all__ = ["TranscriptModeMixin"]
