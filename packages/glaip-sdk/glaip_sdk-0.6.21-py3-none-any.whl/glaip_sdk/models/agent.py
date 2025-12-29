"""Agent response model for AIP SDK.

This module contains the Pydantic model for Agent API responses.
This is a pure data model with no runtime behavior.

For the runtime Agent class with deploy/run methods, use glaip_sdk.agents.Agent.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from datetime import datetime
from typing import Any

from glaip_sdk.config.constants import DEFAULT_AGENT_RUN_TIMEOUT
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Pydantic model for Agent API responses.

    This is a pure data model for deserializing API responses.
    It does NOT have runtime methods (run, update, delete).

    For the runtime Agent class, use glaip_sdk.agents.Agent.
    """

    id: str
    name: str
    instruction: str | None = None
    description: str | None = None
    type: str | None = None
    framework: str | None = None
    version: str | None = None
    tools: list[dict[str, Any]] | None = None
    agents: list[dict[str, Any]] | None = None
    mcps: list[dict[str, Any]] | None = None
    tool_configs: dict[str, Any] | None = None
    mcp_configs: dict[str, Any] | None = None
    agent_config: dict[str, Any] | None = None
    timeout: int = DEFAULT_AGENT_RUN_TIMEOUT
    metadata: dict[str, Any] | None = None
    language_model_id: str | None = None
    a2a_profile: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
