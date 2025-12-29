"""Base MCP adapter for local agent runtime.

This module defines the abstract base class for MCP adapters.
Different backends (LangGraph, Google ADK) implement their own adapters.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMCPAdapter(ABC):
    """Abstract base class for MCP adapters.

    One Interface, Multiple Implementations:
    - LangChainMCPAdapter: Adapts to aip-agents mcp_config format
    - GoogleADKMCPAdapter: Adapts to Google ADK format (future)

    Each backend implements this interface to adapt glaip-sdk MCPs
    to their specific MCP configuration format.
    """

    @abstractmethod
    def adapt_mcps(self, mcp_refs: list[Any]) -> dict[str, Any]:
        """Adapt glaip-sdk MCP references to backend-specific format.

        Args:
            mcp_refs: List of MCP references from Agent definition.
                Can be: MCP class instances, MCP.from_native() refs, etc.

        Returns:
            Backend-specific MCP configuration.
            For LangChain/aip-agents: dict[str, dict[str, Any]] mapping server names to config.
            For Google ADK: dict in Google ADK MCP format.

        Raises:
            ValueError: If MCP is not supported by this backend.
        """
        ...
