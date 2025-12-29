"""CLI context helpers, config loading, and credential resolution.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

import click

from glaip_sdk.cli.config import load_config
from glaip_sdk.cli.hints import command_hint

if TYPE_CHECKING:  # pragma: no cover - import-only during type checking
    from glaip_sdk import Client


@contextmanager
def bind_slash_session_context(ctx: Any, session: Any) -> Any:
    """Temporarily attach a slash session to the Click context.

    Args:
        ctx: Click context object.
        session: SlashSession instance to bind.

    Yields:
        None - context manager for use in with statement.
    """
    ctx_obj = getattr(ctx, "obj", None)
    has_context = isinstance(ctx_obj, dict)
    previous_session = ctx_obj.get("_slash_session") if has_context else None
    if has_context:
        ctx_obj["_slash_session"] = session
    try:
        yield
    finally:
        if has_context:
            if previous_session is None:
                ctx_obj.pop("_slash_session", None)
            else:
                ctx_obj["_slash_session"] = previous_session


def restore_slash_session_context(ctx_obj: dict[str, Any], previous_session: Any | None) -> None:
    """Restore slash session context after operation.

    Args:
        ctx_obj: Click context obj dictionary.
        previous_session: Previous session to restore, or None to remove.
    """
    if previous_session is None:
        ctx_obj.pop("_slash_session", None)
    else:
        ctx_obj["_slash_session"] = previous_session


def handle_best_effort_check(
    check_func: Any,
) -> None:
    """Handle best-effort duplicate/existence checks with proper exception handling.

    Args:
        check_func: Function that performs the check and raises ClickException if duplicate found.
    """
    try:
        check_func()
    except click.ClickException:
        raise
    except Exception:
        # Non-fatal: best-effort duplicate check
        pass


def get_client(ctx: Any) -> Client:  # pragma: no cover
    """Get configured client from context and account store (ctx > account)."""
    # Import here to avoid circular import
    from glaip_sdk.cli.auth import resolve_credentials  # noqa: PLC0415

    module = importlib.import_module("glaip_sdk")
    client_class = cast("type[Client]", module.Client)
    context_config_obj = getattr(ctx, "obj", None)
    context_config = context_config_obj if isinstance(context_config_obj, Mapping) else {}

    account_name = context_config.get("account_name")
    api_url, api_key, _ = resolve_credentials(
        account_name=account_name,
        api_url=context_config.get("api_url"),
        api_key=context_config.get("api_key"),
    )

    if not api_url or not api_key:
        configure_hint = command_hint("accounts add", slash_command="login", ctx=ctx)
        actions: list[str] = []
        if configure_hint:
            actions.append(f"Run `{configure_hint}` to add an account profile")
        else:
            actions.append("add an account with 'aip accounts add'")
        raise click.ClickException(f"Missing api_url/api_key. {' or '.join(actions)}.")

    # Get timeout from context or config
    timeout = context_config.get("timeout")
    if timeout is None:
        raw_timeout = os.getenv("AIP_TIMEOUT", "0") or "0"
        try:
            timeout = float(raw_timeout) if raw_timeout != "0" else None
        except ValueError:
            timeout = None
    if timeout is None:
        # Fallback to legacy config
        file_config = load_config() or {}
        timeout = file_config.get("timeout")

    return client_class(
        api_url=api_url,
        api_key=api_key,
        timeout=float(timeout or 30.0),
    )
