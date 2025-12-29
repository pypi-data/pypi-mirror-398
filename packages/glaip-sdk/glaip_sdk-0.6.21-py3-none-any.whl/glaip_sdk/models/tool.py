"""Tool response model for AIP SDK.

This module contains the Pydantic model for Tool API responses.
This is a pure data model with no runtime behavior.

For the runtime Tool class with update/delete methods, use glaip_sdk.tools.Tool.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from pydantic import BaseModel


class ToolResponse(BaseModel):
    """Pydantic model for Tool API responses.

    This is a pure data model for deserializing API responses.
    It does NOT have runtime methods (update, delete, get_script).

    For the runtime Tool class, use glaip_sdk.tools.Tool.
    """

    id: str
    name: str
    tool_type: str | None = None
    description: str | None = None
    framework: str | None = None
    version: str | None = None
    tool_script: str | None = None
    tool_file: str | None = None
    tags: str | list[str] | None = None
