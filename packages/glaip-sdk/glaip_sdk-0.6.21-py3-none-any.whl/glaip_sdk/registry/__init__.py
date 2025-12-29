"""Registry package for GL AIP platform.

This package provides registries that cache platform objects to avoid
redundant API calls when deploying multi-agent systems.

Example:
    >>> from glaip_sdk.registry import get_agent_registry, get_tool_registry
    >>> agent_registry = get_agent_registry()
    >>> tool_registry = get_tool_registry()
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from glaip_sdk.registry.base import BaseRegistry

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:  # pragma: no cover
    from glaip_sdk.registry.agent import AgentRegistry, get_agent_registry
    from glaip_sdk.registry.mcp import MCPRegistry, get_mcp_registry
    from glaip_sdk.registry.tool import ToolRegistry, get_tool_registry

__all__ = [
    "BaseRegistry",
    "AgentRegistry",
    "get_agent_registry",
    "ToolRegistry",
    "get_tool_registry",
    "MCPRegistry",
    "get_mcp_registry",
]


def __getattr__(name: str) -> type:
    """Lazy import to avoid circular dependencies."""
    _agent_module = "glaip_sdk.registry.agent"
    _tool_module = "glaip_sdk.registry.tool"
    _mcp_module = "glaip_sdk.registry.mcp"

    lazy_imports = {
        "AgentRegistry": _agent_module,
        "get_agent_registry": _agent_module,
        "ToolRegistry": _tool_module,
        "get_tool_registry": _tool_module,
        "MCPRegistry": _mcp_module,
        "get_mcp_registry": _mcp_module,
    }

    if name in lazy_imports:
        module = importlib.import_module(lazy_imports[name])
        return getattr(module, name)

    raise AttributeError(f"module 'glaip_sdk.registry' has no attribute '{name}'")
