"""Configuration management commands.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import getpass
import json
import os
import re
import sys
import threading
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.text import Text

from glaip_sdk.branding import ACCENT_STYLE, ERROR_STYLE, INFO, NEUTRAL, SUCCESS_STYLE, WARNING_STYLE

# Optional import for gitignore support; warn when missing to avoid silent expansion
try:
    import pathspec  # type: ignore[import-untyped]  # noqa: PLC0415
except ImportError:  # pragma: no cover - optional dependency
    pathspec = None  # type: ignore[assignment]
from glaip_sdk.cli.account_store import get_account_store
from glaip_sdk.cli.commands.common_config import check_connection, render_branding_header
from glaip_sdk.cli.config import CONFIG_FILE, load_config, save_config
from glaip_sdk.cli.hints import format_command_hint
from glaip_sdk.cli.masking import mask_api_key_display
from glaip_sdk.cli.rich_helpers import markup_text
from glaip_sdk.cli.utils import command_hint
from glaip_sdk.rich_components import AIPTable

console = Console()
stderr_console = Console(file=sys.stderr)
_PATHSPEC_WARNED = False
_PATHSPEC_WARNED_LOCK = threading.Lock()

# Hard deprecation banner for legacy config commands (v0.6.x)
CONFIG_HARD_DEPRECATION_MSG = (
    f"[{WARNING_STYLE}]⚠️  DEPRECATED: 'aip config ...' commands will be removed in v0.7.0. "
    "Use 'aip accounts ...' (list/add/use/remove/edit) or 'aip configure' for the wizard. "
    "Set AIP_ENABLE_LEGACY_CONFIG=1 to temporarily re-enable these commands.[/]"
)

# Soft deprecation banner (for when env flag is set)
CONFIG_SOFT_DEPRECATION_MSG = (
    f"[{WARNING_STYLE}]Deprecated: 'aip config ...' will be removed in v0.7.0. "
    "Use 'aip accounts ...' (list/add/use/remove/edit) or 'aip configure' for the wizard.[/]"
)

# Target removal version
TARGET_REMOVAL_VERSION = "v0.7.0"

# Command hint constant
CONFIG_CONFIGURE_HINT = "config configure"
_DEFAULT_EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    "build",
    "dist",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}
_MAX_SCAN_FILE_SIZE = 2 * 1024 * 1024  # 2MB cap for default scans


def _is_legacy_config_enabled() -> bool:
    """Check if legacy config commands are enabled via environment variable."""
    env_value = os.environ.get("AIP_ENABLE_LEGACY_CONFIG", "").strip().lower()
    return env_value in ("1", "true", "yes", "on")


def _print_config_deprecation() -> None:
    """Print a standardized deprecation warning for legacy config commands."""
    if _is_legacy_config_enabled():
        # Soft deprecation when env flag is set
        stderr_console.print(CONFIG_SOFT_DEPRECATION_MSG)
    else:
        # Hard deprecation when env flag is not set
        stderr_console.print(CONFIG_HARD_DEPRECATION_MSG)


def _check_legacy_config_gate() -> bool:
    """Return True if legacy config commands are allowed; print banner otherwise."""
    if not _is_legacy_config_enabled():
        stderr_console.print(CONFIG_HARD_DEPRECATION_MSG)
        return False
    return True


def _enforce_legacy_config_gate() -> None:
    """CLI-only gate: exit with code 0 when legacy commands are disabled."""
    if not _check_legacy_config_gate():
        # Spec requires non-breaking exit after banner
        sys.exit(0)


def _emit_telemetry_event(_event_name: str, properties: dict[str, Any] | None = None) -> None:
    """Emit telemetry event for legacy command usage tracking.

    This is a stub implementation that can be connected to a real telemetry system.
    For now, it's a no-op but structured to allow easy integration.

    Args:
        _event_name: Name of the telemetry event (prefixed with _ to indicate unused for now).
        properties: Optional event properties dictionary.

    Note:
        TODO: Connect to actual telemetry system when available.
    """
    if properties is None:
        properties = {}
    # Mark as intentionally unused until telemetry system is integrated
    del _event_name, properties


@click.group()
def config_group() -> None:
    """Configuration management operations (deprecated).

    These commands are deprecated and will be removed in v0.7.0.
    Use 'aip accounts ...' commands instead.
    Set AIP_ENABLE_LEGACY_CONFIG=1 to temporarily re-enable.
    """
    _enforce_legacy_config_gate()
    _print_config_deprecation()
    # Emit telemetry for legacy command invocation
    _emit_telemetry_event(
        "config.command",
        {
            "phase": "hard_deprecation",
            "gated_by_env": _is_legacy_config_enabled(),
        },
    )


@config_group.command("list")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
def list_config(ctx: click.Context, output_json: bool) -> None:
    """List current configuration.

    Deprecated: run 'aip accounts list' for profile-aware output.
    """
    _enforce_legacy_config_gate()
    console.print(f"[{WARNING_STYLE}]Deprecated: run 'aip accounts list' for profile-aware output.[/]")

    # Delegate to accounts list by invoking the command
    from glaip_sdk.cli.commands.accounts import accounts_group  # noqa: PLC0415

    list_cmd = accounts_group.get_command(ctx, "list")
    if list_cmd:
        ctx.invoke(list_cmd, output_json=output_json)


CONFIG_VALUE_TYPES: dict[str, str] = {
    "api_url": "string",
    "api_key": "string",
    "timeout": "float",
    "history_default_limit": "int",
}


def _parse_bool_config(value: str) -> bool:
    """Parse boolean-like CLI input."""
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise click.ClickException("Invalid boolean value. Use one of: true, false, yes, no, 1, 0.")


def _parse_int_config(value: str) -> int:
    """Parse integer CLI input with non-negative enforcement."""
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise click.ClickException("Invalid integer value.") from exc
    if parsed < 0:
        raise click.ClickException("Value must be greater than or equal to 0.")
    return parsed


def _parse_float_config(value: str) -> float:
    """Parse float CLI input with non-negative enforcement."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise click.ClickException("Invalid float value.") from exc
    if parsed < 0:
        raise click.ClickException("Value must be greater than or equal to 0.")
    return parsed


