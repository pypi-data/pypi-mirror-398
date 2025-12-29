"""Textual UI for the /accounts command.

Provides a minimal interactive list with the same columns/order as the Rich
fallback (name, API URL, masked key, status) and keyboard navigation.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from glaip_sdk.cli.account_store import AccountStore, AccountStoreError, get_account_store
from glaip_sdk.cli.commands.common_config import check_connection_with_reason
from glaip_sdk.cli.slash.accounts_shared import (
    build_account_rows,
    build_account_status_string,
    env_credentials_present,
)
from glaip_sdk.cli.slash.tui.background_tasks import BackgroundTaskMixin
from glaip_sdk.cli.slash.tui.loading import hide_loading_indicator, show_loading_indicator
from glaip_sdk.cli.validators import validate_api_key
from glaip_sdk.utils.validation import validate_url

try:  # pragma: no cover - optional dependency
    from textual import events
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input, LoadingIndicator, Static
except Exception:  # pragma: no cover - optional dependency
    events = None  # type: ignore[assignment]
    App = None  # type: ignore[assignment]
    ComposeResult = None  # type: ignore[assignment]
    Binding = None  # type: ignore[assignment]
    Container = None  # type: ignore[assignment]
    Horizontal = None  # type: ignore[assignment]
    Vertical = None  # type: ignore[assignment]
    Button = None  # type: ignore[assignment]
    Checkbox = None  # type: ignore[assignment]
    DataTable = None  # type: ignore[assignment]
    Footer = None  # type: ignore[assignment]
    Header = None  # type: ignore[assignment]
    Input = None  # type: ignore[assignment]
    LoadingIndicator = None  # type: ignore[assignment]
    ModalScreen = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]

TEXTUAL_SUPPORTED = App is not None and DataTable is not None

# Use safe bases so the module remains importable without Textual installed.
if TEXTUAL_SUPPORTED:
    _AccountFormBase = ModalScreen[dict[str, Any] | None]
    _ConfirmDeleteBase = ModalScreen[str | None]
    _AppBase = App[None]
else:
    _AccountFormBase = object
    _ConfirmDeleteBase = object
    _AppBase = object

# Widget IDs for Textual UI
ACCOUNTS_TABLE_ID = "#accounts-table"
FILTER_INPUT_ID = "#filter-input"
STATUS_ID = "#status"
ACCOUNTS_LOADING_ID = "#accounts-loading"
FORM_KEY_ID = "#form-key"

# CSS file name
CSS_FILE_NAME = "accounts.tcss"


@dataclass
class AccountsTUICallbacks:
    """Callbacks invoked by the Textual UI."""

    switch_account: Callable[[str], tuple[bool, str]]


def _build_account_rows_from_store(
    store: AccountStore,
    env_lock: bool,
) -> tuple[list[dict[str, str | bool]], str | None]:
    """Load account rows with masking and active flag."""
    accounts = store.list_accounts()
    active = store.get_active_account()
    rows = build_account_rows(accounts, active, env_lock)
    return rows, active


def _prepare_account_payload(
    *,
    name: str,
    api_url_input: str,
    api_key_input: str,
    existing_url: str | None,
    existing_key: str | None,
    existing_names: set[str],
    mode: str,
    should_test: bool,
    validate_name: Callable[[str], None],
    connection_tester: Callable[[str, str], tuple[bool, str]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and build payload for add/edit operations."""
    name = name.strip()
    api_url_raw = api_url_input.strip()
    api_key_raw = api_key_input.strip()

    error = _validate_account_name(name, existing_names, mode, validate_name)
    if error:
        return None, error

    api_url_candidate = api_url_raw or (existing_url or "")
    api_key_candidate = api_key_raw or (existing_key or "")

    api_url_validated, error = _validate_and_prepare_url(api_url_candidate)
    if error:
        return None, error

    api_key_validated, error = _validate_and_prepare_key(api_key_candidate)
    if error:
        return None, error

    if should_test:
        error = _test_connection(api_url_validated, api_key_validated, connection_tester)
        if error:
            return None, error

    payload: dict[str, Any] = {
        "name": name,
        "api_url": api_url_validated,
        "api_key": api_key_validated,
        "should_test": should_test,
        "mode": mode,
    }
    return payload, None


