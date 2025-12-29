"""Dependency detection utilities for the runner module.

This module provides helpers to detect whether the local runtime dependencies
(aip-agents) are installed and to generate actionable error messages when they
are not available.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

Example:
    >>> from glaip_sdk.runner.deps import check_local_runtime_available
    >>> if not check_local_runtime_available():
    ...     print(get_local_runtime_missing_message())
"""

from __future__ import annotations

import importlib.util

from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)

# Module-level cache for import availability check
_local_runtime_available: bool | None = None


def _probe_aip_agents_import() -> bool:
    """Check if aip_agents is available without importing it.

    Returns:
        True if aip_agents appears importable, False otherwise.
    """
    return importlib.util.find_spec("aip_agents") is not None


def check_local_runtime_available() -> bool:
    """Check if the local runtime dependencies are installed and importable.

    This function probes for the aip_agents module which provides the
    LangGraphReactAgent for local execution. Results are cached for efficiency.

    Returns:
        True if local runtime is available, False otherwise.
    """
    global _local_runtime_available

    if _local_runtime_available is None:
        _local_runtime_available = _probe_aip_agents_import()
        if _local_runtime_available:
            logger.debug("Local runtime dependencies (aip-agents) detected")
        else:
            logger.debug("Local runtime dependencies (aip-agents) not available")

    return _local_runtime_available


# Cached availability flag for use in conditions without function call overhead
LOCAL_RUNTIME_AVAILABLE: bool = check_local_runtime_available()


def get_local_runtime_missing_message() -> str:
    """Generate an actionable error message when local runtime is not available.

    Returns:
        A user-friendly message explaining how to install local runtime dependencies
        or how to use server-backed execution as an alternative.
    """
    return (
        "Local runtime dependencies are not installed. "
        "To run agents locally without an AIP server, install with:\n\n"
        '    pip install "glaip-sdk[local]"\n\n'
        "Alternatively, call deploy() to run this agent on the AIP server."
    )


def get_local_mode_not_supported_for_tool_message(tool_ref: str) -> str:
    """Generate an error message for tools that cannot be used in local mode.

    Args:
        tool_ref: A string identifier for the tool (name, ID, or type description).

    Returns:
        Error message explaining that the tool type is not supported locally.
    """
    return (
        f"Tool '{tool_ref}' cannot be used in local mode. "
        "Local runtime only supports LangChain-compatible tool classes/instances "
        "and Tool.from_langchain(...) references. "
        "Native platform tools (Tool.from_native()) require server-backed execution "
        "via deploy()."
    )


def get_uuid_not_supported_message(key_type: str, uuid_value: str) -> str:
    """Generate an error message when a UUID is used in local mode.

    In local mode, runtime_config keys must be tool/agent/MCP objects or names,
    not UUIDs which require platform registry resolution.

    Args:
        key_type: The type of key (e.g., "tool", "agent", "mcp").
        uuid_value: The UUID that was incorrectly provided.

    Returns:
        Error message explaining that UUIDs are not supported in local mode.
    """
    return (
        f"UUID-like {key_type} key '{uuid_value}' is not supported in local mode. "
        f"Local runtime cannot resolve {key_type} IDs - pass the {key_type} "
        f"class/instance or name instead."
    )
