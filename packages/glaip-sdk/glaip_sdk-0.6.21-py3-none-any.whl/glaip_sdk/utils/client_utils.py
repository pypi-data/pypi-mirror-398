#!/usr/bin/env python3
"""Utility functions for AIP SDK clients.

This module contains generic utility functions that can be reused across
different client types (agents, tools, etc.).

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import logging
from collections.abc import AsyncGenerator, Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import Any, BinaryIO, NoReturn

import httpx
from glaip_sdk.exceptions import AgentTimeoutError
from glaip_sdk.models import AgentResponse, MCPResponse, ToolResponse
from glaip_sdk.utils.resource_refs import extract_ids as extract_ids_new
from glaip_sdk.utils.resource_refs import find_by_name as find_by_name_new

# Set up module-level logger
logger = logging.getLogger("glaip_sdk.client_utils")


class MultipartData:
    """Container for multipart form data with automatic file handle cleanup."""

    def __init__(self, data: dict[str, Any], files: list[tuple[str, Any]]):
        """Initialize multipart data container.

        Args:
            data: Form data dictionary
            files: List of file tuples for multipart form
        """
        self.data = data
        self.files = files
        self._exit_stack = ExitStack()

    def close(self) -> None:
        """Close all opened file handles."""
        self._exit_stack.close()

    def __enter__(self) -> "MultipartData":
        """Enter context manager.

        Returns:
            Self instance for context manager protocol
        """
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: Any,
    ) -> None:
        """Exit context manager and close all file handles.

        Args:
            _exc_type: Exception type (unused)
            _exc_val: Exception value (unused)
            _exc_tb: Exception traceback (unused)
        """
        self.close()


def extract_ids(items: list[str | Any] | None) -> list[str] | None:
    """Extract IDs from a list of objects or strings.

    Args:
        items: List of items that may be strings, objects with .id, or other types

    Returns:
        List of extracted IDs, or None if items is empty/None

    Note:
        This function maintains backward compatibility by returning None for empty input.
        New code should use glaip_sdk.utils.resource_refs.extract_ids which returns [].
    """
    if not items:
        return None

    result = extract_ids_new(items)
    return result if result else None


def create_model_instances(data: list[dict] | None, model_class: type, client: Any) -> list[Any]:
    """Create model instances from API data with client association.

    This is a common pattern used across different clients (agents, tools, mcps)
    to create model instances and associate them with the client.

    For runtime classes (Agent, Tool, MCP) that have a from_response method,
    this function will use the corresponding Response model to parse the API data
    and then create the runtime instance using from_response.

    Args:
        data: List of dictionaries from API response
        model_class: The model class to instantiate
        client: The client instance to associate with models

    Returns:
        List of model instances with client association
    """
    if not data:
        return []

    # Check if the model_class has a from_response method (runtime class pattern)
    if hasattr(model_class, "from_response"):
        # Map runtime classes to their response models
        response_model_map = {
            "Agent": AgentResponse,
            "Tool": ToolResponse,
            "MCP": MCPResponse,
        }

        response_model = response_model_map.get(model_class.__name__)
        if response_model:
            instances = []
            for item_data in data:
                response = response_model(**item_data)
                instance = model_class.from_response(response, client=client)
                instances.append(instance)
            return instances

    # Fallback to direct instantiation for other classes
    return [model_class(**item_data)._set_client(client) for item_data in data]


def find_by_name(items: list[Any], name: str, case_sensitive: bool = False) -> list[Any]:
    """Filter items by name with optional case sensitivity.

    This is a common pattern used across different clients for client-side
    filtering when the backend doesn't support name query parameters.

    Args:
        items: List of items to filter
        name: Name to search for
        case_sensitive: Whether the search should be case sensitive

    Returns:
        Filtered list of items matching the name

    Note:
        This function now delegates to glaip_sdk.utils.resource_refs.find_by_name.
    """
    return find_by_name_new(items, name, case_sensitive)


def _handle_blank_line(
    buf: list[str],
    event_type: str | None,
    event_id: str | None,
) -> tuple[list[str], str | None, str | None, dict[str, Any] | None, bool]:
    """Handle blank SSE lines by returning accumulated data if buffer exists."""
    if buf:
        data = "\n".join(buf)
        return (
            [],
            None,
            None,
            {
                "event": event_type or "message",
                "id": event_id,
                "data": data,
            },
            False,
        )
    return buf, event_type, event_id, None, False


def _handle_data_line(
    line: str,
    buf: list[str],
    event_type: str | None,
    event_id: str | None,
) -> tuple[list[str], str | None, str | None, dict[str, Any] | None, bool]:
    """Handle data: lines, including [DONE] sentinel marker."""
    data_line = line[5:].lstrip()

    if data_line.strip() == "[DONE]":
        if buf:
            data = "\n".join(buf)
            return (
                [],
                None,
                None,
                {
                    "event": event_type or "message",
                    "id": event_id,
                    "data": data,
                },
                True,
            )
        return buf, event_type, event_id, None, True

    buf.append(data_line)
    return buf, event_type, event_id, None, False


def _handle_field_line(
    line: str,
    field_type: str,
    current_value: str | None,
) -> str | None:
    """Handle event: or id: field lines."""
    if field_type == "event":
        return line[6:].strip() or None
    elif field_type == "id":
        return line[3:].strip() or None
    return current_value


def _parse_sse_line(
    line: str,
    buf: list[str],
    event_type: str | None = None,
    event_id: str | None = None,
) -> tuple[list[str], str | None, str | None, dict[str, Any] | None, bool]:
    """Parse a single SSE line and return updated buffer and event metadata."""
    # Normalize CRLF and treat whitespace-only as blank
    line = line.rstrip("\r")

    if not line.strip():  # blank line
        return _handle_blank_line(buf, event_type, event_id)

    if line.startswith(":"):  # comment
        return buf, event_type, event_id, None, False

    if line.startswith("data:"):
        return _handle_data_line(line, buf, event_type, event_id)

    if line.startswith("event:"):
        event_type = _handle_field_line(line, "event", event_type)
    elif line.startswith("id:"):
        event_id = _handle_field_line(line, "id", event_id)

    return buf, event_type, event_id, None, False


def _handle_streaming_error(
    e: Exception,
    timeout_seconds: float | None = None,
    agent_name: str | None = None,
) -> NoReturn:
    """Handle different types of streaming errors with appropriate logging and exceptions."""
    if isinstance(e, httpx.ReadTimeout):
        logger.error(f"Read timeout during streaming: {e}")
        logger.error("This usually indicates the backend is taking too long to respond")
        logger.error("Consider increasing the timeout value or checking backend performance")
        raise AgentTimeoutError(timeout_seconds or 30.0, agent_name)

    elif isinstance(e, httpx.TimeoutException):
        logger.error(f"General timeout during streaming: {e}")
        raise AgentTimeoutError(timeout_seconds or 30.0, agent_name)

    elif isinstance(e, httpx.StreamClosed):
        logger.error(f"Stream closed unexpectedly during streaming: {e}")
        logger.error("This may indicate a backend issue or network problem")
        logger.error("The response stream was closed before all data could be read")
        raise

    elif isinstance(e, httpx.ConnectError):
        logger.error(f"Connection error during streaming: {e}")
        logger.error("Check your network connection and backend availability")
        raise

    else:
        logger.error(f"Unexpected error during streaming: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise


def _process_sse_line(
    line: str, buf: list[str], event_type: str | None, event_id: str | None
) -> tuple[list[str], str | None, str | None, dict[str, Any] | None, bool]:
    """Process a single SSE line and return updated state."""
    result = _parse_sse_line(line, buf, event_type, event_id)
    buf, event_type, event_id, event_data, completed = result
    return buf, event_type, event_id, event_data, completed


def _yield_event_data(event_data: dict[str, Any] | None) -> Iterator[dict[str, Any]]:
    """Yield event data if available."""
    if event_data:
        yield event_data


def _flush_remaining_buffer(buf: list[str], event_type: str | None, event_id: str | None) -> Iterator[dict[str, Any]]:
    """Flush any remaining data in buffer."""
    if buf:
        yield {
            "event": event_type or "message",
            "id": event_id,
            "data": "\n".join(buf),
        }


def iter_sse_events(
    response: httpx.Response,
    timeout_seconds: float | None = None,
    agent_name: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Iterate over Server-Sent Events with proper parsing.

    Args:
        response: HTTP response object with streaming content
        timeout_seconds: Timeout duration in seconds (for error messages)
        agent_name: Agent name (for error messages)

    Yields:
        Dictionary with event data, type, and ID

    Raises:
        AgentTimeoutError: When agent execution times out
        httpx.TimeoutException: When general timeout occurs
        Exception: For other unexpected errors
    """
    buf = []
    event_type = None
    event_id = None

    try:
        for raw in response.iter_lines():
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if line is None:
                continue

            buf, event_type, event_id, event_data, completed = _process_sse_line(line, buf, event_type, event_id)

            yield from _yield_event_data(event_data)
            if completed:
                return

        # Flush any remaining data
        yield from _flush_remaining_buffer(buf, event_type, event_id)

    except Exception as e:
        _handle_streaming_error(e, timeout_seconds, agent_name)


