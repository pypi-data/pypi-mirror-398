"""Shared helpers for configuration/account flows."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.text import Text
from glaip_sdk.branding import PRIMARY, SUCCESS_STYLE, WARNING_STYLE, AIPBranding
from glaip_sdk.cli.utils import sdk_version

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from glaip_sdk import Client


def render_branding_header(console: Console, rule_text: str) -> None:
    """Render the standard CLI branding header with a custom rule text."""
    branding = AIPBranding.create_from_sdk(sdk_version=sdk_version(), package_name="glaip-sdk")
    heading = "[bold]>_ GDP Labs AI Agents Package (AIP CLI)[/bold]"
    console.print(heading)
    console.print()
    console.print(branding.get_welcome_banner())
    console.rule(rule_text, style=PRIMARY)


def check_connection(
    api_url: str,
    api_key: str,
    console: Console,
    *,
    abort_on_error: bool = False,
    extra_hint: str | None = None,
) -> bool:
    """Test connectivity and report results.

    Returns True on success, False on handled failures. Raises click.Abort when
    abort_on_error is True and a fatal error occurs.
    """
    console.print("\n🔌 Testing connection...")
    client: Client | None = None
    try:
        # Import lazily to avoid pulling in SDK dependencies during CLI startup.
        from glaip_sdk import Client  # noqa: PLC0415

        client = Client(api_url=api_url, api_key=api_key)
        try:
            agents = client.list_agents()
            console.print(Text(f"✅ Connection successful! Found {len(agents)} agents", style=SUCCESS_STYLE))
            return True
        except Exception as exc:  # pragma: no cover - API failures depend on network
            console.print(Text(f"⚠️  Connection established but API call failed: {exc}", style=WARNING_STYLE))
            console.print("   You may need to check your API permissions or network access")
            if extra_hint:
                console.print(extra_hint)
            if abort_on_error:
                raise click.Abort() from exc
            return False
    except Exception as exc:
        console.print(Text(f"❌ Connection failed: {exc}"))
        console.print("   Please check your API URL and key")
        if extra_hint:
            console.print(extra_hint)
        if abort_on_error:
            raise click.Abort() from exc
        return False
    finally:
        if client is not None:
            client.close()


def check_connection_with_reason(
    api_url: str,
    api_key: str,
    *,
    abort_on_error: bool = False,
) -> tuple[bool, str]:
    """Test connectivity and return structured reason."""
    client: Client | None = None
    try:
        # Import lazily to avoid pulling in SDK dependencies during CLI startup.
        from glaip_sdk import Client  # noqa: PLC0415

        client = Client(api_url=api_url, api_key=api_key)
        try:
            client.list_agents()
            return True, ""
        except Exception as exc:  # pragma: no cover - API failures depend on network
            if abort_on_error:
                raise click.Abort() from exc
            return False, f"api_failed: {exc}"
    except Exception as exc:
        # Log unexpected exceptions in debug while keeping CLI-friendly messaging
        logging.getLogger(__name__).debug("Unexpected connection error", exc_info=exc)
        if abort_on_error:
            raise click.Abort() from exc
        return False, f"connection_failed: {exc}"
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
