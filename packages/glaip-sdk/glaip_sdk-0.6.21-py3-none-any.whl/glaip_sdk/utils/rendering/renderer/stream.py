"""Event routing and parsing utilities for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Callable
from time import monotonic
from typing import Any


class StreamProcessor:
    """Handles event routing and parsing for streaming agent execution."""

    def __init__(self) -> None:
        """Initialize the stream processor."""
        self.streaming_started_at: float | None = None
        self.server_elapsed_time: float | None = None
        self.current_event_tools: set[str] = set()
        self.current_event_sub_agents: set[str] = set()
        self.current_event_finished_panels: set[str] = set()
        self.last_event_time_by_ctx: dict[str, float] = {}

    def reset_event_tracking(self) -> None:
        """Reset tracking for the current event."""
        self.current_event_tools.clear()
        self.current_event_sub_agents.clear()
        self.current_event_finished_panels.clear()

    def extract_event_metadata(self, event: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from an event.

        Args:
            event: Event dictionary

        Returns:
            Dictionary with extracted metadata
        """
        metadata = event.get("metadata") or {}
        # Update server elapsed timing if backend provides it
        try:
            t = metadata.get("time")
            if isinstance(t, (int, float)):
                self.server_elapsed_time = float(t)
        except Exception:
            pass

        return {
            "kind": metadata.get("kind") if metadata else event.get("kind"),
            "task_id": metadata.get("task_id") or event.get("task_id"),
            "context_id": metadata.get("context_id") or event.get("context_id"),
            "content": event.get("content", ""),
            "status": metadata.get("status") if metadata else event.get("status"),
            "metadata": metadata,
        }

    def _extract_metadata_tool_calls(self, metadata: dict[str, Any]) -> tuple[str | None, dict, Any, list]:
        """Extract tool calls from metadata."""
        tool_calls = metadata.get("tool_calls", [])
        if not tool_calls:
            return None, {}, None, []

        # Take the first tool call if multiple exist
        first_call = tool_calls[0] if isinstance(tool_calls, list) else tool_calls
        tool_name = first_call.get("name")
        tool_args = first_call.get("arguments", {})
        tool_out = first_call.get("output")

        # Collect info for all tool calls
        tool_calls_info = []
        for call in tool_calls if isinstance(tool_calls, list) else [tool_calls]:
            if isinstance(call, dict) and "name" in call:
                tool_calls_info.append(
                    (
                        call.get("name", ""),
                        call.get("arguments", {}),
                        call.get("output"),
                    )
                )

        return tool_name, tool_args, tool_out, tool_calls_info

    def _extract_tool_info_calls(self, tool_info: dict[str, Any]) -> tuple[str | None, dict, Any, list]:
        """Extract tool calls from tool_info structure."""
        tool_calls_info = []
        tool_name = None
        tool_args = {}
        tool_out = None

        # Case 1: tool_info.tool_calls
        ti_calls = tool_info.get("tool_calls")
        if isinstance(ti_calls, list) and ti_calls:
            for call in ti_calls:
                if isinstance(call, dict) and call.get("name"):
                    tool_calls_info.append((call.get("name"), call.get("args", {}), call.get("output")))
            if tool_calls_info:
                tool_name, tool_args, tool_out = tool_calls_info[0]
            return tool_name, tool_args, tool_out, tool_calls_info

        # Case 2: single tool_info name/args/output
        if tool_info.get("name"):
            tool_name = tool_info.get("name")
            tool_args = tool_info.get("args", {})
            tool_out = tool_info.get("output")
            tool_calls_info.append((tool_name, tool_args, tool_out))

        return tool_name, tool_args, tool_out, tool_calls_info

    def _extract_tool_calls_from_metadata(self, metadata: dict[str, Any]) -> tuple[str | None, dict, Any, list]:
        """Extract tool calls from metadata structure."""
        tool_info = metadata.get("tool_info", {}) or {}

        if tool_info:
            return self._extract_tool_info_calls(tool_info)

        return None, {}, None, []

    def parse_tool_calls(self, event: dict[str, Any]) -> tuple[str | None, Any, Any, list[tuple[str, Any, Any]]]:
        """Parse tool call information from an event.

        Args:
            event: Event dictionary

        Returns:
            Tuple of (tool_name, tool_args, tool_output, tool_calls_info)
        """
        metadata = event.get("metadata", {})

        # Try primary extraction method
        tool_calls_result = self._extract_metadata_tool_calls(metadata)
        tool_name, tool_args, tool_out, tool_calls_info = tool_calls_result

        # Fallback to nested metadata.tool_info (newer schema)
        if not tool_calls_info:
            fallback_result = self._extract_tool_calls_from_metadata(metadata)
            tool_name, tool_args, tool_out, tool_calls_info = fallback_result

        return tool_name, tool_args, tool_out, tool_calls_info

    def update_timing(self, context_id: str | None) -> None:
        """Update timing information for the given context.

        Args:
            context_id: Context identifier
        """
        if context_id:
            self.last_event_time_by_ctx[context_id] = monotonic()

    def track_tools_and_agents(
        self,
        tool_name: str | None,
        tool_calls_info: list[tuple[str, Any, Any]],
        is_delegation_tool_func: Callable[[str], bool],
    ) -> None:
        """Track tools and sub-agents mentioned in the current event.

        Args:
            tool_name: Primary tool name
            tool_calls_info: List of tool call information
            is_delegation_tool_func: Function to check if tool is delegation
        """
        # Track all tools mentioned in this event
        if tool_name:
            self.current_event_tools.add(tool_name)
            # If it's a delegation tool, add the sub-agent name
            if is_delegation_tool_func(tool_name):
                sub_agent_name = self._extract_sub_agent_name(tool_name)
                self.current_event_sub_agents.add(sub_agent_name)

        if tool_calls_info:
            for tool_call_name, _, _ in tool_calls_info:
                self.current_event_tools.add(tool_call_name)
                # If it's a delegation tool, add the sub-agent name
                if is_delegation_tool_func(tool_call_name):
                    sub_agent_name = self._extract_sub_agent_name(tool_call_name)
                    self.current_event_sub_agents.add(sub_agent_name)

    def _extract_sub_agent_name(self, tool_name: str) -> str:
        """Extract sub-agent name from delegation tool name.

        Args:
            tool_name: Delegation tool name

        Returns:
            Sub-agent name
        """
        if tool_name.startswith("delegate_to_"):
            return tool_name.replace("delegate_to_", "")
        elif tool_name.startswith("delegate_"):
            return tool_name.replace("delegate_", "")
        else:
            return tool_name

    def get_current_event_tools(self) -> set[str]:
        """Get the set of tools mentioned in the current event."""
        return self.current_event_tools.copy()

    def get_current_event_sub_agents(self) -> set[str]:
        """Get the set of sub-agents mentioned in the current event."""
        return self.current_event_sub_agents.copy()
