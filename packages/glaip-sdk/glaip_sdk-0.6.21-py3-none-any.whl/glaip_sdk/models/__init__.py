"""Models package for AIP SDK.

This package provides Pydantic models for API responses.

For the public runtime API with methods like run(), deploy(), update(), delete():
- glaip_sdk.agents.Agent
- glaip_sdk.tools.Tool
- glaip_sdk.mcps.MCP

The Agent, Tool, and MCP exports from this module are DEPRECATED.
They redirect to glaip_sdk.agents.Agent, glaip_sdk.tools.Tool, glaip_sdk.mcps.MCP
respectively with deprecation warnings.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import warnings

# Pure Pydantic models for API responses (no runtime methods)
from glaip_sdk.models.agent import AgentResponse
from glaip_sdk.models.agent_runs import (
    RunOutputChunk,
    RunsPage,
    RunSummary,
    RunWithOutput,
)
from glaip_sdk.models.common import LanguageModelResponse, TTYRenderer
from glaip_sdk.models.mcp import MCPResponse
from glaip_sdk.models.tool import ToolResponse


def __getattr__(name: str) -> type:
    """Deprecation warnings for backward compatibility."""
    if name == "Agent":
        warnings.warn(
            "Importing Agent from glaip_sdk.models is deprecated. "
            "Use 'from glaip_sdk.agents import Agent' instead. "
            "This will be removed in v1.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        from glaip_sdk.agents import Agent  # noqa: PLC0415

        return Agent

    if name == "Tool":
        warnings.warn(
            "Importing Tool from glaip_sdk.models is deprecated. "
            "Use 'from glaip_sdk.tools import Tool' instead. "
            "This will be removed in v1.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        from glaip_sdk.tools import Tool  # noqa: PLC0415

        return Tool

    if name == "MCP":
        warnings.warn(
            "Importing MCP from glaip_sdk.models is deprecated. "
            "Use 'from glaip_sdk.mcps import MCP' instead. "
            "This will be removed in v1.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        from glaip_sdk.mcps import MCP  # noqa: PLC0415

        return MCP

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Pure Pydantic response models (recommended for type hints)
    "AgentResponse",
    "ToolResponse",
    "MCPResponse",
    # Deprecated aliases (redirect to runtime classes with warning)
    "Agent",
    "Tool",
    "MCP",
    # Other models
    "LanguageModelResponse",
    "TTYRenderer",
    "RunSummary",
    "RunsPage",
    "RunWithOutput",
    "RunOutputChunk",
]
