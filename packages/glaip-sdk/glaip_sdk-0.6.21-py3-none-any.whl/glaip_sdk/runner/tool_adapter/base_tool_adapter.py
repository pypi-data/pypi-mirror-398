"""Base tool adapter for local agent runtime.

This module defines the abstract base class for tool adapters.
Different backends (LangGraph, Google ADK) implement their own adapters.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseToolAdapter(ABC):
    """Abstract base class for tool adapters.

    One Interface, Multiple Implementations:
    - LangChainToolAdapter: Adapts to LangChain BaseTool (for aip-agents)
    - GoogleADKToolAdapter: Adapts to Google ADK format (future)

    Each backend implements this interface to adapt glaip-sdk tools
    to their specific tool format.
    """

    @abstractmethod
    def adapt_tools(self, tool_refs: list[Any]) -> list[Any]:
        """Adapt glaip-sdk tool references to backend-specific format.

        Args:
            tool_refs: List of tool references from Agent definition.
                Can be: LangChain classes/instances, Tool.from_langchain(),
                Tool.from_native(), string names, etc.

        Returns:
            List of tools in backend-specific format.
            For LangChain: list of BaseTool instances.
            For Google ADK: list of Google ADK tool objects.

        Raises:
            ValueError: If tool is not supported by this backend.
        """
        ...
