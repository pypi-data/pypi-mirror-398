"""Authentication export helpers for MCP CLI commands and credential resolution.

This module provides utilities for preparing authentication data for export,
including interactive secret capture and placeholder generation.

It also provides credential resolution for the AIP CLI, supporting multiple
account profiles and environment variable overrides.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os
from collections.abc import Callable, Iterable, Mapping
from typing import Any

import click
from rich.console import Console

from glaip_sdk.branding import HINT_PREFIX_STYLE, WARNING_STYLE
from glaip_sdk.cli.account_store import AccountNotFoundError, AccountStoreError, get_account_store
from glaip_sdk.cli.hints import format_command_hint
from glaip_sdk.cli.utils import command_hint


def prepare_authentication_export(
    auth: dict[str, Any] | None,
    *,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any] | None:
    """Prepare authentication data for export with secret handling.

    This function processes authentication objects from MCP resources and prepares
    them for export. It handles secret capture (interactive or placeholder mode),
    reconstructs proper authentication structures from helper metadata, and ensures
    helper metadata doesn't leak into the final export.

    Args:
        auth: Authentication dictionary from an MCP resource. May contain helper
            metadata like ``header_keys`` that should be consumed and removed.
        prompt_for_secrets: If True, interactively prompt for missing secrets.
            If False, use ``placeholder`` automatically.
        placeholder: Placeholder text to use for missing secrets when not prompting.
        console: Rich ``Console`` instance for user interaction and warnings.

    Returns:
        A prepared authentication dictionary ready for export, or ``None`` if
        ``auth`` is ``None``.

    Notes:
        - Helper metadata (for example, ``header_keys``) is consumed to rebuild
          structures but never appears in the final output.
        - When ``prompt_for_secrets`` is False and stdin is not a TTY, a warning is
          logged.
        - Empty user input during prompts defaults to the placeholder value.
    """
    if auth is None:
        return None

    auth_type = auth.get("type")

    # Handle no-auth case
    if auth_type == "no-auth":
        return {"type": "no-auth"}

    # Handle bearer-token authentication
    if auth_type == "bearer-token":
        return _prepare_bearer_token_auth(auth, prompt_for_secrets, placeholder, console)

    # Handle api-key authentication
    if auth_type == "api-key":
        return _prepare_api_key_auth(auth, prompt_for_secrets, placeholder, console)

    # Handle custom-header authentication
    if auth_type == "custom-header":
        return _prepare_custom_header_auth(auth, prompt_for_secrets, placeholder, console)

    # Unknown auth type - return as-is but strip helper metadata
    result = auth.copy()
    result.pop("header_keys", None)
    return result


def _get_token_value(prompt_for_secrets: bool, placeholder: str, console: Console) -> str:
    """Get bearer token value either by prompting or using a placeholder.

    Args:
        prompt_for_secrets: If True, prompt for the token value.
        placeholder: Placeholder to use when not prompting or when input is empty.
        console: Rich ``Console`` used to display informational messages.

    Returns:
        The token string, either provided by the user or the placeholder.
    """
    if prompt_for_secrets:
        return _prompt_secret_with_placeholder(
            console,
            warning_message="Bearer token is missing or redacted. Please provide the token.",
            prompt_message="Bearer token (leave blank for placeholder)",
            placeholder=placeholder,
            tip_cli_command="configure",
            tip_slash_command="configure",
        )

    if not click.get_text_stream("stdin").isatty():
        console.print(f"[{WARNING_STYLE}]⚠️  Non-interactive mode: using placeholder for bearer token[/]")
    return placeholder


def _normalize_header_keys(
    header_keys: Iterable[str] | str | None,
    *,
    default: Iterable[str] | None = None,
) -> list[str]:
    """Normalize header_keys to a list, handling strings and None safely."""
    if header_keys is None:
        return list(default or [])
    if isinstance(header_keys, str):
        return [header_keys] if header_keys else list(default or [])
    try:
        return list(header_keys)
    except TypeError:
        raise click.ClickException(
            f"Invalid header_keys type: expected string or iterable, got {type(header_keys).__name__}"
        ) from None


def _build_bearer_headers(auth: dict[str, Any], token_value: str) -> dict[str, str]:
    """Build headers for bearer token authentication.

    Args:
        auth: Original authentication dictionary which may include ``header_keys``.
        token_value: The token value to embed into the headers.

    Returns:
        A dictionary of HTTP headers including the Authorization header when
        applicable.
    """
    default_header_keys = ["Authorization"]
    has_header_keys = "header_keys" in auth
    header_keys_raw = auth.get("header_keys") if has_header_keys else default_header_keys
    header_keys = _normalize_header_keys(header_keys_raw, default=None if has_header_keys else default_header_keys)
    headers = {}
    for key in header_keys:
        # Prepend "Bearer " if this is Authorization header
        if key.lower() == "authorization":
            headers[key] = f"Bearer {token_value}"
        else:
            headers[key] = token_value
    return headers


def _prepare_bearer_token_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare bearer-token authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for secrets.
        placeholder: Placeholder value for secrets.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``bearer-token`` authentication dictionary.
    """
    # Check if token exists and is not masked
    token = auth.get("token")
    has_valid_token = token and token not in (None, "", "***", "REDACTED")

    # If we have a valid token, use it
    if has_valid_token:
        return {"type": "bearer-token", "token": token}

    # Get token value (prompt or placeholder)
    token_value = _get_token_value(prompt_for_secrets, placeholder, console)

    # Check if original had headers structure
    if "headers" in auth or "header_keys" in auth:
        headers = _build_bearer_headers(auth, token_value)
        return {"type": "bearer-token", "headers": headers}

    # Use token field structure
    return {"type": "bearer-token", "token": token_value}


