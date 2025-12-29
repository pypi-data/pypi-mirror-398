"""Tool package for GL AIP platform.

This package provides the Tool class, ToolType enum, and ToolRegistry
for managing tools on the GL AIP platform.

Example:
    >>> from glaip_sdk.tools import Tool, ToolType, get_tool_registry
    >>> native_tool = Tool.from_native("web_search")
    >>> custom_tool = Tool.from_langchain(MyCustomTool)
"""

from __future__ import annotations

from glaip_sdk.registry.tool import ToolRegistry, get_tool_registry
from glaip_sdk.tools.base import Tool, ToolType

__all__ = [
    "Tool",
    "ToolType",
    "ToolRegistry",
    "get_tool_registry",
]
