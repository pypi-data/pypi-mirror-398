#!/usr/bin/env python3
"""Rendering helpers for agent streaming flows.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterable, Callable
from time import monotonic
from typing import Any

import httpx
from rich.console import Console as _Console

from glaip_sdk.config.constants import DEFAULT_AGENT_RUN_TIMEOUT
from glaip_sdk.utils.client_utils import iter_sse_events
from glaip_sdk.utils.rendering.models import RunStats
from glaip_sdk.utils.rendering.renderer import (
    RendererFactoryOptions,
    RichStreamRenderer,
    make_default_renderer,
    make_minimal_renderer,
    make_silent_renderer,
    make_verbose_renderer,
)
from glaip_sdk.utils.rendering.state import TranscriptBuffer

NO_AGENT_RESPONSE_FALLBACK = "No agent response received."
_FINAL_EVENT_TYPES = {"final_response", "error", "step_limit_exceeded"}


def _coerce_to_string(value: Any) -> str:
    """Return a best-effort string representation for transcripts."""
    try:
        return str(value)
    except Exception:
        return f"{value}"


def _has_visible_text(value: Any) -> bool:
    """Return True when the value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


class AgentRunRenderingManager:
    """Coordinate renderer creation and streaming event handling."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the rendering manager.

        Args:
            logger: Optional logger instance, creates default if None
        """
        self._logger = logger or logging.getLogger(__name__)
        self._buffer_factory = TranscriptBuffer

    # --------------------------------------------------------------------- #
    # Renderer setup helpers
    # --------------------------------------------------------------------- #
    def create_renderer(
        self,
        renderer_spec: RichStreamRenderer | str | None,
        *,
        verbose: bool = False,
    ) -> RichStreamRenderer:
        """Create an appropriate renderer based on the supplied spec."""
        transcript_buffer = self._buffer_factory()
        base_options = RendererFactoryOptions(console=_Console(), transcript_buffer=transcript_buffer)
        if isinstance(renderer_spec, RichStreamRenderer):
            return renderer_spec

        if isinstance(renderer_spec, str):
            lowered = renderer_spec.lower()
            if lowered == "silent":
                return self._attach_buffer(base_options.build(make_silent_renderer), transcript_buffer)
            if lowered == "minimal":
                return self._attach_buffer(base_options.build(make_minimal_renderer), transcript_buffer)
            if lowered == "verbose":
                return self._attach_buffer(base_options.build(make_verbose_renderer), transcript_buffer)

        if verbose:
            return self._attach_buffer(base_options.build(make_verbose_renderer), transcript_buffer)

        default_options = RendererFactoryOptions(
            console=_Console(),
            transcript_buffer=transcript_buffer,
            verbose=verbose,
        )
        return self._attach_buffer(default_options.build(make_default_renderer), transcript_buffer)

    @staticmethod
    def _attach_buffer(renderer: RichStreamRenderer, buffer: TranscriptBuffer) -> RichStreamRenderer:
        """Attach a captured transcript buffer to a renderer for later inspection."""
        try:
            renderer._captured_transcript_buffer = buffer  # type: ignore[attr-defined]
        except Exception:
            pass
        return renderer

    def build_initial_metadata(
        self,
        agent_id: str,
        message: str,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Construct the initial renderer metadata payload."""
        return {
            "agent_name": kwargs.get("agent_name", agent_id),
            "model": kwargs.get("model"),
            "run_id": None,
            "input_message": message,
        }

    @staticmethod
    def start_renderer(renderer: RichStreamRenderer, meta: dict[str, Any]) -> None:
        """Notify renderer that streaming is starting."""
        renderer.on_start(meta)

    # --------------------------------------------------------------------- #
    # Streaming event handling
    # --------------------------------------------------------------------- #
    def process_stream_events(
        self,
        stream_response: httpx.Response,
        renderer: RichStreamRenderer,
        timeout_seconds: float,
        agent_name: str | None,
        meta: dict[str, Any],
    ) -> tuple[str, dict[str, Any], float | None, float | None]:
        """Process streaming events and accumulate response."""
        final_text = ""
        stats_usage: dict[str, Any] = {}
        started_monotonic: float | None = None

        self._capture_request_id(stream_response, meta, renderer)

        controller = getattr(renderer, "transcript_controller", None)
        if controller and getattr(controller, "enabled", False):
            controller.on_stream_start(renderer)

        try:
            for event in iter_sse_events(stream_response, timeout_seconds, agent_name):
                if started_monotonic is None:
                    started_monotonic = self._maybe_start_timer(event)

                final_text, stats_usage = self._process_single_event(
                    event,
                    renderer,
                    final_text,
                    stats_usage,
                    meta,
                )

                if controller and getattr(controller, "enabled", False):
                    controller.poll(renderer)
                parsed_event = self._parse_event(event)
                if parsed_event and self._is_final_event(parsed_event):
                    break
        finally:
            if controller and getattr(controller, "enabled", False):
                controller.on_stream_complete()

        finished_monotonic = monotonic()
        return final_text, stats_usage, started_monotonic, finished_monotonic

    async def async_process_stream_events(
        self,
        event_stream: AsyncIterable[dict[str, Any]],
        renderer: RichStreamRenderer,
        meta: dict[str, Any],
        *,
        skip_final_render: bool = True,
    ) -> tuple[str, dict[str, Any], float | None, float | None]:
        """Process streaming events from an async event source.

        This method provides unified stream processing for both remote (HTTP)
        and local (LangGraph) agent execution, ensuring consistent behavior.

        Args:
            event_stream: Async iterable yielding SSE-like event dicts.
                Each event should have a "data" key with JSON string, or be
                a pre-parsed dict with "content", "metadata", etc.
            renderer: Renderer to use for displaying events.
            meta: Metadata dictionary for renderer context.
            skip_final_render: If True, skip rendering final_response events
                (they are rendered separately via finalize_renderer).

        Returns:
            Tuple of (final_text, stats_usage, started_monotonic, finished_monotonic).
        """
        final_text = ""
        stats_usage: dict[str, Any] = {}
        started_monotonic: float | None = None
        last_rendered_content: str | None = None

        controller = getattr(renderer, "transcript_controller", None)
        if controller and getattr(controller, "enabled", False):
            controller.on_stream_start(renderer)

        try:
            async for event in event_stream:
                if started_monotonic is None:
                    started_monotonic = monotonic()

                # Parse event if needed (handles both raw SSE and pre-parsed dicts)
                parsed_event = self._parse_event(event)
                if parsed_event is None:
                    continue

                # Process the event and update accumulators
                final_text, stats_usage = self._handle_parsed_event(
                    parsed_event,
                    renderer,
                    final_text,
                    stats_usage,
                    meta,
                    skip_final_render=skip_final_render,
                    last_rendered_content=last_rendered_content,
                )

                # Track last rendered content to avoid duplicates
                content_str = self._extract_content_string(parsed_event)
                if content_str:
                    last_rendered_content = content_str

                if controller and getattr(controller, "enabled", False):
                    controller.poll(renderer)
                if parsed_event and self._is_final_event(parsed_event):
                    break
        finally:
            if controller and getattr(controller, "enabled", False):
                controller.on_stream_complete()

        finished_monotonic = monotonic()
        return final_text, stats_usage, started_monotonic, finished_monotonic

    def _parse_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Parse an SSE event dict into a usable format.

        Args:
            event: Raw event dict, either with "data" key (SSE format) or
                pre-parsed with "content", "metadata", etc.

        Returns:
            Parsed event dict, or None if parsing fails.
        """
        if "data" in event:
            try:
                return json.loads(event["data"])
            except json.JSONDecodeError:
                self._logger.debug("Non-JSON SSE fragment skipped")
                return None
        # Already parsed (e.g., from local runner)
        return event if event else None

    def _handle_parsed_event(
        self,
        ev: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        meta: dict[str, Any],
        *,
        skip_final_render: bool = True,
        last_rendered_content: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Handle a parsed event and update accumulators.

        Args:
            ev: Parsed event dictionary.
            renderer: Renderer instance.
            final_text: Current accumulated final text.
            stats_usage: Usage statistics dictionary.
            meta: Metadata dictionary.
            skip_final_render: If True, skip rendering final_response events.
            last_rendered_content: Last rendered content to avoid duplicates.

        Returns:
            Tuple of (updated_final_text, updated_stats_usage).
        """
        kind = self._get_event_kind(ev)

        # Dispatch to specialized handlers based on event kind
        handler = self._get_event_handler(kind, ev)
        if handler:
            return handler(ev, renderer, final_text, stats_usage, meta, skip_final_render)

        # Default: handle content events
        return self._handle_content_event_async(ev, renderer, final_text, stats_usage, last_rendered_content)

    def _get_event_handler(
        self,
        kind: str | None,
        ev: dict[str, Any],
    ) -> Callable[..., tuple[str, dict[str, Any]]] | None:
        """Get the appropriate handler for an event kind.

        Args:
            kind: Event kind string.
            ev: Event dictionary (for checking is_final flag).

        Returns:
            Handler function or None for default content handling.
        """
        if kind == "usage":
            return self._handle_usage_event
        if kind == "final_response" or ev.get("is_final"):
            return self._handle_final_response_event
        if kind == "run_info":
            return self._handle_run_info_event_wrapper
        if kind in ("artifact", "status_update"):
            return self._handle_render_only_event
        return None

    def _handle_usage_event(
        self,
        ev: dict[str, Any],
        _renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        _meta: dict[str, Any],
        _skip_final_render: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Handle usage events."""
        stats_usage.update(ev.get("usage") or {})
        return final_text, stats_usage

    def _handle_final_response_event(
        self,
        ev: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        _meta: dict[str, Any],
        skip_final_render: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Handle final_response events."""
        content = ev.get("content")
        if content:
            final_text = str(content)
        if not skip_final_render:
            renderer.on_event(ev)
        return final_text, stats_usage

    def _handle_run_info_event_wrapper(
        self,
        ev: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        meta: dict[str, Any],
        _skip_final_render: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Handle run_info events."""
        self._handle_run_info_event(ev, meta, renderer)
        return final_text, stats_usage

    def _handle_render_only_event(
        self,
        ev: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        _meta: dict[str, Any],
        _skip_final_render: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Handle events that only need rendering (artifact, status_update)."""
        renderer.on_event(ev)
        return final_text, stats_usage

    def _handle_content_event_async(
        self,
        ev: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        last_rendered_content: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """Handle content events with deduplication."""
        content = ev.get("content")
        if content:
            content_str = str(content)
            if not content_str.startswith("Artifact received:"):
                kind = self._get_event_kind(ev)
                # Skip accumulating content for status updates and agent steps
                if kind in ("agent_step", "status_update"):
                    renderer.on_event(ev)
                    return final_text, stats_usage

                if self._is_token_event(ev):
                    renderer.on_event(ev)
                    final_text = f"{final_text}{content_str}"
                else:
                    if content_str != last_rendered_content:
                        renderer.on_event(ev)
                    final_text = content_str
        else:
            renderer.on_event(ev)
        return final_text, stats_usage

    def _get_event_kind(self, ev: dict[str, Any]) -> str | None:
        """Extract normalized event kind from parsed event.

        Args:
            ev: Parsed event dictionary.

        Returns:
            Event kind string or None.
        """
        metadata = ev.get("metadata") or {}
        kind = metadata.get("kind")
        if kind:
            return str(kind)
        event_type = ev.get("event_type")
        return str(event_type) if event_type else None

    def _is_token_event(self, ev: dict[str, Any]) -> bool:
        """Return True when the event represents token streaming output.

        Args:
            ev: Parsed event dictionary.

        Returns:
            True when the event is a token chunk, otherwise False.
        """
        metadata = ev.get("metadata") or {}
        kind = metadata.get("kind")
        return str(kind).lower() == "token"

    def _is_final_event(self, ev: dict[str, Any]) -> bool:
        """Return True when the event marks stream termination.

        Args:
            ev: Parsed event dictionary.

        Returns:
            True when the event is terminal, otherwise False.
        """
        if ev.get("is_final") is True or ev.get("final") is True:
            return True
        kind = self._get_event_kind(ev)
        return kind in _FINAL_EVENT_TYPES

    def _extract_content_string(self, event: dict[str, Any]) -> str | None:
        """Extract textual content from a parsed event.

        Args:
            event: Parsed event dictionary.

        Returns:
            Content string or None.
        """
        if not event:
            return None
        content = event.get("content")
        if content:
            return str(content)
        return None

    def _capture_request_id(
        self,
        stream_response: httpx.Response,
        meta: dict[str, Any],
        renderer: RichStreamRenderer,
    ) -> None:
        """Capture request ID from response headers and update metadata.

        Args:
            stream_response: HTTP response stream.
            meta: Metadata dictionary to update.
            renderer: Renderer instance.
        """
        req_id = stream_response.headers.get("x-request-id") or stream_response.headers.get("x-run-id")
        if req_id:
            meta["run_id"] = req_id
            renderer.on_start(meta)

    def _maybe_start_timer(self, event: dict[str, Any]) -> float | None:
        """Start timing if this is a content-bearing event.

        Args:
            event: Event dictionary.

        Returns:
            Monotonic time if timer should start, None otherwise.
        """
        try:
            ev = json.loads(event["data"])
        except json.JSONDecodeError:
            return None

        if "content" in ev or "status" in ev or ev.get("metadata"):
            return monotonic()
        return None

    def _process_single_event(
        self,
        event: dict[str, Any],
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        meta: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Process a single streaming event.

        Args:
            event: Event dictionary.
            renderer: Renderer instance.
            final_text: Accumulated text so far.
            stats_usage: Usage statistics dictionary.
            meta: Metadata dictionary.

        Returns:
            Tuple of (updated_final_text, updated_stats_usage).
        """
        try:
            ev = json.loads(event["data"])
        except json.JSONDecodeError:
            self._logger.debug("Non-JSON SSE fragment skipped")
            return final_text, stats_usage

        kind = (ev.get("metadata") or {}).get("kind")
        renderer.on_event(ev)

        handled = self._handle_metadata_kind(
            kind,
            ev,
            final_text,
            stats_usage,
            meta,
            renderer,
        )
        if handled is not None:
            return handled

        # Only accumulate content for actual content events, not status updates or agent steps
        # Status updates (agent_step) should be rendered but not accumulated in final_text
        if ev.get("content") and kind not in ("agent_step", "status_update"):
            final_text = self._handle_content_event(ev, final_text)

        return final_text, stats_usage

    def _handle_metadata_kind(
        self,
        kind: str | None,
        ev: dict[str, Any],
        final_text: str,
        stats_usage: dict[str, Any],
        meta: dict[str, Any],
        renderer: RichStreamRenderer,
    ) -> tuple[str, dict[str, Any]] | None:
        """Process well-known metadata kinds and return updated state."""
        if kind == "artifact":
            return final_text, stats_usage

        if kind == "final_response":
            content = ev.get("content")
            if content:
                return content, stats_usage
            return final_text, stats_usage

        if kind == "usage":
            stats_usage.update(ev.get("usage") or {})
            return final_text, stats_usage

        if kind == "run_info":
            self._handle_run_info_event(ev, meta, renderer)
            return final_text, stats_usage

        return None

    def _handle_content_event(self, ev: dict[str, Any], final_text: str) -> str:
        """Handle a content event and update final text.

        Args:
            ev: Event dictionary.
            final_text: Current accumulated text.

        Returns:
            Updated final text.
        """
        content = ev.get("content", "")
        if not content.startswith("Artifact received:"):
            if self._is_token_event(ev):
                return f"{final_text}{content}"
            return content
        return final_text

    def _handle_run_info_event(
        self,
        ev: dict[str, Any],
        meta: dict[str, Any],
        renderer: RichStreamRenderer,
    ) -> None:
        """Handle a run_info event and update metadata.

        Args:
            ev: Event dictionary.
            meta: Metadata dictionary to update.
            renderer: Renderer instance.
        """
        if ev.get("model"):
            meta["model"] = ev["model"]
            renderer.on_start(meta)
        if ev.get("run_id"):
            meta["run_id"] = ev["run_id"]
            renderer.on_start(meta)

    def _ensure_renderer_final_content(self, renderer: RichStreamRenderer, text: str) -> None:
        """Populate renderer state with final output when the stream omits it."""
        if not text:
            return

        text_value = _coerce_to_string(text)
        state = getattr(renderer, "state", None)
        if state is None:
            self._ensure_renderer_text(renderer, text_value)
            return

        self._ensure_state_final_text(state, text_value)
        self._ensure_state_buffer(state, text_value)

    def _ensure_renderer_text(self, renderer: RichStreamRenderer, text_value: str) -> None:
        """Best-effort assignment for renderer.final_text."""
        if not hasattr(renderer, "final_text"):
            return
        current_text = getattr(renderer, "final_text", "")
        if _has_visible_text(current_text):
            return
        self._safe_set_attr(renderer, "final_text", text_value)

    def _ensure_state_final_text(self, state: Any, text_value: str) -> None:
        """Best-effort assignment for renderer.state.final_text."""
        current_text = getattr(state, "final_text", "")
        if _has_visible_text(current_text):
            return
        self._safe_set_attr(state, "final_text", text_value)

    def _ensure_state_buffer(self, state: Any, text_value: str) -> None:
        """Append fallback text to the state buffer when available."""
        buffer = getattr(state, "buffer", None)
        if not hasattr(buffer, "append"):
            return
        self._safe_append(buffer.append, text_value)

    @staticmethod
    def _safe_set_attr(target: Any, attr: str, value: str) -> None:
        """Assign attribute while masking renderer-specific failures."""
        try:
            setattr(target, attr, value)
        except Exception:
            pass

    @staticmethod
    def _safe_append(appender: Callable[[str], Any], value: str) -> None:
        """Invoke append-like functions without leaking renderer errors."""
        try:
            appender(value)
        except Exception:
            pass

    # --------------------------------------------------------------------- #
    # Finalisation helpers
    # --------------------------------------------------------------------- #
    def finalize_renderer(
        self,
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        started_monotonic: float | None,
        finished_monotonic: float | None,
    ) -> str:
        """Complete rendering and return the textual result."""
        st = RunStats()
        st.started_at = started_monotonic or st.started_at
        st.finished_at = finished_monotonic or st.started_at
        st.usage = stats_usage

        rendered_text = ""
        buffer_values: Any | None = None

        if hasattr(renderer, "state") and hasattr(renderer.state, "buffer"):
            buffer_values = renderer.state.buffer
        elif hasattr(renderer, "buffer"):
            buffer_values = renderer.buffer

        if isinstance(buffer_values, TranscriptBuffer):
            rendered_text = buffer_values.render()
        elif buffer_values is not None:
            try:
                rendered_text = "".join(buffer_values)
            except TypeError:
                rendered_text = ""

        fallback_text = final_text or rendered_text
        if fallback_text:
            self._ensure_renderer_final_content(renderer, fallback_text)

        renderer.on_complete(st)
        return final_text or rendered_text or NO_AGENT_RESPONSE_FALLBACK


def compute_timeout_seconds(kwargs: dict[str, Any]) -> float:
    """Determine the execution timeout for agent runs.

    Args:
        kwargs: Dictionary containing execution parameters, including timeout.

    Returns:
        The timeout value in seconds, defaulting to DEFAULT_AGENT_RUN_TIMEOUT
        if not specified in kwargs.
    """
    return kwargs.get("timeout", DEFAULT_AGENT_RUN_TIMEOUT)


def finalize_render_manager(
    manager: AgentRunRenderingManager,
    renderer: RichStreamRenderer,
    final_text: str,
    stats_usage: dict[str, Any],
    started_monotonic: float | None,
    finished_monotonic: float | None,
) -> str:
    """Helper to finalize renderer via manager and return final text.

    Args:
        manager: The rendering manager instance.
        renderer: Renderer to finalize.
        final_text: Final text content.
        stats_usage: Usage statistics dictionary.
        started_monotonic: Start time (monotonic).
        finished_monotonic: Finish time (monotonic).

    Returns:
        Final text string.
    """
    return manager.finalize_renderer(
        renderer,
        final_text,
        stats_usage,
        started_monotonic,
        finished_monotonic,
    )
