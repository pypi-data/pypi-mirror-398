"""Client singleton management for GLAIP SDK.

This module provides a singleton pattern for the GLAIP SDK client instance
used by the agents runtime. Uses a class-based singleton pattern consistent
with the registry implementations.

Thread Safety:
    The singleton is created lazily on first access. In Python, the GIL ensures
    that class attribute assignment is atomic, making this pattern safe for
    multi-threaded access. For multiprocessing, each process gets its own
    client instance (no shared state across processes).

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from dotenv import load_dotenv
from glaip_sdk.client import Client


class _ClientSingleton:
    """Singleton holder for GLAIP SDK Client.

    This class follows the same pattern as registry singletons
    (_ToolRegistrySingleton, _MCPRegistrySingleton, _AgentRegistrySingleton).
    """

    _instance: Client | None = None

    @classmethod
    def get_instance(cls) -> Client:
        """Get or create the singleton client instance.

        Returns:
            The singleton client instance.

        Example:
            >>> from glaip_sdk.utils.client import get_client
            >>> client = get_client()
            >>> agents = client.list_agents()
        """
        if cls._instance is None:
            load_dotenv()
            cls._instance = Client()
        return cls._instance

    @classmethod
    def set_instance(cls, client: Client) -> None:
        """Set the singleton client instance.

        Useful for testing or when you need to configure the client manually.

        Args:
            client: The client instance to use.

        Example:
            >>> from glaip_sdk import Client
            >>> from glaip_sdk.utils.client import set_client
            >>> client = Client(api_key="my-key")
            >>> set_client(client)
        """
        cls._instance = client

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton client instance.

        Useful for testing to ensure a fresh client is created.
        """
        cls._instance = None


def get_client() -> Client:
    """Get or create singleton client instance.

    Returns:
        The singleton client instance.

    Example:
        >>> from glaip_sdk.utils.client import get_client
        >>> client = get_client()
        >>> agents = client.list_agents()
    """
    return _ClientSingleton.get_instance()


def set_client(client: Client) -> None:
    """Set the singleton client instance.

    Useful for testing or when you need to configure the client manually.

    Args:
        client: The client instance to use.

    Example:
        >>> from glaip_sdk import Client
        >>> from glaip_sdk.utils.client import set_client
        >>> client = Client(api_key="my-key")
        >>> set_client(client)
    """
    _ClientSingleton.set_instance(client)


def reset_client() -> None:
    """Reset the singleton client instance.

    Useful for testing to ensure a fresh client is created.
    """
    _ClientSingleton.reset()
