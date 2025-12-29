"""Shared utilities for tool type detection.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any


def is_langchain_tool(ref: Any) -> bool:
    """Check if ref is a LangChain BaseTool class or instance.

    Shared by:
    - ToolRegistry._is_custom_tool() (for upload detection)
    - LangChainToolAdapter._is_langchain_tool() (for adaptation)

    Args:
        ref: Object to check.

    Returns:
        True if ref is a LangChain BaseTool class or instance.
    """
    try:
        from langchain_core.tools import BaseTool  # noqa: PLC0415

        if isinstance(ref, type) and issubclass(ref, BaseTool):
            return True
        if isinstance(ref, BaseTool):
            return True
    except ImportError:
        pass

    return False
