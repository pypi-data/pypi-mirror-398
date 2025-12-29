"""MCP response model for AIP SDK.

This module contains the Pydantic model for MCP API responses.
This is a pure data model with no runtime behavior.

For the runtime MCP class with update/delete methods, use glaip_sdk.mcps.MCP.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any

from pydantic import BaseModel


class MCPResponse(BaseModel):
    """Pydantic model for MCP API responses.

    This is a pure data model for deserializing API responses.
    It does NOT have runtime methods (update, delete, get_tools).

    For the runtime MCP class, use glaip_sdk.mcps.MCP.
    """

    id: str
    name: str
    description: str | None = None
    config: dict[str, Any] | None = None
    transport: str | None = None  # "sse" or "http"
    authentication: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
