"""Validation utilities for resource names, timeouts, and other constraints.

This module provides pure validation functions that raise ValueError for invalid
inputs. CLI layer wraps these with click.ClickException for user-friendly errors.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import re
from pathlib import Path
from typing import Any

from glaip_sdk.config.constants import DEFAULT_AGENT_RUN_TIMEOUT
from glaip_sdk.utils.resource_refs import validate_name_format

# Constants for validation
RESERVED_NAMES = ["admin", "root", "system", "api", "test", "demo"]


def _validate_named_resource(name: str, resource_type: str) -> str:
    """Shared validator that prevents reserved-name duplication."""
    cleaned_name = validate_name_format(name, resource_type)

    if cleaned_name.lower() in RESERVED_NAMES:
        raise ValueError(f"{resource_type.capitalize()} name '{cleaned_name}' is reserved and cannot be used")

    return cleaned_name


def validate_agent_name(name: str) -> str:
    """Validate agent name and return cleaned version.

    Args:
        name: Agent name to validate

    Returns:
        Cleaned agent name

    Raises:
        ValueError: If name is invalid
    """
    return _validate_named_resource(name, "agent")


def validate_agent_instruction(instruction: str) -> str:
    """Validate agent instruction and return cleaned version.

    Args:
        instruction: Agent instruction to validate

    Returns:
        Cleaned agent instruction

    Raises:
        ValueError: If instruction is invalid
    """
    if not instruction or not instruction.strip():
        raise ValueError("Agent instruction cannot be empty or whitespace")

    cleaned_instruction = instruction.strip()

    if len(cleaned_instruction) > 100000:
        raise ValueError("Agent instruction cannot be longer than 100,000 characters")

    return cleaned_instruction


def validate_tool_name(name: str) -> str:
    """Validate tool name and return cleaned version.

    Args:
        name: Tool name to validate

    Returns:
        Cleaned tool name

    Raises:
        ValueError: If name is invalid
    """
    return _validate_named_resource(name, "tool")


def validate_mcp_name(name: str) -> str:
    """Validate MCP name and return cleaned version.

    Args:
        name: MCP name to validate

    Returns:
        Cleaned MCP name

    Raises:
        ValueError: If name is invalid
    """
    return _validate_named_resource(name, "mcp")


def validate_timeout(timeout: int) -> int:
    """Validate timeout value.

    Args:
        timeout: Timeout value in seconds

    Returns:
        Validated timeout value

    Raises:
        ValueError: If timeout is invalid
    """
    if timeout < 1:
        raise ValueError("Timeout must be at least 1 second")

    if timeout > 3600:  # 1 hour max
        raise ValueError("Timeout cannot be longer than 1 hour (3600 seconds)")

    return timeout


def coerce_timeout(value: Any) -> int:
    """Coerce timeout value to integer, handling various input types.

    Args:
        value: The timeout value to coerce (int, float, str, etc.)

    Returns:
        Integer timeout value

    Raises:
        ValueError: If value cannot be coerced to valid timeout

    Examples:
        coerce_timeout(300) -> 300
        coerce_timeout(300.0) -> 300
        coerce_timeout("300") -> 300
        coerce_timeout(None) -> 300  # Uses DEFAULT_AGENT_RUN_TIMEOUT
    """
    if value is None:
        return DEFAULT_AGENT_RUN_TIMEOUT
    elif isinstance(value, int):
        return validate_timeout(value)
    elif isinstance(value, float):
        if value.is_integer():
            return validate_timeout(int(value))
        return validate_timeout(int(value))  # Truncate if not integer
    elif isinstance(value, str):
        try:
            fval = float(value)
            return validate_timeout(int(fval))
        except ValueError as err:
            raise ValueError(f"Invalid timeout value: {value}") from err
    else:
        try:
            return validate_timeout(int(value))
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid timeout value: {value}") from err


def validate_file_path(file_path: str | Path, must_exist: bool = True) -> Path:
    """Validate file path.

    Args:
        file_path: File path to validate
        must_exist: Whether file must exist

    Returns:
        Path object

    Raises:
        ValueError: If file path is invalid
    """
    path = Path(file_path)

    if must_exist and not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    if must_exist and not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path


def validate_directory_path(dir_path: str | Path, must_exist: bool = True) -> Path:
    """Validate directory path.

    Args:
        dir_path: Directory path to validate
        must_exist: Whether directory must exist

    Returns:
        Path object

    Raises:
        ValueError: If directory path is invalid
    """
    path = Path(dir_path)

    if must_exist and not path.exists():
        raise ValueError(f"Directory does not exist: {dir_path}")

    if must_exist and not path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")

    return path


def validate_url(url: str) -> str:
    """Validate URL format (HTTPS only).

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValueError: If URL is invalid
    """
    url_pattern = re.compile(
        r"^https://"  # https:// only
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        raise ValueError("API URL must start with https:// and be a valid host.")

    return url


def validate_api_key(api_key: str) -> str:
    """Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        Validated API key

    Raises:
        ValueError: If API key is invalid
    """
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")

    cleaned_key = api_key.strip()

    if len(cleaned_key) < 10:
        raise ValueError("API key appears to be too short")

    if len(cleaned_key) > 200:
        raise ValueError("API key appears to be too long")

    # Check for potentially invalid characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", cleaned_key):
        raise ValueError(
            "API key contains invalid characters. Only letters, numbers, hyphens, and underscores are allowed."
        )

    return cleaned_key
