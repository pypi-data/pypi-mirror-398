"""A2A (Agent-to-Agent) event processing utilities.

This module provides utilities for processing A2A stream events emitted by
agent execution backends. Used by the runner module and CLI rendering.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from glaip_sdk.utils.a2a.event_processor import (
    EVENT_TYPE_ERROR,
    EVENT_TYPE_FINAL_RESPONSE,
    EVENT_TYPE_STATUS_UPDATE,
    EVENT_TYPE_TOOL_CALL,
    EVENT_TYPE_TOOL_RESULT,
    A2AEventStreamProcessor,
    extract_final_response,
    get_event_type,
    is_error_event,
    is_tool_event,
)

__all__ = [
    "A2AEventStreamProcessor",
    "EVENT_TYPE_ERROR",
    "EVENT_TYPE_FINAL_RESPONSE",
    "EVENT_TYPE_STATUS_UPDATE",
    "EVENT_TYPE_TOOL_CALL",
    "EVENT_TYPE_TOOL_RESULT",
    "extract_final_response",
    "get_event_type",
    "is_error_event",
    "is_tool_event",
]