def _coerce_config_value(key: str, raw_value: str) -> str | bool | int | float:
    """Convert CLI string values to their target config types."""
    kind = CONFIG_VALUE_TYPES.get(key, "string")
    if kind == "bool":
        return _parse_bool_config(raw_value)
    if kind == "int":
        return _parse_int_config(raw_value)
    if kind == "float":
        return _parse_float_config(raw_value)
    return raw_value


@config_group.command("set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--account",
    "account_name",
    help="Account name to set value for (defaults to active account)",
)
def set_config(key: str, value: str, account_name: str | None) -> None:
    """Set a configuration value.

    For api_url and api_key, this operates on the specified account (or active account).
    Other keys (timeout, history_default_limit) are global settings.

    Deprecated: use 'aip accounts edit <name>' instead.
    """
    _enforce_legacy_config_gate()
    # For other keys, use legacy config
    valid_keys = tuple(CONFIG_VALUE_TYPES.keys())
    if key not in valid_keys:
        console.print(f"[{ERROR_STYLE}]Error: Invalid key '{key}'. Valid keys are: {', '.join(valid_keys)}[/]")
        raise click.ClickException(f"Invalid configuration key: {key}")

    store = get_account_store()
    # For api_url and api_key, update account profile but also mirror to legacy config
    if key in ("api_url", "api_key"):
        target_account = account_name or store.get_active_account() or "default"
        try:
            account = store.get_account(target_account) or {}
            account[key] = value
            store.add_account(
                target_account,
                account.get("api_url", ""),
                account.get("api_key", ""),
                overwrite=True,
            )
        except Exception:
            # If account store persistence fails (e.g., mocked I/O), continue with legacy config
            pass

        # Always update legacy config for backward compatibility and test isolation
        legacy_config = load_config()
        legacy_config[key] = value
        save_config(legacy_config)

        display_value = _mask_api_key(value) if key == "api_key" else value
        console.print(Text(f"✅ Set {key} = {display_value} for account '{target_account}'", style=SUCCESS_STYLE))
        return

    coerced_value = _coerce_config_value(key, value)
    config = load_config()
    config[key] = coerced_value
    save_config(config)

    display_value = _mask_api_key(coerced_value) if key == "api_key" else str(coerced_value)
    console.print(Text(f"✅ Set {key} = {display_value}", style=SUCCESS_STYLE))


