#!/usr/bin/env python3
"""Main client for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glaip_sdk.client.agents import AgentClient
from glaip_sdk.client.base import BaseClient
from glaip_sdk.client.mcps import MCPClient
from glaip_sdk.client.shared import build_shared_config
from glaip_sdk.client.tools import ToolClient

if TYPE_CHECKING:  # pragma: no cover
    from glaip_sdk.agents import Agent
    from glaip_sdk.client._agent_payloads import AgentListResult
    from glaip_sdk.mcps import MCP
    from glaip_sdk.tools import Tool


class Client(BaseClient):
    """Main client that composes all specialized clients and shares one HTTP session."""

    def __init__(self, **kwargs):
        """Initialize the main client.

        Args:
            **kwargs: Client configuration arguments (api_url, api_key, timeout, etc.)
        """
        super().__init__(**kwargs)
        # Share the single httpx.Client + config with sub-clients
        shared_config = build_shared_config(self)
        self.agents = AgentClient(**shared_config)
        self.tools = ToolClient(**shared_config)
        self.mcps = MCPClient(**shared_config)

    # ---- Core API Methods (Public Interface) ----

    # Agents
    def create_agent(self, **kwargs) -> Agent:
        """Create a new agent."""
        return self.agents.create_agent(**kwargs)

    def create_agent_from_file(self, *args, **kwargs) -> Agent:
        """Create a new agent from a JSON or YAML configuration file."""
        return self.agents.create_agent_from_file(*args, **kwargs)

    def list_agents(
        self,
        agent_type: str | None = None,
        framework: str | None = None,
        name: str | None = None,
        version: str | None = None,
        sync_langflow_agents: bool = False,
    ) -> AgentListResult:
        """List agents with optional filtering.

        Args:
            agent_type: Filter by agent type (config, code, a2a)
            framework: Filter by framework (langchain, langgraph, google_adk)
            name: Filter by partial name match (case-insensitive)
            version: Filter by exact version match
            sync_langflow_agents: Sync with LangFlow server before listing (only applies when agent_type=langflow)

        Returns:
            AgentListResult with agents and pagination metadata. Supports iteration and indexing.
        """
        return self.agents.list_agents(
            agent_type=agent_type,
            framework=framework,
            name=name,
            version=version,
            sync_langflow_agents=sync_langflow_agents,
        )

    def get_agent_by_id(self, agent_id: str) -> Agent | None:
        """Get agent by ID."""
        return self.agents.get_agent_by_id(agent_id)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent by ID (alias for get_agent_by_id)."""
        return self.get_agent_by_id(agent_id)

    def find_agents(self, name: str | None = None) -> list[Agent]:
        """Find agents by name."""
        return self.agents.find_agents(name)

    def update_agent(self, agent_id: str, **kwargs) -> Agent:
        """Update an existing agent."""
        return self.agents.update_agent(agent_id, **kwargs)

    def update_agent_from_file(self, agent_id: str, *args, **kwargs) -> Agent:
        """Update an existing agent using a JSON or YAML configuration file."""
        return self.agents.update_agent_from_file(agent_id, *args, **kwargs)

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        return self.agents.delete_agent(agent_id)

    def run_agent(self, agent_id: str, message: str, **kwargs) -> str:
        """Run an agent with a message."""
        return self.agents.run_agent(agent_id, message, **kwargs)

    def sync_langflow_agents(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Sync LangFlow agents by fetching flows from the LangFlow server.

        This method synchronizes agents with LangFlow flows. It fetches all flows
        from the configured LangFlow server and creates/updates corresponding agents.

        Args:
            base_url: Custom LangFlow server base URL. If not provided, uses LANGFLOW_BASE_URL env var.
            api_key: Custom LangFlow API key. If not provided, uses LANGFLOW_API_KEY env var.

        Returns:
            Response containing sync results and statistics
        """
        return self.agents.sync_langflow_agents(base_url=base_url, api_key=api_key)

    # Tools
    def create_tool(self, **kwargs) -> Tool:
        """Create a new tool."""
        return self.tools.create_tool(**kwargs)

    def create_tool_from_code(self, **kwargs) -> Tool:
        """Create a new tool from code."""
        return self.tools.create_tool_from_code(**kwargs)

    def list_tools(self, tool_type: str | None = None) -> list[Tool]:
        """List tools with optional type filtering."""
        return self.tools.list_tools(tool_type=tool_type)

    def get_tool_by_id(self, tool_id: str) -> Tool | None:
        """Get tool by ID."""
        return self.tools.get_tool_by_id(tool_id)

    def get_tool(self, tool_id: str) -> Tool | None:
        """Backward-compatible alias for get_tool_by_id."""
        return self.get_tool_by_id(tool_id)

    def find_tools(self, name: str) -> list[Tool]:
        """Find tools by name."""
        return self.tools.find_tools(name)

    def update_tool(self, tool_id: str, **kwargs) -> Tool:
        """Update an existing tool."""
        return self.tools.update_tool(tool_id, **kwargs)

    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool."""
        return self.tools.delete_tool(tool_id)

    def get_tool_script(self, tool_id: str) -> str:
        """Get tool script content."""
        return self.tools.get_tool_script(tool_id)

    def update_tool_via_file(self, tool_id: str, file_path: str, **kwargs) -> Tool:
        """Update tool via file."""
        return self.tools.update_tool_via_file(tool_id, file_path, **kwargs)

    # MCPs
    def create_mcp(self, **kwargs) -> MCP:
        """Create a new MCP."""
        return self.mcps.create_mcp(**kwargs)

    def list_mcps(self) -> list[MCP]:
        """List all MCPs."""
        return self.mcps.list_mcps()

    def get_mcp_by_id(self, mcp_id: str) -> MCP | None:
        """Get MCP by ID."""
        return self.mcps.get_mcp_by_id(mcp_id)

    def get_mcp(self, mcp_id: str) -> MCP | None:
        """Backward-compatible alias for get_mcp_by_id."""
        return self.get_mcp_by_id(mcp_id)

    def find_mcps(self, name: str) -> list[MCP]:
        """Find MCPs by name."""
        return self.mcps.find_mcps(name)

    def update_mcp(self, mcp_id: str, **kwargs) -> MCP:
        """Update an existing MCP."""
        return self.mcps.update_mcp(mcp_id, **kwargs)

    def delete_mcp(self, mcp_id: str) -> bool:
        """Delete an MCP."""
        return self.mcps.delete_mcp(mcp_id)

    def test_mcp_connection(self, config: dict) -> dict:
        """Test MCP connection."""
        return self.mcps.test_mcp_connection(config)

    def test_mcp_connection_from_config(self, config: dict) -> dict:
        """Test MCP connection from config."""
        return self.mcps.test_mcp_connection_from_config(config)

    def get_mcp_tools_from_config(self, config: dict) -> list[dict]:
        """Get MCP tools from config."""
        return self.mcps.get_mcp_tools_from_config(config)

    # Language Models
    def list_language_models(self) -> list[dict]:
        """List available language models."""
        data = self._request("GET", "/language-models")
        return data or []

    # ---- Timeout propagation ----
    @property
    def timeout(self) -> float:  # type: ignore[override]
        """Get the client timeout value."""
        return super().timeout

    @timeout.setter
    def timeout(self, value: float) -> None:  # type: ignore[override]
        """Set the client timeout and propagate to sub-clients.

        Args:
            value: Timeout value in seconds.
        """
        # Rebuild the root http client
        BaseClient.timeout.fset(self, value)  # call parent setter
        # Propagate the new session to sub-clients so they don't hold a closed client
        try:
            if hasattr(self, "agents"):
                self.agents.http_client = self.http_client
            if hasattr(self, "tools"):
                self.tools.http_client = self.http_client
            if hasattr(self, "mcps"):
                self.mcps.http_client = self.http_client
        except Exception:
            pass

    # ---- Health Check ----
    def ping(self) -> bool:
        """Check if the API is reachable."""
        try:
            self._request("GET", "/health-check")
            return True
        except Exception:
            return False
