#!/usr/bin/env python3
"""Custom exceptions for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any


class AIPError(Exception):
    """Base exception for AIP SDK."""

    pass


class APIError(AIPError):
    """Base API exception with rich context."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_type: str | None = None,
        payload: Any = None,
        request_id: str | None = None,
    ):
        """Initialize the API error.

        Args:
            message: The error message
            status_code: HTTP status code
            error_type: Type of error
            payload: Additional error payload
            request_id: Request identifier
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type
        self.payload = payload
        self.request_id = request_id


class AuthenticationError(APIError):
    """Authentication failed."""

    pass


class ValidationError(APIError):
    """Validation failed."""

    pass


class ForbiddenError(APIError):
    """Access forbidden."""

    pass


class NotFoundError(APIError):
    """Resource not found."""

    pass


class ConflictError(APIError):
    """Resource conflict."""

    pass


class AmbiguousResourceError(APIError):
    """Multiple resources match the query."""

    pass


class ServerError(APIError):
    """Server error."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class TimeoutError(APIError):
    """Request timeout."""

    pass


class AgentTimeoutError(TimeoutError):
    """Agent execution timeout with specific duration information."""

    def __init__(self, timeout_seconds: float, agent_name: str = None):
        """Initialize the agent timeout error.

        Args:
            timeout_seconds: The timeout duration in seconds
            agent_name: Optional name of the agent that timed out
        """
        agent_info = f" for agent '{agent_name}'" if agent_name else ""
        message = f"Agent execution timed out after {timeout_seconds} seconds{agent_info}"
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.agent_name = agent_name
