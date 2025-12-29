"""MCP (Model Context Protocol) helper for glaip_sdk.

Provides a simple, migration-ready way to declare and resolve MCPs with
in-memory caching and create-on-missing functionality.

The MCP class also supports runtime operations (update, delete, get_tools)
when retrieved from the API via client.mcps.get().

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

Example - Lazy Reference:
    >>> from glaip_sdk.mcps import MCP
    >>>
    >>> # Create from known ID
    >>> mcp = MCP.from_id("mcp_abc123")
    >>>
    >>> # Create lookup-only by name (error if not found)
    >>> mcp = MCP.from_native("arxiv-search")
    >>>
    >>> # Create for lookup/creation by name (create if missing)
    >>> mcp = MCP(name="my-filesystem-mcp", transport="sse", config={"url": "..."})

Example - Runtime Operations:
    >>> from glaip_sdk import Glaip
    >>>
    >>> client = Glaip()
    >>> mcp = client.mcps.get("mcp-123")
    >>> tools = mcp.get_tools()  # Get tools from MCP
    >>> mcp.update(description="Updated description")
    >>> mcp.delete()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glaip_sdk.models import MCPResponse

# Type alias for MCP configuration values
MCPConfigValue = str | int | bool | list[str] | dict[str, str]

_MCP_NOT_DEPLOYED_MSG = "MCP not available on platform. No ID set."
_CLIENT_NOT_AVAILABLE_MSG = "Client not available. Use client.mcps.get() to get a client-connected MCP."


class MCP:
    """MCP reference helper for declaring MCPs in Agent definitions.

    Supports both lazy references and runtime operations:
    - Lazy reference: Created via from_native() or from_id()
    - Runtime: Created via from_response() or client.mcps.get()

    Attributes:
        name: Human-readable MCP name (used for lookup/creation).
        id: Backend MCP ID (used for direct fetch if known).
        transport: Transport type (e.g., "sse", "stdio", "websocket").
        config: Transport configuration dict (URLs, args, env vars).
        description: Optional description for the MCP.
        metadata: Optional additional metadata dict.
        authentication: Authentication configuration.

    Example - Lazy Reference:
        >>> # Create from known ID
        >>> mcp = MCP.from_id("mcp_abc123")
        >>>
        >>> # Create lookup-only by name (error if not found)
        >>> mcp = MCP.from_native("arxiv-search")
        >>>
        >>> # Create for lookup/creation by name (create if missing)
        >>> mcp = MCP(name="my-filesystem-mcp", transport="sse", config={"url": "..."})

    Example - Runtime Operations:
        >>> mcp = client.mcps.get("mcp-123")
        >>> mcp.update(description="New description")
        >>> mcp.delete()
    """

    def __init__(
        self,
        name: str | None = None,
        *,
        id: str | None = None,  # noqa: A002 - Allow shadowing builtin for API compat
        transport: str | None = None,
        config: dict[str, MCPConfigValue] | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        authentication: dict[str, Any] | None = None,
        _lookup_only: bool = False,
        _client: Any = None,
    ) -> None:
        """Initialize an MCP.

        Args:
            name: Human-readable MCP name.
            id: Backend MCP ID.
            transport: Transport type (e.g., "sse", "stdio").
            config: Transport configuration dict.
            description: Optional description.
            metadata: Optional metadata dict.
            authentication: Authentication configuration.
            _lookup_only: If True, don't create if not found.
            _client: Internal client reference.

        Raises:
            ValueError: If neither name nor id is provided.
        """
        if not name and not id:
            raise ValueError("At least one of 'name' or 'id' must be provided")

        self.name = name
        self._id = id
        self.transport = transport
        self.config = config
        self.description = description
        self.metadata = metadata
        self.authentication = authentication
        self._lookup_only = _lookup_only
        self._client = _client

    @property
    def id(self) -> str | None:  # noqa: A003 - Allow shadowing builtin for API compat
        """MCP ID on the platform."""
        return self._id

    @id.setter
    def id(self, value: str | None) -> None:  # noqa: A003
        """Set the MCP ID."""
        self._id = value

    def __repr__(self) -> str:
        """Return string representation."""
        if self._id:
            return f"MCP(id={self._id!r}, name={self.name!r})"
        if self._lookup_only:
            return f"MCP.from_native({self.name!r})"
        return f"MCP(name={self.name!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on id if available, else name."""
        if not isinstance(other, MCP):
            return NotImplemented
        if self._id and other._id:
            return self._id == other._id
        return self.name == other.name

    def __hash__(self) -> int:
        """Hash based on id if available, else name."""
        if self._id:
            return hash(self._id)
        return hash(self.name)

    def model_dump(self, *, exclude_none: bool = False) -> dict[str, Any]:
        """Return a dict representation of the MCP.

        Provides Pydantic-style serialization for backward compatibility.

        Args:
            exclude_none: If True, exclude None values from the output.

        Returns:
            Dictionary containing MCP attributes.
        """
        data = {
            "id": self._id,
            "name": self.name,
            "transport": self.transport,
            "config": self.config,
            "description": self.description,
            "metadata": self.metadata,
            "authentication": self.authentication,
        }
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        return data

    @classmethod
    def from_native(cls, name: str) -> MCP:
        """Create a lookup-only MCP reference by name.

        Use this when referencing an MCP that already exists on the platform.
        Resolution will NOT create the MCP if not found - it will raise an error.

        Args:
            name: The name of the existing MCP.

        Returns:
            MCP instance configured for lookup-only resolution.

        Raises:
            ValueError: If name is empty.

        Example:
            >>> mcp = MCP.from_native("arxiv-search")
            >>> # Registry will find by name, error if not found or ambiguous
        """
        if not name:
            raise ValueError("Name cannot be empty")
        return cls(name=name, _lookup_only=True)

    @classmethod
    def from_id(cls, mcp_id: str) -> MCP:
        """Create an MCP helper for lookup-only by ID.

        This creates a minimal MCP reference that will be resolved
        from the backend using the ID. Use this when you know the
        backend MCP ID but don't have the full configuration.

        Args:
            mcp_id: The backend MCP ID.

        Returns:
            An MCP instance with only the ID set, marked for lookup-only.

        Raises:
            ValueError: If mcp_id is empty.

        Example:
            >>> mcp = MCP.from_id("550e8400-e29b-41d4-a716-446655440000")
            >>> # Registry will fetch directly by ID
        """
        if not mcp_id:
            raise ValueError("ID cannot be empty")
        return cls(id=mcp_id, _lookup_only=True)

    # ─────────────────────────────────────────────────────────────────
    # Runtime Methods (require client connection)
    # ─────────────────────────────────────────────────────────────────

    def _set_client(self, client: Any) -> MCP:
        """Set the client reference for this MCP.

        Args:
            client: The Glaip client instance.

        Returns:
            Self for method chaining.
        """
        self._client = client
        return self

    def get_tools(self) -> list[dict[str, Any]]:
        """Get tools available from this MCP.

        Returns:
            List of tool definitions from the MCP.

        Raises:
            ValueError: If the MCP has no ID.
            RuntimeError: If client is not available.
        """
        if not self._id:
            raise ValueError(_MCP_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        # Delegate to the client's MCP tools endpoint
        return self._client.mcps.get_tools(mcp_id=self._id)

    def update(self, **kwargs: Any) -> MCP:
        """Update the MCP with new configuration.

        Args:
            **kwargs: MCP properties to update (name, description, config, etc.).

        Returns:
            Self with updated properties.

        Raises:
            ValueError: If the MCP has no ID.
            RuntimeError: If client is not available.
        """
        if not self._id:
            raise ValueError(_MCP_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        response = self._client.mcps.update(mcp_id=self._id, **kwargs)

        # Update local properties from response
        if hasattr(response, "name") and response.name:
            self.name = response.name
        if hasattr(response, "description"):
            self.description = response.description
        if hasattr(response, "config"):
            self.config = response.config
        if hasattr(response, "transport"):
            self.transport = response.transport

        return self

    def delete(self) -> None:
        """Delete the MCP from the platform.

        Raises:
            ValueError: If the MCP has no ID.
            RuntimeError: If client is not available.
        """
        if not self._id:
            raise ValueError(_MCP_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        self._client.mcps.delete(mcp_id=self._id)
        self._id = None
        self._client = None

    @classmethod
    def from_response(
        cls,
        response: MCPResponse,
        client: Any = None,
    ) -> MCP:
        """Create an MCP instance from an API response.

        This allows you to work with MCPs retrieved from the API
        as full MCP instances with all methods available.

        Args:
            response: The MCPResponse from an API call.
            client: The Glaip client instance for API operations.

        Returns:
            An MCP instance initialized from the response.

        Example:
            >>> response = client.mcps.get("mcp-123")
            >>> mcp = MCP.from_response(response, client)
            >>> tools = mcp.get_tools()
        """
        mcp = cls(
            name=response.name,
            id=response.id,
            description=getattr(response, "description", None),
            transport=getattr(response, "transport", None),
            config=getattr(response, "config", None),
            metadata=getattr(response, "metadata", None),
            authentication=getattr(response, "authentication", None),
        )

        if client:
            mcp._set_client(client)

        return mcp
