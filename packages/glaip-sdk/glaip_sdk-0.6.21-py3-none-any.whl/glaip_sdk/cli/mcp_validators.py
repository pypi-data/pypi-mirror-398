"""MCP configuration and authentication validation for CLI.

This module provides validation functions for MCP config and auth structures
that are used in CLI commands. It ensures data conforms to the MCP schema
documented in docs/reference/schemas/mcps.md.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import Any
from urllib.parse import urlparse

import click


def format_validation_error(prefix: str, detail: str | None = None) -> str:
    r"""Format a validation error message with optional detail.

    Args:
        prefix: Main error message
        detail: Optional additional detail to append

    Returns:
        Formatted error message string

    Examples:
        >>> format_validation_error("Invalid config", "Missing 'url' field")
        "Invalid config\nMissing 'url' field"
    """
    parts = [prefix]
    if detail:
        parts.append(detail)
    return "\n".join(parts)


def validate_mcp_config_structure(
    config: Any, *, transport: str | None = None, source: str = "--config"
) -> dict[str, Any]:
    """Validate MCP configuration structure for CLI commands.

    Validates that the config is a dictionary with a valid 'url' field.
    The 'url' must be an absolute HTTP/HTTPS URL as required by the MCP schema.

    Args:
        config: Configuration value to validate (expected to be a dict)
        transport: Optional transport type ('http' or 'sse') for context in errors
        source: Source parameter name for error messages (default: "--config")

    Returns:
        Validated configuration dictionary

    Raises:
        click.ClickException: If config is not a dict, missing 'url', or URL is invalid

    Examples:
        >>> validate_mcp_config_structure({"url": "https://api.example.com"})
        {'url': 'https://api.example.com'}

        >>> validate_mcp_config_structure([1, 2, 3])  # doctest: +SKIP
        ClickException: Invalid --config value
        Expected a JSON object representing MCP configuration.

    Schema Reference:
        See docs/reference/schemas/mcps.md - Config Object Structure
        - Required field: 'url' (string, must be valid HTTP/HTTPS URL)
        - Additional fields allowed and passed through
    """
    if not isinstance(config, dict):
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "Expected a JSON object representing MCP configuration.",
            )
        )

    url_value = config.get("url")
    if not isinstance(url_value, str) or not url_value.strip():
        requirement = "Missing required 'url' field with a non-empty string value."
        if transport:
            requirement += f" Required for transport '{transport}'."
        raise click.ClickException(format_validation_error(f"Invalid {source} value", requirement))

    parsed_url = urlparse(url_value)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "'url' must be an absolute HTTP or HTTPS URL.",
            )
        )

    return config


def _validate_headers_mapping(headers: Any, *, source: str, context: str) -> dict[str, str]:
    """Validate headers mapping for authentication.

    Args:
        headers: Headers value to validate (expected to be a non-empty dict)
        source: Source parameter name for error messages
        context: Context description for error messages (e.g., "bearer-token authentication")

    Returns:
        Validated headers dictionary with string keys and values

    Raises:
        click.ClickException: If headers is not a dict, empty, or contains invalid entries
    """
    if not isinstance(headers, dict) or not headers:
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                f"{context} must provide a non-empty 'headers' object with string keys and values.",
            )
        )

    normalized: dict[str, str] = {}
    for key, value in headers.items():
        if not isinstance(key, str) or not key.strip():
            raise click.ClickException(
                format_validation_error(
                    f"Invalid {source} value",
                    "Header names must be non-empty strings.",
                )
            )
        if not isinstance(value, str) or not value.strip():
            raise click.ClickException(
                format_validation_error(
                    f"Invalid {source} value",
                    f"Header '{key}' must have a non-empty string value.",
                )
            )
        normalized[key] = value
    return normalized


def _validate_bearer_token_auth(auth: dict[str, Any], source: str) -> dict[str, Any]:
    """Validate bearer-token authentication.

    Args:
        auth: Authentication dictionary
        source: Source parameter name for error messages

    Returns:
        Validated bearer-token authentication dictionary

    Raises:
        click.ClickException: If bearer-token structure is invalid
    """
    token = auth.get("token")
    if isinstance(token, str) and token.strip():
        return {"type": "bearer-token", "token": token}
    headers = auth.get("headers")
    normalized_headers = _validate_headers_mapping(headers, source=source, context="bearer-token authentication")
    return {"type": "bearer-token", "headers": normalized_headers}


def _validate_api_key_auth(auth: dict[str, Any], source: str) -> dict[str, Any]:
    """Validate api-key authentication.

    Args:
        auth: Authentication dictionary
        source: Source parameter name for error messages

    Returns:
        Validated api-key authentication dictionary

    Raises:
        click.ClickException: If api-key structure is invalid
    """
    headers = auth.get("headers")
    if headers is not None:
        normalized_headers = _validate_headers_mapping(headers, source=source, context="api-key authentication")
        return {"type": "api-key", "headers": normalized_headers}

    key = auth.get("key")
    value = auth.get("value")
    if not isinstance(key, str) or not key.strip():
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "api-key authentication requires a non-empty 'key'.",
            )
        )
    if not isinstance(value, str) or not value.strip():
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "api-key authentication requires a non-empty 'value'.",
            )
        )
    return {"type": "api-key", "key": key, "value": value}


def _validate_custom_header_auth(auth: dict[str, Any], source: str) -> dict[str, Any]:
    """Validate custom-header authentication.

    Args:
        auth: Authentication dictionary
        source: Source parameter name for error messages

    Returns:
        Validated custom-header authentication dictionary

    Raises:
        click.ClickException: If custom-header structure is invalid
    """
    headers = auth.get("headers")
    normalized_headers = _validate_headers_mapping(headers, source=source, context="custom-header authentication")
    return {"type": "custom-header", "headers": normalized_headers}


def validate_mcp_auth_structure(auth: Any, *, source: str = "--auth") -> dict[str, Any]:
    """Validate MCP authentication structure for CLI commands.

    Validates authentication objects according to the MCP schema, supporting:
    - no-auth: No authentication required
    - bearer-token: Bearer token via 'token' field or 'headers'
    - api-key: API key via 'key'/'value' fields or 'headers'
    - custom-header: Custom headers via 'headers' object

    Args:
        auth: Authentication value to validate (expected to be a dict or None)
        source: Source parameter name for error messages (default: "--auth")

    Returns:
        Validated authentication dictionary, or empty dict if auth is None

    Raises:
        click.ClickException: If auth structure is invalid or type is unsupported

    Examples:
        >>> validate_mcp_auth_structure(None)
        {}

        >>> validate_mcp_auth_structure({"type": "no-auth"})
        {'type': 'no-auth'}

        >>> validate_mcp_auth_structure({"type": "bearer-token", "token": "abc123"})
        {'type': 'bearer-token', 'token': 'abc123'}

    Schema Reference:
        See docs/reference/schemas/mcps.md - Authentication Types
        - Required field: 'type' (string, one of: no-auth, bearer-token, api-key, custom-header)
        - Additional fields depend on type
    """
    if auth is None:
        return {}

    if not isinstance(auth, dict):
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "Expected a JSON object representing MCP authentication.",
            )
        )

    raw_type = auth.get("type")
    if not isinstance(raw_type, str) or not raw_type.strip():
        raise click.ClickException(
            format_validation_error(
                f"Invalid {source} value",
                "Authentication objects must include a non-empty 'type' field.",
            )
        )

    auth_type = raw_type.strip()

    # Dispatch to type-specific validators
    if auth_type == "no-auth":
        return {"type": "no-auth"}
    if auth_type == "bearer-token":
        return _validate_bearer_token_auth(auth, source)
    if auth_type == "api-key":
        return _validate_api_key_auth(auth, source)
    if auth_type == "custom-header":
        return _validate_custom_header_auth(auth, source)

    # Unknown type
    raise click.ClickException(
        format_validation_error(
            f"Invalid {source} value",
            f"Unsupported authentication type '{auth_type}'. "
            f"Supported types: no-auth, bearer-token, api-key, custom-header",
        )
    )
