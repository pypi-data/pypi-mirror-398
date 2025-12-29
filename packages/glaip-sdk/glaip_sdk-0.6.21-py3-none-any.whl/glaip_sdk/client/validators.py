"""Validation utilities for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any
from uuid import UUID

from glaip_sdk.exceptions import AmbiguousResourceError, NotFoundError, ValidationError
from glaip_sdk.models import Tool


class ResourceValidator:
    """Validates and resolves resource references."""

    RESERVED_NAMES = {
        "research-agent",
        "github-agent",
        "aws-pricing-filter-generator-agent",
    }

    @classmethod
    def is_reserved_name(cls, name: str) -> bool:
        """Check if a name is reserved."""
        return name in cls.RESERVED_NAMES

    def _is_uuid_string(self, value: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            UUID(value)
            return True
        except ValueError:
            return False

    def _resolve_tool_by_name(self, tool_name: str, client: Any) -> str:
        """Resolve tool name to ID."""
        found_tools = client.find_tools(name=tool_name)
        if len(found_tools) == 1:
            return str(found_tools[0].id)
        elif len(found_tools) > 1:
            raise AmbiguousResourceError(f"Multiple tools found with name '{tool_name}': {[t.id for t in found_tools]}")
        else:
            raise NotFoundError(f"Tool not found: {tool_name}")

    def _resolve_tool_by_name_attribute(self, tool: Tool, client: Any) -> str:
        """Resolve tool by name attribute."""
        found_tools = client.find_tools(name=tool.name)
        if len(found_tools) == 1:
            return str(found_tools[0].id)
        elif len(found_tools) > 1:
            raise AmbiguousResourceError(f"Multiple tools found with name '{tool.name}': {[t.id for t in found_tools]}")
        else:
            raise NotFoundError(f"Tool not found: {tool.name}")

    def _process_tool_string(self, tool: str, client: Any) -> str:
        """Process a string tool reference."""
        if self._is_uuid_string(tool):
            return tool  # Already a UUID string
        else:
            return self._resolve_tool_by_name(tool, client)

    def _process_tool_object(self, tool: Tool, client: Any) -> str:
        """Process a Tool object reference."""
        if hasattr(tool, "id") and tool.id is not None:
            return str(tool.id)
        elif isinstance(tool, UUID):
            return str(tool)
        elif hasattr(tool, "name") and tool.name is not None:
            return self._resolve_tool_by_name_attribute(tool, client)
        else:
            raise ValidationError(f"Invalid tool reference: {tool} - must have 'id' or 'name' attribute")

    def _process_single_tool(self, tool: str | Tool, client: Any) -> str:
        """Process a single tool reference and return its ID."""
        if isinstance(tool, str):
            return self._process_tool_string(tool, client)
        else:
            return self._process_tool_object(tool, client)

    @classmethod
    def extract_tool_ids(cls, tools: list[str | Tool], client: Any) -> list[str]:
        """Extract tool IDs from a list of tool names, IDs, or Tool objects.

        For agent creation, the backend expects tool IDs (UUIDs).
        This method handles:
        - Tool objects (extracts their ID)
        - UUID strings (passes through)
        - Tool names (finds tool and extracts ID)
        """
        tool_ids = []
        for tool in tools:
            try:
                tool_id = cls()._process_single_tool(tool, client)
                tool_ids.append(tool_id)
            except (AmbiguousResourceError, NotFoundError) as err:
                # Determine the tool name for the error message
                tool_name = tool if isinstance(tool, str) else getattr(tool, "name", str(tool))
                raise ValidationError(f"Failed to resolve tool name '{tool_name}' to ID: {err}") from err
            except Exception as err:
                # For other exceptions, wrap them appropriately
                tool_name = tool if isinstance(tool, str) else getattr(tool, "name", str(tool))
                raise ValidationError(f"Failed to resolve tool name '{tool_name}' to ID: {err}") from err

        return tool_ids

    def _resolve_agent_by_name(self, agent_name: str, client: Any) -> str:
        """Resolve agent name to ID."""
        found_agents = client.find_agents(name=agent_name)
        if len(found_agents) == 1:
            return str(found_agents[0].id)
        elif len(found_agents) > 1:
            raise AmbiguousResourceError(
                f"Multiple agents found with name '{agent_name}': {[a.id for a in found_agents]}"
            )
        else:
            raise NotFoundError(f"Agent not found: {agent_name}")

    def _resolve_agent_by_name_attribute(self, agent: Any, client: Any) -> str:
        """Resolve agent by name attribute."""
        found_agents = client.find_agents(name=agent.name)
        if len(found_agents) == 1:
            return str(found_agents[0].id)
        elif len(found_agents) > 1:
            raise AmbiguousResourceError(
                f"Multiple agents found with name '{agent.name}': {[a.id for a in found_agents]}"
            )
        else:
            raise NotFoundError(f"Agent not found: {agent.name}")

    def _process_agent_string(self, agent: str, client: Any) -> str:
        """Process a string agent reference."""
        if self._is_uuid_string(agent):
            return agent  # Already a UUID string
        else:
            return self._resolve_agent_by_name(agent, client)

    def _process_agent_object(self, agent: Any, client: Any) -> str:
        """Process an Agent object reference."""
        if hasattr(agent, "id") and agent.id is not None:
            return str(agent.id)
        elif isinstance(agent, UUID):
            return str(agent)
        elif hasattr(agent, "name") and agent.name is not None:
            return self._resolve_agent_by_name_attribute(agent, client)
        else:
            raise ValidationError(f"Invalid agent reference: {agent} - must have 'id' or 'name' attribute")

    def _process_single_agent(self, agent: str | Any, client: Any) -> str:
        """Process a single agent reference and return its ID."""
        if isinstance(agent, str):
            return self._process_agent_string(agent, client)
        else:
            return self._process_agent_object(agent, client)

    @classmethod
    def extract_agent_ids(cls, agents: list[str | Any], client: Any) -> list[str]:
        """Extract agent IDs from a list of agent names, IDs, or agent objects.

        For agent creation, the backend expects agent IDs (UUIDs).
        This method handles:
        - Agent objects (extracts their ID)
        - UUID strings (passes through)
        - Agent names (finds agent and extracts ID)
        """
        agent_ids = []
        for agent in agents:
            try:
                agent_id = cls()._process_single_agent(agent, client)
                agent_ids.append(agent_id)
            except (AmbiguousResourceError, NotFoundError) as err:
                # Determine the agent name for the error message
                agent_name = agent if isinstance(agent, str) else getattr(agent, "name", str(agent))
                raise ValidationError(f"Failed to resolve agent name '{agent_name}' to ID: {err}") from err
            except Exception as err:
                # For other exceptions, wrap them appropriately
                agent_name = agent if isinstance(agent, str) else getattr(agent, "name", str(agent))
                raise ValidationError(f"Failed to resolve agent name '{agent_name}' to ID: {err}") from err

        return agent_ids

    @classmethod
    def validate_tools_exist(cls, tool_ids: list[str], client: Any) -> None:
        """Validate that all tool IDs exist."""
        for tool_id in tool_ids:
            try:
                client.get_tool_by_id(tool_id)
            except NotFoundError as err:
                raise ValidationError(f"Tool not found: {tool_id}") from err

    @classmethod
    def validate_agents_exist(cls, agent_ids: list[str], client: Any) -> None:
        """Validate that all agent IDs exist."""
        for agent_id in agent_ids:
            try:
                client.get_agent_by_id(agent_id)
            except NotFoundError as err:
                raise ValidationError(f"Agent not found: {agent_id}") from err