@config_group.command("get")
@click.argument("key")
def get_config(key: str) -> None:
    """Get a configuration value.

    Deprecated: use 'aip accounts show <name>' or read ~/.aip/config.yaml directly.
    """
    _enforce_legacy_config_gate()
    config = load_config()

    value = config.get(key)

    # Fallback to account store for api_url/api_key when legacy config lacks the key
    if value is None and key in {"api_url", "api_key"}:
        store = get_account_store()
        active = store.get_active_account() or "default"
        account = store.get_account(active) or {}
        value = account.get(key)

    if value is None:
        console.print(markup_text(f"[{WARNING_STYLE}]Configuration key '{key}' not found.[/]"))
        raise click.ClickException(f"Configuration key not found: {key}")

    if key == "api_key":
        console.print(_mask_api_key(value))
    else:
        console.print(value)


@config_group.command("unset")
@click.argument("key")
def unset_config(key: str) -> None:
    """Remove a configuration value.

    Deprecated: use 'aip accounts edit <name>' to clear specific fields.
    """
    _enforce_legacy_config_gate()
    config = load_config()

    if key not in config:
        console.print(markup_text(f"[{WARNING_STYLE}]Configuration key '{key}' not found.[/]"))
        return

    del config[key]
    save_config(config)

    console.print(Text(f"✅ Removed {key} from configuration", style=SUCCESS_STYLE))


