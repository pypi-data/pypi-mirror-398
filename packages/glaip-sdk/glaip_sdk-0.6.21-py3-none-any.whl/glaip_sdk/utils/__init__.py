"""Utility modules for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import importlib
from typing import TYPE_CHECKING

from glaip_sdk.utils.datetime_helpers import coerce_datetime, from_numeric_timestamp
from glaip_sdk.utils.display import (
    RICH_AVAILABLE,
    print_agent_created,
    print_agent_deleted,
    print_agent_output,
    print_agent_updated,
)
from glaip_sdk.utils.general import format_datetime, format_file_size, progress_bar
from glaip_sdk.utils.rendering.models import RunStats, Step
from glaip_sdk.utils.rendering.renderer.base import RichStreamRenderer
from glaip_sdk.utils.rendering.steps import StepManager
from glaip_sdk.utils.resource_refs import is_uuid, sanitize_name

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:  # pragma: no cover
    from glaip_sdk.utils.bundler import ToolBundler
    from glaip_sdk.utils.client import get_client, reset_client, set_client
    from glaip_sdk.utils.discovery import find_agent, find_tool
    from glaip_sdk.utils.import_resolver import ImportResolver
    from glaip_sdk.utils.instructions import load_instruction_from_file
    from glaip_sdk.utils.sync import update_or_create_agent, update_or_create_tool

__all__ = [
    "RICH_AVAILABLE",
    "format_datetime",
    "format_file_size",
    "is_uuid",
    "print_agent_created",
    "print_agent_deleted",
    "print_agent_output",
    "print_agent_updated",
    "progress_bar",
    "sanitize_name",
    "RichStreamRenderer",
    "RunStats",
    "Step",
    "StepManager",
    "coerce_datetime",
    "from_numeric_timestamp",
    "ToolBundler",
    "ImportResolver",
    "load_instruction_from_file",
    "find_agent",
    "find_tool",
    "update_or_create_agent",
    "update_or_create_tool",
    "get_client",
    "set_client",
    "reset_client",
]


def __getattr__(name: str) -> type:
    """Lazy import to avoid circular dependencies."""
    _client_module = "glaip_sdk.utils.client"
    _discovery_module = "glaip_sdk.utils.discovery"
    _sync_module = "glaip_sdk.utils.sync"

    lazy_imports = {
        "ToolBundler": "glaip_sdk.utils.bundler",
        "ImportResolver": "glaip_sdk.utils.import_resolver",
        "load_instruction_from_file": "glaip_sdk.utils.instructions",
        "find_agent": _discovery_module,
        "find_tool": _discovery_module,
        "update_or_create_agent": _sync_module,
        "update_or_create_tool": _sync_module,
        "get_client": _client_module,
        "set_client": _client_module,
        "reset_client": _client_module,
    }

    if name in lazy_imports:
        module = importlib.import_module(lazy_imports[name])
        return getattr(module, name)

    raise AttributeError(f"module 'glaip_sdk.utils' has no attribute '{name}'")
