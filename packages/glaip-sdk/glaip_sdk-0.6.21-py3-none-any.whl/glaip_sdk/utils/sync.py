"""Agent and tool synchronization (create/update) operations.

This module provides convenience functions for tool classes that need bundling.

For direct upsert operations, use the client methods:
    - client.agents.upsert_agent(identifier, **kwargs)
    - client.tools.upsert_tool(identifier, code, **kwargs)
    - client.mcps.upsert_mcp(identifier, **kwargs)

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glaip_sdk.utils.bundler import ToolBundler
from glaip_sdk.utils.import_resolver import load_class
from gllm_core.utils import LoggerManager

if TYPE_CHECKING:
    from glaip_sdk.models import Agent, Tool

logger = LoggerManager().get_logger(__name__)


def _extract_tool_name(tool_class: Any) -> str:
    """Extract tool name from a class, handling Pydantic v2 models."""
    # Direct attribute access (works for non-Pydantic classes)
    if hasattr(tool_class, "name"):
        name = getattr(tool_class, "name", None)
        if isinstance(name, str):
            return name

    # Pydantic v2 model - check model_fields
    if hasattr(tool_class, "model_fields"):
        model_fields = getattr(tool_class, "model_fields", {})
        if "name" in model_fields:
            field_info = model_fields["name"]
            if hasattr(field_info, "default") and isinstance(field_info.default, str):
                return field_info.default

    raise ValueError(f"Cannot extract name from tool class: {tool_class}")


def _extract_tool_description(tool_class: Any) -> str:
    """Extract tool description from a class, handling Pydantic v2 models."""
    # Direct attribute access
    if hasattr(tool_class, "description"):
        desc = getattr(tool_class, "description", None)
        if isinstance(desc, str):
            return desc

    # Pydantic v2 model - check model_fields
    if hasattr(tool_class, "model_fields"):
        model_fields = getattr(tool_class, "model_fields", {})
        if "description" in model_fields:
            field_info = model_fields["description"]
            if hasattr(field_info, "default") and isinstance(field_info.default, str):
                return field_info.default

    return ""


def update_or_create_tool(tool_ref: Any) -> Tool:
    """Create or update a tool from a tool class with bundled source code.

    This function takes a tool class (LangChain BaseTool), bundles its source
    code with inlined imports, and creates/updates it in the backend.

    Args:
        tool_ref: A tool class (LangChain BaseTool subclass) or import path string.

    Returns:
        The created or updated tool.

    Example:
        >>> from glaip_sdk.utils.sync import update_or_create_tool
        >>> from my_tools import WeatherAPITool
        >>> tool = update_or_create_tool(WeatherAPITool)
    """
    from glaip_sdk.utils.client import get_client  # noqa: PLC0415

    client = get_client()

    # Handle string import path
    if isinstance(tool_ref, str):
        tool_class = load_class(tool_ref)
    else:
        tool_class = tool_ref

    # Get tool info - handle Pydantic v2 model classes
    tool_name = _extract_tool_name(tool_class)
    tool_description = _extract_tool_description(tool_class)

    # Bundle source code
    bundler = ToolBundler(tool_class)
    bundled_source = bundler.bundle()

    logger.info("Tool info: name='%s', description='%s...'", tool_name, tool_description[:50])
    logger.info("Bundled source code: %d characters", len(bundled_source))

    # Use client's upsert method
    return client.tools.upsert_tool(
        tool_name,
        code=bundled_source,
        description=tool_description,
    )


def update_or_create_agent(agent_config: dict[str, Any]) -> Agent:
    """Create or update an agent from configuration.

    Args:
        agent_config: Agent configuration dictionary containing:
            - name (str): Agent name (required)
            - description (str): Agent description
            - instruction (str): Agent instruction
            - tools (list, optional): List of tool IDs
            - agents (list, optional): List of sub-agent IDs
            - metadata (dict, optional): Additional metadata

    Returns:
        The created or updated agent.

    Example:
        >>> from glaip_sdk.utils.sync import update_or_create_agent
        >>> config = {
        ...     "name": "weather_reporter",
        ...     "description": "Weather reporting agent",
        ...     "instruction": "You are a weather reporter.",
        ... }
        >>> agent = update_or_create_agent(config)
    """
    from glaip_sdk.utils.client import get_client  # noqa: PLC0415

    client = get_client()
    agent_name = agent_config.pop("name")

    # Use client's upsert method
    return client.agents.upsert_agent(agent_name, **agent_config)