async def aiter_sse_events(
    response: httpx.Response, timeout_seconds: float = None, agent_name: str = None
) -> AsyncGenerator[dict, None]:
    """Async iterate over Server-Sent Events with proper parsing.

    Args:
        response: HTTP response object with streaming content
        timeout_seconds: Timeout duration in seconds (for error messages)
        agent_name: Agent name (for error messages)

    Yields:
        Dictionary with event data, type, and ID

    Raises:
        AgentTimeoutError: When agent execution times out
        httpx.TimeoutException: When general timeout occurs
        Exception: For other unexpected errors
    """
    buf = []
    event_type = None
    event_id = None

    try:
        async for raw in response.aiter_lines():
            line = raw
            if line is None:
                continue

            result = _parse_sse_line(line, buf, event_type, event_id)
            buf, event_type, event_id, event_data, completed = result

            if event_data:
                yield event_data
            if completed:
                return

        # Flush any remaining data
        if buf:
            yield {
                "event": event_type or "message",
                "id": event_id,
                "data": "\n".join(buf),
            }

    except Exception as e:
        _handle_streaming_error(e, timeout_seconds, agent_name)


def _create_form_data(message: str) -> dict[str, Any]:
    """Create form data with message and stream flag."""
    return {"input": message, "message": message, "stream": True}