@config_group.command("reset")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def reset_config(force: bool) -> None:
    """Reset all configuration to defaults.

    Deprecated: use 'aip accounts remove <name>' for each account or manually edit ~/.aip/config.yaml.
    """
    _enforce_legacy_config_gate()
    if not force:
        console.print(f"[{WARNING_STYLE}]This will remove all AIP configuration.[/]")
        confirm = input("Are you sure? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            console.print("Cancelled.")
            return

    config_data = load_config()
    file_exists = CONFIG_FILE.exists()

    if not file_exists and not config_data:
        console.print(f"[{WARNING_STYLE}]No configuration found to reset.[/]")
        console.print(Text("✅ Configuration reset (nothing to remove).", style=SUCCESS_STYLE))
        return

    if file_exists:
        try:
            CONFIG_FILE.unlink()
        except FileNotFoundError:  # pragma: no cover - defensive cleanup
            pass
    else:
        # In-memory configuration (e.g., tests) needs explicit clearing
        save_config({})

    hint = command_hint(CONFIG_CONFIGURE_HINT, slash_command="login")
    message = Text("✅ Configuration reset.", style=SUCCESS_STYLE)
    if hint:
        message.append(f" Run '{hint}' to set up again.")
    console.print(message)


def _configure_interactive(account_name: str | None = None) -> None:
    """Shared configuration logic for both configure commands."""
    store = get_account_store()

    # Determine account name (use provided, active, or default)
    if not account_name:
        account_name = store.get_active_account() or "default"

    # Get existing account if it exists
    existing = store.get_account(account_name)

    _render_configuration_header()
    config = _prompt_configuration_inputs_for_account(existing)

    # Save to account store
    api_url = config.get("api_url", "")
    api_key = config.get("api_key", "")
    if api_url and api_key:
        store.add_account(account_name, api_url, api_key, overwrite=True)
        console.print(Text(f"\n✅ Configuration saved to account '{account_name}'", style=SUCCESS_STYLE))

    _test_and_report_connection_for_account(account_name)
    _print_post_configuration_hints()
    # Show active account footer
    from glaip_sdk.cli.commands.accounts import _print_active_account_footer  # noqa: PLC0415

    _print_active_account_footer(store)


@config_group.command("audit")
@click.option(
    "--path",
    "paths",
    multiple=True,
    help="Glob pattern(s) to search (repeatable). Defaults to current directory.",
)
@click.option(
    "--stdin",
    "read_from_stdin",
    is_flag=True,
    help="Read file list from stdin (one path per line).",
)
@click.option(
    "--no-gitignore",
    is_flag=True,
    help="Disable .gitignore filtering (default: respects .gitignore).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--fail-on-hit/--no-fail-on-hit",
    default=True,
    help="Exit with code 1 if hits are found (default: fail on hit).",
)
@click.option(
    "--silent",
    is_flag=True,
    help="Suppress Rich table output when --json is used.",
)
def audit_config(
    paths: tuple[str, ...],
    read_from_stdin: bool,
    no_gitignore: bool,
    output_json: bool,
    fail_on_hit: bool,
    silent: bool,
) -> None:
    """Scan scripts/configs for deprecated 'aip config' command usage.

    Finds strings matching 'aip config' (including variations like 'aip-config',
    'python -m glaip_sdk.cli config') in scripts, CI manifests, and docs.

    Examples:
        aip config audit
        aip config audit --path "**/*.sh" --path "**/*.yml"
        aip config audit --stdin < file_list.txt
        aip config audit --json --no-fail-on-hit
    """
    _enforce_legacy_config_gate()
    # Collect files to scan
    files_to_scan = _collect_files_to_scan(paths, read_from_stdin)

    # Filter by gitignore if enabled
    files_to_scan = _filter_by_gitignore(files_to_scan, no_gitignore)

    # Scan files for matches
    hits = _scan_files_for_matches(files_to_scan)

    # Emit telemetry
    _emit_telemetry_event(
        "config.audit",
        {
            "audit_invoked": True,
            "hits_found": len(hits),
            "files_scanned": len(files_to_scan),
        },
    )

    # Output results
    _output_audit_results(hits, len(files_to_scan), output_json, silent)

    # Exit with appropriate code
    if hits and fail_on_hit:
        sys.exit(1)
    sys.exit(0)


# Patterns to match deprecated config command usage
_AUDIT_PATTERNS = [
    r"aip\s+config",
    r"aip-config",
    r"python\s+-m\s+glaip_sdk\.cli\s+config",
    r"python\s+-m\s+glaip_sdk\.cli\.main\s+config",
]
_COMPILED_AUDIT_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in _AUDIT_PATTERNS]


def _collect_files_from_stdin() -> list[Path]:
    """Collect files to scan from stdin input.

    Returns:
        List of file paths read from stdin.
    """
    files_to_scan: list[Path] = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                file_path = Path(line).expanduser().resolve()
            except Exception:
                continue
            if file_path.exists() and file_path.is_file():
                if _should_skip_file(file_path):
                    continue
                files_to_scan.append(file_path)
    return files_to_scan


def _collect_files_from_patterns(paths: tuple[str, ...]) -> list[Path]:
    """Collect files to scan from glob patterns.

    Args:
        paths: Glob patterns to search.

    Returns:
        List of file paths matching the patterns.
    """
    files_to_scan: list[Path] = []
    for pattern in paths:
        for file_path in Path.cwd().rglob(pattern):
            if file_path.is_file() and not _should_skip_file(file_path):
                files_to_scan.append(file_path)
    return files_to_scan


