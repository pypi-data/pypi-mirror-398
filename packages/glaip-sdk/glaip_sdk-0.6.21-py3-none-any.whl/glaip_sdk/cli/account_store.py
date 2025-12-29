"""Account store for managing multiple credential profiles.

This module provides the AccountStore class for managing multiple account profiles
with API URL and API key pairs, supporting migration from legacy single-profile configs.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    import fcntl  # type: ignore
except ImportError:  # pragma: no cover - platform-specific
    fcntl = None  # type: ignore[assignment]

import yaml

from glaip_sdk.cli.config import CONFIG_FILE

# POSIX-only locking; Windows falls back to no-op so CLI can still import/run.
LOCKING_SUPPORTED: bool = fcntl is not None

# Account name validation: alphanumeric plus "-" or "_", 1-32 chars
ACCOUNT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
CONFIG_VERSION = 2
# Toggle to stop mirroring top-level api_url/api_key after deprecation window
MIRROR_TOP_LEVEL_CREDS = True


class AccountStoreError(Exception):
    """Base exception for account store operations."""


class InvalidAccountNameError(AccountStoreError):
    """Raised when an account name doesn't match validation rules."""


class AccountNotFoundError(AccountStoreError):
    """Raised when a requested account doesn't exist."""


class AccountStore:
    """Manages multiple account profiles in versioned config.yaml.

    Supports migration from legacy single-profile configs and provides
    thread-safe operations with file locking.
    """

    def __init__(self, config_file: Path | None = None):
        """Initialize the account store.

        Args:
            config_file: Optional path to config file (for testing).
                Defaults to ~/.aip/config.yaml.
        """
        self.config_file = config_file or CONFIG_FILE
        self.config_dir = self.config_file.parent
        self.lock_file = self.config_file.with_name(f"{self.config_file.name}.lock")

    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self, file_handle: Any) -> None:
        """Acquire an exclusive lock on the config file.

        Args:
            file_handle: File handle to lock.

        Raises:
            AccountStoreError: If lock cannot be acquired.
        """
        if not LOCKING_SUPPORTED:
            return

        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        except (OSError, AttributeError) as e:
            raise AccountStoreError(f"Failed to acquire lock on config file: {e}") from e

    def _release_lock(self, file_handle: Any) -> None:
        """Release the lock on the config file.

        Args:
            file_handle: File handle to unlock.
        """
        if not LOCKING_SUPPORTED:
            return

        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except (OSError, AttributeError):
            # Lock release failures are non-fatal
            pass

    def _load_raw_config(self) -> dict[str, Any]:
        """Load raw config file without migration or validation."""
        if not self.config_file.exists():
            return {}

        self._ensure_config_dir()
        lock_handle = None
        lock_acquired = False
        try:
            lock_handle = open(self.lock_file, "a+", encoding="utf-8")
            self._acquire_lock(lock_handle)
            lock_acquired = True

            with open(self.config_file, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise AccountStoreError(f"Failed to parse config file: {e}") from e
        finally:
            if lock_handle:
                if lock_acquired:
                    self._release_lock(lock_handle)
                lock_handle.close()

    def _save_config(self, config: dict[str, Any]) -> None:
        """Atomically save config file with proper permissions.

        Also mirrors active profile credentials to top-level api_url/api_key
        for backward compatibility with older CLIs during deprecation window.

        Args:
            config: Configuration dictionary to save.
        """
        self._ensure_config_dir()

        # Mirror active profile to top-level for backward compatibility
        if MIRROR_TOP_LEVEL_CREDS:
            active_account = config.get("active_account")
            accounts = config.get("accounts", {})
            if active_account and active_account in accounts:
                account = accounts[active_account]
                config["api_url"] = account.get("api_url", "")
                config["api_key"] = account.get("api_key", "")
            else:
                # Clear top-level creds if no active account
                config.pop("api_url", None)
                config.pop("api_key", None)

        # Atomic write: write to temp file, then replace with lock held
        tmp_path = self.config_file.with_name(f"{self.config_file.name}.tmp")
        lock_handle = None
        lock_acquired = False
        try:
            lock_handle = open(self.lock_file, "a+", encoding="utf-8")
            self._acquire_lock(lock_handle)
            lock_acquired = True

            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            tmp_path.replace(self.config_file)

            # Set secure file permissions
            try:
                os.chmod(self.config_file, 0o600)
            except OSError:  # pragma: no cover - permission errors are expected in some environments
                pass
        except Exception as e:
            # Clean up temp file on error
            if tmp_path.exists():
                tmp_path.unlink()
            raise AccountStoreError(f"Failed to save config file: {e}") from e
        finally:
            if lock_handle:
                if lock_acquired:
                    self._release_lock(lock_handle)
                lock_handle.close()

    def _needs_migration(self, config: dict[str, Any]) -> bool:
        """Check if config needs migration from legacy format.

        Args:
            config: Raw config dictionary.

        Returns:
            True if migration is needed.
        """
        return "version" not in config

    def _load_auth_json_credentials(self, api_url: str | None, api_key: str | None) -> tuple[str | None, str | None]:
        """Load credentials from auth.json if missing.

        Args:
            api_url: Existing API URL or None.
            api_key: Existing API key or None.

        Returns:
            Tuple of (api_url, api_key) with values from auth.json if missing.
        """
        auth_json_path = self.config_dir / "auth.json"
        if (not api_url or not api_key) and auth_json_path.exists():
            try:
                with open(auth_json_path, encoding="utf-8") as f:
                    auth_data = json.load(f)
                    if not api_url:
                        api_url = auth_data.get("api_url") or api_url
                    if not api_key:
                        api_key = auth_data.get("api_key") or api_key
            except (json.JSONDecodeError, OSError):
                # Ignore errors reading auth.json
                pass
        return api_url, api_key

    def _create_default_account(self, api_url: str | None, api_key: str | None) -> dict[str, dict[str, str]]:
        """Create default account from legacy credentials.

        Args:
            api_url: API URL or None.
            api_key: API key or None.

        Returns:
            Dictionary with "default" account if both credentials exist and are non-empty, empty dict otherwise.
        """
        accounts = {}
        # Only create default account if both URL and key are present and non-empty
        if api_url and api_key and api_url.strip() and api_key.strip():
            accounts["default"] = {
                "api_url": api_url.strip(),
                "api_key": api_key.strip(),
            }
        return accounts

    def _preserve_legacy_keys(self, config: dict[str, Any]) -> dict[str, Any]:
        """Preserve legacy top-level keys for backward compatibility.

        Args:
            config: Legacy config dictionary.

        Returns:
            Dictionary with preserved keys.
        """
        preserved = {}
        for key in ["timeout", "history_default_limit"]:
            if key in config:
                preserved[key] = config[key]
        return preserved

    def _migrate_legacy_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Migrate legacy config to versioned structure.

        Args:
            config: Legacy config dictionary.

        Returns:
            Migrated config dictionary.
        """
        migrated = {
            "version": CONFIG_VERSION,
            "active_account": "default",
            "accounts": {},
        }

        # Preserve existing accounts if they exist (shouldn't happen in true migration, but defensive)
        existing_accounts = config.get("accounts", {})
        if existing_accounts:
            migrated["accounts"] = existing_accounts.copy()
            existing_active = config.get("active_account")
            if existing_active and existing_active in existing_accounts:
                migrated["active_account"] = existing_active
            elif "default" in existing_accounts:
                migrated["active_account"] = "default"
            else:
                migrated["active_account"] = sorted(existing_accounts.keys())[0]
        else:
            # Extract legacy api_url and api_key only if no accounts exist
            api_url = config.get("api_url")
            api_key = config.get("api_key")

            # Check for auth.json from secure login MVP (only during migration)
            api_url, api_key = self._load_auth_json_credentials(api_url, api_key)

            # Create default account if we have valid credentials
            migrated["accounts"] = self._create_default_account(api_url, api_key)
            # Only set active_account to default if we actually created a default account
            if not migrated["accounts"]:
                migrated.pop("active_account", None)

        # Preserve other top-level keys for backward compatibility
        migrated.update(self._preserve_legacy_keys(config))

        return migrated

    def _ensure_migrated(self) -> None:
        """Ensure config is migrated to versioned structure.

        This should be called before any account operations to ensure
        the config file is in the correct format.
        """
        config = self._load_raw_config()

        if self._needs_migration(config):
            migrated = self._migrate_legacy_config(config)
            try:
                self._save_config(migrated)
            except AccountStoreError:
                # Gracefully skip migration when persistence is blocked (e.g., mocked I/O in tests)
                return

    def load_config(self) -> dict[str, Any]:
        """Load config with automatic migration.

        Returns:
            Versioned config dictionary.
        """
        self._ensure_migrated()
        return self._load_raw_config()

    def validate_account_name(self, name: str) -> None:
        """Validate an account name.

        Args:
            name: Account name to validate.

        Raises:
            InvalidAccountNameError: If name is invalid.
        """
        if not name:
            raise InvalidAccountNameError("Account name cannot be empty")
        if not ACCOUNT_NAME_PATTERN.match(name):
            raise InvalidAccountNameError(
                f"Invalid account name '{name}'. Must be 1-32 characters, alphanumeric, dash, or underscore."
            )

    def list_accounts(self) -> dict[str, dict[str, str]]:
        """List all account profiles.

        Returns:
            Dictionary mapping account names to their profiles.
        """
        config = self.load_config()
        return config.get("accounts", {}).copy()

    def get_account(self, name: str) -> dict[str, str] | None:
        """Get a specific account profile.

        Args:
            name: Account name.

        Returns:
            Account profile dictionary with api_url and api_key, or None if not found.
        """
        accounts = self.list_accounts()
        return accounts.get(name)

    def get_active_account(self) -> str | None:
        """Get the name of the active account.

        Returns:
            Active account name, or None if not set.
        """
        config = self.load_config()
        return config.get("active_account")

    def set_active_account(self, name: str) -> None:
        """Set the active account.

        Args:
            name: Account name to activate.

        Raises:
            AccountNotFoundError: If account doesn't exist.
        """
        self.validate_account_name(name)

        config = self.load_config()
        accounts = config.get("accounts", {})

        if name not in accounts:
            raise AccountNotFoundError(f"Account '{name}' not found")

        config["active_account"] = name
        self._save_config(config)

    def add_account(
        self,
        name: str,
        api_url: str,
        api_key: str,
        *,
        overwrite: bool = False,
    ) -> None:
        """Add or update an account profile.

        Args:
            name: Account name.
            api_url: API URL for this account.
            api_key: API key for this account.
            overwrite: If True, overwrite existing account without prompting.

        Raises:
            InvalidAccountNameError: If name is invalid.
            AccountStoreError: If account exists and overwrite is False.
        """
        self.validate_account_name(name)

        config = self.load_config()
        accounts = config.setdefault("accounts", {})

        if name in accounts and not overwrite:
            raise AccountStoreError(f"Account '{name}' already exists. Use --yes to overwrite.")

        accounts[name] = {
            "api_url": api_url,
            "api_key": api_key,
        }

        # If this is the first account, make it active
        if not config.get("active_account") and len(accounts) == 1:
            config["active_account"] = name

        self._save_config(config)

    def remove_account(self, name: str) -> None:
        """Remove an account profile.

        Args:
            name: Account name to remove.

        Raises:
            AccountNotFoundError: If account doesn't exist.
            AccountStoreError: If trying to remove the last account.
        """
        config = self.load_config()
        accounts = config.get("accounts", {})

        if name not in accounts:
            raise AccountNotFoundError(f"Account '{name}' not found")

        if len(accounts) <= 1:
            raise AccountStoreError("Cannot remove the last remaining account")

        del accounts[name]

        # If we removed the active account, switch to another account
        active_account = config.get("active_account")
        if active_account == name:
            # Prefer "default" if it exists, otherwise use first alphabetical account
            if "default" in accounts:
                config["active_account"] = "default"
            elif accounts:
                # Sort accounts alphabetically and pick the first one
                sorted_names = sorted(accounts.keys())
                config["active_account"] = sorted_names[0]
            else:
                # No accounts remaining (shouldn't happen due to check above)
                config.pop("active_account", None)

        self._save_config(config)

    def get_credentials(
        self,
        account_name: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Get credentials for an account.

        Args:
            account_name: Account name, or None to use active account.

        Returns:
            Tuple of (api_url, api_key), or (None, None) if not found.
        """
        config = self.load_config()

        # Determine which account to use
        if account_name:
            target_account = account_name
        else:
            target_account = config.get("active_account")

        if not target_account:
            return None, None

        accounts = config.get("accounts", {})
        account = accounts.get(target_account)

        if not account:
            return None, None

        return account.get("api_url"), account.get("api_key")

    def rename_account(self, current_name: str, new_name: str, *, overwrite: bool = False) -> None:
        """Rename an existing account profile.

        Args:
            current_name: The existing account name.
            new_name: The desired new account name.
            overwrite: Whether to overwrite an existing target account.

        Raises:
            InvalidAccountNameError: If either name is invalid.
            AccountNotFoundError: If the source account does not exist.
            AccountStoreError: If the target exists and overwrite is False.
        """
        self.validate_account_name(current_name)
        self.validate_account_name(new_name)

        if current_name == new_name:
            # No-op rename; keep behavior predictable without mutating config
            return

        config = self.load_config()
        accounts = config.get("accounts", {})

        if current_name not in accounts:
            raise AccountNotFoundError(f"Account '{current_name}' not found")

        if new_name in accounts and not overwrite:
            raise AccountStoreError(f"Account '{new_name}' already exists. Use --yes to overwrite.")

        accounts[new_name] = accounts[current_name]
        del accounts[current_name]

        if config.get("active_account") == current_name:
            config["active_account"] = new_name

        self._save_config(config)


# Global instance for convenience
_account_store = AccountStore()


def get_account_store() -> AccountStore:
    """Get the global account store instance."""
    from glaip_sdk.cli import config as config_module  # noqa: PLC0415

    global _account_store

    if _account_store is None or _account_store.config_file != config_module.CONFIG_FILE:
        _account_store = AccountStore(config_module.CONFIG_FILE)

    return _account_store
