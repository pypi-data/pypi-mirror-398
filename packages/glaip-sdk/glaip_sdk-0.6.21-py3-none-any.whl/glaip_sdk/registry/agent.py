"""Agent registry for glaip_sdk.

This module provides the AgentRegistry that caches deployed agents
to avoid redundant API calls when deploying multi-agent systems.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from glaip_sdk.registry.base import BaseRegistry

if TYPE_CHECKING:
    from glaip_sdk.agents import Agent

logger = logging.getLogger(__name__)


class AgentRegistry(BaseRegistry["Agent"]):
    """Registry for agents.

    Resolves agent references to glaip_sdk.models.Agent objects.
    Caches results to avoid redundant API calls and duplicate deployments.

    Handles:
        - glaip_sdk.agents.Agent classes → deploy, cache, return Agent
        - glaip_sdk.agents.Agent instances → deploy, cache, return Agent
        - glaip_sdk.models.Agent → return as-is (uses agent.id)
        - String names → lookup on platform, cache, return Agent

    Attributes:
        _cache: Internal cache mapping names to Agent objects.

    Example:
        >>> registry = get_agent_registry()
        >>> agent = registry.resolve(GreeterAgent)  # Returns deployed Agent
        >>> print(agent.id)   # "uuid-123"
        >>> print(agent.name) # "greeter_agent"
    """

    def _extract_name(self, ref: Any) -> str:
        """Extract agent name from a reference.

        Args:
            ref: An agent class, instance, or string name.

        Returns:
            The extracted agent name.

        Raises:
            ValueError: If name cannot be extracted from the reference.
        """
        # Lazy import to avoid circular dependency
        from glaip_sdk.agents.base import Agent  # noqa: PLC0415

        # Agent class
        if isinstance(ref, type) and issubclass(ref, Agent):
            return ref().name

        # Agent instance
        if isinstance(ref, Agent):
            return ref.name

        # Already deployed agent (glaip_sdk.models.Agent)
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            return ref.name

        # String name
        if isinstance(ref, str):
            return ref

        raise ValueError(f"Cannot extract name from: {ref}")

    def _resolve_and_cache(self, ref: Any, name: str) -> Agent:
        """Resolve agent reference - deploy if class/instance, find if string.

        Args:
            ref: The agent reference to resolve.
            name: The extracted agent name.

        Returns:
            The resolved glaip_sdk.models.Agent object.

        Raises:
            ValueError: If the agent cannot be resolved.
        """
        # Lazy imports to avoid circular dependency
        from glaip_sdk.agents.base import Agent  # noqa: PLC0415
        from glaip_sdk.utils.discovery import find_agent  # noqa: PLC0415

        # Agent class
        if isinstance(ref, type) and issubclass(ref, Agent):
            logger.info("Deploying Agent class: %s", name)
            deployed = ref().deploy()
            self._cache[name] = deployed
            return deployed

        # Agent instance
        if isinstance(ref, Agent):
            logger.info("Deploying Agent instance: %s", name)
            deployed = ref.deploy()
            self._cache[name] = deployed
            return deployed

        # Already deployed agent (glaip_sdk.models.Agent) - just cache and return
        if hasattr(ref, "id") and hasattr(ref, "name") and not isinstance(ref, type):
            logger.debug("Caching already deployed agent: %s", name)
            self._cache[name] = ref
            return ref

        # String name - look up on platform
        if isinstance(ref, str):
            logger.info("Looking up agent by name: %s", name)
            agent = find_agent(name)
            if agent:
                self._cache[name] = agent
                return agent
            raise ValueError(f"Agent not found on platform: {name}")

        raise ValueError(f"Could not resolve agent reference: {ref}")


class _AgentRegistrySingleton:
    """Singleton holder for AgentRegistry to avoid global statement."""

    _instance: AgentRegistry | None = None

    @classmethod
    def get_instance(cls) -> AgentRegistry:
        """Get or create the singleton instance.

        Returns:
            The global AgentRegistry instance.
        """
        if cls._instance is None:
            cls._instance = AgentRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None


def get_agent_registry() -> AgentRegistry:
    """Get the singleton AgentRegistry instance.

    Returns a global AgentRegistry that caches agents across the session.
    Use this function to get the registry instead of creating instances directly.

    Returns:
        The global AgentRegistry instance.

    Example:
        >>> from glaip_sdk.registry import get_agent_registry
        >>> registry = get_agent_registry()
        >>> agent = registry.resolve("weather_agent")
        >>> print(agent.name)
    """
    return _AgentRegistrySingleton.get_instance()