def _extract_api_key_name(auth: dict[str, Any]) -> str | None:
    """Extract the API key name from an authentication dictionary.

    Args:
        auth: Authentication dictionary that may contain ``key`` or ``header_keys``.

    Returns:
        The API key name if available, otherwise ``None``.
    """
    key_name = auth.get("key")
    if not key_name and "header_keys" in auth:
        header_keys = _normalize_header_keys(auth["header_keys"])
        if header_keys:
            key_name = header_keys[0]
    return key_name


def _get_api_key_value(
    key_name: str | None,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> str:
    """Get API key value either by prompting or using a placeholder.

    Args:
        key_name: The name of the API key; used in prompt messages.
        prompt_for_secrets: If True, prompt for the API key value.
        placeholder: Placeholder to use when not prompting or when input is empty.
        console: Rich ``Console`` used to display informational messages.

    Returns:
        The API key value, either provided by the user or the placeholder.
    """
    if prompt_for_secrets:
        return _prompt_secret_with_placeholder(
            console,
            warning_message=f"API key value for '{key_name}' is missing or redacted.",
            prompt_message=f"API key value for '{key_name}' (leave blank for placeholder)",
            placeholder=placeholder,
            tip_cli_command="configure api-key",
            tip_slash_command="configure",
        )

    if not click.get_text_stream("stdin").isatty():
        console.print(f"[{WARNING_STYLE}]⚠️  Non-interactive mode: using placeholder for API key '{key_name}'[/]")
    return placeholder


def _build_api_key_headers(auth: dict[str, Any], key_name: str | None, key_value: str) -> dict[str, str]:
    """Build headers for API key authentication.

    Args:
        auth: Original authentication dictionary which may include ``header_keys``.
        key_name: The header key name if present.
        key_value: The API key value to populate.

    Returns:
        A dictionary of HTTP headers for API key authentication.
    """
    default_header_keys = [key_name] if key_name else []
    has_header_keys = "header_keys" in auth
    header_keys_raw = auth.get("header_keys") if has_header_keys else default_header_keys
    header_keys_list = _normalize_header_keys(header_keys_raw, default=None if has_header_keys else default_header_keys)
    filtered_keys = [k for k in header_keys_list if k]
    return dict.fromkeys(filtered_keys, key_value)


def _prepare_api_key_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare api-key authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for secrets.
        placeholder: Placeholder value for secrets.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``api-key`` authentication dictionary.
    """
    # Extract key name and value
    key_name = _extract_api_key_name(auth)
    key_value = auth.get("value")

    # Check if we have a valid value
    has_valid_value = key_value and key_value not in (None, "", "***", "REDACTED")

    # Capture or use placeholder for value
    if not has_valid_value:
        key_value = _get_api_key_value(key_name, prompt_for_secrets, placeholder, console)

    # Check if original had headers structure
    if "headers" in auth or "header_keys" in auth:
        headers = _build_api_key_headers(auth, key_name, key_value)
        return {"type": "api-key", "headers": headers}

    # Use key/value field structure
    return {"type": "api-key", "key": key_name, "value": key_value}


def _prepare_custom_header_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare custom-header authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for header values.
        placeholder: Placeholder value when not prompting or input is empty.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``custom-header`` authentication dictionary.
    """
    existing_headers: dict[str, Any] = auth.get("headers", {})
    header_names = _extract_header_names(existing_headers, auth.get("header_keys", []))

    if not header_names:
        return {"type": "custom-header", "headers": {}}

    headers = _build_custom_headers(
        existing_headers=existing_headers,
        header_names=header_names,
        prompt_for_secrets=prompt_for_secrets,
        placeholder=placeholder,
        console=console,
    )

    return {"type": "custom-header", "headers": headers}


def _extract_header_names(existing_headers: Mapping[str, Any] | None, header_keys: Iterable[str] | None) -> list[str]:
    """Extract the list of header names to process.

    Args:
        existing_headers: Existing headers mapping from the auth object.
        header_keys: Optional helper metadata listing header names.

    Returns:
        A list of header names to process.
    """
    if existing_headers:
        return list(existing_headers.keys())
    return _normalize_header_keys(header_keys)


def _is_valid_secret(value: Any) -> bool:
    """Determine whether a secret value is present and not masked.

    Args:
        value: The value to test.

    Returns:
        True if the value is non-empty and not one of the masked placeholders.
    """
    return bool(value) and value not in (None, "", "***", "REDACTED")


def _prompt_or_placeholder(
    name: str,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> str:
    """Prompt for a header value or return the placeholder when not prompting.

    Args:
        name: Header name used in prompt messages.
        prompt_for_secrets: If True, prompt for the value interactively.
        placeholder: Placeholder value used when not prompting or empty input.
        console: Rich ``Console`` instance for user-facing messages.

    Returns:
        The provided value or the placeholder.
    """
    if prompt_for_secrets:
        return _prompt_secret_with_placeholder(
            console,
            warning_message=f"Header '{name}' is missing or redacted.",
            prompt_message=f"Value for header '{name}' (leave blank for placeholder)",
            placeholder=placeholder,
            tip_cli_command="configure",
            tip_slash_command="configure",
        )

    if not click.get_text_stream("stdin").isatty():
        console.print(f"[{WARNING_STYLE}]⚠️  Non-interactive mode: using placeholder for header '{name}'[/]")
    return placeholder


def _build_custom_headers(
    *,
    existing_headers: Mapping[str, Any],
    header_names: Iterable[str],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, str]:
    """Build a headers mapping for custom-header authentication.

    Args:
        existing_headers: Existing headers mapping from the auth object.
        header_names: Header names to process.
        prompt_for_secrets: Whether to prompt for missing values.
        placeholder: Placeholder to use for missing or masked values.
        console: Rich ``Console`` used for prompt/warning messages.

    Returns:
        A dictionary mapping header names to resolved values.
    """
    headers: dict[str, str] = {}
    for name in header_names:
        existing_value = existing_headers.get(name)
        if _is_valid_secret(existing_value):
            headers[name] = str(existing_value)
            continue

        headers[name] = _prompt_or_placeholder(
            name=name,
            prompt_for_secrets=prompt_for_secrets,
            placeholder=placeholder,
            console=console,
        )

    return headers


def _prompt_secret_with_placeholder(
    console: Console,
    *,
    warning_message: str,
    prompt_message: str,
    placeholder: str,
    tip_cli_command: str | None = "configure",
    tip_slash_command: str | None = "configure",
    mask_input: bool = True,
    retry_limit: int = 1,
) -> str:
    """Prompt for a secret value with masking, retries, and placeholder fallback.

    Args:
        console: Rich console used to render messaging.
        warning_message: Message shown before prompting (rendered with warning style).
        prompt_message: The message passed to :func:`click.prompt`.
        placeholder: Placeholder value inserted when the user skips input.
        tip_cli_command: CLI command (without ``aip`` prefix) used to build hints.
        tip_slash_command: Slash command counterpart used in hints.
        mask_input: Whether to hide user input while typing.
        retry_limit: Number of additional attempts when the user submits empty input.

    Returns:
        The value entered by the user or the provided placeholder.
    """
    console.print(f"[{WARNING_STYLE}]{warning_message}[/]")

    tip = command_hint(tip_cli_command, tip_slash_command)
    if tip:
        console.print(
            f"[{HINT_PREFIX_STYLE}]Tip:[/] use {format_command_hint(tip) or tip} later "
            "if you want to update these credentials."
        )

    attempts = 0
    while attempts <= retry_limit:  # pragma: no cover
        response = click.prompt(
            prompt_message,
            default="",
            show_default=False,
            hide_input=mask_input,
        )
        value = response.strip()
        if value:
            return value

        if attempts < retry_limit:
            console.print(
                f"[{WARNING_STYLE}]No value entered. Enter a value or press Enter again to use the placeholder.[/]"
            )
            attempts += 1
            continue

        console.print("[dim]Using placeholder value.[/dim]")
        return placeholder

    # This line is unreachable as the loop always returns
    # return placeholder


# ----------------------------- Credential Resolution ----------------------------- #


def resolve_api_url_from_context(
    ctx: Any,
    *,
    get_api_url: Callable[[Any], str | None] | None = None,
    get_account_name: Callable[[Any], str | None] | None = None,
) -> str | None:
    """Resolve API URL from context using account store (CLI/palette ignores env creds).

    Helper function to extract API URL from various context formats.
    Used by transcript capture and slash session to avoid code duplication.

    Args:
        ctx: Context object (can be dict, click.Context, or any object with attributes).
        get_api_url: Optional function to extract api_url from context.
            If None, tries ctx.obj.get("api_url") or ctx.get("api_url").
        get_account_name: Optional function to extract account_name from context.
            If None, tries ctx.obj.get("account_name") or ctx.get("account_name").

    Returns:
        Resolved API URL or None.
    """
    api_url = None
    account_name = None

    if get_api_url:
        api_url = get_api_url(ctx)
    elif isinstance(ctx, dict):
        api_url = ctx.get("api_url")
    elif hasattr(ctx, "obj") and isinstance(ctx.obj, dict):
        api_url = ctx.obj.get("api_url")

    if get_account_name:
        account_name = get_account_name(ctx)
    elif isinstance(ctx, dict):
        account_name = ctx.get("account_name")
    elif hasattr(ctx, "obj") and isinstance(ctx.obj, dict):
        account_name = ctx.obj.get("account_name")

    resolved_url, _, _ = resolve_credentials(
        account_name=account_name,
        api_url=api_url,
        api_key=None,
        ignore_env_creds=True,
    )
    return resolved_url


def _resolve_account_name(account_name: str | None) -> str | None:
    """Resolve account name from parameter (env var removed for CLI/palette)."""
    return account_name


def _validate_account_exists(account_name: str | None, store: Any) -> None:
    """Validate that the specified account exists.

    Raises:
        AccountNotFoundError: If account_name is specified but account doesn't exist.
    """
    if account_name:
        account = store.get_account(account_name)
        if not account:
            raise AccountNotFoundError(
                f"Account '{account_name}' not found. Run 'aip accounts list' to see available accounts."
            )


def _merge_credentials(
    api_url: str | None,
    api_key: str | None,
    profile_url: str | None,
    profile_key: str | None,
    ignore_env_creds: bool,
) -> tuple[str | None, str | None]:
    """Merge credentials from multiple sources.

    Args:
        api_url: Explicit API URL override.
        api_key: Explicit API key override.
        profile_url: Profile API URL.
        profile_key: Profile API key.
        ignore_env_creds: If True, ignore env vars.

    Returns:
        Tuple of (final_url, final_key).
    """
    if not ignore_env_creds:
        env_url = os.getenv("AIP_API_URL")
        env_key = os.getenv("AIP_API_KEY")
        final_url = api_url or env_url or profile_url
        final_key = api_key or env_key or profile_key
    else:
        final_url = api_url or profile_url
        final_key = api_key or profile_key
    return final_url, final_key


def _determine_source(
    api_url: str | None,
    api_key: str | None,
    account_name: str | None,
    store: Any,
) -> str:
    """Determine the source of credentials.

    Returns:
        Source string describing where credentials came from.
    """
    if api_url or api_key:
        return "flag"
    if account_name:
        return f"account:{account_name}"
    active = store.get_active_account()
    return f"active_profile:{active}" if active else "none"


_ENV_WARNING_EMITTED = False


def _maybe_warn_env_creds_ignored(ignore_env_creds: bool) -> None:
    """Emit a one-time warning when env credentials are present but ignored."""
    global _ENV_WARNING_EMITTED

    if _ENV_WARNING_EMITTED or not ignore_env_creds:
        return

    if os.getenv("AIP_API_URL") or os.getenv("AIP_API_KEY"):
        click.echo(
            "Warning: CLI ignores AIP_API_URL/AIP_API_KEY; use account profiles via 'aip accounts add/use'. "
            "Python SDK callers can opt in with ignore_env_creds=False.",
            err=True,
        )
        _ENV_WARNING_EMITTED = True


def resolve_credentials(
    account_name: str | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
    *,
    ignore_env_creds: bool = True,
) -> tuple[str | None, str | None, str]:
    """Resolve credentials from multiple sources with precedence.

    For CLI/palette: ignores raw credential env vars (AIP_API_URL/AIP_API_KEY),
    and only uses explicit account selection (no AIP_ACCOUNT env). Python SDK can use
    ignore_env_creds=False to honor env vars if needed.

    Precedence order (CLI/palette):
    1. Explicit parameters (api_url, api_key)
    2. Account profile (from account_name or active_account)

    Args:
        account_name: Account name to use, or None for active account.
        api_url: Explicit API URL override.
        api_key: Explicit API key override.
        ignore_env_creds: If True (default), ignore AIP_API_URL/AIP_API_KEY env vars.

    Returns:
        Tuple of (api_url, api_key, source) where source describes where
        credentials came from (e.g., "flag", "active_profile", "account:name").

    Raises:
        click.ClickException: If a requested account does not exist.
    """
    _maybe_warn_env_creds_ignored(ignore_env_creds)

    # 1. Explicit parameters take highest precedence
    if api_url and api_key:
        return api_url, api_key, "flag"

    # 2. Account profile resolution
    account_name = _resolve_account_name(account_name)
    store = get_account_store()
    try:
        _validate_account_exists(account_name, store)
    except AccountNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        profile_url, profile_key = store.get_credentials(account_name)
    except AccountStoreError:
        profile_url, profile_key = None, None

    final_url, final_key = _merge_credentials(api_url, api_key, profile_url, profile_key, ignore_env_creds)
    source = _determine_source(api_url, api_key, account_name, store)

    return final_url, final_key, source


def get_credentials(
    account_name: str | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
) -> tuple[str | None, str | None]:
    """Get credentials for CLI commands (backward compatible wrapper).

    This function maintains backward compatibility with existing code that
    expects (url, key) tuple. For source information, use resolve_credentials.

    Args:
        account_name: Account name to use, or None for active account.
        api_url: Explicit API URL override.
        api_key: Explicit API key override.

    Returns:
        Tuple of (api_url, api_key).
    """
    url, key, _ = resolve_credentials(account_name, api_url, api_key)
    return url, key
