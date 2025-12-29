"""Main CLI entry point for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import logging
import subprocess
import sys
from typing import Any

import click
from rich.console import Console
from glaip_sdk.branding import (
    ERROR,
    ERROR_STYLE,
    INFO,
    INFO_STYLE,
    NEUTRAL,
    SUCCESS,
    SUCCESS_STYLE,
    WARNING,
    WARNING_STYLE,
    AIPBranding,
)
from glaip_sdk.cli.account_store import get_account_store
from glaip_sdk.cli.auth import resolve_credentials
from glaip_sdk.cli.commands.accounts import accounts_group
from glaip_sdk.cli.commands.agents import agents_group
from glaip_sdk.cli.commands.configure import (
    config_group,
    configure_command,
)
from glaip_sdk.cli.commands.mcps import mcps_group
from glaip_sdk.cli.commands.models import models_group
from glaip_sdk.cli.commands.tools import tools_group
from glaip_sdk.cli.commands.transcripts import transcripts_group
from glaip_sdk.cli.commands.update import (
    _build_missing_pip_guidance,
    _build_manual_upgrade_command,
    _build_upgrade_command,
    _is_pip_available,
    _is_uv_managed_environment,
    update_command,
)
from glaip_sdk.cli.config import load_config
from glaip_sdk.cli.hints import in_slash_mode
from glaip_sdk.cli.transcript import get_transcript_cache_stats
from glaip_sdk.cli.update_notifier import maybe_notify_update
from glaip_sdk.cli.utils import format_size, sdk_version, spinner_context, update_spinner
from glaip_sdk.config.constants import (
    DEFAULT_AGENT_RUN_TIMEOUT,
)
from glaip_sdk.icons import ICON_AGENT
from glaip_sdk.rich_components import AIPPanel, AIPTable

# Constants
UPDATE_ERROR_TITLE = "❌ Update Error"

Client: type[Any] | None = None


def _resolve_client_class() -> type[Any]:
    """Resolve the Client class lazily to avoid heavy imports at CLI startup."""
    global Client
    if Client is None:
        from glaip_sdk import Client as ClientClass  # noqa: PLC0415

        Client = ClientClass
    return Client


def _suppress_chatty_loggers() -> None:
    """Silence noisy SDK/httpx logs for CLI output."""
    noisy_loggers = [
        "glaip_sdk.client",
        "httpx",
        "httpcore",
    ]
    for name in noisy_loggers:
        logger = logging.getLogger(name)
        # Respect existing configuration: only raise level when unset,
        # and avoid changing propagation if a custom handler is already attached.
        if logger.level == logging.NOTSET:
            logger.setLevel(logging.WARNING)
        if not logger.handlers:
            logger.propagate = False


# Import SlashSession for potential mocking in tests
try:
    from glaip_sdk.cli.slash import SlashSession
except ImportError:  # pragma: no cover - optional slash dependencies
    # Slash dependencies might not be available in all environments
    SlashSession = None

# Constants
AVAILABLE_STATUS = "✅ Available"


@click.group(invoke_without_command=True)
@click.version_option(package_name="glaip-sdk", prog_name="aip")
@click.option(
    "--api-url",
    help="(Deprecated) AIP API URL; use profiles via --account instead",
    hidden=True,
)
@click.option(
    "--api-key",
    help="(Deprecated) AIP API Key; use profiles via --account instead",
    hidden=True,
)
@click.option("--timeout", default=30.0, help="Request timeout in seconds")
@click.option(
    "--view",
    "view",
    type=click.Choice(["rich", "plain", "json", "md"]),
    default="rich",
    help="Output view format",
)
@click.option("--no-tty", is_flag=True, help="Disable TTY renderer")
@click.option(
    "--account",
    "account_name",
    help="Target a named account profile for this command",
    hidden=True,  # Hidden by default, shown with --help --all
)
@click.pass_context
def main(
    ctx: Any,
    api_url: str | None,
    api_key: str | None,
    timeout: float | None,
    view: str | None,
    no_tty: bool,
    account_name: str | None,
) -> None:
    r"""GL AIP SDK Command Line Interface.

    A comprehensive CLI for managing GL AIP resources including
    agents, tools, MCPs, and more.

    \b
    Examples:
      aip version                     # Show detailed version info
      aip configure                   # Configure credentials
      aip accounts add prod           # Add account profile
      aip accounts use staging        # Switch account
      aip agents list                 # List all agents
      aip tools create my_tool.py     # Create a new tool
      aip agents run my-agent "Hello world"  # Run an agent

    \b
    NEW: Store multiple accounts via 'aip accounts add' and switch with 'aip accounts use'.
    """
    # Store configuration in context
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["api_key"] = api_key
    ctx.obj["timeout"] = timeout
    ctx.obj["view"] = view
    ctx.obj["account_name"] = account_name

    _suppress_chatty_loggers()

    ctx.obj["tty"] = not no_tty

    launching_slash = (
        ctx.invoked_subcommand is None
        and not ctx.resilient_parsing
        and _should_launch_slash(ctx)
        and SlashSession is not None
    )

    if not ctx.resilient_parsing and ctx.obj["tty"] and not launching_slash:
        console = Console()
        preferred_console = maybe_notify_update(
            sdk_version(),
            console=console,
            ctx=ctx,
            slash_command="update",
        )
        ctx.obj["_preferred_console"] = preferred_console or console

    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        if launching_slash:
            session = SlashSession(ctx)
            session.run()
            ctx.exit()
        else:
            click.echo(ctx.get_help())
            ctx.exit()


# Add command groups
main.add_command(accounts_group)
main.add_command(agents_group)
main.add_command(config_group)
main.add_command(tools_group)
main.add_command(mcps_group)
main.add_command(models_group)
main.add_command(transcripts_group)

# Add top-level commands
main.add_command(configure_command)
main.add_command(update_command)


# Tip: `--version` is provided by click.version_option above.


def _should_launch_slash(ctx: click.Context) -> bool:
    """Determine whether to open the command palette automatically."""
    ctx_obj = ctx.obj or {}
    if not bool(ctx_obj.get("tty", True)):
        return False

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False

    return True


def _load_and_merge_config(ctx: click.Context) -> dict:
    """Load configuration from multiple sources and merge them."""
    context_config = ctx.obj or {}
    account_name = context_config.get("account_name")

    # Resolve credentials using new account store system
    api_url, api_key, source = resolve_credentials(
        account_name=account_name,
        api_url=context_config.get("api_url"),
        api_key=context_config.get("api_key"),
    )

    # Load other config values (timeout, etc.) from legacy config
    legacy_config = load_config()
    timeout = context_config.get("timeout") or legacy_config.get("timeout")

    return {
        "api_url": api_url,
        "api_key": api_key,
        "timeout": timeout,
        "_source": source,  # Track where credentials came from
    }


def _validate_config_and_show_error(config: dict, console: Console) -> None:
    """Validate configuration and show error if incomplete."""
    store = get_account_store()
    has_accounts = bool(store.list_accounts())
    if not config.get("api_url") or not config.get("api_key"):
        no_accounts_hint = "" if has_accounts else "\n   • No accounts found; create one now to continue"
        console.print(
            AIPPanel(
                f"[{ERROR_STYLE}]❌ Configuration incomplete[/]\n\n"
                f"🔍 Current config:\n"
                f"   • API URL: {config.get('api_url', 'Not set')}\n"
                f"   • API Key: {'***' + config.get('api_key', '')[-4:] if config.get('api_key') else 'Not set'}\n\n"
                f"💡 To fix this:\n"
                f"   • Run 'aip accounts add default' to set up credentials\n"
                f"   • Or run 'aip configure' for interactive setup\n"
                f"   • Or run 'aip accounts list' to see current accounts{no_accounts_hint}",
                title="❌ Configuration Error",
                border_style=ERROR,
            ),
        )
        console.print(f"\n[{SUCCESS_STYLE}]✅ AIP - Ready[/] (SDK v{sdk_version()}) - Configure to connect")
        sys.exit(1)


def _resolve_status_console(ctx: Any) -> tuple[Console, bool]:
    """Return the console to use and whether we are in slash mode."""
    ctx_obj = ctx.obj if isinstance(ctx.obj, dict) else None
    console_override = ctx_obj.get("_slash_console") if ctx_obj else None
    preferred_console = ctx_obj.get("_preferred_console") if ctx_obj else None
    if preferred_console is None:
        # In heavily mocked tests, maybe_notify_update may be patched with a return_value
        preferred_console = getattr(maybe_notify_update, "return_value", None)
    console = console_override or preferred_console or Console()
    slash_mode = in_slash_mode(ctx)
    return console, slash_mode


def _render_status_heading(console: Console, slash_mode: bool, config: dict) -> bool:
    """Print the status heading/banner.

    Returns True if a generic ready line was printed (to avoid duplication).
    """
    del slash_mode  # heading now consistent across invocation contexts
    ready_printed = False
    console.print(f"[{INFO_STYLE}]GL AIP status[/]")
    console.print("")

    # Show account information
    source = str(config.get("_source") or "unknown")
    account_name = None
    if source.startswith("account:") or source.startswith("active_profile:"):
        account_name = source.split(":", 1)[1]

    if account_name:
        store = get_account_store()
        account = store.get_account(account_name)
        if account:
            url = account.get("api_url", "")
            # Format source to match spec: "active_profile" instead of "active_profile:name"
            display_source = source.split(":")[0] if ":" in source else source
            console.print(f"[{SUCCESS_STYLE}]Account: {account_name} (source={display_source}) · API URL: {url}[/]")
        else:
            console.print(f"[{SUCCESS_STYLE}]✅ GL AIP ready[/] (SDK v{sdk_version()})")
            ready_printed = True
    elif source == "flag":
        console.print(f"[{SUCCESS_STYLE}]Account: (source={source})[/]")
    else:
        console.print(f"[{SUCCESS_STYLE}]✅ GL AIP ready[/] (SDK v{sdk_version()})")
        ready_printed = True

    return ready_printed


def _collect_cache_summary() -> tuple[str | None, str | None]:
    """Collect transcript cache summary and optional note."""
    try:
        cache_stats = get_transcript_cache_stats()
    except Exception:
        return "[dim]Saved transcripts[/dim]: unavailable", None

    runs_text = f"{cache_stats.entry_count} runs saved"
    if cache_stats.total_bytes:
        size_part = f" · {format_size(cache_stats.total_bytes)} used"
    else:
        size_part = ""

    cache_line = f"[dim]Saved transcripts[/dim]: {runs_text}{size_part} · {cache_stats.cache_dir}"
    return cache_line, None


def _display_cache_summary(console: Console, slash_mode: bool, cache_line: str | None, cache_note: str | None) -> None:
    """Render the cache summary details."""
    if cache_line:
        console.print(cache_line)
    if cache_note and not slash_mode:
        console.print(cache_note)


def _safe_list_call(obj: Any, attr: str) -> list[Any]:
    """Call list-like client methods defensively, returning an empty list on failure."""
    func = getattr(obj, attr, None)
    if callable(func):
        try:
            return func()
        except Exception as exc:
            logging.getLogger(__name__).debug(
                "Failed to call %s on %s: %s", attr, type(obj).__name__, exc, exc_info=True
            )
            return []
    return []


def _get_client_from_config(config: dict) -> Any:
    """Return a Client instance built from config."""
    client_class = _resolve_client_class()
    return client_class(
        api_url=config["api_url"],
        api_key=config["api_key"],
        timeout=config.get("timeout", 30.0),
    )


def _create_and_test_client(config: dict, console: Console, *, compact: bool = False) -> Any:
    """Create client and test connection by fetching resources."""
    client: Any = _get_client_from_config(config)

    # Test connection by listing resources with a spinner where available
    try:
        with spinner_context(
            None,
            "[bold blue]Checking GL AIP status…[/bold blue]",
            console_override=console,
            spinner_style=INFO,
        ) as status_indicator:
            update_spinner(status_indicator, "[bold blue]Fetching agents…[/bold blue]")
            agents = client.list_agents()

            update_spinner(status_indicator, "[bold blue]Fetching tools…[/bold blue]")
            tools = client.list_tools()

            update_spinner(status_indicator, "[bold blue]Fetching MCPs…[/bold blue]")
            mcps = client.list_mcps()
    except Exception as e:
        # Show AIP Ready status even if connection fails
        if compact:
            status_text = "API call failed"
            api_url = getattr(client, "api_url", config.get("api_url", ""))
            console.print(f"[dim]• Base URL[/dim]: {api_url} ({status_text})")
            console.print(f"[{ERROR_STYLE}]• Error[/]: {e}")
            console.print("[dim]• Tip[/dim]: Check network connectivity or API permissions and try again.")
            console.print("[dim]• Resources[/dim]: unavailable")
        else:
            api_url = getattr(client, "api_url", config.get("api_url", ""))
            console.print(
                AIPPanel(
                    f"[{WARNING_STYLE}]⚠️  Connection established but API call failed[/]\n"
                    f"🔗 API URL: {api_url}\n"
                    f"❌ Error: {e}\n\n"
                    f"💡 This usually means:\n"
                    f"   • Network connectivity issues\n"
                    f"   • API permissions problems\n"
                    f"   • Backend service issues",
                    title="⚠️  Partial Connection",
                    border_style=WARNING,
                ),
            )
        return client

    # Create status table
    table = AIPTable(title="🔗 GL AIP Status")
    table.add_column("Resource", style=INFO, width=15)
    table.add_column("Count", style=NEUTRAL, width=10)
    table.add_column("Status", style=SUCCESS_STYLE, width=15)

    table.add_row("Agents", str(len(agents)), AVAILABLE_STATUS)
    table.add_row("Tools", str(len(tools)), AVAILABLE_STATUS)
    table.add_row("MCPs", str(len(mcps)), AVAILABLE_STATUS)

    if compact:
        connection_summary = "GL AIP reachable"
        console.print(f"[dim]• Base URL[/dim]: {client.api_url} ({connection_summary})")
        console.print(f"[dim]• Agent timeout[/dim]: {DEFAULT_AGENT_RUN_TIMEOUT}s")
        console.print(f"[dim]• Resources[/dim]: agents {len(agents)}, tools {len(tools)}, mcps {len(mcps)}")
    else:
        console.print(  # pragma: no cover - UI display formatting
            AIPPanel(
                f"[{SUCCESS_STYLE}]✅ Connected to GL AIP[/]\n"
                f"🔗 API URL: {client.api_url}\n"
                f"{ICON_AGENT} Agent Run Timeout: {DEFAULT_AGENT_RUN_TIMEOUT}s",
                title="🚀 Connection Status",
                border_style=SUCCESS,
            ),
        )

        console.print(table)  # pragma: no cover - UI display formatting

    return client


def _handle_connection_error(config: dict, console: Console, error: Exception) -> None:
    """Handle connection errors and show troubleshooting information."""
    console.print(
        AIPPanel(
            f"[{ERROR_STYLE}]❌ Connection failed[/]\n\n"
            f"🔍 Error: {error}\n\n"
            f"💡 Troubleshooting steps:\n"
            f"   • Verify your API URL and key are correct\n"
            f"   • Check network connectivity to {config.get('api_url', 'your API')}\n"
            f"   • Run 'aip configure' to update credentials\n"
            f"   • Run 'aip config list' to check configuration",
            title="❌ Connection Error",
            border_style=ERROR,
        ),
    )
    # Log and return; callers decide whether to exit.


@main.command()
@click.option(
    "--account",
    "account_name",
    help="Target a named account profile for this command",
)
@click.pass_context
def status(ctx: Any, account_name: str | None) -> None:
    """Show connection status and basic info."""
    config: dict = {}
    console: Console | None = None
    try:
        if account_name:
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj["account_name"] = account_name

        console, slash_mode = _resolve_status_console(ctx)

        # Load and merge configuration
        config = _load_and_merge_config(ctx)

        ready_printed = _render_status_heading(console, slash_mode, config)
        if not ready_printed:
            console.print(f"[{SUCCESS_STYLE}]✅ GL AIP ready[/] (SDK v{sdk_version()})")

        cache_result = _collect_cache_summary()
        if isinstance(cache_result, tuple) and len(cache_result) == 2:
            cache_line, cache_note = cache_result
        else:
            cache_line, cache_note = cache_result, None
        _display_cache_summary(console, slash_mode, cache_line, cache_note)

        # Validate configuration
        _validate_config_and_show_error(config, console)

        # Create and test client connection using unified compact layout
        client = _create_and_test_client(config, console, compact=True)
        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    except Exception as e:
        # Handle any unexpected errors during the process and exit with error code
        fallback_console = console or Console()
        _handle_connection_error(config or {}, fallback_console, e)
        sys.exit(1)


@main.command()
def version() -> None:
    """Show version information."""
    branding = AIPBranding.create_from_sdk(sdk_version=sdk_version(), package_name="glaip-sdk")
    branding.display_version_panel()


@main.command()
@click.option("--check-only", is_flag=True, help="Only check for updates without installing")
@click.option(
    "--force",
    is_flag=True,
    help="Force reinstall even if already up-to-date (adds --force-reinstall)",
)
def update(check_only: bool, force: bool) -> None:
    """Update AIP SDK to the latest version from PyPI."""
    slash_mode = in_slash_mode()
    try:
        console = Console()

        if check_only:
            console.print(
                AIPPanel(
                    "[bold blue]🔍 Checking for updates...[/bold blue]\n\n💡 To install updates, run: aip update",
                    title="📋 Update Check",
                    border_style="blue",
                ),
            )
            return

        update_hint = ""
        if not slash_mode:
            update_hint = "\n💡 Use --check-only to just check for updates"

        console.print(
            AIPPanel(
                "[bold blue]🔄 Updating AIP SDK...[/bold blue]\n\n"
                "📦 This will update the package from PyPI"
                f"{update_hint}",
                title="Update Process",
                border_style="blue",
                padding=(0, 1),
            ),
        )

        # Update using pip or uv tool install
        try:
            is_uv = _is_uv_managed_environment()
            if not is_uv and not _is_pip_available():
                error_detail, troubleshooting = _build_missing_pip_guidance(
                    include_prerelease=False,
                    package_name="glaip-sdk",
                    force_reinstall=force,
                )
                console.print(
                    AIPPanel(
                        f"[{ERROR_STYLE}]❌ Update failed[/]\n\n🔍 Error: {error_detail}\n\n{troubleshooting}",
                        title=UPDATE_ERROR_TITLE,
                        border_style=ERROR,
                        padding=(0, 1),
                    ),
                )
                sys.exit(1)
            cmd = list(
                _build_upgrade_command(
                    include_prerelease=False,
                    package_name="glaip-sdk",
                    is_uv=is_uv,
                    force_reinstall=force,
                )
            )

            manual_cmd = _build_manual_upgrade_command(
                include_prerelease=False,
                package_name="glaip-sdk",
                is_uv=is_uv,
                force_reinstall=force,
            )
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            verify_hint = ""
            if not slash_mode:
                verify_hint = "\n💡 Restart your terminal or run 'aip --version' to verify"

            console.print(
                AIPPanel(
                    f"[{SUCCESS_STYLE}]✅ Update successful![/]\n\n"
                    "🔄 AIP SDK has been updated to the latest version"
                    f"{verify_hint}",
                    title="🎉 Update Complete",
                    border_style=SUCCESS,
                    padding=(0, 1),
                ),
            )

            # Show new version
            version_result = subprocess.run(
                [sys.executable, "-m", "glaip_sdk.cli.main", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            console.print(f"📋 New version: {version_result.stdout.strip()}")

        except FileNotFoundError:
            troubleshooting = f"💡 Troubleshooting:\n   • Try running: {manual_cmd}\n"
            if is_uv:
                troubleshooting += "   • Ensure uv is installed: curl -LsSf https://astral.sh/uv/install.sh | sh"
                error_detail = "uv executable not found in your PATH."
            else:
                troubleshooting += "   • Ensure Python and pip are installed"
                error_detail = "Python executable not found to run pip."
            console.print(
                AIPPanel(
                    f"[{ERROR_STYLE}]❌ Update failed[/]\n\n🔍 Error: {error_detail}\n\n{troubleshooting}",
                    title=UPDATE_ERROR_TITLE,
                    border_style=ERROR,
                    padding=(0, 1),
                ),
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            troubleshooting = (
                f"💡 Troubleshooting:\n   • Check your internet connection\n   • Try running: {manual_cmd}\n"
            )
            if is_uv:
                troubleshooting += "   • Ensure uv is installed: curl -LsSf https://astral.sh/uv/install.sh | sh"
            else:
                troubleshooting += "   • Check if you have write permissions"

            console.print(
                AIPPanel(
                    f"[{ERROR_STYLE}]❌ Update failed[/]\n\n🔍 Error: {e.stderr}\n\n{troubleshooting}",
                    title=UPDATE_ERROR_TITLE,
                    border_style=ERROR,
                    padding=(0, 1),
                ),
            )
            sys.exit(1)

    except ImportError:
        console.print(
            AIPPanel(
                f"[{ERROR_STYLE}]❌ Rich library not available[/]\n\n"
                "💡 Install rich: pip install rich\n"
                "   Then try: aip update",
                title="❌ Missing Dependency",
                border_style=ERROR,
            ),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
