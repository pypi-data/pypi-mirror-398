"""GL AIP - Python SDK for GDP Labs AI Agent Package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from glaip_sdk._version import __version__

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from glaip_sdk.agents import Agent
    from glaip_sdk.client import Client
    from glaip_sdk.exceptions import AIPError
    from glaip_sdk.mcps import MCP
    from glaip_sdk.tools import Tool

__all__ = ["Client", "Agent", "Tool", "MCP", "AIPError", "__version__"]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "Client": ("glaip_sdk.client", "Client"),
    "Agent": ("glaip_sdk.agents", "Agent"),
    "Tool": ("glaip_sdk.tools", "Tool"),
    "MCP": ("glaip_sdk.mcps", "MCP"),
    "AIPError": ("glaip_sdk.exceptions", "AIPError"),
}


def __getattr__(name: str) -> Any:
    """Lazy attribute access for public SDK symbols to defer heavy imports."""
    if name == "__version__":
        # Import __version__ when accessed via __getattr__
        # This ensures coverage even if __version__ was removed from __dict__ for testing
        from glaip_sdk._version import __version__ as version  # noqa: PLC0415

        globals()["__version__"] = version
        return version
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        attr = getattr(module, attr_name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module 'glaip_sdk' has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return module attributes for dir()."""
    return sorted(__all__)
