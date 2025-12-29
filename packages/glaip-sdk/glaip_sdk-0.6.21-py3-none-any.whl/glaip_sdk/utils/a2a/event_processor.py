"""A2A event stream processing utilities.

This module provides helpers for processing the A2AEvent stream emitted by
agent execution backends (e.g., `arun_a2a_stream()`).

The MVP implementation focuses on extracting final response text;
full A2AConnector-equivalent normalization is deferred to follow-up PRs.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)

# A2A event type constants (matching aip_agents.schema.a2a.A2AStreamEventType)
EVENT_TYPE_FINAL_RESPONSE = "final_response"
EVENT_TYPE_STATUS_UPDATE = "status_update"
EVENT_TYPE_TOOL_CALL = "tool_call"
EVENT_TYPE_TOOL_RESULT = "tool_result"
EVENT_TYPE_ERROR = "error"


@dataclass(frozen=True, slots=True)
class A2AEventStreamProcessor:
    """Processor for `arun_a2a_stream()` event dictionaries.

    The SDK uses lightweight dictionaries to represent A2A stream events.
    This helper centralizes event-type normalization and MVP final-text extraction.

    Example:
        >>> processor = A2AEventStreamProcessor()
        >>> events = [{"event_type": "final_response", "content": "Hello!", "is_final": True}]
        >>> result = processor.extract_final_response(events)
        >>> print(result)
        Hello!
    """

    def extract_final_response(self, events: list[dict[str, Any]]) -> str:
        """Extract the final response text from a list of A2AEvents.

        Scans the event list for the final_response event and returns its content.
        If no final_response is found, raises a RuntimeError.

        Args:
            events: List of A2AEvent dictionaries from arun_a2a_stream().

        Returns:
            The content string from the final_response event.

        Raises:
            RuntimeError: If no final_response event is found in the stream.
        """
        for event in reversed(events):
            if self._is_final_response_event(event):
                content = event.get("content", "")
                logger.debug("Extracted final response: %d characters", len(str(content)))
                return str(content)

        # Fallback: check for events with is_final=True
        for event in reversed(events):
            if event.get("is_final", False):
                content = event.get("content", "")
                if content:
                    logger.debug("Extracted final from is_final flag: %d chars", len(str(content)))
                    return str(content)

        raise RuntimeError(
            "No final response received from the agent. The agent execution completed without producing a final answer."
        )

    def get_event_type(self, event: dict[str, Any]) -> str:
        """Get the normalized event type string from an A2AEvent.

        Args:
            event: An A2AEvent dictionary.

        Returns:
            The event type as a lowercase string.
        """
        event_type = event.get("event_type", "unknown")
        if isinstance(event_type, str):
            return event_type.lower()
        # Handle enum types (A2AStreamEventType)
        return getattr(event_type, "value", str(event_type)).lower()

    def is_tool_event(self, event: dict[str, Any]) -> bool:
        """Check if an event is a tool-related event.

        Args:
            event: An A2AEvent dictionary.

        Returns:
            True if this is a tool_call or tool_result event.
        """
        event_type = self.get_event_type(event)
        return event_type in (EVENT_TYPE_TOOL_CALL, EVENT_TYPE_TOOL_RESULT)

    def is_error_event(self, event: dict[str, Any]) -> bool:
        """Check if an event is an error event.

        Args:
            event: An A2AEvent dictionary.

        Returns:
            True if this is an error event.
        """
        return self.get_event_type(event) == EVENT_TYPE_ERROR

    def _is_final_response_event(self, event: dict[str, Any]) -> bool:
        """Check if an event is a final_response event.

        Args:
            event: An A2AEvent dictionary.

        Returns:
            True if this is a final_response event, False otherwise.
        """
        return self.get_event_type(event) == EVENT_TYPE_FINAL_RESPONSE


# Default processor instance for convenience functions
_DEFAULT_PROCESSOR = A2AEventStreamProcessor()


def extract_final_response(events: list[dict[str, Any]]) -> str:
    """Extract the final response text from a list of A2AEvents.

    Convenience function that uses the default A2AEventStreamProcessor.

    Args:
        events: List of A2AEvent dictionaries from arun_a2a_stream().

    Returns:
        The content string from the final_response event.

    Raises:
        RuntimeError: If no final_response event is found in the stream.
    """
    return _DEFAULT_PROCESSOR.extract_final_response(events)


def get_event_type(event: dict[str, Any]) -> str:
    """Get the normalized event type string from an A2AEvent.

    Convenience function that uses the default A2AEventStreamProcessor.

    Args:
        event: An A2AEvent dictionary.

    Returns:
        The event type as a lowercase string.
    """
    return _DEFAULT_PROCESSOR.get_event_type(event)


def is_tool_event(event: dict[str, Any]) -> bool:
    """Check if an event is a tool-related event.

    Convenience function that uses the default A2AEventStreamProcessor.

    Args:
        event: An A2AEvent dictionary.

    Returns:
        True if this is a tool_call or tool_result event.
    """
    return _DEFAULT_PROCESSOR.is_tool_event(event)


def is_error_event(event: dict[str, Any]) -> bool:
    """Check if an event is an error event.

    Convenience function that uses the default A2AEventStreamProcessor.

    Args:
        event: An A2AEvent dictionary.

    Returns:
        True if this is an error event.
    """
    return _DEFAULT_PROCESSOR.is_error_event(event)
