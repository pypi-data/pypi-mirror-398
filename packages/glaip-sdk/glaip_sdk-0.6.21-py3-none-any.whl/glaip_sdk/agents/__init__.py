"""Agent package for GL AIP platform.

This package provides the Agent class and AgentRegistry for deploying
and managing AI agents on the GL AIP platform.

Example:
    >>> from glaip_sdk.agents import Agent, get_agent_registry
    >>> agent = Agent(name="my_agent", instruction="Be helpful")
    >>> deployed = agent.deploy()
"""

from __future__ import annotations

from glaip_sdk.agents.base import Agent
from glaip_sdk.registry.agent import AgentRegistry, get_agent_registry
from glaip_sdk.registry.mcp import MCPRegistry, get_mcp_registry
from glaip_sdk.registry.tool import ToolRegistry, get_tool_registry

__all__ = [
    "Agent",
    "AgentRegistry",
    "get_agent_registry",
    "MCPRegistry",
    "get_mcp_registry",
    "ToolRegistry",
    "get_tool_registry",
]
