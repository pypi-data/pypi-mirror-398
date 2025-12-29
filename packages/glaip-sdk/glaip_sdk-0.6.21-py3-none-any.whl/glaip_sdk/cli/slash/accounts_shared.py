"""Shared helpers for palette `/accounts`.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
from typing import Any

from glaip_sdk.cli.masking import mask_api_key_display


def build_account_status_string(row: dict[str, Any], *, use_markup: bool = False) -> str:
    """Build status string for an account row (active/env-lock).

    When `use_markup` is True, returns Rich markup strings for Textual/Rich rendering;
    when False, returns plain text for console output.

    Example:
        build_account_status_string({"active": True, "env_lock": True}, use_markup=True)
        returns "[bold green]● active[/] · [yellow]🔒 env-lock[/]"
        use_markup=False returns "● active · 🔒 env-lock"
    """
    status_parts: list[str] = []
    if row.get("active"):
        status_parts.append("[bold green]● active[/]" if use_markup else "● active")
    if row.get("env_lock"):
        status_parts.append("[yellow]🔒 env-lock[/]" if use_markup else "🔒 env-lock")
    return " · ".join(status_parts)


def env_credentials_present(*, partial: bool = False) -> bool:
    """Return True when env credentials are present.

    Args:
        partial: When True, treat either AIP_API_URL or AIP_API_KEY as present
            (used by UIs that should lock on any env override). When False,
            require both to be non-empty (used for context display).
    """
    api_url = (os.getenv("AIP_API_URL") or "").strip()
    api_key = (os.getenv("AIP_API_KEY") or "").strip()
    if partial:
        return bool(api_url or api_key)
    return bool(api_url and api_key)


def build_account_rows(
    accounts: dict[str, dict[str, str]],
    active_account: str | None,
    env_lock: bool,
) -> list[dict[str, str | bool]]:
    """Build account rows for display from accounts dict.

    Args:
        accounts: Dictionary mapping account names to account data.
        active_account: Name of the currently active account.
        env_lock: Whether environment credentials are locking account switching.

    Returns:
        List of account row dictionaries with name, api_url, masked_key, active, and env_lock.
    """
    rows: list[dict[str, str | bool]] = []
    for name, account in sorted(accounts.items()):
        rows.append(
            {
                "name": name,
                "api_url": account.get("api_url", ""),
                "masked_key": mask_api_key_display(account.get("api_key", "")),
                "active": name == active_account,
                "env_lock": env_lock,
            }
        )
    return rows
