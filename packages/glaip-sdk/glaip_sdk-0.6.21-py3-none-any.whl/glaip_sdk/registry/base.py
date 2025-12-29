"""Abstract base registry for caching platform objects.

This module provides the BaseRegistry abstract class that serves as the
foundation for type-specific registries (AgentRegistry, ToolRegistry, MCPRegistry).

The registry pattern provides:
    - In-memory caching to avoid redundant API calls
    - Transparent resolution of various reference types
    - Simple invalidation and cache management

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)


T = TypeVar("T")


class BaseRegistry(ABC, Generic[T]):
    """Abstract base registry for caching platform objects.

    Provides a caching layer between local code and the AIP platform.
    Subclasses implement type-specific resolution logic.

    The registry follows a simple flow:
        1. Check if reference is already a platform object → return as-is
        2. Extract name from reference
        3. Check cache → return if found
        4. Resolve via subclass logic → cache and return

    Attributes:
        _cache: Internal cache mapping names to objects.

    Example:
        >>> class MyRegistry(BaseRegistry):
        ...     def _extract_name(self, ref: Any) -> str:
        ...         return ref.name if hasattr(ref, 'name') else str(ref)
        ...
        ...     def _resolve_and_cache(self, ref: Any, name: str) -> MyType:
        ...         obj = fetch_from_platform(name)
        ...         self._cache[name] = obj
        ...         return obj
    """

    def __init__(self) -> None:
        """Initialize the registry with an empty cache."""
        self._cache: dict[str, T] = {}

    def resolve(self, ref: Any) -> T:
        """Resolve a reference to a platform object.

        This is the main entry point for the registry. It handles:
            - Cached references (returned from cache)
            - New references (resolved via subclass, then cached)

        Args:
            ref: A reference to resolve. Can be a class, string name,
                or platform object depending on the registry type.

        Returns:
            The resolved platform object.

        Raises:
            ValueError: If the reference cannot be resolved.
        """
        name = self._extract_name(ref)

        if name in self._cache:
            logger.debug("Cache hit: %s", name)
            return self._cache[name]

        return self._resolve_and_cache(ref, name)

    def get(self, name: str) -> T | None:
        """Get a cached object by name.

        Args:
            name: The name of the object to retrieve.

        Returns:
            The cached object, or None if not found.
        """
        return self._cache.get(name)

    def invalidate(self, name: str) -> None:
        """Remove an object from the cache.

        Use this to force a re-fetch on the next resolve call.

        Args:
            name: The name of the object to invalidate.
        """
        self._cache.pop(name, None)
        logger.debug("Invalidated cache entry: %s", name)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.debug("Cleared registry cache")

    @abstractmethod
    def _extract_name(self, ref: Any) -> str:
        """Extract the name from a reference.

        Args:
            ref: The reference to extract a name from.

        Returns:
            The extracted name string.

        Raises:
            ValueError: If name cannot be extracted.
        """

    @abstractmethod
    def _resolve_and_cache(self, ref: Any, name: str) -> T:
        """Resolve the reference and cache the result.

        Subclasses implement type-specific resolution logic here.
        This method MUST cache the result in self._cache[name].

        Args:
            ref: The reference to resolve.
            name: The extracted name for caching.

        Returns:
            The resolved platform object.

        Raises:
            ValueError: If resolution fails.
        """
