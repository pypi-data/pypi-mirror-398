"""Configuration management utilities.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

_ENV_CONFIG_DIR = os.getenv("AIP_CONFIG_DIR")
# Detect pytest environment: check for pytest markers or test session
# This provides automatic test isolation even if conftest.py doesn't set AIP_CONFIG_DIR
# Note: conftest.py sets AIP_CONFIG_DIR before imports, which takes precedence
_TEST_ENV = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PYTEST_XDIST_WORKER") or os.getenv("_PYTEST_RAISE")

if _ENV_CONFIG_DIR:
    # Explicit override via environment variable (highest priority)
    # This is set by conftest.py before imports, ensuring test isolation
    CONFIG_DIR = Path(_ENV_CONFIG_DIR)
elif _TEST_ENV:
    # Isolate test runs (including xdist workers) from the real user config directory
    # Use a per-process unique temp directory to avoid conflicts in parallel test runs
    import tempfile
    import uuid

    # Create a unique temp dir per test process to avoid conflicts
    temp_base = Path(tempfile.gettempdir())
    test_config_dir = temp_base / f"aip-test-config-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    CONFIG_DIR = test_config_dir
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
else:  # pragma: no cover - default path used outside test runs
    CONFIG_DIR = Path.home() / ".aip"

CONFIG_FILE = CONFIG_DIR / "config.yaml"
_ALLOWED_KEYS = {
    "api_url",
    "api_key",
    "timeout",
    "history_default_limit",
}
# Keys that must be preserved for multi-account support
_PRESERVE_KEYS = {
    "version",
    "active_account",
    "accounts",
}


def _sanitize_config(data: dict[str, Any] | None) -> dict[str, Any]:
    """Return config filtered to allowed keys only, preserving multi-account keys."""
    if not data:
        return {}
    result: dict[str, Any] = {}
    # Preserve multi-account structure (defensively copy to avoid callers mutating source)
    for key in _PRESERVE_KEYS:
        if key in data:
            result[key] = deepcopy(data[key])
    # Add allowed legacy keys (copied to avoid side effects)
    for key in _ALLOWED_KEYS:
        if key in data:
            result[key] = deepcopy(data[key])
    return result


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            loaded = yaml.safe_load(f) or {}
            return _sanitize_config(loaded)
    except yaml.YAMLError:
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(exist_ok=True)

    sanitized = _sanitize_config(config)

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(sanitized, f, default_flow_style=False)

    # Set secure file permissions
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:  # pragma: no cover - permission errors are expected in some environments
        pass
