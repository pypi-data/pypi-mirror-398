"""MCP (Model Context Protocol) package for GL AIP platform.

This package provides the MCP class and MCPRegistry for managing
Model Context Protocol configurations on the GL AIP platform.

Example:
    >>> from glaip_sdk.mcps import MCP, get_mcp_registry
    >>> mcp = MCP.from_native("arxiv-search")
"""

from __future__ import annotations

from glaip_sdk.mcps.base import MCP, MCPConfigValue
from glaip_sdk.registry.mcp import MCPRegistry, get_mcp_registry

__all__ = [
    "MCP",
    "MCPConfigValue",
    "MCPRegistry",
    "get_mcp_registry",
]
