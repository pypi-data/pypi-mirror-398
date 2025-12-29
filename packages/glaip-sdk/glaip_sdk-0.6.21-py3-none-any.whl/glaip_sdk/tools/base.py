"""Tool class for lazy tool references.

This module provides the Tool class that serves as a lazy reference
to tools on the GL AIP platform. Tools are only resolved when
Agent.deploy() is called.

The Tool class also supports runtime operations (update, delete, get_script)
when retrieved from the API via client.tools.get().

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

Example - Lazy Reference:
    >>> from glaip_sdk.tools import Tool
    >>>
    >>> # Reference a native platform tool
    >>> time_tool = Tool.from_native("time_tool")
    >>>
    >>> # Reference a custom LangChain tool
    >>> greeting_tool = Tool.from_langchain(GreetingTool)
    >>>
    >>> # Use in an agent
    >>> class MyAgent(Agent):
    ...     @property
    ...     def tools(self) -> list:
    ...         return [time_tool, greeting_tool]

Example - Runtime Operations:
    >>> from glaip_sdk import Glaip
    >>>
    >>> client = Glaip()
    >>> tool = client.tools.get("tool-123")
    >>> script = tool.get_script()  # Get tool script content
    >>> tool.update(description="Updated description")
    >>> tool.delete()
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glaip_sdk.models import ToolResponse

_TOOL_NOT_DEPLOYED_MSG = "Tool not available on platform. No ID set."
_CLIENT_NOT_AVAILABLE_MSG = "Client not available. Use client.tools.get() to get a client-connected tool."


class ToolType(StrEnum):
    """Type of tool reference."""

    NATIVE = "native"
    CUSTOM = "custom"


class Tool:
    """Tool class for GL AIP platform.

    Supports both lazy references and runtime operations:
    - Lazy reference: Created via from_native() or from_langchain()
    - Runtime: Created via from_response() or client.tools.get()

    Use factory methods to create Tool instances:
        - Tool.from_native(name) - Reference a native platform tool
        - Tool.from_langchain(tool_class) - Reference a custom LangChain tool
        - Tool.from_response(response, client) - From API response

    Attributes:
        name: Tool name (for native tools) or from tool_class.
        id: Tool ID on the platform (set after deployment or from API).
        tool_class: LangChain BaseTool class (for custom tools) or None.
        tool_type: Type of tool (native or custom).
        description: Tool description (from API response).
        tool_script: Tool script content (from API response).

    Example - Lazy Reference:
        >>> # Native tool
        >>> time_tool = Tool.from_native("time_tool")
        >>>
        >>> # Custom tool
        >>> greeting_tool = Tool.from_langchain(GreetingTool)

    Example - Runtime Operations:
        >>> tool = client.tools.get("tool-123")
        >>> tool.update(description="New description")
        >>> tool.delete()
    """

    def __init__(
        self,
        name: str | None = None,
        tool_class: type | None = None,
        tool_type: str | ToolType | None = None,
        *,
        id: str | None = None,  # noqa: A002 - Allow shadowing builtin for API compat
        description: str | None = None,
        tool_script: str | None = None,
        tool_file: str | None = None,
        framework: str | None = None,
        version: str | None = None,
        tags: str | list[str] | None = None,
        type: (str | ToolType | None) = None,  # noqa: A002 - Backward compat alias for tool_type
        _client: Any = None,
    ) -> None:
        """Initialize a Tool.

        Args:
            name: Tool name (for native tools).
            tool_class: LangChain BaseTool class (for custom tools).
            tool_type: Type of tool (native or custom). Accepts str or ToolType.
            id: Tool ID on the platform.
            description: Tool description.
            tool_script: Tool script content.
            tool_file: Tool file path.
            framework: Tool framework.
            version: Tool version.
            tags: Tool tags.
            type: Backward compatibility alias for tool_type.
            _client: Internal client reference.
        """
        self.name = name
        self.tool_class = tool_class
        # Use type as alias for tool_type (backward compatibility)
        effective_type = tool_type if tool_type is not None else type
        if effective_type is None:
            effective_type = ToolType.NATIVE
        # Normalize type to ToolType enum
        if isinstance(effective_type, str):
            self._type = ToolType(effective_type) if effective_type in ToolType.__members__.values() else effective_type
        else:
            self._type = effective_type
        self._id = id
        self.description = description
        self.tool_script = tool_script
        self.tool_file = tool_file
        self.framework = framework
        self.version = version
        self.tags = tags
        self._client = _client

    @property
    def tool_type(self) -> str | ToolType:
        """Tool type (native or custom)."""
        return self._type

    @tool_type.setter
    def tool_type(self, value: str | ToolType) -> None:
        """Set the tool type."""
        if isinstance(value, str):
            self._type = ToolType(value) if value in ToolType.__members__.values() else value
        else:
            self._type = value

    @property
    def type(
        self,
    ) -> str | ToolType:  # noqa: A003 - Allow shadowing builtin for API compat
        """Tool type (native or custom). Alias for 'tool_type' for backward compatibility."""
        return self._type

    @type.setter
    def type(self, value: str | ToolType) -> None:  # noqa: A003
        """Set the tool type. Alias for 'tool_type' for backward compatibility."""
        self.tool_type = value

    @property
    def id(self) -> str | None:  # noqa: A003 - Allow shadowing builtin for API compat
        """Tool ID on the platform."""
        return self._id

    @id.setter
    def id(self, value: str | None) -> None:  # noqa: A003
        """Set the tool ID."""
        self._id = value

    def __repr__(self) -> str:
        """Return string representation."""
        if self._id:
            return f"Tool(id={self._id!r}, name={self.name!r})"
        if self.type == ToolType.NATIVE:
            return f"Tool.from_native({self.name!r})"
        if self.tool_class is not None:
            return f"Tool.from_langchain({self.tool_class.__name__})"
        return f"Tool(name={self.name!r}, type={self.type})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on id if available, else name and type."""
        if not isinstance(other, Tool):
            return NotImplemented
        if self._id and other._id:
            return self._id == other._id
        return self.name == other.name and self.type == other.type

    def __hash__(self) -> int:
        """Hash based on id if available, else name and type."""
        if self._id:
            return hash(self._id)
        return hash((self.name, self.type))

    def model_dump(self, *, exclude_none: bool = False) -> dict[str, Any]:
        """Return a dict representation of the Tool.

        Provides Pydantic-style serialization for backward compatibility.

        Args:
            exclude_none: If True, exclude None values from the output.

        Returns:
            Dictionary containing Tool attributes.
        """
        data = {
            "id": self._id,
            "name": self.name,
            "type": str(self.type) if self.type else None,
            "description": self.description,
            "tool_script": self.tool_script,
            "tool_file": self.tool_file,
            "framework": self.framework,
            "version": self.version,
            "tags": self.tags,
        }
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        return data

    @classmethod
    def from_native(cls, name: str) -> Tool:
        """Create a reference to a native platform tool.

        Native tools are pre-existing tools on the GL AIP platform
        that don't require uploading (e.g., "time_tool", "web_search").

        Args:
            name: The name of the native tool on the platform.

        Returns:
            A Tool reference that will be resolved during Agent.deploy().

        Example:
            >>> time_tool = Tool.from_native("time_tool")
            >>> web_search = Tool.from_native("web_search")
        """
        return cls(name=name, type=ToolType.NATIVE)

    @classmethod
    def from_langchain(cls, tool_class: type) -> Tool:
        """Create a reference to a custom LangChain tool.

        Custom tools are user-defined LangChain BaseTool subclasses
        that will be uploaded to the platform during deployment.

        Args:
            tool_class: A LangChain BaseTool subclass.

        Returns:
            A Tool reference that will be uploaded during Agent.deploy().

        Example:
            >>> from langchain_core.tools import BaseTool
            >>>
            >>> class GreetingTool(BaseTool):
            ...     name: str = "greeting_tool"
            ...     description: str = "Greets the user"
            ...     def _run(self, name: str) -> str:
            ...         return f"Hello, {name}!"
            >>>
            >>> greeting_tool = Tool.from_langchain(GreetingTool)
        """
        return cls(tool_class=tool_class, type=ToolType.CUSTOM)

    def get_import_path(self) -> str | None:
        """Get the import path for custom tools.

        Returns:
            Import path string for custom tools, None for native tools.
        """
        if self.tool_class is None:
            return None
        return f"{self.tool_class.__module__}.{self.tool_class.__name__}"

    def get_name(self) -> str:
        """Get the tool name.

        Returns:
            The tool name (from name attribute or tool_class).

        Raises:
            ValueError: If name cannot be determined.
        """
        if self.name is not None:
            return self.name

        if self.tool_class is not None:
            # LangChain BaseTool - get name from model_fields
            if hasattr(self.tool_class, "model_fields"):
                name_field = self.tool_class.model_fields.get("name")
                if name_field and name_field.default:
                    return name_field.default

            # Direct name attribute
            if hasattr(self.tool_class, "name"):
                return self.tool_class.name

        raise ValueError(f"Cannot determine name for tool: {self}")

    # ─────────────────────────────────────────────────────────────────
    # Runtime Methods (require client connection)
    # ─────────────────────────────────────────────────────────────────

    def _set_client(self, client: Any) -> Tool:
        """Set the client reference for this tool.

        Args:
            client: The Glaip client instance.

        Returns:
            Self for method chaining.
        """
        self._client = client
        return self

    def get_script(self) -> str:
        """Get the tool script content.

        Returns:
            The tool script content, or a placeholder message.
        """
        if self.tool_script:
            return self.tool_script
        elif self.tool_file:
            return f"Script content from file: {self.tool_file}"
        else:
            return "No script content available"

    def update(self, **kwargs: Any) -> Tool:
        """Update the tool with new configuration.

        Supports both metadata updates and file uploads.
        Pass 'file' parameter to update tool code via file upload.

        Args:
            **kwargs: Tool properties to update (name, description, etc.).

        Returns:
            Self with updated properties.

        Raises:
            ValueError: If the tool has no ID.
            RuntimeError: If client is not available.
        """
        if not self._id:
            raise ValueError(_TOOL_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        # Check if file upload is requested
        if "file" in kwargs:
            file_path = kwargs.pop("file")
            response = self._client.tools.update_via_file(self._id, file_path, **kwargs)
        else:
            response = self._client.tools.update(tool_id=self._id, **kwargs)

        # Update local properties from response
        if hasattr(response, "name") and response.name:
            self.name = response.name
        if hasattr(response, "description"):
            self.description = response.description
        if hasattr(response, "tool_script"):
            self.tool_script = response.tool_script

        return self

    def delete(self) -> None:
        """Delete the tool from the platform.

        Raises:
            ValueError: If the tool has no ID.
            RuntimeError: If client is not available.
        """
        if not self._id:
            raise ValueError(_TOOL_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        self._client.tools.delete(tool_id=self._id)
        self._id = None
        self._client = None

    @classmethod
    def from_response(
        cls,
        response: ToolResponse,
        client: Any = None,
    ) -> Tool:
        """Create a Tool instance from an API response.

        This allows you to work with tools retrieved from the API
        as full Tool instances with all methods available.

        Args:
            response: The ToolResponse from an API call.
            client: The Glaip client instance for API operations.

        Returns:
            A Tool instance initialized from the response.

        Example:
            >>> response = client.tools.get("tool-123")
            >>> tool = Tool.from_response(response, client)
            >>> script = tool.get_script()
        """
        # Use tool_type from backend; infer CUSTOM when code is present but tool_type is missing
        raw_type = getattr(response, "tool_type", None)
        if raw_type is None and (
            getattr(response, "tool_script", None) is not None or getattr(response, "tool_file", None) is not None
        ):
            raw_type = ToolType.CUSTOM

        tool = cls(
            name=response.name,
            id=response.id,
            tool_type=raw_type,
            description=getattr(response, "description", None),
            tool_script=getattr(response, "tool_script", None),
            tool_file=getattr(response, "tool_file", None),
            framework=getattr(response, "framework", None),
            version=getattr(response, "version", None),
            tags=getattr(response, "tags", None),
        )

        if client:
            tool._set_client(client)

        return tool
