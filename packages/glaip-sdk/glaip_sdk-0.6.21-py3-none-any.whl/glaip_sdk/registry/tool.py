"""Tool registry for glaip_sdk.

This module provides the ToolRegistry that caches deployed tools
to avoid redundant API calls when deploying agents with tools.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from glaip_sdk.registry.base import BaseRegistry

if TYPE_CHECKING:
    from glaip_sdk.tools import Tool

logger = logging.getLogger(__name__)


class ToolRegistry(BaseRegistry["Tool"]):
    """Registry for tools.

    Resolves tool references to glaip_sdk.models.Tool objects.
    Caches results to avoid redundant API calls and duplicate uploads.

    Handles:
        - Tool classes (LangChain BaseTool subclasses) → upload, cache, return Tool
        - glaip_sdk.models.Tool → return as-is (uses tool.id)
        - String names → lookup on platform, cache, return Tool

    Attributes:
        _cache: Internal cache mapping names to Tool objects.

    Example:
        >>> registry = get_tool_registry()
        >>> tool = registry.resolve(WebSearchTool)
        >>> print(tool.id)
    """

    def _get_name_from_model_fields(self, ref: type) -> str | None:
        """Extract name from Pydantic model_fields if available."""
        model_fields = getattr(ref, "model_fields", {})
        if "name" not in model_fields:
            return None
        field_info = model_fields["name"]
        default = getattr(field_info, "default", None)
        return default if isinstance(default, str) else None

    def _get_string_attr(self, obj: Any, attr: str) -> str | None:
        """Get attribute if it's a string, otherwise None."""
        value = getattr(obj, attr, None)
        return value if isinstance(value, str) else None

    def _extract_name(self, ref: Any) -> str:
        """Extract tool name from a reference.

        Args:
            ref: A tool class, instance, dict, or string name.

        Returns:
            The extracted tool name.

        Raises:
            ValueError: If name cannot be extracted from the reference.
        """
        if isinstance(ref, str):
            return ref

        # Dict from API response - extract name or id
        if isinstance(ref, dict):
            return ref.get("name") or ref.get("id") or ""

        # Tool instance (not a class) with name attribute
        if not isinstance(ref, type):
            name = self._get_string_attr(ref, "name")
            if name:
                return name

        # Tool class - try direct attribute first, then model_fields
        if isinstance(ref, type):
            name = self._get_string_attr(ref, "name") or self._get_name_from_model_fields(ref)
            if name:
                return name

        raise ValueError(f"Cannot extract name from: {ref}")

    def _resolve_and_cache(self, ref: Any, name: str) -> Tool:
        """Resolve tool reference - upload if class, find if string/native.

        Args:
            ref: The tool reference to resolve.
            name: The extracted tool name.

        Returns:
            The resolved glaip_sdk.models.Tool object.

        Raises:
            ValueError: If the tool cannot be resolved.
        """
        # Lazy imports to avoid circular dependency
        from glaip_sdk.utils.discovery import find_tool  # noqa: PLC0415
        from glaip_sdk.utils.sync import update_or_create_tool  # noqa: PLC0415

        # Already deployed tool (glaip_sdk.models.Tool with ID) - just cache and return
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            if ref.id is not None:
                logger.debug("Caching already deployed tool: %s", name)
                self._cache[name] = ref
                return ref

            # Tool without ID (e.g., Tool.from_native()) - look up on platform
            logger.info("Looking up native tool: %s", name)
            tool = find_tool(name)
            if tool:
                self._cache[name] = tool
                return tool
            raise ValueError(f"Native tool not found on platform: {name}")

        # Custom tool class - upload it
        if self._is_custom_tool(ref):
            logger.info("Uploading custom tool: %s", name)
            tool = update_or_create_tool(ref)
            self._cache[name] = tool
            if tool.id:
                self._cache[tool.id] = tool
            return tool

        # Dict from API response - use ID directly if available
        if isinstance(ref, dict):
            tool_id = ref.get("id")
            if tool_id:
                from glaip_sdk.tools.base import Tool  # noqa: PLC0415

                tool = Tool(id=tool_id, name=ref.get("name", ""))
                self._cache[name] = tool
                return tool
            raise ValueError(f"Tool dict missing 'id': {ref}")

        # String name - look up on platform (could be native or existing tool)
        if isinstance(ref, str):
            logger.info("Looking up tool by name: %s", name)
            tool = find_tool(name)
            if tool:
                self._cache[name] = tool
                return tool
            raise ValueError(f"Tool not found on platform: {name}")

        raise ValueError(f"Could not resolve tool reference: {ref}")

    def _is_custom_tool(self, ref: Any) -> bool:
        """Check if reference is a custom tool class/instance.

        Args:
            ref: The reference to check.

        Returns:
            True if ref is a custom tool that needs uploading.
        """
        try:
            from glaip_sdk.utils.tool_detection import (  # noqa: PLC0415
                is_langchain_tool,
            )
        except ImportError:
            return False

        return is_langchain_tool(ref)

    def resolve(self, ref: Any) -> Tool:
        """Resolve a tool reference to a platform Tool object.

        Overrides base resolve to handle SDK tools differently.

        Args:
            ref: The tool reference to resolve.

        Returns:
            The resolved glaip_sdk.models.Tool object.
        """
        # Check if it's a Tool instance (not a class)
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            # If Tool has an ID, it's already deployed - return as-is
            if ref.id is not None:
                name = self._extract_name(ref)
                if name not in self._cache:
                    self._cache[name] = ref
                return ref

            # Tool without ID (e.g., from Tool.from_native()) - needs platform lookup
            # Fall through to normal resolution

        return super().resolve(ref)


class _ToolRegistrySingleton:
    """Singleton holder for ToolRegistry to avoid global statement."""

    _instance: ToolRegistry | None = None

    @classmethod
    def get_instance(cls) -> ToolRegistry:
        """Get or create the singleton instance.

        Returns:
            The global ToolRegistry instance.
        """
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None


def get_tool_registry() -> ToolRegistry:
    """Get the singleton ToolRegistry instance.

    Returns a global ToolRegistry that caches tools across the session.

    Returns:
        The global ToolRegistry instance.

    Example:
        >>> from glaip_sdk.registry import get_tool_registry
        >>> registry = get_tool_registry()
        >>> tool = registry.resolve("web_search")
    """
    return _ToolRegistrySingleton.get_instance()