def _prepare_file_entry(item: str | BinaryIO, stack: ExitStack) -> tuple[str, tuple[str, BinaryIO, str]]:
    """Prepare a single file entry for multipart data."""
    if isinstance(item, str):
        return _prepare_path_entry(item, stack)
    else:
        return _prepare_stream_entry(item)


def _prepare_path_entry(path_str: str, stack: ExitStack) -> tuple[str, tuple[str, BinaryIO, str]]:
    """Prepare a file path entry."""
    file_path = Path(path_str)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path_str}")

    handle = stack.enter_context(open(file_path, "rb"))
    return (
        "files",
        (
            file_path.name,
            handle,
            "application/octet-stream",
        ),
    )


def _prepare_stream_entry(
    file_obj: BinaryIO,
) -> tuple[str, tuple[str, BinaryIO, str]]:
    """Prepare a file object entry."""
    if not hasattr(file_obj, "read"):
        raise ValueError(f"Invalid file object: {file_obj}")

    raw_name = getattr(file_obj, "name", "file")
    filename = Path(raw_name).name if raw_name else "file"

    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
    except (OSError, ValueError):
        pass

    return (
        "files",
        (
            filename,
            file_obj,
            "application/octet-stream",
        ),
    )


def add_kwargs_to_payload(payload: dict[str, Any], kwargs: dict[str, Any], excluded_keys: set[str]) -> None:
    """Add kwargs to payload excluding specified keys.

    Args:
        payload: Payload dictionary to update.
        kwargs: Keyword arguments to add.
        excluded_keys: Keys to exclude from kwargs.
    """
    for key, value in kwargs.items():
        if key not in excluded_keys:
            payload[key] = value


def prepare_multipart_data(message: str, files: list[str | BinaryIO]) -> MultipartData:
    """Prepare multipart form data for file uploads.

    Args:
        message: Text message to include with the upload
        files: List of file paths or file-like objects

    Returns:
        MultipartData object with automatic file handle cleanup

    Raises:
        FileNotFoundError: When a file path doesn't exist
        ValueError: When a file object is invalid
    """
    form_data = _create_form_data(message)
    stack = ExitStack()
    multipart_data = MultipartData(form_data, [])
    multipart_data._exit_stack = stack

    try:
        file_entries = [_prepare_file_entry(item, stack) for item in files]
        multipart_data.files = file_entries
        return multipart_data
    except Exception:
        stack.close()
        raise