def _collect_files_default() -> list[Path]:
    """Collect all files from current directory recursively.

    Returns:
        List of all file paths in current directory.
    """
    files_to_scan: list[Path] = []
    base = Path.cwd()
    max_files = _resolve_audit_max_files()

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in _DEFAULT_EXCLUDE_DIRS]
        for file in files:
            file_path = Path(root) / file
            if _should_skip_file(file_path):
                continue
            files_to_scan.append(file_path)
            if max_files and len(files_to_scan) >= max_files:
                _warn_scan_truncated(max_files)
                return files_to_scan

    return files_to_scan


def _resolve_audit_max_files() -> int | None:
    """Resolve optional scan limit from env."""
    max_files_env = os.getenv("AIP_CONFIG_AUDIT_MAX_FILES")
    if not max_files_env:
        return None
    try:
        parsed = int(max_files_env, 10)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _warn_scan_truncated(max_files: int) -> None:
    """Warn when scanning is truncated to avoid surprises on huge repos."""
    console.print(
        f"[{WARNING_STYLE}]Scanning limited to the first {max_files} files. "
        "Use --path to narrow the search or increase AIP_CONFIG_AUDIT_MAX_FILES to scan more.[/]"
    )


def _collect_files_to_scan(paths: tuple[str, ...], read_from_stdin: bool) -> list[Path]:
    """Collect files to scan based on input method.

    Args:
        paths: Glob patterns to search (if not reading from stdin).
        read_from_stdin: Whether to read file list from stdin.

    Returns:
        List of file paths to scan.
    """
    if read_from_stdin:
        return _collect_files_from_stdin()
    if paths:
        return _collect_files_from_patterns(paths)
    return _collect_files_default()


def _filter_by_gitignore(files_to_scan: list[Path], no_gitignore: bool) -> list[Path]:
    """Filter files by .gitignore patterns if enabled.

    Args:
        files_to_scan: List of file paths to filter.
        no_gitignore: If True, skip gitignore filtering.

    Returns:
        Filtered list of file paths.
    """
    global _PATHSPEC_WARNED
    if no_gitignore or pathspec is None:
        if not no_gitignore and pathspec is None and not _PATHSPEC_WARNED:
            msg = (
                f"[{WARNING_STYLE}]Warning:[/] pathspec is not installed; "
                "gitignore filtering for 'aip config audit' will be skipped."
            )
            with _PATHSPEC_WARNED_LOCK:
                if not _PATHSPEC_WARNED:
                    stderr_console.print(msg)
                    _PATHSPEC_WARNED = True
        return files_to_scan

    # Load .gitignore patterns
    gitignore_path = Path.cwd() / ".gitignore"
    if not gitignore_path.exists():
        return files_to_scan

    try:
        with gitignore_path.open(encoding="utf-8", errors="ignore") as f:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", f)

            # Guard against files outside CWD; fallback to absolute path in that case
            def _to_git_path(path: Path) -> str:
                try:
                    return str(path.relative_to(Path.cwd()))
                except ValueError:
                    return str(path)

            return [path for path in files_to_scan if not spec.match_file(_to_git_path(path))]
    except Exception:
        # If gitignore parsing fails, return all files
        return files_to_scan


def _should_skip_file(file_path: Path) -> bool:
    """Check whether a file should be skipped based on size."""
    try:
        return file_path.stat().st_size > _MAX_SCAN_FILE_SIZE
    except OSError:
        return False


def _extract_match_snippet(line: str, match_obj: re.Match[str]) -> str:
    """Extract a snippet around a match for display.

    Args:
        line: The full line containing the match.
        match_obj: The regex match object.

    Returns:
        A snippet of text around the match.
    """
    start = max(0, match_obj.start() - 20)
    end = min(len(line), match_obj.end() + 20)
    return line[start:end].strip()