def _validate_account_name(
    name: str,
    existing_names: set[str],
    mode: str,
    validate_name: Callable[[str], None],
) -> str | None:
    """Validate account name."""
    if not name:
        return "Account name cannot be empty."

    try:
        validate_name(name)
    except Exception as exc:
        return str(exc)

    if mode == "add" and name in existing_names:
        return f"Account '{name}' already exists. Choose a unique name."

    return None


def _validate_and_prepare_url(api_url_candidate: str) -> tuple[str, str | None]:
    """Validate and prepare API URL."""
    if not api_url_candidate:
        return "", "API URL is required."
    try:
        return validate_url(api_url_candidate), None
    except Exception as exc:
        return "", str(exc)


def _validate_and_prepare_key(api_key_candidate: str) -> tuple[str, str | None]:
    """Validate and prepare API key."""
    if not api_key_candidate:
        return "", "API key is required."
    try:
        return validate_api_key(api_key_candidate), None
    except Exception as exc:
        return "", str(exc)


def _test_connection(
    api_url: str,
    api_key: str,
    connection_tester: Callable[[str, str], tuple[bool, str]],
) -> str | None:
    """Test API connection."""
    ok, reason = connection_tester(api_url, api_key)
    if not ok:
        detail = reason or "connection_failed"
        return f"Connection test failed: {detail}"
    return None


def run_accounts_textual(
    rows: list[dict[str, str | bool]],
    *,
    active_account: str | None,
    env_lock: bool,
    callbacks: AccountsTUICallbacks,
) -> None:
    """Launch the Textual accounts browser if dependencies are available."""
    if not TEXTUAL_SUPPORTED:
        return
    app = AccountsTextualApp(rows, active_account, env_lock, callbacks)
    app.run()


class AccountFormModal(_AccountFormBase):  # pragma: no cover - interactive
    """Modal form for add/edit account."""

    CSS_PATH = CSS_FILE_NAME

    def __init__(
        self,
        *,
        mode: str,
        existing: dict[str, str] | None,
        existing_names: set[str],
        connection_tester: Callable[[str, str], tuple[bool, str]],
        validate_name: Callable[[str], None],
    ) -> None:
        """Initialize the account form modal.

        Args:
            mode: Form mode, either "add" or "edit".
            existing: Existing account data for edit mode.
            existing_names: Set of existing account names for validation.
            connection_tester: Callable to test API connection.
            validate_name: Callable to validate account name.
        """
        super().__init__()
        self._mode = mode
        self._existing = existing or {}
        self._existing_names = existing_names
        self._connection_tester = connection_tester
        self._validate_name = validate_name

    def compose(self) -> ComposeResult:
        """Render the form controls."""
        title = "Add account" if self._mode == "add" else "Edit account"
        name_input = Input(
            value=self._existing.get("name", ""),
            placeholder="account-name",
            id="form-name",
            disabled=self._mode == "edit",
        )
        url_input = Input(value=self._existing.get("api_url", ""), placeholder="https://api.example.com", id="form-url")
        key_input = Input(value="", placeholder="sk-...", password=True, id="form-key")
        test_checkbox = Checkbox(
            "Test connection before save",
            value=True,
            id="form-test",
        )
        status = Static("", id="form-status")

        yield Static(title, id="form-title")
        yield Static("Name", classes="form-label")
        yield name_input
        yield Static("API URL", classes="form-label")
        yield url_input
        yield Static("API Key", classes="form-label")
        yield key_input
        yield Horizontal(
            Button("Show key", id="toggle-key"),
            Button("Clear key", id="clear-key"),
            id="form-key-actions",
        )
        yield test_checkbox
        yield Horizontal(
            Button("Save", id="form-save", variant="primary"),
            Button("Cancel", id="form-cancel"),
            id="form-actions",
        )
        yield status

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id or ""
        if btn_id == "form-cancel":
            self.dismiss(None)
            return
        if btn_id == "toggle-key":
            key_input = self.query_one(FORM_KEY_ID, Input)
            key_input.password = not key_input.password
            key_input.focus()
            return
        if btn_id == "clear-key":
            key_input = self.query_one(FORM_KEY_ID, Input)
            key_input.value = ""
            key_input.focus()
            return
        if btn_id == "form-save":
            self._handle_submit()

    def _handle_submit(self) -> None:
        """Validate inputs and dismiss with payload on success."""
        status = self.query_one("#form-status", Static)
        name_input = self.query_one("#form-name", Input)
        url_input = self.query_one("#form-url", Input)
        key_input = self.query_one(FORM_KEY_ID, Input)
        test_checkbox = self.query_one("#form-test", Checkbox)

        payload, error = _prepare_account_payload(
            name=name_input.value or "",
            api_url_input=url_input.value or "",
            api_key_input=key_input.value or "",
            existing_url=self._existing.get("api_url"),
            existing_key=self._existing.get("api_key"),
            existing_names=self._existing_names,
            mode=self._mode,
            should_test=bool(test_checkbox.value),
            validate_name=self._validate_name,
            connection_tester=self._connection_tester,
        )
        if error:
            status.update(f"[red]{error}[/]")
            if error.startswith("Connection test failed") and hasattr(self.app, "_set_status"):
                try:
                    # Surface a status-bar cue so errors remain visible after closing the modal.
                    self.app._set_status(error, "yellow")  # type: ignore[attr-defined]
                except Exception:
                    pass
            return
        status.update("[green]Saving...[/]")
        self.dismiss(payload)


