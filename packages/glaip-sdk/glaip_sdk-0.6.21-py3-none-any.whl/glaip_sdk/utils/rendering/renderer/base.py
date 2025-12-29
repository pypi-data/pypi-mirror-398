"""Base renderer class that orchestrates all rendering components.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from time import monotonic
from typing import Any

from rich.console import Console as RichConsole
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

from glaip_sdk.icons import ICON_AGENT, ICON_AGENT_STEP, ICON_DELEGATE, ICON_TOOL_STEP
from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.rendering.formatting import (
    format_main_title,
    is_step_finished,
    normalise_display_label,
)
from glaip_sdk.utils.rendering.models import RunStats, Step
from glaip_sdk.utils.rendering.layout.panels import create_main_panel
from glaip_sdk.utils.rendering.layout.progress import (
    build_progress_footer,
    format_elapsed_time,
    format_working_indicator,
    get_spinner_char,
    is_delegation_tool,
)
from glaip_sdk.utils.rendering.layout.summary import render_summary_panels
from glaip_sdk.utils.rendering.layout.transcript import (
    DEFAULT_TRANSCRIPT_THEME,
    TranscriptSnapshot,
    build_final_panel,
    build_transcript_snapshot,
    build_transcript_view,
    extract_query_from_meta,
    format_final_panel_title,
)
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event
from glaip_sdk.utils.rendering.renderer.stream import StreamProcessor
from glaip_sdk.utils.rendering.renderer.thinking import ThinkingScopeController
from glaip_sdk.utils.rendering.renderer.tool_panels import ToolPanelController
from glaip_sdk.utils.rendering.renderer.transcript_mode import TranscriptModeMixin
from glaip_sdk.utils.rendering.state import (
    RendererState,
    TranscriptBuffer,
    coerce_received_at,
    truncate_display,
)
from glaip_sdk.utils.rendering.steps import (
    StepManager,
    format_step_label,
)
from glaip_sdk.utils.rendering.timing import coerce_server_time

_NO_STEPS_TEXT = Text("No steps yet", style="dim")

# Configure logger
logger = logging.getLogger("glaip_sdk.run_renderer")

# Constants
RUNNING_STATUS_HINTS = {"running", "started", "pending", "working"}
ARGS_VALUE_MAX_LEN = 160


class RichStreamRenderer(TranscriptModeMixin):
    """Live, modern terminal renderer for agent execution with rich visual output."""

    def __init__(
        self,
        console: RichConsole | None = None,
        *,
        cfg: RendererConfig | None = None,
        verbose: bool = False,
        transcript_buffer: TranscriptBuffer | None = None,
        callbacks: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the renderer.

        Args:
            console: Rich console instance
            cfg: Renderer configuration
            verbose: Whether to enable verbose mode
            transcript_buffer: Optional transcript buffer for capturing output
            callbacks: Optional dictionary of callback functions
        """
        super().__init__()
        self.console = console or RichConsole()
        self.cfg = cfg or RendererConfig()
        self.verbose = verbose

        # Initialize components
        self.stream_processor = StreamProcessor()
        self.state = RendererState()
        if transcript_buffer is not None:
            self.state.buffer = transcript_buffer

        self._callbacks = callbacks or {}

        # Initialize step manager and other state
        self.steps = StepManager(max_steps=self.cfg.summary_max_steps)
        # Live display instance (single source of truth)
        self.live: Live | None = None
        self._step_spinners: dict[str, Spinner] = {}
        self._last_steps_panel_template: Any | None = None

        # Tool tracking and thinking scopes
        self._step_server_start_times: dict[str, float] = {}
        self.tool_controller = ToolPanelController(
            steps=self.steps,
            stream_processor=self.stream_processor,
            console=self.console,
            cfg=self.cfg,
            step_server_start_times=self._step_server_start_times,
            output_prefix="**Output:**\n",
        )
        self.thinking_controller = ThinkingScopeController(
            self.steps,
            step_server_start_times=self._step_server_start_times,
        )
        self._root_agent_friendly: str | None = None
        self._root_agent_step_id: str | None = None
        self._root_query: str | None = None
        self._root_query_attached: bool = False

        # Timing
        self._started_at: float | None = None

        # Header/text
        self.header_text: str = ""
        # Track per-step server start times for accurate elapsed labels
        # Output formatting constants
        self.OUTPUT_PREFIX: str = "**Output:**\n"

        self._final_transcript_snapshot: TranscriptSnapshot | None = None
        self._final_transcript_renderables: tuple[list[Any], list[Any]] | None = None

    def on_start(self, meta: dict[str, Any]) -> None:
        """Handle renderer start event."""
        if self.cfg.live:
            # Defer creating Live to _ensure_live so tests and prod both work
            pass

        # Set up initial state
        self._started_at = monotonic()
        try:
            self.state.meta = json.loads(json.dumps(meta))
        except Exception:
            self.state.meta = dict(meta)

        meta_payload = meta or {}
        self.steps.set_root_agent(meta_payload.get("agent_id"))
        self._root_agent_friendly = self._humanize_agent_slug(meta_payload.get("agent_name"))
        self._root_query = truncate_display(
            meta_payload.get("input_message")
            or meta_payload.get("query")
            or meta_payload.get("message")
            or (meta_payload.get("meta") or {}).get("input_message")
            or ""
        )
        if not self._root_query:
            self._root_query = None
        self._root_query_attached = False

        # Print compact header and user request (parity with old renderer)
        self._render_header(meta)
        self._render_user_query(meta)

    def _render_header(self, meta: dict[str, Any]) -> None:
        """Render the agent header with metadata."""
        parts = self._build_header_parts(meta)
        self.header_text = " ".join(parts)

        if not self.header_text:
            return

        # Use a rule-like header for readability with fallback
        if not self._render_header_rule():
            self._render_header_fallback()

    def _build_header_parts(self, meta: dict[str, Any]) -> list[str]:
        """Build header text parts from metadata."""
        parts: list[str] = [ICON_AGENT]
        agent_name = meta.get("agent_name", "agent")
        if agent_name:
            parts.append(agent_name)

        model = meta.get("model", "")
        if model:
            parts.extend(["•", model])

        run_id = meta.get("run_id", "")
        if run_id:
            parts.extend(["•", run_id])

        return parts

    def _render_header_rule(self) -> bool:
        """Render header as a rule. Returns True if successful."""
        try:
            self.console.rule(self.header_text)
            return True
        except Exception:  # pragma: no cover - defensive fallback
            logger.exception("Failed to render header rule")
            return False

    def _render_header_fallback(self) -> None:
        """Fallback header rendering."""
        try:
            self.console.print(self.header_text)
        except Exception:
            logger.exception("Failed to print header fallback")

    def _build_user_query_panel(self, query: str) -> AIPPanel:
        """Create the panel used to display the user request."""
        return AIPPanel(
            Markdown(f"**Query:** {query}"),
            title="User Request",
            border_style="#d97706",
            padding=(0, 1),
        )

    def _render_user_query(self, meta: dict[str, Any]) -> None:
        """Render the user query panel."""
        query = extract_query_from_meta(meta)
        if not query:
            return
        self.console.print(self._build_user_query_panel(query))

    def _render_summary_static_sections(self) -> None:
        """Re-render header and user query when returning to summary mode."""
        meta = getattr(self.state, "meta", None)
        if meta:
            self._render_header(meta)
        elif self.header_text and not self._render_header_rule():
            self._render_header_fallback()

        query = extract_query_from_meta(meta) or self._root_query
        if query:
            self.console.print(self._build_user_query_panel(query))

    def _render_summary_after_transcript_toggle(self) -> None:
        """Render the summary panel after leaving transcript mode."""
        if self.state.finalizing_ui:
            self._render_final_summary_panels()
        elif self.live:
            self._refresh_live_panels()
        else:
            self._render_static_summary_panels()

    def _render_final_summary_panels(self) -> None:
        """Render a static summary and disable live mode for final output."""
        self.cfg.live = False
        self.live = None
        self._render_static_summary_panels()

    def _render_static_summary_panels(self) -> None:
        """Render the steps and main panels in a static (non-live) layout."""
        summary_window = self._summary_window_size()
        window_arg = summary_window if summary_window > 0 else None
        status_overrides = self._build_step_status_overrides()
        for renderable in render_summary_panels(
            self.state,
            self.steps,
            summary_window=window_arg,
            include_query_panel=False,
            step_status_overrides=status_overrides,
        ):
            self.console.print(renderable)

    def _ensure_streaming_started_baseline(self, timestamp: float) -> None:
        """Synchronize streaming start state across renderer components."""
        self.state.start_stream_timer(timestamp)
        self.stream_processor.streaming_started_at = timestamp
        self._started_at = timestamp

    def on_event(self, ev: dict[str, Any]) -> None:
        """Handle streaming events from the backend."""
        received_at = self._resolve_received_timestamp(ev)
        self._capture_event(ev, received_at)
        self.stream_processor.reset_event_tracking()

        self._sync_stream_start(ev, received_at)

        metadata = self.stream_processor.extract_event_metadata(ev)

        self._maybe_render_debug(ev, received_at)
        try:
            self._dispatch_event(ev, metadata)
        finally:
            self.stream_processor.update_timing(metadata.get("context_id"))

    def _resolve_received_timestamp(self, ev: dict[str, Any]) -> datetime:
        """Return the timestamp an event was received, normalising inputs."""
        received_at = coerce_received_at(ev.get("received_at"))
        if received_at is None:
            received_at = datetime.now(timezone.utc)

        if self.state.streaming_started_event_ts is None:
            self.state.streaming_started_event_ts = received_at

        return received_at

    def _sync_stream_start(self, ev: dict[str, Any], received_at: datetime | None) -> None:
        """Ensure renderer and stream processor share a streaming baseline."""
        baseline = self.state.streaming_started_at
        if baseline is None:
            baseline = monotonic()
            self._ensure_streaming_started_baseline(baseline)
        elif getattr(self.stream_processor, "streaming_started_at", None) is None:
            self._ensure_streaming_started_baseline(baseline)

        if ev.get("status") == "streaming_started":
            self.state.streaming_started_event_ts = received_at
            self._ensure_streaming_started_baseline(monotonic())

    def _maybe_render_debug(
        self, ev: dict[str, Any], received_at: datetime
    ) -> None:  # pragma: no cover - guard rails for verbose mode
        """Render debug view when verbose mode is enabled."""
        if not self.verbose:
            return

        self._ensure_transcript_header()
        render_debug_event(
            ev,
            self.console,
            received_ts=received_at,
            baseline_ts=self.state.streaming_started_event_ts,
        )
        self._print_transcript_hint()

    def _dispatch_event(self, ev: dict[str, Any], metadata: dict[str, Any]) -> None:
        """Route events to the appropriate renderer handlers."""
        kind = metadata["kind"]
        content = metadata["content"]

        if kind == "status":
            self._handle_status_event(ev)
        elif kind == "content":
            self._handle_content_event(content)
        elif kind == "token":
            # Token events should stream content incrementally with immediate console output
            self._handle_token_event(content)
        elif kind == "final_response":
            self._handle_final_response_event(content, metadata)
        elif kind in {"agent_step", "agent_thinking_step"}:
            self._handle_agent_step_event(ev, metadata)
        else:
            self._ensure_live()

    def _handle_status_event(self, ev: dict[str, Any]) -> None:
        """Handle status events."""
        status = ev.get("status")
        if status == "streaming_started":
            return

    def _handle_content_event(self, content: str) -> None:
        """Handle content streaming events."""
        if content:
            self.state.append_transcript_text(content)
            self._ensure_live()

    def _handle_token_event(self, content: str) -> None:
        """Handle token streaming events - print immediately for real-time streaming."""
        if content:
            self.state.append_transcript_text(content)
            # Print token content directly to stdout for immediate visibility when not verbose
            # This bypasses Rich's Live display which has refresh rate limitations
            if not self.verbose:
                try:
                    # Mark that we're streaming tokens directly to prevent Live display from starting
                    self._streaming_tokens_directly = True
                    # Stop Live display if active to prevent it from intercepting stdout
                    # and causing each token to appear on a new line
                    if self.live is not None:
                        self._stop_live_display()
                    # Write directly to stdout - tokens will stream on the same line
                    # since we're bypassing Rich's console which adds newlines
                    sys.stdout.write(content)
                    sys.stdout.flush()
                except Exception:
                    # Fallback to live display if direct write fails
                    self._ensure_live()
            else:
                # In verbose mode, use normal live display (debug panels handle the output)
                self._ensure_live()

    def _handle_final_response_event(self, content: str, metadata: dict[str, Any]) -> None:
        """Handle final response events."""
        if content:
            self.state.append_transcript_text(content)
            self.state.set_final_output(content)

            meta_payload = metadata.get("metadata") or {}
            final_time = coerce_server_time(meta_payload.get("time"))
            self._update_final_duration(final_time)
            self.thinking_controller.close_active_scopes(final_time)
            self._finish_running_steps()
            self.tool_controller.finish_all_panels()
            self._normalise_finished_icons()

        self._ensure_live()
        self._print_final_panel_if_needed()

    def _normalise_finished_icons(self) -> None:
        """Ensure finished steps release any running spinners."""
        for step in self.steps.by_id.values():
            if getattr(step, "status", None) != "running":
                self._step_spinners.pop(step.step_id, None)

    def _handle_agent_step_event(self, ev: dict[str, Any], metadata: dict[str, Any]) -> None:
        """Handle agent step events."""
        # Extract tool information using stream processor
        tool_calls_result = self.stream_processor.parse_tool_calls(ev)
        tool_name, tool_args, tool_out, tool_calls_info = tool_calls_result

        payload = metadata.get("metadata") or {}

        tracked_step: Step | None = None
        try:
            tracked_step = self.steps.apply_event(ev)
        except ValueError:
            logger.debug("Malformed step event skipped", exc_info=True)
        else:
            self._record_step_server_start(tracked_step, payload)
            self.thinking_controller.update_timeline(
                tracked_step,
                payload,
                enabled=self.cfg.render_thinking,
            )
            self._maybe_override_root_agent_label(tracked_step, payload)
            self._maybe_attach_root_query(tracked_step)

        # Track tools and sub-agents for transcript/debug context
        self.stream_processor.track_tools_and_agents(tool_name, tool_calls_info, is_delegation_tool)

        # Handle tool execution
        self.tool_controller.handle_agent_step(
            ev,
            tool_name,
            tool_args,
            tool_out,
            tool_calls_info,
            tracked_step=tracked_step,
        )

        # Update live display
        self._ensure_live()

    def _maybe_attach_root_query(self, step: Step | None) -> None:
        """Attach the user query to the root agent step for display."""
        if not step or self._root_query_attached or not self._root_query or step.kind != "agent" or step.parent_id:
            return

        args = dict(getattr(step, "args", {}) or {})
        args.setdefault("query", self._root_query)
        step.args = args
        self._root_query_attached = True

    def _record_step_server_start(self, step: Step | None, payload: dict[str, Any]) -> None:
        """Store server-provided start times for elapsed calculations."""
        if not step:
            return
        server_time = payload.get("time")
        if not isinstance(server_time, (int, float)):
            return
        self._step_server_start_times.setdefault(step.step_id, float(server_time))

    def _maybe_override_root_agent_label(self, step: Step | None, payload: dict[str, Any]) -> None:
        """Ensure the root agent row uses the human-friendly name and shows the ID."""
        if not step or step.kind != "agent" or step.parent_id:
            return
        friendly = self._root_agent_friendly or self._humanize_agent_slug((payload or {}).get("agent_name"))
        if not friendly:
            return
        agent_identifier = step.name or step.step_id
        if not agent_identifier:
            return
        step.display_label = normalise_display_label(f"{ICON_AGENT} {friendly} ({agent_identifier})")
        if not self._root_agent_step_id:
            self._root_agent_step_id = step.step_id

    # Thinking scope management is handled by ThinkingScopeController.

    def _apply_root_duration(self, duration_seconds: float | None) -> None:
        """Propagate the final run duration to the root agent step."""
        if duration_seconds is None or not self._root_agent_step_id:
            return
        root_step = self.steps.by_id.get(self._root_agent_step_id)
        if not root_step:
            return
        try:
            duration_ms = max(0, int(round(float(duration_seconds) * 1000)))
        except Exception:
            return
        root_step.duration_ms = duration_ms
        root_step.duration_source = root_step.duration_source or "run"
        root_step.status = "finished"

    @staticmethod
    def _humanize_agent_slug(value: Any) -> str | None:
        """Convert a slugified agent name into Title Case."""
        if not isinstance(value, str):
            return None
        cleaned = value.replace("_", " ").replace("-", " ").strip()
        if not cleaned:
            return None
        parts = [part for part in cleaned.split() if part]
        return " ".join(part[:1].upper() + part[1:] for part in parts)

    def _finish_running_steps(self) -> None:
        """Mark any running steps as finished to avoid lingering spinners."""
        for st in self.steps.by_id.values():
            if not is_step_finished(st):
                self._mark_incomplete_step(st)

    def _mark_incomplete_step(self, step: Step) -> None:
        """Mark a lingering step as incomplete/warning with unknown duration."""
        step.status = "finished"
        step.duration_unknown = True
        if step.duration_ms is None:
            step.duration_ms = 0
        step.duration_source = step.duration_source or "unknown"

    def _stop_live_display(self) -> None:
        """Stop live display and clean up."""
        self._shutdown_live()

    def _print_final_panel_if_needed(self) -> None:
        """Print final result when configuration requires it."""
        if self.state.printed_final_output:
            return

        body = (self.state.final_text or self.state.buffer.render() or "").strip()
        if not body:
            return

        if getattr(self, "_transcript_mode_enabled", False):
            return

        # When verbose=False and tokens were streamed directly, skip final panel
        # The user's script will print the final result, avoiding duplication
        if not self.verbose and getattr(self, "_streaming_tokens_directly", False):
            # Add a newline after streaming tokens for clean separation
            try:
                sys.stdout.write("\n")
                sys.stdout.flush()
            except Exception:
                pass
            self.state.printed_final_output = True
            return

        if self.verbose:
            panel = build_final_panel(
                self.state,
                title=self._final_panel_title(),
            )
            if panel is None:
                return
            self.console.print(panel)
            self.state.printed_final_output = True

    def finalize(self) -> tuple[list[Any], list[Any]]:
        """Compose the final transcript renderables."""
        return self._compose_final_transcript()

    def _compose_final_transcript(self) -> tuple[list[Any], list[Any]]:
        """Build the transcript snapshot used for final summaries."""
        summary_window = self._summary_window_size()
        summary_window = summary_window if summary_window > 0 else None
        snapshot = build_transcript_snapshot(
            self.state,
            self.steps,
            query_text=extract_query_from_meta(self.state.meta),
            meta=self.state.meta,
            summary_window=summary_window,
            step_status_overrides=self._build_step_status_overrides(),
        )
        header, body = build_transcript_view(snapshot)
        self._final_transcript_snapshot = snapshot
        self._final_transcript_renderables = (header, body)
        return header, body

    def _render_final_summary(self, header: list[Any], body: list[Any]) -> None:
        """Print the composed transcript summary for non-live renders."""
        renderables = list(header) + list(body)
        for renderable in renderables:
            try:
                self.console.print(renderable)
                self.console.print()
            except Exception:
                pass

    def on_complete(self, stats: RunStats) -> None:
        """Handle completion event."""
        self.state.finalizing_ui = True

        self._handle_stats_duration(stats)
        self.thinking_controller.close_active_scopes(self.state.final_duration_seconds)
        self._cleanup_ui_elements()
        self._finalize_display()
        self._print_completion_message()

    def _handle_stats_duration(self, stats: RunStats) -> None:
        """Handle stats processing and duration calculation."""
        if not isinstance(stats, RunStats):
            return

        duration = None
        try:
            if stats.finished_at is not None and stats.started_at is not None:
                duration = max(0.0, float(stats.finished_at) - float(stats.started_at))
        except Exception:
            duration = None

        if duration is not None:
            self._update_final_duration(duration, overwrite=True)

    def _cleanup_ui_elements(self) -> None:
        """Clean up running UI elements."""
        # Mark any running steps as finished to avoid lingering spinners
        self._finish_running_steps()

        # Mark unfinished tool panels as finished
        self.tool_controller.finish_all_panels()

    def _finalize_display(self) -> None:
        """Finalize live display and render final output."""
        # When verbose=False and tokens were streamed directly, skip live display updates
        # to avoid showing duplicate final result
        if not self.verbose and getattr(self, "_streaming_tokens_directly", False):
            # Just add a newline after streaming tokens for clean separation
            try:
                sys.stdout.write("\n")
                sys.stdout.flush()
            except Exception:
                pass
            self._stop_live_display()
            self.state.printed_final_output = True
            return

        # Final refresh
        self._ensure_live()

        header, body = self.finalize()

        # Stop live display
        self._stop_live_display()

        # Render final output based on configuration
        if self.cfg.live:
            self._print_final_panel_if_needed()
        else:
            self._render_final_summary(header, body)

    def _print_completion_message(self) -> None:
        """Print completion message based on current mode."""
        if self._transcript_mode_enabled:
            try:
                self.console.print(
                    "[dim]Run finished. Press Ctrl+T to return to the summary view or stay here to inspect events. "
                    "Use the post-run viewer for export.[/dim]"
                )
            except Exception:
                pass
        else:
            # No transcript toggle in summary mode; nothing to print here.
            return

    def _ensure_live(self) -> None:
        """Ensure live display is updated."""
        if getattr(self, "_transcript_mode_enabled", False):
            return
        # When verbose=False, don't start Live display if we're streaming tokens directly
        # This prevents Live from intercepting stdout and causing tokens to appear on separate lines
        if not self.verbose and getattr(self, "_streaming_tokens_directly", False):
            return
        if not self._ensure_live_stack():
            return

        self._start_live_if_needed()

        if self.live:
            self._refresh_live_panels()
            if (
                not self._transcript_mode_enabled
                and not self.state.finalizing_ui
                and not self._summary_hint_printed_once
            ):
                self._print_summary_hint(force=True)

    def _ensure_live_stack(self) -> bool:
        """Guarantee the console exposes the internal live stack Rich expects."""
        live_stack = getattr(self.console, "_live_stack", None)
        if isinstance(live_stack, list):
            return True

        try:
            self.console._live_stack = []  # type: ignore[attr-defined]
            return True
        except Exception:
            # If the console forbids attribute assignment we simply skip the live
            # update for this cycle and fall back to buffered printing.
            logger.debug(
                "Console missing _live_stack; skipping live UI initialisation",
                exc_info=True,
            )
            return False

    def _start_live_if_needed(self) -> None:
        """Create and start a Live instance when configuration allows."""
        if self.live is not None or not self.cfg.live:
            return

        try:
            self.live = Live(
                console=self.console,
                refresh_per_second=1 / self.cfg.refresh_debounce,
                transient=not self.cfg.persist_live,
            )
            self.live.start()
        except Exception:
            self.live = None

    def _refresh_live_panels(self) -> None:
        """Render panels and push them to the active Live display."""
        if not self.live:
            return

        steps_body = self._render_steps_text()
        template_panel = getattr(self, "_last_steps_panel_template", None)
        if template_panel is None:
            template_panel = self._resolve_steps_panel()
        steps_panel = AIPPanel(
            steps_body,
            title=getattr(template_panel, "title", "Steps"),
            border_style=getattr(template_panel, "border_style", "blue"),
            padding=getattr(template_panel, "padding", (0, 1)),
        )

        main_panel = self._render_main_panel()
        panels = self._build_live_panels(main_panel, steps_panel)

        self.live.update(Group(*panels))

    def _build_live_panels(
        self,
        main_panel: Any,
        steps_panel: Any,
    ) -> list[Any]:
        """Assemble the panel order for the live display."""
        if self.verbose:
            return [main_panel, steps_panel]

        return [steps_panel, main_panel]

    def _render_main_panel(self) -> Any:
        """Render the main content panel."""
        body = self.state.buffer.render().strip()
        theme = DEFAULT_TRANSCRIPT_THEME
        if not self.verbose:
            panel = build_final_panel(self.state, theme=theme)
            if panel is not None:
                return panel
        # Dynamic title with spinner + elapsed/hints
        title = self._format_enhanced_main_title()
        return create_main_panel(body, title, theme)

    def _final_panel_title(self) -> str:
        """Compose title for the final result panel including duration."""
        return format_final_panel_title(self.state)

    def apply_verbosity(self, verbose: bool) -> None:
        """Update verbose behaviour at runtime."""
        if self.verbose == verbose:
            return

        self.verbose = verbose
        desired_live = not verbose
        if desired_live != self.cfg.live:
            self.cfg.live = desired_live
            if not desired_live:
                self._shutdown_live()
            else:
                self._ensure_live()

        if self.cfg.live:
            self._ensure_live()

    # Transcript helper implementations live in TranscriptModeMixin.

    def get_aggregated_output(self) -> str:
        """Return the concatenated assistant output collected so far."""
        return self.state.buffer.render().strip()

    def get_transcript_events(self) -> list[dict[str, Any]]:
        """Return captured SSE events."""
        return list(self.state.events)

    def _format_working_indicator(self, started_at: float | None) -> str:
        """Format working indicator."""
        return format_working_indicator(
            started_at,
            self.stream_processor.server_elapsed_time,
            self.state.streaming_started_at,
        )

    def close(self) -> None:
        """Gracefully stop any live rendering and release resources."""
        self._shutdown_live()

    def __del__(self) -> None:
        """Destructor that ensures live rendering is properly shut down.

        This is a safety net to prevent resource leaks if the renderer
        is not explicitly stopped.
        """
        # Destructors must never raise
        try:
            self._shutdown_live(reset_attr=False)
        except Exception:  # pragma: no cover - destructor safety net
            pass

    def _shutdown_live(self, reset_attr: bool = True) -> None:
        """Stop the live renderer without letting exceptions escape."""
        live = getattr(self, "live", None)
        if not live:
            if reset_attr and not hasattr(self, "live"):
                self.live = None
            return

        try:
            live.stop()
        except Exception:
            logger.exception("Failed to stop live display")
        finally:
            if reset_attr:
                self.live = None

    def _get_analysis_progress_info(self) -> dict[str, Any]:
        total_steps = len(self.steps.order)
        completed_steps = sum(1 for sid in self.steps.order if is_step_finished(self.steps.by_id[sid]))
        current_step = None
        for sid in self.steps.order:
            if not is_step_finished(self.steps.by_id[sid]):
                current_step = sid
                break
        # Prefer server elapsed time when available
        elapsed = 0.0
        if isinstance(self.stream_processor.server_elapsed_time, (int, float)):
            elapsed = float(self.stream_processor.server_elapsed_time)
        elif self._started_at is not None:
            elapsed = monotonic() - self._started_at
        progress_percent = int((completed_steps / total_steps) * 100) if total_steps else 0
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "current_step": current_step,
            "progress_percent": progress_percent,
            "elapsed_time": elapsed,
            "has_running_steps": self._has_running_steps(),
        }

    def _format_enhanced_main_title(self) -> str:
        base = format_main_title(
            header_text=self.header_text,
            has_running_steps=self._has_running_steps(),
            get_spinner_char=get_spinner_char,
        )
        # Add elapsed time and subtle progress hints for long operations
        info = self._get_analysis_progress_info()
        elapsed = info.get("elapsed_time", 0.0)
        if elapsed and elapsed > 0:
            base += f" · {format_elapsed_time(elapsed)}"
        if info.get("total_steps", 0) > 1 and info.get("has_running_steps"):
            if elapsed > 60:
                base += " 🐌"
            elif elapsed > 30:
                base += " ⚠️"
        return base

    # Modern interface only — no legacy helper shims below

    def _refresh(self, _force: bool | None = None) -> None:
        # In the modular renderer, refreshing simply updates the live group
        self._ensure_live()

    def _has_running_steps(self) -> bool:
        """Check if any steps are still running."""
        for _sid, st in self.steps.by_id.items():
            if not is_step_finished(st):
                return True
        return False

    def _get_step_icon(self, step_kind: str) -> str:
        """Get icon for step kind."""
        if step_kind == "tool":
            return ICON_TOOL_STEP
        elif step_kind == "delegate":
            return ICON_DELEGATE
        elif step_kind == "agent":
            return ICON_AGENT_STEP
        return ""

    def _format_step_status(self, step: Step) -> str:
        """Format step status with elapsed time or duration."""
        if is_step_finished(step):
            return self._format_finished_badge(step)
        else:
            # Calculate elapsed time for running steps
            elapsed = self._calculate_step_elapsed_time(step)
            if elapsed >= 0.1:
                return f"[{elapsed:.2f}s]"
            ms = int(round(elapsed * 1000))
            if ms <= 0:
                return ""
            return f"[{ms}ms]"

    def _format_finished_badge(self, step: Step) -> str:
        """Compose duration badge for finished steps including source tagging."""
        if getattr(step, "duration_unknown", False) is True:
            payload = "??s"
        else:
            duration_ms = step.duration_ms
            if duration_ms is None:
                payload = "<1ms"
            elif duration_ms < 0:
                payload = "<1ms"
            elif duration_ms >= 100:
                payload = f"{duration_ms / 1000:.2f}s"
            elif duration_ms > 0:
                payload = f"{duration_ms}ms"
            else:
                payload = "<1ms"

        return f"[{payload}]"

    def _calculate_step_elapsed_time(self, step: Step) -> float:
        """Calculate elapsed time for a running step."""
        server_elapsed = self.stream_processor.server_elapsed_time
        server_start = self._step_server_start_times.get(step.step_id)

        if isinstance(server_elapsed, (int, float)) and isinstance(server_start, (int, float)):
            return max(0.0, float(server_elapsed) - float(server_start))

        try:
            return max(0.0, float(monotonic() - step.started_at))
        except Exception:
            return 0.0

    def _get_step_display_name(self, step: Step) -> str:
        """Get display name for a step."""
        if step.name and step.name != "step":
            return step.name
        return "thinking..." if step.kind == "agent" else f"{step.kind} step"

    def _resolve_step_label(self, step: Step) -> str:
        """Return the display label for a step with sensible fallbacks."""
        return format_step_label(step)

    def _check_parallel_tools(self) -> dict[tuple[str | None, str | None], list]:
        """Check for parallel running tools."""
        running_by_ctx: dict[tuple[str | None, str | None], list] = {}
        for sid in self.steps.order:
            st = self.steps.by_id[sid]
            if st.kind == "tool" and not is_step_finished(st):
                key = (st.task_id, st.context_id)
                running_by_ctx.setdefault(key, []).append(st)
        return running_by_ctx

    def _is_parallel_tool(
        self,
        step: Step,
        running_by_ctx: dict[tuple[str | None, str | None], list],
    ) -> bool:
        """Return True if multiple tools are running in the same context."""
        key = (step.task_id, step.context_id)
        return len(running_by_ctx.get(key, [])) > 1

    def _build_step_status_overrides(self) -> dict[str, str]:
        """Return status text overrides for steps (running duration badges)."""
        overrides: dict[str, str] = {}
        for sid in self.steps.order:
            step = self.steps.by_id.get(sid)
            if not step:
                continue
            try:
                status_text = self._format_step_status(step)
            except Exception:
                status_text = ""
            if status_text:
                overrides[sid] = status_text
        return overrides

    def _resolve_steps_panel(self) -> AIPPanel:
        """Return the shared steps panel renderable generated by layout helpers."""
        window_arg = self._summary_window_size()
        window_arg = window_arg if window_arg > 0 else None
        panels = render_summary_panels(
            self.state,
            self.steps,
            summary_window=window_arg,
            include_query_panel=False,
            include_final_panel=False,
            step_status_overrides=self._build_step_status_overrides(),
        )
        steps_panel = next((panel for panel in panels if getattr(panel, "title", "").lower() == "steps"), None)
        panel_cls = AIPPanel if isinstance(AIPPanel, type) else None
        if steps_panel is not None and (panel_cls is None or isinstance(steps_panel, panel_cls)):
            return steps_panel
        return AIPPanel(_NO_STEPS_TEXT.copy(), title="Steps", border_style="blue")

    def _prepare_steps_renderable(self, *, include_progress: bool) -> tuple[AIPPanel, Any]:
        """Return the template panel and content renderable for steps."""
        panel = self._resolve_steps_panel()
        self._last_steps_panel_template = panel
        base_renderable: Any = getattr(panel, "renderable", panel)

        if include_progress and not self.state.finalizing_ui:
            footer = build_progress_footer(
                state=self.state,
                steps=self.steps,
                started_at=self._started_at,
                server_elapsed_time=self.stream_processor.server_elapsed_time,
            )
            if footer is not None:
                if isinstance(base_renderable, Group):
                    base_renderable = Group(*base_renderable.renderables, footer)
                else:
                    base_renderable = Group(base_renderable, footer)
        return panel, base_renderable

    def _build_steps_body(self, *, include_progress: bool) -> Any:
        """Return the rendered steps body with optional progress footer."""
        _, renderable = self._prepare_steps_renderable(include_progress=include_progress)
        if isinstance(renderable, Group):
            return renderable
        return Group(renderable)

    def _render_steps_text(self) -> Any:
        """Return the rendered steps body used by transcript capture."""
        return self._build_steps_body(include_progress=True)

    def _summary_window_size(self) -> int:
        """Return the active window size for step display."""
        if self.state.finalizing_ui:
            return 0
        return int(self.cfg.summary_display_window or 0)

    def _update_final_duration(self, duration: float | None, *, overwrite: bool = False) -> None:
        """Store formatted duration for eventual final panels."""
        if duration is None:
            return

        try:
            duration_val = max(0.0, float(duration))
        except Exception:
            return

        existing = self.state.final_duration_seconds

        if not overwrite and existing is not None:
            return

        if overwrite and existing is not None:
            duration_val = max(existing, duration_val)

        formatted = format_elapsed_time(duration_val)
        self.state.mark_final_duration(duration_val, formatted=formatted)
        self._apply_root_duration(duration_val)
