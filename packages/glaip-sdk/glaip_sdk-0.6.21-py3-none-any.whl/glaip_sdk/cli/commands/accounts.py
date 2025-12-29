"""Account management commands for multi-account profiles.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import getpass
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.text import Text

from glaip_sdk.branding import (
    ACCENT_STYLE,
    ERROR_STYLE,
    INFO,
    NEUTRAL,
    SUCCESS,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.account_store import (
    AccountNotFoundError,
    AccountStore,
    AccountStoreError,
    InvalidAccountNameError,
    get_account_store,
)
from glaip_sdk.cli.commands.common_config import check_connection, render_branding_header
from glaip_sdk.cli.hints import format_command_hint
from glaip_sdk.cli.masking import mask_api_key_display
from glaip_sdk.cli.slash.accounts_shared import env_credentials_present
from glaip_sdk.cli.utils import command_hint
from glaip_sdk.icons import ICON_TOOL
from glaip_sdk.rich_components import AIPPanel, AIPTable

console = Console()


@click.group()
def accounts_group() -> None:
    """Manage multiple account profiles."""


_mask_api_key = mask_api_key_display


def _print_active_account_footer(store: AccountStore) -> None:
    """Print footer showing active account."""
    active = store.get_active_account()
    if active:
        account = store.get_account(active)
        if account:
            url = account.get("api_url", "")
            masked_key = _mask_api_key(account.get("api_key"))
            console.print(f"\n[{SUCCESS_STYLE}]Active account[/]: {active} · {url} · {masked_key}")


@accounts_group.command("list")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def list_accounts(output_json: bool) -> None:
    """List all account profiles."""
    store = get_account_store()
    accounts = store.list_accounts()
    active_account = store.get_active_account()

    if output_json:
        accounts_list = []
        for name, account in accounts.items():
            accounts_list.append(
                {
                    "name": name,
                    "api_url": account.get("api_url", ""),
                    "has_key": bool(account.get("api_key")),
                    "active": name == active_account,
                },
            )
        click.echo(json.dumps(accounts_list, indent=2))
        return

    if not accounts:
        console.print(f"[{WARNING_STYLE}]No accounts found.[/]")
        hint = command_hint("accounts add", slash_command="login")
        if hint:
            console.print(f"Run {format_command_hint(hint) or hint} to add an account.")
        return

    # Render table
    table = AIPTable(title=f"{ICON_TOOL} AIP Accounts")
    table.add_column("Name", style=INFO, width=20)
    table.add_column("API URL", style=SUCCESS, width=40)
    table.add_column("Key (masked)", style=NEUTRAL, width=20)
    table.add_column("Status", style=SUCCESS_STYLE, width=10)

    for name, account in sorted(accounts.items()):
        url = account.get("api_url", "")
        masked_key = _mask_api_key(account.get("api_key"))
        is_active = name == active_account
        status = "[bold green]●[/bold green] active" if is_active else ""

        table.add_row(name, url, masked_key, status)

    console.print(table)

    if active_account:
        console.print(f"\n[{SUCCESS_STYLE}]Active account[/]: {active_account}")

    # Show hint for updating accounts
    console.print(f"\n[{INFO}]💡 Tip[/]: To update an account's URL or key, use: [bold]aip accounts edit <name>[/bold]")


def _build_account_json_payload(
    name: str,
    api_url: str,
    masked_key: str,
    config_path: str,
    is_active: bool,
    env_lock: bool,
    metadata: dict[str, str | None],
) -> dict[str, str | bool | None]:
    """Build JSON payload for account display.

    Args:
        name: Account name.
        api_url: API URL.
        masked_key: Masked API key.
        config_path: Config file path.
        is_active: Whether account is active.
        env_lock: Whether env credentials are set.
        metadata: Account metadata dict.

    Returns:
        JSON payload dict.
    """
    payload: dict[str, str | bool | None] = {
        "name": name,
        "api_url": api_url,
        "api_key_masked": masked_key,
        "config_path": config_path,
        "active": is_active,
        "env_lock": env_lock,
    }
    for key, value in metadata.items():
        if value:
            payload[key] = value
    return payload


def _format_config_path(config_path: str) -> str:
    """Format config path for display, shortening under home."""
    path_obj = Path(config_path).expanduser()
    try:
        home = Path.home().expanduser()
        resolved = path_obj.resolve(strict=False)
        relative = resolved.relative_to(home).as_posix()
        return f"~/{relative}"
    except ValueError:
        # Not under home; return expanded path
        return str(path_obj)
    except OSError:
        # Fall back to original string on resolution errors
        return config_path


def _build_account_display_lines(
    name: str,
    api_url: str,
    masked_key: str,
    config_path: str,
    is_active: bool,
    env_lock: bool,
    metadata: dict[str, str | None],
) -> list[str]:
    """Build display lines for account information.

    Args:
        name: Account name.
        api_url: API URL.
        masked_key: Masked API key.
        config_path: Config file path.
        is_active: Whether account is active.
        env_lock: Whether env credentials are set.
        metadata: Account metadata dict.

    Returns:
        List of formatted display lines.
    """
    lines = [
        f"[{SUCCESS_STYLE}]Name[/]: {name}{' (active)' if is_active else ''}",
        f"[{SUCCESS_STYLE}]API URL[/]: {api_url or 'not set'}",
        f"[{SUCCESS_STYLE}]Key[/]: {masked_key or 'not set'}",
        f"[{SUCCESS_STYLE}]Config[/]: {config_path}",
    ]

    label_map = {
        "notes": "Notes",
        "last_used_at": "Last used",
        "last_validated_at": "Last validated",
        "created_with": "Created with",
    }
    for key, label in label_map.items():
        value = metadata.get(key)
        if value:
            lines.append(f"[{SUCCESS_STYLE}]{label}[/]: {value}")

    if env_lock:
        lines.append(
            f"[{WARNING_STYLE}]Env credentials detected (AIP_API_URL/AIP_API_KEY); stored profile may be ignored.[/]"
        )

    return lines


@accounts_group.command("show")
@click.argument("name")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def show_account(name: str, output_json: bool) -> None:
    """Show details for a single account profile."""
    store = get_account_store()
    account = store.get_account(name)

    if not account:
        console.print(f"[{ERROR_STYLE}]Error: Account '{name}' not found.[/]")
        raise click.Abort()

    api_url = account.get("api_url", "")
    api_key = account.get("api_key")
    masked_key = _mask_api_key(api_key or "")
    active_account = store.get_active_account()
    is_active = active_account == name
    env_lock = env_credentials_present(partial=True)
    config_path_raw = str(store.config_file)
    config_path_display = _format_config_path(config_path_raw)

    metadata = {
        "notes": account.get("notes"),
        "last_used_at": account.get("last_used_at"),
        "last_validated_at": account.get("last_validated_at"),
        "created_with": account.get("created_with"),
    }

    if output_json:
        payload = _build_account_json_payload(name, api_url, masked_key, config_path_raw, is_active, env_lock, metadata)
        click.echo(json.dumps(payload, indent=2))
        return

    lines = _build_account_display_lines(name, api_url, masked_key, config_path_display, is_active, env_lock, metadata)

    lock_badge = " 🔒 Env lock" if env_lock else ""
    console.print(
        AIPPanel(
            "\n".join(lines),
            title=f"AIP Account{lock_badge}",
            border_style=ACCENT_STYLE,
        ),
    )


def _check_account_overwrite(name: str, store: AccountStore, overwrite: bool) -> dict[str, str] | None:
    """Check if account exists and handle overwrite logic.

    Args:
        name: Account name.
        store: Account store instance.
        overwrite: Whether to allow overwrite.

    Returns:
        Existing account dict or None.

    Raises:
        click.Abort: If account exists and overwrite is False.
    """
    existing = store.get_account(name)
    if existing and not overwrite:
        console.print(f"[{WARNING_STYLE}]Account '{name}' already exists.[/] Use --yes to overwrite.")
        raise click.Abort()
    return existing


def _get_credentials_non_interactive(
    url: str,
    read_key_from_stdin: bool,
    name: str,
    command_name: str = "aip accounts add",
) -> tuple[str, str]:
    """Get credentials in non-interactive mode.

    Args:
        url: API URL from flag.
        read_key_from_stdin: Whether to read key from stdin.
        name: Account name (for error messages).
        command_name: Command name for guidance text.

    Returns:
        Tuple of (api_url, api_key).

    Raises:
        click.Abort: If stdin is required but not available, or if --key used without --url.
    """
    if read_key_from_stdin:
        if not sys.stdin.isatty():
            return url, sys.stdin.read().strip()
        console.print(
            f"[{ERROR_STYLE}]Error: --key expects stdin or an explicit value. "
            f"Use '--key <value>' or pipe: cat key.txt | {command_name} {name} --url {url} --key[/]",
        )
        raise click.Abort()
    # URL provided, prompt for key
    console.print(f"\n[{ACCENT_STYLE}]AIP API Key[/]:")
    return url, getpass.getpass("> ")


def _get_credentials_interactive(read_key_from_stdin: bool, existing: dict[str, str] | None) -> tuple[str, str]:
    """Get credentials in interactive mode.

    Args:
        read_key_from_stdin: Whether --key flag was used.
        existing: Existing account data.

    Returns:
        Tuple of (api_url, api_key).

    Raises:
        click.Abort: If --key used without --url.
    """
    if read_key_from_stdin:
        console.print(
            f"[{ERROR_STYLE}]Error: --key requires --url. "
            f"Provide --url with --key <value|-> for non-interactive use or omit --key to be prompted.[/]",
        )
        raise click.Abort()
    # Fully interactive
    _render_configuration_header()
    return _prompt_account_inputs(existing)


def _handle_key_rotation(
    name: str,
    existing_url: str,
    command_name: str,
) -> tuple[str, str]:
    """Handle key rotation using stored URL.

    Args:
        name: Account name (for error messages).
        existing_url: Existing account URL.
        command_name: Command name for error messages.

    Returns:
        Tuple of (api_url, api_key).

    Raises:
        click.Abort: If existing URL is missing.
    """
    if not existing_url:
        console.print(f"[{ERROR_STYLE}]Error: Account '{name}' is missing an API URL. Provide --url to set it.[/]")
        raise click.Abort()
    return _get_credentials_non_interactive(existing_url, True, name, command_name)


def _preserve_existing_values(
    api_url: str,
    api_key: str,
    existing_url: str,
    existing_key: str,
) -> tuple[str, str]:
    """Preserve stored values when blank input is provided during edit.

    Args:
        api_url: Collected API URL.
        api_key: Collected API key.
        existing_url: Existing account URL.
        existing_key: Existing account key.

    Returns:
        Tuple of (api_url, api_key) with preserved values.
    """
    if not api_url and existing_url:
        api_url = existing_url
    if not api_key and existing_key:
        api_key = existing_key
    return api_url, api_key


def _collect_credentials_from_inputs(
    url: str | None,
    api_key_input: str | None,
    name: str,
    existing: dict[str, str] | None,
    command_name: str,
    existing_url: str,
) -> tuple[str, str]:
    """Collect credentials based on input flags and existing data.

    Args:
        url: Optional URL from flag.
        api_key_input: API key value from flag (or "-" when stdin requested).
        name: Account name (for error messages).
        existing: Existing account data.
        command_name: Command name for error messages.
        existing_url: Existing account URL.

    Returns:
        Tuple of (api_url, api_key).
    """
    provided_key = api_key_input if api_key_input not in (None, "-") else None
    read_key_from_stdin = api_key_input == "-"

    if provided_key and url:
        # Fully non-interactive: URL and key provided via flags
        return url, provided_key

    if provided_key:
        # Reuse stored URL if present; otherwise require --url
        if existing_url:
            return existing_url, provided_key
        if existing:
            console.print(
                f"[{ERROR_STYLE}]Error: Account '{name}' is missing an API URL. "
                f"Provide --url to set it when rotating the key.[/]"
            )
        else:
            console.print(
                f"[{ERROR_STYLE}]Error: --key requires --url for new accounts. "
                f"Run without --key for prompts or pass both flags for non-interactive setup.[/]",
            )
        raise click.Abort()

    if url and read_key_from_stdin:
        # Non-interactive: URL from flag, key from stdin
        return _get_credentials_non_interactive(url, True, name, command_name)
    if url:
        # URL provided, prompt for key
        return _get_credentials_non_interactive(url, False, name, command_name)
    if read_key_from_stdin and existing:
        # Key rotation using stored URL
        return _handle_key_rotation(name, existing_url, command_name)
    # Fully interactive or error case
    return _get_credentials_interactive(read_key_from_stdin, existing)


def _collect_account_credentials(
    url: str | None,
    api_key_input: str | None,
    name: str,
    existing: dict[str, str] | None,
) -> tuple[str, str]:
    """Collect account credentials from various input methods.

    Examples:
        # Inline key
        aip accounts add prod --url https://api.example.com --key sk-abc123

        # Stdin (useful for scripts)
        echo "sk-abc123" | aip accounts add prod --url https://api.example.com --key

        # Fully interactive
        aip accounts add prod

    Args:
        url: Optional URL from flag.
        api_key_input: API key value from flag (or "-" when stdin requested).
        name: Account name (for error messages).
        existing: Existing account data.

    Returns:
        Tuple of (api_url, api_key).

    Raises:
        click.Abort: If credentials cannot be collected or are invalid.
    """
    command_name = "aip accounts edit" if existing else "aip accounts add"
    existing_url = existing.get("api_url", "") if existing else ""
    existing_key = existing.get("api_key", "") if existing else ""

    api_url, api_key = _collect_credentials_from_inputs(url, api_key_input, name, existing, command_name, existing_url)

    # Preserve stored values when blank input is provided during edit
    api_url, api_key = _preserve_existing_values(api_url, api_key, existing_url, existing_key)

    if not api_url or not api_key:
        console.print(f"[{ERROR_STYLE}]Error: Both API URL and API key are required.[/]")
        raise click.Abort()
    return api_url, api_key


@accounts_group.command("add")
@click.argument("name")
@click.option("--url", help="API URL (required for non-interactive mode)")
@click.option(
    "--key",
    "api_key_input",
    type=str,
    is_flag=False,
    flag_value="-",
    default=None,
    help="API key value. Pass without a value or '-' to read from stdin. Requires --url for non-interactive use.",
)
@click.option(
    "--yes",
    "overwrite",
    is_flag=True,
    help="Overwrite existing account without prompting",
)
def add_account(
    name: str,
    url: str | None,
    api_key_input: str | None,
    overwrite: bool,
) -> None:
    """Add a new account profile.

    NAME is the account name (1-32 chars, alphanumeric, dash, underscore).

    By default, this command runs interactively, prompting for API URL and key.
    For non-interactive use, provide --url with --key <value> or --key - (stdin).

    If the account already exists, use --yes to overwrite without prompting.
    To update an existing account, use [bold]aip accounts edit <name>[/bold] instead.
    """
    store = get_account_store()

    # Check account overwrite
    existing = _check_account_overwrite(name, store, overwrite)

    # Collect credentials
    api_url, api_key = _collect_account_credentials(url, api_key_input, name, existing)

    # Save account
    try:
        store.add_account(name, api_url, api_key, overwrite=True)
        console.print(Text(f"✅ Account '{name}' saved successfully", style=SUCCESS_STYLE))
        _print_active_account_footer(store)
    except InvalidAccountNameError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e
    except AccountStoreError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e


@accounts_group.command("edit")
@click.argument("name")
@click.option("--url", help="API URL (optional, leave blank to keep current)")
@click.option(
    "--key",
    "api_key_input",
    type=str,
    is_flag=False,
    flag_value="-",
    default=None,
    help="API key value. Pass without a value or '-' to read from stdin. Uses stored URL unless --url is provided.",
)
def edit_account(
    name: str,
    url: str | None,
    api_key_input: str | None,
) -> None:
    """Edit an existing account profile's URL or key.

    NAME is the account name to edit.

    By default, this command runs interactively, showing current values and
    prompting for new ones. Leave fields blank to keep current values.

    For non-interactive use, provide --url to change the URL, --key <value> to rotate the key,
    or --key - (stdin) for scripts. Stored values are reused for any fields not provided.
    """
    store = get_account_store()

    # Account must exist for edit
    existing = store.get_account(name)
    if not existing:
        console.print(f"[{ERROR_STYLE}]Error: Account '{name}' not found.[/]")
        console.print(f"Use [bold]aip accounts add {name}[/bold] to create a new account.")
        raise click.Abort()

    # Collect credentials (will pre-fill existing values in interactive mode)
    api_url, api_key = _collect_account_credentials(url, api_key_input, name, existing)

    # Save account
    try:
        store.add_account(name, api_url, api_key, overwrite=True)
        console.print(Text(f"✅ Account '{name}' updated successfully", style=SUCCESS_STYLE))
        _print_active_account_footer(store)
    except InvalidAccountNameError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e
    except AccountStoreError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e


@accounts_group.command("use")
@click.argument("name")
def use_account(name: str) -> None:
    """Switch to a different account profile."""
    store = get_account_store()

    try:
        account = store.get_account(name)
        if not account:
            console.print(f"[{ERROR_STYLE}]Error: Account '{name}' not found.[/]")
            raise click.Abort()

        url = account.get("api_url", "")
        masked_key = _mask_api_key(account.get("api_key"))
        api_key = account.get("api_key", "")

        if not url or not api_key:
            console.print(
                f"[{ERROR_STYLE}]Error: Account '{name}' is missing credentials. "
                f"Use [bold]aip accounts edit {name}[/bold] to update credentials.[/]"
            )
            raise click.Abort()

        # Always validate before switching
        check_connection(url, api_key, console, abort_on_error=True)

        store.set_active_account(name)

        console.print(
            AIPPanel(
                f"[{SUCCESS_STYLE}]Active account ➜ {name}[/]\nAPI URL: {url}\nKey: {masked_key}",
                title="✅ Account Switched",
                border_style=SUCCESS,
            ),
        )
    except click.Abort:
        # check_connection already printed the failure context; just propagate
        raise
    except AccountNotFoundError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e


@accounts_group.command("rename")
@click.argument("current_name")
@click.argument("new_name")
@click.option(
    "--yes",
    "overwrite",
    is_flag=True,
    help="Overwrite target account if it already exists",
)
def rename_account(current_name: str, new_name: str, overwrite: bool) -> None:
    """Rename an account profile."""
    store = get_account_store()

    if current_name == new_name:
        console.print(f"[{WARNING_STYLE}]Source and target names are the same; nothing to rename.[/]")
        return

    try:
        if not store.get_account(current_name):
            console.print(f"[{ERROR_STYLE}]Error: Account '{current_name}' not found.[/]")
            raise click.Abort()

        # Guard before calling store.rename_account to keep consistent messaging with add --yes
        if store.get_account(new_name) and not overwrite:
            console.print(f"[{WARNING_STYLE}]Account '{new_name}' already exists.[/] Use --yes to overwrite.")
            raise click.Abort()

        store.rename_account(current_name, new_name, overwrite=overwrite)
        console.print(Text(f"✅ Account '{current_name}' renamed to '{new_name}'", style=SUCCESS_STYLE))
        _print_active_account_footer(store)
    except AccountStoreError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e
    except Exception as e:  # pragma: no cover - defensive catch-all
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e


@accounts_group.command("remove")
@click.argument("name")
@click.option("--yes", "force", is_flag=True, help="Skip confirmation prompt")
def remove_account(name: str, force: bool) -> None:
    """Remove an account profile."""
    store = get_account_store()

    account = store.get_account(name)
    if not account:
        console.print(f"[{WARNING_STYLE}]Account '{name}' not found.[/]")
        return

    if not force:
        console.print(f"[{WARNING_STYLE}]This will remove account '{name}'.[/]")
        confirm = input("Are you sure? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            console.print("Cancelled.")
            return

    try:
        store.remove_account(name)
        console.print(Text(f"✅ Account '{name}' removed", style=SUCCESS_STYLE))

        # Show new active account if it changed
        active = store.get_active_account()
        if active:
            console.print(f"[{SUCCESS_STYLE}]Active account is now: {active}[/]")
    except AccountStoreError as e:
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        raise click.Abort() from e


def _render_configuration_header() -> None:
    """Display the interactive configuration heading/banner."""
    render_branding_header(console, "[bold]AIP Account Configuration[/bold]")


def _prompt_account_inputs(existing: dict[str, str] | None) -> tuple[str, str]:
    """Interactively prompt for account credentials."""
    console.print("\n[bold]Enter your AIP configuration:[/bold]")
    if existing:
        console.print("(Leave blank to keep current values)")
    console.print("─" * 50)

    # Prompt for URL
    current_url = existing.get("api_url", "") if existing else ""
    suffix = f"(current: {current_url})" if current_url else ""
    console.print(f"\n[{ACCENT_STYLE}]AIP API URL[/] {suffix}:")
    new_url = input("> ").strip()
    api_url = new_url if new_url else current_url
    if not api_url:
        api_url = "https://your-aip-instance.com"

    # Prompt for key
    current_key_masked = _mask_api_key(existing.get("api_key")) if existing else ""
    suffix = f"(current: {current_key_masked})" if current_key_masked else ""
    console.print(f"\n[{ACCENT_STYLE}]AIP API Key[/] {suffix}:")
    new_key = getpass.getpass("> ")
    if new_key:
        api_key = new_key
    elif existing:
        api_key = existing.get("api_key", "")
    else:
        api_key = ""

    return api_url, api_key
