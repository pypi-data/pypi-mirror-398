"""Agent and tool discovery functions.

This module provides functions for finding agents and tools
from the GLAIP backend.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gllm_core.utils import LoggerManager

if TYPE_CHECKING:
    from glaip_sdk.agents import Agent
    from glaip_sdk.tools import Tool

logger = LoggerManager().get_logger(__name__)


def find_agent(name: str) -> Agent | None:
    """Find an agent by name using GLAIP SDK.

    Args:
        name: The name of the agent to find.

    Returns:
        The agent if found, None otherwise.

    Example:
        >>> from glaip_sdk.utils.discovery import find_agent
        >>> agent = find_agent("weather_reporter")
        >>> if agent:
        ...     print(f"Found agent: {agent.name}")
    """
    from glaip_sdk.utils.client import get_client  # noqa: PLC0415

    client = get_client()
    try:
        agents = client.list_agents()
        for agent in agents:
            if agent.name == name:
                return agent
        return None
    except Exception as e:
        logger.error("Error finding agent '%s': %s", name, e)
        return None


def find_tool(name: str) -> Tool | None:
    """Find a tool by name using GLAIP SDK.

    Args:
        name: The name of the tool to find.

    Returns:
        The tool if found, None otherwise.

    Example:
        >>> from glaip_sdk.utils.discovery import find_tool
        >>> tool = find_tool("weather_api")
        >>> if tool:
        ...     print(f"Found tool: {tool.name}")
    """
    from glaip_sdk.utils.client import get_client  # noqa: PLC0415

    client = get_client()
    try:
        tools = client.find_tools(name)
        for tool in tools:
            if tool.name == name:
                return tool
        return None
    except Exception as e:
        logger.error("Error finding tool '%s': %s", name, e)
        return None