def _process_file_for_matches(file_path: Path, compiled_patterns: list[re.Pattern[str]]) -> list[dict[str, Any]]:
    """Process a single file for deprecated config command matches.

    Args:
        file_path: Path to the file to scan.
        compiled_patterns: List of compiled regex patterns to match.

    Returns:
        List of hit dictionaries found in this file.
    """
    hits: list[dict[str, Any]] = []
    if _should_skip_file(file_path):
        return hits
    try:
        with file_path.open(encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                for pattern in compiled_patterns:
                    match_obj = pattern.search(line)
                    if match_obj:
                        snippet = _extract_match_snippet(line, match_obj)
                        replacement = _suggest_replacement(line.strip())

                        try:
                            file_str = str(file_path.relative_to(Path.cwd()))
                        except ValueError:
                            file_str = str(file_path)

                        hits.append(
                            {
                                "file": file_str,
                                "line": line_num,
                                "match": snippet,
                                "replacement": replacement,
                            }
                        )
                        break  # Only count once per line
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        pass
    except OSError:
        # Skip files with permission errors
        pass

    return hits


def _scan_files_for_matches(files_to_scan: list[Path]) -> list[dict[str, Any]]:
    """Scan files for deprecated config command usage.

    Args:
        files_to_scan: List of file paths to scan.

    Returns:
        List of hit dictionaries with file, line, match, and replacement info.
    """
    hits: list[dict[str, Any]] = []

    for file_path in files_to_scan:
        file_hits = _process_file_for_matches(file_path, _COMPILED_AUDIT_PATTERNS)
        hits.extend(file_hits)

    return hits


def _output_audit_results(hits: list[dict[str, Any]], files_scanned: int, output_json: bool, silent: bool) -> None:
    """Output audit results in the requested format.

    Args:
        hits: List of hit dictionaries.
        files_scanned: Number of files scanned.
        output_json: If True, output JSON format.
        silent: If True, suppress Rich output when using JSON.
    """
    if output_json:
        result = {
            "hits": hits,
            "total_hits": len(hits),
            "files_scanned": files_scanned,
        }
        click.echo(json.dumps(result, indent=2))
        return

    if silent:
        return

    if hits:
        table = AIPTable(title="⚠️  Deprecated 'aip config' Usage Found")
        table.add_column("File", style=INFO, width=30)
        table.add_column("Line", style=NEUTRAL, width=8)
        table.add_column("Match", style=WARNING_STYLE, width=40)
        table.add_column("Suggested Replacement", style=SUCCESS_STYLE, width=40)

        for hit in hits:
            table.add_row(
                hit["file"],
                str(hit["line"]),
                hit["match"],
                hit["replacement"],
            )

        console.print(table)
        console.print(f"\n[{WARNING_STYLE}]Found {len(hits)} deprecated usage(s).[/]")
    else:
        console.print(f"[{SUCCESS_STYLE}]✅ No deprecated 'aip config' usage found.[/]")


def _suggest_replacement(line: str) -> str:
    """Suggest a replacement command for deprecated config usage."""
    line_lower = line.lower()

    # Map common patterns to replacements
    if "config list" in line_lower:
        return "aip accounts list"
    elif "config set" in line_lower:
        if "api_url" in line_lower or "api_key" in line_lower:
            return "aip accounts edit <name> [--url URL] [--key]"
        return "aip accounts edit <name>"
    elif "config get" in line_lower:
        return "aip accounts show <name> (or read ~/.aip/config.yaml)"
    elif "config unset" in line_lower:
        return "aip accounts edit <name> (to clear specific fields)"
    elif "config reset" in line_lower:
        return "aip accounts remove <name> (for each account)"
    # Generic "config" usage (command-like), but avoid matching any arbitrary
    # mention of the word "config" in unrelated text.
    elif "aip config" in line_lower or " config " in f" {line_lower} " or CONFIG_CONFIGURE_HINT in line_lower:
        return "aip configure or aip accounts add <name>"
    else:
        return "Use 'aip accounts ...' or 'aip configure'"


@config_group.command()
@click.option(
    "--account",
    "account_name",
    help="Account name to configure (defaults to active account)",
)
def configure(account_name: str | None) -> None:
    """Configure AIP CLI credentials and settings interactively.

    This command is an alias for 'aip accounts add <name>' and will
    configure the specified account (or active account if not specified).
    """
    _enforce_legacy_config_gate()
    _configure_interactive(account_name)


# Alias command for backward compatibility
@click.command()
@click.option(
    "--account",
    "account_name",
    help="Account name to configure (defaults to active account)",
)
def configure_command(account_name: str | None) -> None:
    """Configure AIP CLI credentials and settings interactively.

    This is an alias for 'aip config configure' for backward compatibility.
    For multi-account support, use 'aip accounts add <name>' instead.
    """
    _enforce_legacy_config_gate()
    suppress_tip = os.environ.get("AIP_SUPPRESS_CONFIGURE_TIP", "").strip().lower() in {"1", "true", "yes", "on"}
    if not suppress_tip:
        tip_prefix = f"[{WARNING_STYLE}]Setup tip:[/] "
        tip_body = (
            "Prefer 'aip accounts add <name>' or 'aip configure' from your terminal for multi-account setup. "
            "Launching the interactive wizard now..."
        )
        console.print(f"{tip_prefix}{tip_body}")
    # Delegate to the shared function
    _configure_interactive(account_name)


# Note: The config command group should be registered in main.py
_mask_api_key = mask_api_key_display


def _render_configuration_header() -> None:
    """Display the interactive configuration heading/banner."""
    render_branding_header(console, "[bold]AIP Configuration[/bold]")


def _prompt_configuration_inputs_for_account(existing: dict[str, str] | None) -> dict[str, str]:
    """Interactively prompt for account configuration values."""
    console.print("\n[bold]Enter your AIP configuration:[/bold]")
    if existing:
        console.print("(Leave blank to keep current values)")
    console.print("─" * 50)

    config = existing.copy() if existing else {}

    _prompt_api_url(config)
    _prompt_api_key(config)

    return config


def _prompt_api_url(config: dict[str, str]) -> None:
    """Ask the user for the API URL, preserving existing values by default."""
    current_url = config.get("api_url", "")
    suffix = f"(current: {current_url})" if current_url else ""
    console.print(f"\n[{ACCENT_STYLE}]AIP API URL[/] {suffix}:")
    new_url = input("> ").strip()
    if new_url:
        config["api_url"] = new_url
    elif not current_url:
        config["api_url"] = "https://your-aip-instance.com"


def _prompt_api_key(config: dict[str, str]) -> None:
    """Prompt the user for the API key while masking previous input."""
    current_key_masked = _mask_api_key(config.get("api_key"))
    suffix = f"(current: {current_key_masked})" if current_key_masked else ""
    console.print(f"\n[{ACCENT_STYLE}]AIP API Key[/] {suffix}:")
    new_key = getpass.getpass("> ")
    if new_key:
        config["api_key"] = new_key


def _test_and_report_connection_for_account(account_name: str) -> None:
    """Sanity-check the provided credentials against the backend."""
    store = get_account_store()
    account = store.get_account(account_name)
    if not account:
        return

    api_url = account.get("api_url", "")
    api_key = account.get("api_key", "")
    if not api_url or not api_key:
        return

    hint_status = command_hint("status", slash_command="status")
    extra_hint = None
    if hint_status:
        extra_hint = f"   You can run {format_command_hint(hint_status) or hint_status} later to test again"

    check_connection(api_url, api_key, console, abort_on_error=False, extra_hint=extra_hint)


def _print_post_configuration_hints() -> None:
    """Offer next-step guidance after configuration completes."""
    console.print("\n💡 You can now use AIP CLI commands!")
    hint_status = command_hint("status", slash_command="status")
    if hint_status:
        console.print(f"   • Run {format_command_hint(hint_status) or hint_status} to check connection")
    hint_agents = command_hint("agents list", slash_command="agents")
    if hint_agents:
        console.print(f"   • Run {format_command_hint(hint_agents) or hint_agents} to see your agents")
