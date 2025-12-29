"""Central version definition for glaip_sdk.

Resolves from installed package metadata to avoid hardcoding.
Falls back to a dev marker when running from source without installation.
"""

from __future__ import annotations

from pathlib import Path

try:
    from importlib.metadata import PackageNotFoundError, version  # Python 3.8+
except Exception:  # pragma: no cover - extremely unlikely
    PackageNotFoundError = Exception  # type: ignore

    def version(_: str) -> str:  # type: ignore
        """Fallback version function when importlib.metadata is unavailable.

        Args:
            _: Package name (ignored in fallback).

        Returns:
            Default dev version string.
        """
        return "0.0.0.dev0"


try:
    import tomllib as _toml  # Python 3.11+
except Exception:  # pragma: no cover
    try:
        import tomli as _toml  # type: ignore
    except Exception:  # pragma: no cover
        _toml = None  # type: ignore


def _try_get_installed_version() -> str | None:
    """Try to get version from installed package."""
    try:
        return version("glaip-sdk")
    except PackageNotFoundError:
        return None


def _try_get_dev_version() -> str | None:
    """Try to get version from local pyproject.toml for development."""
    if _toml is None:
        return None

    try:
        here = Path(__file__).resolve()
        root = here.parent.parent  # project root (contains pyproject.toml)
        pyproject = root / "pyproject.toml"
        if not pyproject.is_file():
            return None

        data = _toml.loads(pyproject.read_text(encoding="utf-8"))
        ver = data.get("project", {}).get("version") or data.get("tool", {}).get("poetry", {}).get("version")
        if isinstance(ver, str) and ver:
            return ver
    except Exception:
        pass
    return None


def _get_version() -> str:
    """Return the SDK version from install metadata or fallbacks."""
    # Try installed version first
    installed_version = _try_get_installed_version()
    if installed_version:
        return installed_version

    # Try development version
    dev_version = _try_get_dev_version()
    if dev_version:
        return dev_version

    return "0.0.0.dev0"


__version__ = _get_version()