class ConfirmDeleteModal(_ConfirmDeleteBase):  # pragma: no cover - interactive
    """Modal requiring typed confirmation for delete."""

    CSS_PATH = CSS_FILE_NAME

    def __init__(self, name: str) -> None:
        """Initialize the delete confirmation modal.

        Args:
            name: Name of the account to delete.
        """
        super().__init__()
        self._name = name

    def compose(self) -> ComposeResult:
        """Render confirmation form."""
        yield Static(f"Type '{self._name}' to confirm deletion. This cannot be undone.", id="confirm-text")
        yield Input(placeholder=self._name, id="confirm-input")
        yield Horizontal(
            Button("Delete", id="confirm-delete", variant="error"),
            Button("Cancel", id="confirm-cancel"),
            id="confirm-actions",
        )
        yield Static("", id="confirm-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle confirmation buttons."""
        btn_id = event.button.id or ""
        if btn_id == "confirm-cancel":
            self.dismiss(None)
            return
        if btn_id == "confirm-delete":
            self._handle_confirm()

    def _handle_confirm(self) -> None:
        """Dismiss with name when confirmation matches."""
        status = self.query_one("#confirm-status", Static)
        input_widget = self.query_one("#confirm-input", Input)
        if (input_widget.value or "").strip() != self._name:
            status.update(f"[yellow]Name does not match; type '{self._name}' to confirm.[/]")
            input_widget.focus()
            return
        self.dismiss(self._name)


class AccountsTextualApp(BackgroundTaskMixin, _AppBase):  # pragma: no cover - interactive
    """Textual application for browsing accounts."""

    CSS_PATH = CSS_FILE_NAME
    BINDINGS = [
        Binding("enter", "switch_row", "Switch", show=True),
        Binding("return", "switch_row", "Switch", show=False),
        Binding("/", "focus_filter", "Filter", show=True),
        Binding("a", "add_account", "Add", show=True),
        Binding("e", "edit_account", "Edit", show=True),
        Binding("d", "delete_account", "Delete", show=True),
        # Esc clears filter when focused/non-empty; otherwise exits
        Binding("escape", "clear_or_exit", "Close", priority=True),
        Binding("q", "app_exit", "Close", priority=True),
    ]

    def __init__(
        self,
        rows: list[dict[str, str | bool]],
        active_account: str | None,
        env_lock: bool,
        callbacks: AccountsTUICallbacks,
    ) -> None:
        """Initialize the Textual accounts app.

        Args:
            rows: Account data rows to display.
            active_account: Name of the currently active account.
            env_lock: Whether environment credentials are locking account switching.
            callbacks: Callbacks for account switching operations.
        """
        super().__init__()
        self._store = get_account_store()
        self._all_rows = rows
        self._active_account = active_account
        self._env_lock = env_lock
        self._callbacks = callbacks
        self._filter_text: str = ""
        self._is_switching = False

    def compose(self) -> ComposeResult:
        """Build the Textual layout."""
        header_text = self._header_text()
        yield Static(header_text, id="header-info")
        if self._env_lock:
            yield Static(
                "Env credentials detected (AIP_API_URL/AIP_API_KEY); add/edit/delete are disabled.",
                id="env-lock",
            )
        clear_btn = Button("Clear", id="filter-clear")
        clear_btn.display = False  # hide until filter has content
        filter_bar = Horizontal(
            Static("Filter (/):", id="filter-label"),
            Input(placeholder="Type to filter by name or host", id="filter-input"),
            clear_btn,
            id="filter-container",
        )
        filter_bar.styles.padding = (0, 0)
        main = Vertical(
            filter_bar,
            DataTable(id=ACCOUNTS_TABLE_ID.lstrip("#")),
        )
        # Avoid large gaps; keep main content filling available space
        main.styles.height = "1fr"
        main.styles.padding = (0, 0)
        yield main
        yield Horizontal(
            LoadingIndicator(id=ACCOUNTS_LOADING_ID.lstrip("#")),
            Static("", id=STATUS_ID.lstrip("#")),
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Configure table columns and load rows."""
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.add_column("Name", width=20)
        table.add_column("API URL", width=40)
        table.add_column("Key (masked)", width=20)
        table.add_column("Status", width=14)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.styles.height = "1fr"  # Fill available space below the filter
        table.styles.margin = 0
        self._reload_rows()
        table.focus()
        # Keep the filter tight to the table
        main = self.query_one(Vertical)
        main.styles.gap = 0
        self._update_filter_button_visibility()

    def _header_text(self) -> str:
        """Build header text with active account and host."""
        host = self._get_active_host() or "Not configured"
        lock_icon = " [yellow]🔒[/]" if self._env_lock else ""
        active = self._active_account or "None"
        return f"[green]Active:[/] [bold]{active}[/] ([cyan]{host}[/]){lock_icon}"

    def _get_active_host(self) -> str | None:
        """Return the API host for the active account (shortened)."""
        return self._get_host_for_name(self._active_account)

    def _get_host_for_name(self, name: str | None) -> str | None:
        """Return shortened API URL for a given account name."""
        if not name:
            return None
        for row in self._all_rows:
            if row.get("name") == name:
                url = str(row.get("api_url", ""))
                return url if len(url) <= 40 else f"{url[:37]}..."
        return None

    def action_focus_filter(self) -> None:
        """Focus the filter input and clear previous text."""
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        filter_input.value = self._filter_text
        filter_input.focus()

    def action_switch_row(self) -> None:
        """Switch to the currently selected account."""
        if self._env_lock:
            self._set_status("Switching disabled: env credentials in use.", "yellow")
            return
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        if table.cursor_row is None:
            self._set_status("No account selected.", "yellow")
            return
        try:
            row_key = table.get_row_at(table.cursor_row)[0]
        except Exception:
            self._set_status("Unable to read selected row.", "red")
            return
        name = str(row_key)
        if self._is_switching:
            self._set_status("Already switching...", "yellow")
            return
        self._is_switching = True
        host = self._get_host_for_name(name)
        if host:
            self._show_loading(f"Connecting to '{name}' ({host})...")
        else:
            self._show_loading(f"Connecting to '{name}'...")
        self._queue_switch(name)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:  # type: ignore[override]
        """Handle mouse click selection by triggering switch."""
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        try:
            # Move cursor to clicked row then switch
            table.cursor_coordinate = (event.cursor_row, 0)
        except Exception:
            return
        self.action_switch_row()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Apply filter when user presses Enter inside filter input."""
        self._filter_text = (event.value or "").strip()
        self._reload_rows()
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.focus()
        self._update_filter_button_visibility()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Apply filter live as the user types."""
        self._filter_text = (event.value or "").strip()
        self._reload_rows()
        self._update_filter_button_visibility()

    def _reload_rows(self, preferred_name: str | None = None) -> None:
        """Refresh table rows based on current filter/active state."""
        # Work on a copy to avoid mutating the backing rows list
        rows_copy = [dict(row) for row in self._all_rows]
        for row in rows_copy:
            row["active"] = row.get("name") == self._active_account

        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.clear()
        filtered = self._filtered_rows(rows_copy)
        for row in filtered:
            row_for_status = dict(row)
            row_for_status["active"] = row_for_status.get("name") == self._active_account
            # Use markup to align status colors with Rich fallback (green active badge).
            status = build_account_status_string(row_for_status, use_markup=True)
            # pylint: disable=duplicate-code
            # Reuses shared status builder; columns mirror accounts_controller Rich table.
            table.add_row(
                str(row.get("name", "")),
                str(row.get("api_url", "")),
                str(row.get("masked_key", "")),
                status,
            )
        # Move cursor to active or first row
        cursor_idx = 0
        target_name = preferred_name or self._active_account
        for idx, row in enumerate(filtered):
            if row.get("name") == target_name:
                cursor_idx = idx
                break
        if filtered:
            table.cursor_coordinate = (cursor_idx, 0)
        else:
            self._set_status("No accounts match the current filter.", "yellow")
            return

        # Update status to reflect filter state
        if self._filter_text:
            self._set_status(f"Filtered: {self._filter_text}", "cyan")
        else:
            self._set_status("", "white")

    def _filtered_rows(self, rows: list[dict[str, str | bool]] | None = None) -> list[dict[str, str | bool]]:
        """Return rows filtered by name or API URL substring."""
        base_rows = rows if rows is not None else [dict(row) for row in self._all_rows]
        if not self._filter_text:
            return list(base_rows)
        needle = self._filter_text.lower()
        filtered = [
            row
            for row in base_rows
            if needle in str(row.get("name", "")).lower() or needle in str(row.get("api_url", "")).lower()
        ]

        # Sort so name matches surface first, then URL matches, then alphabetically
        def score(row: dict[str, str | bool]) -> tuple[int, str]:
            name = str(row.get("name", "")).lower()
            url = str(row.get("api_url", "")).lower()
            name_hit = needle in name
            url_hit = needle in url
            # Extract nested conditional into clear statement
            if name_hit:
                priority = 0
            elif url_hit:
                priority = 1
            else:
                priority = 2
            return (priority, name)

        return sorted(filtered, key=score)

    def _set_status(self, message: str, style: str) -> None:
        """Update status line with message."""
        status = self.query_one(STATUS_ID, Static)
        status.update(f"[{style}]{message}[/]")

    def _show_loading(self, message: str | None = None) -> None:
        """Show the loading indicator and optional status message."""
        show_loading_indicator(self, ACCOUNTS_LOADING_ID, message=message, set_status=self._set_status)

    def _hide_loading(self) -> None:
        """Hide the loading indicator."""
        hide_loading_indicator(self, ACCOUNTS_LOADING_ID)

    def _clear_filter(self) -> None:
        """Clear the filter input and reset filter state."""
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        filter_input.value = ""
        self._filter_text = ""
        self._update_filter_button_visibility()

    def _queue_switch(self, name: str) -> None:
        """Run switch in background to keep UI responsive."""

        async def perform() -> None:
            try:
                switched, message = await asyncio.to_thread(self._callbacks.switch_account, name)
            except Exception as exc:  # pragma: no cover - defensive
                self._set_status(f"Switch failed: {exc}", "red")
                return
            finally:
                self._hide_loading()
                self._is_switching = False

            if switched:
                self._active_account = name
                self._set_status(message or f"Switched to '{name}'.", "green")
                self._update_header()
                self._reload_rows()
            else:
                self._set_status(message or "Switch failed; kept previous account.", "yellow")

        try:
            self.track_task(perform(), logger=logging.getLogger(__name__))
        except Exception as exc:
            # If scheduling the task fails, clear loading/switching state and surface the error.
            self._hide_loading()
            self._is_switching = False
            self._set_status(f"Switch failed to start: {exc}", "red")
            logging.getLogger(__name__).debug("Failed to schedule switch task", exc_info=exc)

    def _update_header(self) -> None:
        """Refresh header text to reflect active/lock state."""
        header = self.query_one("#header-info", Static)
        header.update(self._header_text())

    def action_clear_or_exit(self) -> None:
        """Clear or exit filter when focused; otherwise exit app.

        UX note: helps users reset the list without leaving the TUI.
        """
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        if filter_input.has_focus:
            # Clear when there is text; otherwise just move focus back to the table
            if filter_input.value or self._filter_text:
                self._clear_filter()
                self._reload_rows()
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
            table.focus()
            return
        self.exit()

    def action_app_exit(self) -> None:
        """Exit the application regardless of focus state."""
        self.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter bar buttons."""
        if event.button.id == "filter-clear":
            self._clear_filter()
            self._reload_rows()
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
            table.focus()

    def action_add_account(self) -> None:
        """Open add account modal."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows}
        modal = AccountFormModal(
            mode="add",
            existing=None,
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.push_screen(modal, self._on_form_result)

    def action_edit_account(self) -> None:
        """Open edit account modal for selected row."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to edit.", "yellow")
            return
        account = self._store.get_account(name)
        if not account:
            self._set_status(f"Account '{name}' not found.", "red")
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows if str(row.get("name", "")) != name}
        modal = AccountFormModal(
            mode="edit",
            existing={"name": name, "api_url": account.get("api_url", ""), "api_key": account.get("api_key", "")},
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.push_screen(modal, self._on_form_result)

    def action_delete_account(self) -> None:
        """Open delete confirmation modal."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to delete.", "yellow")
            return
        accounts = self._store.list_accounts()
        if len(accounts) <= 1:
            self._set_status("Cannot remove the last remaining account.", "red")
            return
        self.push_screen(ConfirmDeleteModal(name), self._on_delete_result)

    def _check_env_lock_hotkey(self) -> bool:
        """Prevent mutations when env credentials are present."""
        if not self._is_env_locked():
            return False
        self._env_lock = True
        self._set_status("Disabled by env-lock.", "yellow")
        # Refresh UI to reflect env-lock state (header/banners/rows)
        self._refresh_rows(preferred_name=self._active_account)
        return True

    def _on_form_result(self, payload: dict[str, Any] | None) -> None:
        """Handle add/edit modal result."""
        if payload is None:
            self._set_status("Edit/add cancelled.", "yellow")
            return
        self._save_account(payload)

    def _on_delete_result(self, confirmed_name: str | None) -> None:
        """Handle delete confirmation result."""
        if not confirmed_name:
            self._set_status("Delete cancelled.", "yellow")
            return
        try:
            self._store.remove_account(confirmed_name)
        except AccountStoreError as exc:
            self._set_status(f"Delete failed: {exc}", "red")
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._set_status(f"Unexpected delete error: {exc}", "red")
            return

        self._set_status(f"Account '{confirmed_name}' deleted.", "green")
        # Clear filter before refresh to show all accounts
        self._clear_filter()
        # Refresh rows without preferred name to show all accounts
        # Active account will be cleared if the deleted account was active
        self._refresh_rows(preferred_name=None)
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.focus()

    def _save_account(self, payload: dict[str, Any]) -> None:
        """Persist account data from modal payload."""
        if self._is_env_locked():
            self._set_status("Disabled by env-lock.", "yellow")
            return

        name = str(payload.get("name", ""))
        api_url = str(payload.get("api_url", ""))
        api_key = str(payload.get("api_key", ""))
        set_active = bool(payload.get("set_active", payload.get("mode") == "add"))
        is_edit = payload.get("mode") == "edit"

        try:
            self._store.add_account(name, api_url, api_key, overwrite=is_edit)
        except AccountStoreError as exc:
            self._set_status(f"Save failed: {exc}", "red")
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._set_status(f"Unexpected save error: {exc}", "red")
            return

        if set_active:
            try:
                self._store.set_active_account(name)
                self._active_account = name
            except Exception as exc:  # pragma: no cover - defensive
                self._set_status(f"Saved but could not set active: {exc}", "yellow")
            else:
                self._announce_active_change(name)
                self._update_header()

        self._set_status(f"Account '{name}' saved.", "green")
        # Clear filter before refresh to show all accounts
        self._clear_filter()
        # Refresh rows with preferred name to highlight the saved account
        self._refresh_rows(preferred_name=name)
        # Return focus to the table for immediate hotkey use
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.focus()

    def _refresh_rows(self, preferred_name: str | None = None) -> None:
        """Reload rows from store and preserve filter/cursor."""
        self._env_lock = self._is_env_locked()
        self._all_rows, self._active_account = _build_account_rows_from_store(self._store, self._env_lock)
        self._reload_rows(preferred_name=preferred_name)
        self._update_header()

    def _get_selected_name(self) -> str | None:
        """Return selected account name, if any."""
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        if table.cursor_row is None:
            return None
        try:
            row = table.get_row_at(table.cursor_row)
        except Exception:
            return None
        return str(row[0]) if row else None

    def _is_env_locked(self) -> bool:
        """Return True when env credentials are set (even partially)."""
        return env_credentials_present(partial=True)

    def _announce_active_change(self, name: str) -> None:
        """Surface active account change in status bar."""
        account = self._store.get_account(name) or {}
        host = account.get("api_url", "")
        host_suffix = f" • {host}" if host else ""
        self._set_status(f"Active account ➜ {name}{host_suffix}", "green")

    def _should_block_actions(self) -> bool:
        """Return True when mutating hotkeys are blocked by filter focus."""
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        if filter_input.has_focus:
            self._set_status("Exit filter (Esc or Clear) to add/edit/delete.", "yellow")
            return True
        return False

    def _update_filter_button_visibility(self) -> None:
        """Show clear button only when filter has content."""
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        clear_btn = self.query_one("#filter-clear", Button)
        clear_btn.display = bool(filter_input.value or self._filter_text)
