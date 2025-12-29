"""MCP registry for glaip_sdk.

This module provides the MCPRegistry that caches MCPs (Model Context Protocols)
to avoid redundant API calls when deploying agents with MCPs.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from glaip_sdk.registry.base import BaseRegistry
from glaip_sdk.utils.resource_refs import is_uuid

if TYPE_CHECKING:
    from glaip_sdk.mcps import MCP

logger = logging.getLogger(__name__)


class MCPRegistry(BaseRegistry["MCP"]):
    """Registry for MCPs (Model Context Protocols).

    Resolves MCP references to glaip_sdk.models.MCP objects.
    Caches results to avoid redundant API calls.

    Handles:
        - glaip_sdk.models.MCP → return as-is (uses mcp.id)
        - String names/IDs → lookup on platform, cache, return MCP

    Attributes:
        _cache: Internal cache mapping names to MCP objects.

    Example:
        >>> registry = get_mcp_registry()
        >>> mcp = registry.resolve("arxiv-mcp")
        >>> print(mcp.id)
    """

    def _extract_name(self, ref: Any) -> str:
        """Extract MCP name from a reference.

        Args:
            ref: An MCP object, dict, or string name.

        Returns:
            The extracted MCP name.

        Raises:
            ValueError: If name cannot be extracted from the reference.
        """
        # String name
        if isinstance(ref, str):
            return ref

        # Dict from API response - extract name or id
        if isinstance(ref, dict):
            return ref.get("name") or ref.get("id") or ""

        # Already resolved MCP (glaip_sdk.models.MCP)
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            return ref.name or ref.id

        raise ValueError(f"Cannot extract name from: {ref}")

    def _resolve_and_cache(self, ref: Any, name: str) -> MCP:
        """Resolve MCP reference - find by name/ID or create if needed.

        Args:
            ref: The MCP reference to resolve.
            name: The extracted MCP name.

        Returns:
            The resolved glaip_sdk.models.MCP object.

        Raises:
            ValueError: If the MCP cannot be resolved.
        """
        # MCP object (check if already has ID)
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            if ref.id is not None:
                # Already resolved MCP with ID - just cache and return
                logger.debug("Caching already resolved MCP: %s", name)
                self._cache[name] = ref
                return ref

            # MCP without ID - need to look up or create
            return self._lookup_or_create_mcp(ref, name)

        # Dict from API response - use ID directly if available
        if isinstance(ref, dict):
            mcp_id = ref.get("id")
            if mcp_id:
                from glaip_sdk.mcps.base import MCP  # noqa: PLC0415

                mcp = MCP(id=mcp_id, name=ref.get("name", ""))
                self._cache[name] = mcp
                return mcp
            raise ValueError(f"MCP dict missing 'id': {ref}")

        # String name - look up on platform
        if isinstance(ref, str):
            return self._lookup_mcp_by_name(name)

        raise ValueError(f"Could not resolve MCP reference: {ref}")

    def _lookup_or_create_mcp(self, ref: Any, name: str) -> MCP:
        """Look up or create an MCP from a reference.

        Args:
            ref: The MCP reference with config details.
            name: The extracted MCP name.

        Returns:
            The resolved or created glaip_sdk.models.MCP object.
        """
        # Check if this MCP is lookup-only (e.g., from MCP.from_native)
        if getattr(ref, "_lookup_only", False):
            return self._lookup_native_mcp(name)

        return self._upsert_mcp_from_ref(ref, name)

    def _lookup_native_mcp(self, name: str) -> MCP:
        """Look up a native MCP that must exist on the platform.

        Used for MCP.from_native() references that should not be created.

        Args:
            name: The MCP name to look up.

        Returns:
            The found MCP.

        Raises:
            ValueError: If MCP not found or multiple found.
        """
        from glaip_sdk.utils.client import get_client  # noqa: PLC0415

        client = get_client()
        logger.info("Looking up native MCP: %s", name)

        results = client.find_mcps(name)
        exact_matches = [mcp for mcp in results if getattr(mcp, "name", None) == name]
        if len(exact_matches) == 1:
            mcp = exact_matches[0]
            self._cache[name] = mcp
            return mcp
        if len(exact_matches) > 1:
            raise ValueError(f"Multiple MCPs found with name '{name}'")
        raise ValueError(f"MCP not found on platform: {name}")

    def _upsert_mcp_from_ref(self, ref: Any, name: str) -> MCP:
        """Create or update an MCP from a reference with config.

        Args:
            ref: The MCP reference with config details.
            name: The extracted MCP name.

        Returns:
            The created or updated MCP.
        """
        from glaip_sdk.utils.client import get_client  # noqa: PLC0415

        client = get_client()
        logger.info("Upserting MCP: %s", name)

        mcp = client.mcps.upsert_mcp(
            name,
            description=getattr(ref, "description", None),
            config=getattr(ref, "config", None),
            transport=getattr(ref, "transport", None),
            metadata=getattr(ref, "metadata", None),
            authentication=getattr(ref, "authentication", None),
        )
        self._cache[name] = mcp
        return mcp

    def _lookup_mcp_by_name(self, name: str) -> MCP:
        """Look up MCP by name or ID on the platform.

        Args:
            name: The MCP name or ID to look up.

        Returns:
            The resolved glaip_sdk.models.MCP object.

        Raises:
            ValueError: If the MCP cannot be found.
        """
        # Lazy imports to avoid circular dependency
        from glaip_sdk.utils.client import get_client  # noqa: PLC0415

        client = get_client()
        logger.info("Looking up MCP by name: %s", name)

        # Check if it's a valid UUID
        if is_uuid(name):
            mcp = client.get_mcp_by_id(name)
            if mcp:
                self._cache[name] = mcp
                return mcp
        else:
            results = client.find_mcps(name)
            exact_matches = [mcp for mcp in results if getattr(mcp, "name", None) == name]
            if len(exact_matches) == 1:
                mcp = exact_matches[0]
                self._cache[name] = mcp
                return mcp
            if len(exact_matches) > 1:
                raise ValueError(f"Multiple MCPs found with name '{name}'")

        raise ValueError(f"MCP not found on platform: {name}")


class _MCPRegistrySingleton:
    """Singleton holder for MCPRegistry to avoid global statement."""

    _instance: MCPRegistry | None = None

    @classmethod
    def get_instance(cls) -> MCPRegistry:
        """Get or create the singleton instance.

        Returns:
            The global MCPRegistry instance.
        """
        if cls._instance is None:
            cls._instance = MCPRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None


def get_mcp_registry() -> MCPRegistry:
    """Get the singleton MCPRegistry instance.

    Returns a global MCPRegistry that caches MCPs across the session.

    Returns:
        The global MCPRegistry instance.

    Example:
        >>> from glaip_sdk.registry import get_mcp_registry
        >>> registry = get_mcp_registry()
        >>> mcp = registry.resolve("arxiv-mcp")
    """
    return _MCPRegistrySingleton.get_instance()
