"""Shared helpers for client configuration wiring.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import Any

from glaip_sdk.client.base import BaseClient


def build_shared_config(client: BaseClient) -> dict[str, Any]:
    """Return the keyword arguments used to initialize sub-clients."""
    return {
        "parent_client": client,
        "api_url": client.api_url,
        "api_key": client.api_key,
        "timeout": client._timeout,
    }
