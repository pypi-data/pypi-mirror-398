"""Abstract base class for agent execution runners.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glaip_sdk.agents.base import Agent


class BaseRunner(ABC):
    """Abstract base class for agent execution runners.

    Runners are responsible for executing glaip-sdk Agent instances
    and returning results. Different runner implementations may use
    different execution backends (LangGraph, Google ADK, etc.).
    """

    @abstractmethod
    def run(
        self,
        agent: Agent,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute agent synchronously and return final response text.

        Args:
            agent: The glaip_sdk Agent to execute.
            message: The user message to send to the agent.
            verbose: If True, emit debug trace output during execution.
                Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, etc.
                Defaults to None.
            chat_history: Optional list of prior conversation messages.
                Defaults to None.
            **kwargs: Additional keyword arguments passed to the backend.

        Returns:
            The final response text from the agent.

        Raises:
            RuntimeError: If execution fails.
        """
        ...

    @abstractmethod
    async def arun(
        self,
        agent: Agent,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute agent asynchronously and return final response text.

        Args:
            agent: The glaip_sdk Agent to execute.
            message: The user message to send to the agent.
            verbose: If True, emit debug trace output during execution.
                Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, etc.
                Defaults to None.
            chat_history: Optional list of prior conversation messages.
                Defaults to None.
            **kwargs: Additional keyword arguments passed to the backend.

        Returns:
            The final response text from the agent.

        Raises:
            RuntimeError: If execution fails.
        """
        ...
