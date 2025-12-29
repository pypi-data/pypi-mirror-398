"""Utility helpers for checking and displaying SDK update notifications.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import Any, Literal

import click
import httpx
from packaging.version import InvalidVersion, Version
from rich import box
from rich.console import Console

from glaip_sdk.branding import (
    ACCENT_STYLE,
    ERROR_STYLE,
    INFO_STYLE,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.commands.update import (
    PACKAGE_NAME,
    _build_command_parts,
    _build_manual_upgrade_command,
    _is_uv_managed_environment,
    update_command,
)
from glaip_sdk.cli.constants import UPDATE_CHECK_ENABLED
from glaip_sdk.cli.hints import format_command_hint
from glaip_sdk.cli.utils import command_hint
from glaip_sdk.rich_components import AIPPanel

FetchLatestVersion = Callable[[], str | None]

PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"
DEFAULT_TIMEOUT = 1.5  # seconds

_LOGGER = logging.getLogger(__name__)


def _parse_version(value: str) -> Version | None:
    """Parse a version string into a `Version`, returning None on failure."""
    try:
        return Version(value)
    except InvalidVersion:
        return None


def _fetch_latest_version(package_name: str) -> str | None:
    """Fetch the latest published version from PyPI."""
    url = PYPI_JSON_URL.format(package=package_name)
    timeout = httpx.Timeout(DEFAULT_TIMEOUT)

    try:
        with _suppress_library_logging():
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
    except httpx.HTTPError as exc:
        _LOGGER.debug("Update check failed: %s", exc, exc_info=True)
        return None
    except ValueError as exc:
        _LOGGER.debug("Invalid JSON while checking for updates: %s", exc, exc_info=True)
        return None

    info = payload.get("info") if isinstance(payload, dict) else None
    latest_version = info.get("version") if isinstance(info, dict) else None
    if isinstance(latest_version, str) and latest_version.strip():
        return latest_version.strip()
    return None


def _should_check_for_updates() -> bool:
    """Return False when update checks are explicitly disabled."""
    # Check module attribute first (for test overrides), then fall back to imported constant
    module = sys.modules.get(__name__)
    if module and hasattr(module, "UPDATE_CHECK_ENABLED"):
        return getattr(module, "UPDATE_CHECK_ENABLED")
    return UPDATE_CHECK_ENABLED


def _build_update_panel(
    current_version: str,
    latest_version: str,
    command_text: str,
    *,
    show_command_hint: bool,
) -> AIPPanel:
    """Create a Rich panel that prompts the user to update."""
    command_markup = format_command_hint(command_text) or command_text
    message = (
        f"[{WARNING_STYLE}]✨ Update available![/] "
        f"{current_version} → {latest_version}\n\n"
        "See the latest release notes:\n"
        f"https://pypi.org/project/glaip-sdk/{latest_version}/"
    )
    if show_command_hint:
        message += f"\n\n[{ACCENT_STYLE}]Run[/] {command_markup} to install."
    return AIPPanel(
        message,
        title=f"[{SUCCESS_STYLE}]AIP SDK Update[/]",
        box=box.ROUNDED,
        padding=(0, 3),
        expand=False,
    )


def maybe_notify_update(
    current_version: str,
    *,
    package_name: str = "glaip-sdk",
    console: Console | None = None,
    fetch_latest_version: FetchLatestVersion | None = None,
    ctx: Any | None = None,
    slash_command: str | None = None,
    style: Literal["panel", "inline"] = "panel",
) -> None:
    """Check PyPI for a newer version and display a prompt if one exists."""
    if not _should_check_for_updates():
        return

    fetcher = fetch_latest_version or (lambda: _fetch_latest_version(package_name))
    latest_version = fetcher()
    if not latest_version:
        return

    current = _parse_version(current_version)
    latest = _parse_version(latest_version)
    if current is None or latest is None or latest <= current:
        return

    command_text = command_hint("update", slash_command=slash_command, ctx=ctx)
    if command_text is None:
        return

    active_console = console or Console()
    should_prompt = _should_prompt_for_action(active_console, ctx)

    if style == "inline":
        if should_prompt:
            message = (
                f"[{WARNING_STYLE}]✨ Update[/] "
                f"{current_version} → {latest_version} "
                "- choose Update now or Skip to continue."
            )
            active_console.print(message)
            _handle_update_decision(active_console, ctx)
            return

        command_markup = format_command_hint(command_text) or command_text
        active_console.print(f"[{WARNING_STYLE}]✨ Update[/] {current_version} → {latest_version} - {command_markup}")
        return

    panel = _build_update_panel(
        current_version,
        latest_version,
        command_text,
        show_command_hint=not should_prompt,
    )
    active_console.print(panel)
    if should_prompt:
        _handle_update_decision(active_console, ctx)


def _handle_update_decision(console: Console, ctx: Any) -> None:
    """Prompt the user to take action on the available update."""
    choice = _prompt_update_decision(console)
    if choice == "skip":
        return

    _run_update_command(console, ctx)


def _should_prompt_for_action(console: Console, ctx: Any | None) -> bool:
    """Return True when we can safely block for interactive input."""
    if ctx is None or not hasattr(ctx, "invoke"):
        return False

    is_interactive = getattr(console, "is_interactive", False)
    if not isinstance(is_interactive, bool) or not is_interactive:
        return False

    is_terminal = getattr(console, "is_terminal", False)
    if not isinstance(is_terminal, bool) or not is_terminal:
        return False

    input_method = getattr(console, "input", None)
    return callable(input_method)


def _prompt_update_decision(console: Console) -> Literal["update", "skip"]:
    """Ask the user to choose between updating now or skipping."""
    console.print(
        f"[{ACCENT_STYLE}]Select an option to continue:[/]\n"
        f"  [{SUCCESS_STYLE}]1.[/] Update now\n"
        f"  [{WARNING_STYLE}]2.[/] Skip\n"
    )
    console.print("[dim]Press Enter after typing your choice.[/]")

    while True:
        try:
            response = console.input("Choice [1/2]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{WARNING_STYLE}]Update skipped.[/]")
            return "skip"

        if response in {"1", "update", "u"}:
            return "update"
        if response in {"2", "skip", "s"}:
            return "skip"

        console.print(f"[{ERROR_STYLE}]Please enter 1 to update now or 2 to skip.[/]")


def _get_manual_upgrade_command(is_uv: bool) -> str:
    """Get the manual upgrade command for the given environment type.

    Args:
        is_uv: True if running in uv tool environment, False for pip environment.

    Returns:
        Manual upgrade command string.
    """
    try:
        return _build_manual_upgrade_command(include_prerelease=False, is_uv=is_uv)
    except Exception:
        # Fallback: rebuild from shared command parts to avoid hardcoded strings.
        try:
            command_parts, _ = _build_command_parts(
                package_name=PACKAGE_NAME,
                is_uv=is_uv,
                force_reinstall=False,
                include_prerelease=False,
            )
        except Exception:
            command_parts = (
                ["uv", "tool", "install", "--upgrade", PACKAGE_NAME]
                if is_uv
                else ["pip", "install", "--upgrade", PACKAGE_NAME]
            )
        return " ".join(command_parts)


def _show_proactive_uv_guidance(console: Console, is_uv: bool) -> None:
    """Show proactive guidance for uv environments before update attempt.

    Args:
        console: Rich console for output.
        is_uv: True if running in uv tool environment.
    """
    if not is_uv:
        return

    manual_cmd = _get_manual_upgrade_command(is_uv=True)
    console.print(
        f"[{INFO_STYLE}]💡 Detected uv tool environment.[/] "
        f"If automatic update fails, run: [{ACCENT_STYLE}]{manual_cmd}[/]"
    )


def _show_error_guidance(console: Console, is_uv: bool) -> None:
    """Show error guidance with correct manual command based on environment.

    Args:
        console: Rich console for output.
        is_uv: True if running in uv tool environment.
    """
    try:
        manual_cmd = _get_manual_upgrade_command(is_uv=is_uv)
        console.print(f"[{INFO_STYLE}]💡 Tip:[/] Run this command manually:\n   [{ACCENT_STYLE}]{manual_cmd}[/]")
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.debug("Failed to render update tip: %s", exc, exc_info=True)


def _run_update_command(console: Console, ctx: Any) -> None:
    """Invoke the built-in update command and surface any errors."""
    # Detect uv environment proactively before attempting update
    is_uv = _is_uv_managed_environment()

    # Provide proactive guidance for uv environments
    # This helps users on older versions (e.g., 0.6.19) that don't have uv detection
    # in their update command
    _show_proactive_uv_guidance(console, is_uv)

    try:
        ctx.invoke(update_command)
    except click.ClickException as exc:
        exc.show()
        console.print(f"[{ERROR_STYLE}]Update command exited with an error.[/]")
        _show_error_guidance(console, is_uv)
    except click.Abort:
        console.print(f"[{WARNING_STYLE}]Update aborted by user.[/]")
    except Exception as exc:  # pragma: no cover - defensive guard
        console.print(f"[{ERROR_STYLE}]Unexpected error while running update: {exc}[/]")
        # Also provide guidance for unexpected errors in uv environments
        if is_uv:
            manual_cmd = _get_manual_upgrade_command(is_uv=True)
            console.print(f"[{INFO_STYLE}]💡 Tip:[/] Try running manually:\n   [{ACCENT_STYLE}]{manual_cmd}[/]")
    else:
        _refresh_installed_version(console, ctx)


@contextmanager
def _suppress_library_logging(
    logger_names: Iterable[str] | None = None, *, level: int = logging.WARNING
) -> Iterator[None]:
    """Temporarily raise log level for selected libraries during update checks."""
    names = tuple(logger_names) if logger_names is not None else ("httpx",)
    captured: list[tuple[logging.Logger, int]] = []
    try:
        for name in names:
            logger = logging.getLogger(name)
            captured.append((logger, logger.level))
            logger.setLevel(level)
        yield
    finally:
        for logger, previous_level in captured:
            logger.setLevel(previous_level)


def _refresh_installed_version(console: Console, ctx: Any) -> None:
    """Reload runtime metadata after an in-process upgrade."""
    new_version: str | None = None
    branding_module: Any | None = None

    try:
        version_module = importlib.reload(importlib.import_module("glaip_sdk._version"))
        new_version = getattr(version_module, "__version__", None)
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.debug("Failed to reload glaip_sdk._version: %s", exc, exc_info=True)

    try:
        branding_module = importlib.reload(importlib.import_module("glaip_sdk.branding"))
        if new_version:
            branding_module.SDK_VERSION = new_version
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.debug("Failed to update branding metadata: %s", exc, exc_info=True)
        branding_module = None

    session = _get_slash_session(ctx)
    if session and hasattr(session, "refresh_branding"):
        try:
            branding_cls = getattr(branding_module, "AIPBranding", None) if branding_module else None
            session.refresh_branding(new_version, branding_cls=branding_cls)
            return
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.debug("Failed to refresh active slash session: %s", exc, exc_info=True)

    if new_version:
        console.print(f"[{SUCCESS_STYLE}]CLI now running glaip-sdk {new_version}.[/]")


def _get_slash_session(ctx: Any) -> Any | None:
    """Return active slash session from the Click context if present."""
    ctx_obj = getattr(ctx, "obj", None)
    if isinstance(ctx_obj, dict):
        return ctx_obj.get("_slash_session")
    return None


__all__ = ["maybe_notify_update"]
