"""Accounts controller for the /accounts slash command.

Provides a lightweight Textual list with fallback Rich snapshot to switch
between stored accounts using the shared AccountStore and CLI validation.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from getpass import getpass
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.prompt import Prompt

from glaip_sdk.branding import ERROR_STYLE, INFO_STYLE, SUCCESS_STYLE, WARNING_STYLE
from glaip_sdk.cli.account_store import AccountStore, AccountStoreError, get_account_store
from glaip_sdk.cli.commands.common_config import check_connection_with_reason
from glaip_sdk.cli.masking import mask_api_key_display
from glaip_sdk.cli.validators import validate_api_key
from glaip_sdk.cli.slash.accounts_shared import (
    build_account_rows,
    build_account_status_string,
    env_credentials_present,
)
from glaip_sdk.cli.slash.tui.accounts_app import TEXTUAL_SUPPORTED, AccountsTUICallbacks, run_accounts_textual
from glaip_sdk.rich_components import AIPPanel, AIPTable
from glaip_sdk.utils.validation import validate_url

if TYPE_CHECKING:  # pragma: no cover
    from glaip_sdk.cli.slash.session import SlashSession

TEXTUAL_AVAILABLE = bool(TEXTUAL_SUPPORTED)


class AccountsController:
    """Controller for listing and switching accounts inside the palette."""

    def __init__(self, session: SlashSession) -> None:
        """Initialize the accounts controller.

        Args:
            session: The slash session context.
        """
        self.session = session
        self.console: Console = session.console
        self.ctx = session.ctx

    def handle_accounts_command(self, args: list[str]) -> bool:
        """Handle `/accounts` with optional `/accounts <name>` quick switch."""
        store = get_account_store()
        env_lock = env_credentials_present(partial=True)
        accounts = store.list_accounts()

        if not accounts:
            self.console.print(f"[{WARNING_STYLE}]No accounts found. Use `/login` to add credentials.[/]")
            return self.session._continue_session()

        if args:
            name = args[0]
            self._switch_account(store, name, env_lock)
            return self.session._continue_session()

        rows = self._build_rows(accounts, store.get_active_account(), env_lock)

        if self._should_use_textual():
            self._render_textual(rows, store, env_lock)
        else:
            self._render_rich_interactive(store, env_lock)

        return self.session._continue_session()

    def _should_use_textual(self) -> bool:
        """Return whether Textual UI should be used."""
        if not TEXTUAL_AVAILABLE:
            return False

        def _is_tty(stream: Any) -> bool:
            isatty = getattr(stream, "isatty", None)
            if not callable(isatty):
                return False
            try:
                return bool(isatty())
            except Exception:
                return False

        return _is_tty(sys.stdin) and _is_tty(sys.stdout)

    def _build_rows(
        self,
        accounts: dict[str, dict[str, str]],
        active_account: str | None,
        env_lock: bool,
    ) -> list[dict[str, str | bool]]:
        """Normalize account rows for display."""
        return build_account_rows(accounts, active_account, env_lock)

    def _render_rich(self, rows: Iterable[dict[str, str | bool]], env_lock: bool) -> None:
        """Render a Rich snapshot with columns matching TUI."""
        if env_lock:
            self.console.print(
                f"[{WARNING_STYLE}]Env credentials detected (AIP_API_URL/AIP_API_KEY); add/edit/delete are disabled.[/]"
            )

        table = AIPTable(title="AIP Accounts")
        table.add_column("Name", style=INFO_STYLE, width=20)
        table.add_column("API URL", style=SUCCESS_STYLE, width=40)
        table.add_column("Key (masked)", style="dim", width=20)
        table.add_column("Status", style=SUCCESS_STYLE, width=14)

        for row in rows:
            status = build_account_status_string(row, use_markup=True)
            # pylint: disable=duplicate-code
            # Similar to accounts_app.py but uses Rich AIPTable API
            table.add_row(
                str(row.get("name", "")),
                str(row.get("api_url", "")),
                str(row.get("masked_key", "")),
                status,
            )

        self.console.print(table)

    def _render_rich_interactive(self, store: AccountStore, env_lock: bool) -> None:
        """Render Rich snapshot and run linear add/edit/delete prompts."""
        if env_lock:
            rows = self._build_rows(store.list_accounts(), store.get_active_account(), env_lock)
            self._render_rich(rows, env_lock)
            return

        while True:  # pragma: no cover - interactive prompt loop
            rows = self._build_rows(store.list_accounts(), store.get_active_account(), env_lock)
            self._render_rich(rows, env_lock)
            action = self._prompt_action()
            if action == "q":
                break
            if action == "a":
                self._rich_add_flow(store)
            elif action == "e":
                self._rich_edit_flow(store)
            elif action == "d":
                self._rich_delete_flow(store)
            elif action == "s":
                self._rich_switch_flow(store, env_lock)
            else:
                self.console.print(f"[{WARNING_STYLE}]Invalid choice. Use a/e/d/s/q.[/]")

    def _render_textual(self, rows: list[dict[str, str | bool]], store: AccountStore, env_lock: bool) -> None:
        """Launch the Textual accounts browser."""
        active_before = store.get_active_account()
        notified = False

        def _switch_in_textual(name: str) -> tuple[bool, str]:
            nonlocal notified
            switched, message = self._switch_account(
                store,
                name,
                env_lock,
                emit_console=False,
                invalidate_session=True,
            )
            if switched:
                notified = True
            return switched, message

        callbacks = AccountsTUICallbacks(switch_account=_switch_in_textual)
        active = next((row["name"] for row in rows if row.get("active")), None)
        try:
            run_accounts_textual(rows, active_account=active, env_lock=env_lock, callbacks=callbacks)
        except Exception as exc:  # pragma: no cover - defensive around Textual failures
            self.console.print(f"[{WARNING_STYLE}]Accounts browser exited unexpectedly: {exc}[/]")

        # Exit snapshot: surface a success banner when a switch occurred inside the TUI.
        # Always notify when the active account changed, even if Textual raised.
        active_after = store.get_active_account()
        if active_after != active_before and not notified:
            self._notify_account_switched(active_after)
        if active_after != active:
            host_after = ""
            display_account = active_after or "default"
            account_after = store.get_account(display_account) if hasattr(store, "get_account") else None
            if account_after:
                host_after = account_after.get("api_url", "")
            host_suffix = f" • {host_after}" if host_after else ""
            self.console.print(
                AIPPanel(
                    f"[{SUCCESS_STYLE}]Active account ➜ {display_account}[/]{host_suffix}",
                    title="✅ Account Switched",
                    border_style=SUCCESS_STYLE,
                )
            )

    def _format_connection_error_message(self, error_reason: str, account_name: str, api_url: str) -> str:
        """Format error message for connection validation failures."""
        code, detail = self._parse_error_reason(error_reason)
        if code == "connection_failed":
            return f"Switch aborted: cannot reach {api_url}. Check URL or network."
        if code == "api_failed":
            return f"Switch aborted: API error for '{account_name}'. Check credentials."
        detail_suffix = f": {detail}" if detail else ""
        return f"Switch aborted: {code or 'Validation failed'}{detail_suffix}"

    def _emit_error_message(self, msg: str, style: str = ERROR_STYLE) -> None:
        """Emit an error or warning message to the console."""
        self.console.print(f"[{style}]{msg}[/]")

    def _validate_account_switch(
        self, store: AccountStore, name: str, env_lock: bool, emit_console: bool
    ) -> tuple[bool, str, dict[str, str] | None]:
        """Validate account switch prerequisites; returns (is_valid, error_msg, account_dict)."""
        if env_lock:
            msg = "Env credentials detected (AIP_API_URL/AIP_API_KEY); switching is disabled."
            if emit_console:
                self._emit_error_message(msg, WARNING_STYLE)
            return False, msg, None

        account = store.get_account(name)
        if not account:
            msg = f"Account '{name}' not found."
            if emit_console:
                self._emit_error_message(msg)
            return False, msg, None

        api_url = account.get("api_url", "")
        api_key = account.get("api_key", "")
        if not api_url or not api_key:
            edit_cmd = f"aip accounts edit {name}"
            msg = f"Account '{name}' is missing credentials. Use `/login` or `{edit_cmd}`."
            if emit_console:
                self._emit_error_message(msg)
            return False, msg, None

        ok, error_reason = check_connection_with_reason(api_url, api_key, abort_on_error=False)
        if not ok:
            msg = self._format_connection_error_message(error_reason, name, api_url)
            if emit_console:
                self._emit_error_message(msg, WARNING_STYLE)
            return False, msg, None

        return True, "", account

    def _execute_account_switch(
        self, store: AccountStore, name: str, account: dict[str, str], invalidate_session: bool, emit_console: bool
    ) -> tuple[bool, str]:
        """Execute the account switch and emit success message."""
        try:
            store.set_active_account(name)
            api_url = account.get("api_url", "")
            api_key = account.get("api_key", "")
            masked_key = mask_api_key_display(api_key)
            if invalidate_session:
                self._notify_account_switched(name)
            if emit_console:
                self.console.print(
                    AIPPanel(
                        f"[{SUCCESS_STYLE}]Active account ➜ {name}[/]\nAPI URL: {api_url}\nKey: {masked_key}",
                        title="✅ Account Switched",
                        border_style=SUCCESS_STYLE,
                    )
                )
            return True, f"Switched to '{name}'."
        except AccountStoreError as exc:
            msg = f"Failed to set active account: {exc}"
            if emit_console:
                self._emit_error_message(msg)
            return False, msg
        except Exception as exc:  # NOSONAR(S1045) - catch-all needed for unexpected errors
            msg = f"Unexpected error while switching to '{name}': {exc}"
            if emit_console:
                self._emit_error_message(msg)
            return False, msg

    def _switch_account(
        self,
        store: AccountStore,
        name: str,
        env_lock: bool,
        *,
        emit_console: bool = True,
        invalidate_session: bool = True,
    ) -> tuple[bool, str]:
        """Validate and switch active account; returns (success, message)."""
        is_valid, error_msg, account = self._validate_account_switch(store, name, env_lock, emit_console)
        if not is_valid:
            return False, error_msg

        if account is None:  # Defensive – should never happen, but avoid crashing in production
            return False, "Unable to locate account after validation."
        return self._execute_account_switch(store, name, account, invalidate_session, emit_console)

    @staticmethod
    def _parse_error_reason(reason: str | None) -> tuple[str, str]:
        """Parse error reason into (code, detail) to avoid fragile substring checks."""
        if not reason:
            return "", ""
        if ":" in reason:
            code, _, detail = reason.partition(":")
            return code.strip(), detail.strip()
        return reason.strip(), ""

    def _prompt_action(self) -> str:
        """Prompt for add/edit/delete/quit action."""
        try:
            choice = Prompt.ask("(a)dd / (e)dit / (d)elete / (s)witch / (q)uit", default="q")
        except Exception:  # pragma: no cover - defensive around prompt failures
            return "q"
        return (choice or "").strip().lower()[:1]

    def _prompt_yes_no(self, prompt: str, *, default: bool = True) -> bool:
        """Prompt a yes/no question with a default."""
        default_str = "Y/n" if default else "y/N"
        try:
            answer = Prompt.ask(f"{prompt} ({default_str})", default="y" if default else "n")
        except Exception:  # pragma: no cover - defensive around prompt failures
            return default
        normalized = (answer or "").strip().lower()
        if not normalized:
            return default
        return normalized in {"y", "yes"}

    def _prompt_account_name(self, store: AccountStore, *, for_edit: bool) -> str | None:
        """Prompt for an account name, validating per store rules."""
        while True:  # pragma: no cover - interactive prompt loop
            name = self._get_name_input(for_edit)
            if name is None:
                return None
            if not name:
                self.console.print(f"[{WARNING_STYLE}]Name is required.[/]")
                continue
            if not self._validate_name_format(store, name):
                continue
            if not self._validate_name_existence(store, name, for_edit):
                continue
            return name

    def _get_name_input(self, for_edit: bool) -> str | None:
        """Get account name input from user."""
        try:
            prompt_text = "Account name" + (" (existing)" if for_edit else "")
            name = Prompt.ask(prompt_text)
            return name.strip() if name else None
        except Exception:
            return None

    def _validate_name_format(self, store: AccountStore, name: str) -> bool:
        """Validate account name format."""
        try:
            store.validate_account_name(name)
            return True
        except Exception as exc:
            self.console.print(f"[{ERROR_STYLE}]{exc}[/]")
            return False

    def _validate_name_existence(self, store: AccountStore, name: str, for_edit: bool) -> bool:
        """Validate account name existence based on mode."""
        account_exists = store.get_account(name) is not None
        if not for_edit and account_exists:
            self.console.print(
                f"[{WARNING_STYLE}]Account '{name}' already exists. Use edit instead or choose a new name.[/]"
            )
            return False
        if for_edit and not account_exists:
            self.console.print(f"[{WARNING_STYLE}]Account '{name}' not found. Try again or quit.[/]")
            return False
        return True

    def _prompt_api_url(self, existing_url: str | None = None) -> str | None:
        """Prompt for API URL with HTTPS validation."""
        placeholder = existing_url or "https://your-aip-instance.com"
        while True:  # pragma: no cover - interactive prompt loop
            try:
                entered = Prompt.ask("API URL", default=placeholder)
            except Exception:
                return None
            url = (entered or "").strip()
            if not url and existing_url:
                return existing_url
            if not url:
                self.console.print(f"[{WARNING_STYLE}]API URL is required.[/]")
                continue
            try:
                return validate_url(url)
            except Exception as exc:
                self.console.print(f"[{ERROR_STYLE}]{exc}[/]")

    def _prompt_api_key(self, existing_key: str | None = None) -> str | None:
        """Prompt for API key (masked)."""
        mask_hint = "leave blank to keep current" if existing_key else None
        while True:  # pragma: no cover - interactive prompt loop
            try:
                entered = getpass(f"API key ({mask_hint or 'input hidden'}): ")
            except Exception:
                return None
            if not entered and existing_key:
                return existing_key
            if not entered:
                self.console.print(f"[{WARNING_STYLE}]API key is required.[/]")
                continue
            try:
                return validate_api_key(entered)
            except Exception as exc:
                self.console.print(f"[{ERROR_STYLE}]{exc}[/]")

    def _rich_add_flow(self, store: AccountStore) -> None:
        """Run Rich add prompts and save."""
        name = self._prompt_account_name(store, for_edit=False)
        if not name:
            return
        api_url = self._prompt_api_url()
        if not api_url:
            return
        api_key = self._prompt_api_key()
        if not api_key:
            return
        should_test = self._prompt_yes_no("Test connection before save?", default=True)
        self._save_account(store, name, api_url, api_key, should_test, True, is_edit=False)

    def _rich_edit_flow(self, store: AccountStore) -> None:
        """Run Rich edit prompts and save."""
        name = self._prompt_account_name(store, for_edit=True)
        if not name:
            return
        existing = store.get_account(name) or {}
        api_url = self._prompt_api_url(existing.get("api_url"))
        if not api_url:
            return
        api_key = self._prompt_api_key(existing.get("api_key"))
        if not api_key:
            return
        should_test = self._prompt_yes_no("Test connection before save?", default=True)
        self._save_account(store, name, api_url, api_key, should_test, False, is_edit=True)

    def _rich_switch_flow(self, store: AccountStore, env_lock: bool) -> None:
        """Run Rich switch prompt and set active account."""
        name = self._prompt_account_name(store, for_edit=True)
        if not name:
            return
        self._switch_account(store, name, env_lock)

    def _save_account(
        self,
        store: AccountStore,
        name: str,
        api_url: str,
        api_key: str,
        should_test: bool,
        set_active: bool,
        *,
        is_edit: bool,
    ) -> None:
        """Validate, optionally test, and persist account changes."""
        if should_test and not self._run_connection_test_with_retry(api_url, api_key):
            return

        try:
            store.add_account(name, api_url, api_key, overwrite=is_edit)
        except AccountStoreError as exc:
            self.console.print(f"[{ERROR_STYLE}]Save failed: {exc}[/]")
            return
        except Exception as exc:
            self.console.print(f"[{ERROR_STYLE}]Unexpected error while saving: {exc}[/]")
            return

        self.console.print(f"[{SUCCESS_STYLE}]Account '{name}' saved.[/]")
        if set_active:
            try:
                store.set_active_account(name)
            except Exception as exc:
                self.console.print(f"[{WARNING_STYLE}]Account saved but could not set active: {exc}[/]")
            else:
                self._notify_account_switched(name)
                self._announce_active_change(store, name)

    def _notify_account_switched(self, name: str | None) -> None:
        """Best-effort notify the hosting session that the active account changed."""
        notify = getattr(self.session, "on_account_switched", None)
        if callable(notify):
            try:
                notify(name)
            except Exception:  # pragma: no cover - best-effort callback
                pass

    def _confirm_delete_prompt(self, name: str) -> bool:
        """Ask for delete confirmation; return True when confirmed."""
        self.console.print(f"[{WARNING_STYLE}]Type '{name}' to confirm deletion. This cannot be undone.[/]")
        while True:  # pragma: no cover - interactive prompt loop
            confirmation = Prompt.ask("Confirm name (or blank to cancel)", default="")
            if confirmation is None or not confirmation.strip():
                self.console.print(f"[{WARNING_STYLE}]Deletion cancelled.[/]")
                return False
            if confirmation.strip() != name:
                self.console.print(f"[{WARNING_STYLE}]Name does not match; type '{name}' to confirm.[/]")
                continue
            return True

    def _delete_account_and_notify(self, store: AccountStore, name: str, active_before: str | None) -> None:
        """Remove account with error handling and announce active change."""
        try:
            store.remove_account(name)
        except AccountStoreError as exc:
            self.console.print(f"[{ERROR_STYLE}]Delete failed: {exc}[/]")
            return
        except Exception as exc:
            self.console.print(f"[{ERROR_STYLE}]Unexpected error while deleting: {exc}[/]")
            return

        self.console.print(f"[{SUCCESS_STYLE}]Account '{name}' deleted.[/]")
        # Announce active account change if it changed
        active_after = store.get_active_account()
        if active_after is not None and active_after != active_before:
            self._announce_active_change(store, active_after)
        elif active_after is None and active_before == name:
            self.console.print(f"[{WARNING_STYLE}]No account is currently active. Select an account to activate it.[/]")

    def _rich_delete_flow(self, store: AccountStore) -> None:
        """Run Rich delete prompts with name confirmation."""
        name = self._prompt_account_name(store, for_edit=True)
        if not name:
            return

        # Check if this is the last remaining account before prompting for confirmation
        accounts = store.list_accounts()
        if len(accounts) <= 1 and name in accounts:
            self.console.print(f"[{WARNING_STYLE}]Cannot remove the last remaining account.[/]")
            return

        if not self._confirm_delete_prompt(name):
            return

        # Re-check after confirmation prompt (race condition guard)
        accounts = store.list_accounts()
        if len(accounts) <= 1 and name in accounts:
            self.console.print(f"[{WARNING_STYLE}]Cannot remove the last remaining account.[/]")
            return

        active_before = store.get_active_account()
        self._delete_account_and_notify(store, name, active_before)

    def _format_connection_failure(self, code: str, detail: str, api_url: str) -> str:
        """Build a user-facing connection failure message."""
        detail_suffix = f": {detail}" if detail else ""
        if code == "connection_failed":
            return f"Connection test failed: cannot reach {api_url}{detail_suffix}"
        if code == "api_failed":
            return f"Connection test failed: API error{detail_suffix}"
        return f"Connection test failed{detail_suffix}"

    def _run_connection_test_with_retry(self, api_url: str, api_key: str) -> bool:
        """Run connection test with retry/skip prompts."""
        skip_prompt_shown = False
        while True:
            ok, reason = check_connection_with_reason(api_url, api_key, abort_on_error=False)
            if ok:
                return True
            code, detail = self._parse_error_reason(reason)
            message = self._format_connection_failure(code, detail, api_url)
            self.console.print(f"[{WARNING_STYLE}]{message}[/]")
            retry = self._prompt_yes_no("Retry connection test?", default=True)
            if retry:
                continue
            if not skip_prompt_shown:
                skip_prompt_shown = True
                skip = self._prompt_yes_no("Skip connection test and save?", default=False)
                if skip:
                    return True
            self.console.print(f"[{WARNING_STYLE}]Cancelled save after failed connection test.[/]")
            return False

    def _announce_active_change(self, store: AccountStore, name: str) -> None:
        """Print active account change announcement."""
        account = store.get_account(name) or {}
        host = account.get("api_url", "")
        host_suffix = f" • {host}" if host else ""
        self.console.print(f"[{SUCCESS_STYLE}]Active account ➜ {name}{host_suffix}[/]")
