"""CLI output utilities: Table/console output utilities, list rendering.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.syntax import Syntax

from glaip_sdk.branding import ACCENT_STYLE, SUCCESS_STYLE, WARNING_STYLE
from glaip_sdk.cli import display as cli_display, masking, pager
from glaip_sdk.cli.constants import LITERAL_STRING_THRESHOLD, TABLE_SORT_ENABLED
from glaip_sdk.cli.context import _get_view, detect_export_format as _detect_export_format
from glaip_sdk.cli.hints import command_hint
from glaip_sdk.cli.io import export_resource_to_file_with_validation
from glaip_sdk.cli.rich_helpers import markup_text, print_markup
from glaip_sdk.rich_components import AIPPanel, AIPTable
from glaip_sdk.utils import format_datetime, is_uuid
from .prompting import (
    _fuzzy_pick,
    _fuzzy_pick_for_resources,
    _load_questionary_module,
    _make_questionary_choice,
)
from .rendering import _spinner_stop, _spinner_update, spinner_context

_VERSION_MODULE_MISSING = object()
_version_module: Any | None = _VERSION_MODULE_MISSING

console = Console()
pager.console = console
logger = logging.getLogger("glaip_sdk.cli.core.output")
_version_logger = logging.getLogger("glaip_sdk.cli.version")
_WARNED_SDK_VERSION_FALLBACK = False


def _is_tty(fd: int) -> bool:
    """Return True if the file descriptor is a valid TTY."""
    try:
        return os.isatty(fd)
    except OSError:
        return False


class _LiteralYamlDumper(yaml.SafeDumper):
    """YAML dumper that emits literal scalars for multiline strings."""


def _literal_str_representer(dumper: yaml.Dumper, data: str) -> yaml.nodes.ScalarNode:
    """Represent strings in YAML, using literal blocks for verbose values."""
    needs_literal = "\n" in data or "\r" in data
    if not needs_literal and LITERAL_STRING_THRESHOLD and len(data) >= LITERAL_STRING_THRESHOLD:  # pragma: no cover
        needs_literal = True

    style = "|" if needs_literal else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_LiteralYamlDumper.add_representer(str, _literal_str_representer)


def detect_export_format(file_path: str | os.PathLike[str]) -> str:
    """Backward-compatible proxy to `glaip_sdk.cli.context.detect_export_format`."""
    return _detect_export_format(file_path)


def format_size(num: int | None) -> str:
    """Format byte counts using short human-friendly units.

    Args:
        num: Number of bytes to format (can be None or 0)

    Returns:
        Human-readable size string (e.g., "1.5KB", "2MB")
    """
    if not num or num <= 0:
        return "0B"

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B" or value >= 100:
                return f"{value:.0f}{unit}"
            if value >= 10:
                return f"{value:.1f}{unit}"
            return f"{value:.2f}{unit}"
        value /= 1024
    return f"{value:.1f}TB"  # pragma: no cover - defensive fallback


def parse_json_line(line: str) -> dict[str, Any] | None:
    """Parse a JSON line into a dictionary payload.

    Args:
        line: JSON line string to parse

    Returns:
        Parsed dictionary or None if parsing fails or result is not a dict
    """
    line = line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def format_datetime_fields(
    data: dict[str, Any], fields: tuple[str, ...] = ("created_at", "updated_at")
) -> dict[str, Any]:
    """Format datetime fields in a data dictionary for display.

    Args:
        data: Dictionary containing the data to format
        fields: Tuple of field names to format (default: created_at, updated_at)

    Returns:
        New dictionary with formatted datetime fields
    """
    formatted = data.copy()
    for field in fields:
        if field in formatted:
            formatted[field] = format_datetime(formatted[field])
    return formatted


def fetch_resource_for_export(
    ctx: Any,
    resource: Any,
    resource_type: str,
    get_by_id_func: Callable[[str], Any],
    console_override: Console | None = None,
) -> Any:
    """Fetch full resource details for export, handling errors gracefully.

    Args:
        ctx: Click context for spinner management
        resource: Resource object to fetch details for
        resource_type: Type of resource (e.g., "MCP", "Agent", "Tool")
        get_by_id_func: Function to fetch resource by ID
        console_override: Optional console override

    Returns:
        Resource object with full details, or original resource if fetch fails
    """
    active_console = console_override or console
    resource_id = str(getattr(resource, "id", "")).strip()

    if not resource_id:
        return resource

    try:
        with spinner_context(
            ctx,
            f"[bold blue]Fetching {resource_type} details…[/bold blue]",
            console_override=active_console,
        ):
            return get_by_id_func(resource_id)
    except Exception:
        # Return original resource if fetch fails
        return resource


def handle_resource_export(
    ctx: Any,
    resource: Any,
    export_path: Path,
    resource_type: str,
    get_by_id_func: Callable[[str], Any],
    console_override: Console | None = None,
) -> None:
    """Handle resource export to file with format detection and error handling.

    Args:
        ctx: Click context for spinner management
        resource: Resource object to export
        export_path: Target file path (format detected from extension)
        resource_type: Type of resource (e.g., "agent", "tool")
        get_by_id_func: Function to fetch resource by ID
        console_override: Optional console override
    """
    active_console = console_override or console

    # Auto-detect format from file extension
    detected_format = detect_export_format(export_path)

    # Try to fetch full details for export
    full_resource = fetch_resource_for_export(
        ctx,
        resource,
        resource_type.capitalize(),
        get_by_id_func,
        console_override=active_console,
    )

    # Export the resource
    try:
        with spinner_context(
            ctx,
            f"[bold blue]Exporting {resource_type}…[/bold blue]",
            console_override=active_console,
        ):
            export_resource_to_file_with_validation(full_resource, export_path, detected_format)
    except Exception:
        cli_display.handle_rich_output(
            ctx,
            markup_text(f"[{WARNING_STYLE}]⚠️  Failed to fetch full details, using available data[/]"),
        )
        # Fallback: export with available data
        export_resource_to_file_with_validation(resource, export_path, detected_format)

    print_markup(
        f"[{SUCCESS_STYLE}]✅ {resource_type.capitalize()} exported to: {export_path} (format: {detected_format})[/]",
        console=active_console,
    )


def sdk_version() -> str:
    """Return the current SDK version, warning if metadata is unavailable."""
    global _WARNED_SDK_VERSION_FALLBACK, _version_module

    if _version_module is _VERSION_MODULE_MISSING:
        try:
            from importlib import import_module  # noqa: PLC0415

            _version_module = import_module("glaip_sdk._version")
        except Exception:  # pragma: no cover - defensive fallback
            _version_module = None

    if _version_module is None:
        if not _WARNED_SDK_VERSION_FALLBACK:
            _version_logger.warning("Unable to resolve glaip-sdk version metadata; using fallback '0.0.0'.")
            _WARNED_SDK_VERSION_FALLBACK = True
        return "0.0.0"

    version = getattr(_version_module, "__version__", None)
    if isinstance(version, str) and version:
        return version

    # Use module-level flag to avoid repeated warnings
    if not _WARNED_SDK_VERSION_FALLBACK:
        _version_logger.warning("Unable to resolve glaip-sdk version metadata; using fallback '0.0.0'.")
        _WARNED_SDK_VERSION_FALLBACK = True

    return "0.0.0"


def _coerce_result_payload(result: Any) -> Any:
    """Convert renderer outputs into plain dict/list structures when possible."""
    try:
        to_dict = getattr(result, "to_dict", None)
        if callable(to_dict):
            return to_dict()
    except Exception:
        return result
    return result


def _ensure_displayable(payload: Any) -> Any:
    """Best-effort coercion into JSON/str-safe payloads for console rendering."""
    if isinstance(payload, (dict, list, str, int, float, bool)) or payload is None:
        return payload

    if hasattr(payload, "__dict__"):
        try:
            return dict(payload)
        except Exception:
            try:
                return dict(payload.__dict__)
            except Exception:
                pass

    try:
        return str(payload)
    except Exception:
        return repr(payload)


def _render_markdown_output(data: Any) -> None:
    """Render markdown output using Rich when available."""
    try:
        console.print(Markdown(str(data)))
    except ImportError:
        click.echo(str(data))


def _format_yaml_text(data: Any) -> str:
    """Convert structured payloads to YAML for readability."""
    try:
        yaml_text = yaml.dump(
            data,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            Dumper=_LiteralYamlDumper,
        )
    except Exception:  # pragma: no cover - defensive YAML fallback
        try:
            return str(data)
        except Exception:  # pragma: no cover - defensive str fallback
            return repr(data)

    yaml_text = yaml_text.rstrip()
    if yaml_text.endswith("..."):  # pragma: no cover - defensive YAML cleanup
        yaml_text = yaml_text[:-3].rstrip()
    return yaml_text


def _build_yaml_renderable(data: Any) -> Any:
    """Return a syntax-highlighted YAML renderable when possible."""
    yaml_text = _format_yaml_text(data) or "# No data"
    try:
        return Syntax(yaml_text, "yaml", word_wrap=False)
    except Exception:  # pragma: no cover - defensive syntax highlighting fallback
        return yaml_text


def output_result(
    ctx: Any,
    result: Any,
    title: str = "Result",
    panel_title: str | None = None,
) -> None:
    """Output a result to the console with optional title.

    Args:
        ctx: Click context
        result: Result data to output
        title: Optional title for the output
        panel_title: Optional Rich panel title for structured output
    """
    fmt = _get_view(ctx)

    data = _coerce_result_payload(result)
    data = masking.mask_payload(data)
    data = _ensure_displayable(data)

    if fmt == "json":
        click.echo(json.dumps(data, indent=2, default=str))
        return

    if fmt == "plain":
        click.echo(str(data))
        return

    if fmt == "md":
        _render_markdown_output(data)
        return

    renderable = _build_yaml_renderable(data)
    if panel_title:
        console.print(AIPPanel(renderable, title=panel_title))
    else:
        console.print(markup_text(f"[{ACCENT_STYLE}]{title}:[/]"))
        console.print(renderable)


def _normalise_rows(items: list[Any], transform_func: Callable[[Any], dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Convert heterogeneous item lists into table rows."""
    try:
        rows: list[dict[str, Any]] = []
        for item in items:
            if transform_func:
                rows.append(transform_func(item))
            elif hasattr(item, "to_dict"):
                rows.append(item.to_dict())
            elif hasattr(item, "__dict__"):
                rows.append(vars(item))
            elif isinstance(item, dict):
                rows.append(item)
            else:
                rows.append({"value": item})
        return rows
    except Exception:
        return []


def _render_plain_list(rows: list[dict[str, Any]], title: str, columns: list[tuple]) -> None:
    """Display tabular data as a simple pipe-delimited list."""
    if not rows:
        click.echo(f"No {title.lower()} found.")
        return
    for row in rows:
        row_str = " | ".join(str(row.get(key, "N/A")) for key, _, _, _ in columns)
        click.echo(row_str)


def _render_markdown_list(rows: list[dict[str, Any]], title: str, columns: list[tuple]) -> None:
    """Display tabular data using markdown table syntax."""
    if not rows:
        click.echo(f"No {title.lower()} found.")
        return
    headers = [header for _, header, _, _ in columns]
    click.echo(f"| {' | '.join(headers)} |")
    click.echo(f"| {' | '.join('---' for _ in headers)} |")
    for row in rows:
        row_str = " | ".join(str(row.get(key, "N/A")) for key, _, _, _ in columns)
        click.echo(f"| {row_str} |")


def _should_sort_rows(rows: list[dict[str, Any]]) -> bool:
    """Return True when rows should be name-sorted prior to rendering."""
    return TABLE_SORT_ENABLED and rows and isinstance(rows[0], dict) and "name" in rows[0]


def _create_table(columns: list[tuple[str, str, str, int | None]], title: str) -> Any:
    """Build a configured Rich table for the provided columns."""
    table = AIPTable(title=title, expand=True)
    for _key, header, style, width in columns:
        table.add_column(header, style=style, width=width)
    return table


def _build_table_group(rows: list[dict[str, Any]], columns: list[tuple], title: str) -> Group:
    """Return a Rich group containing the table and a small footer summary."""
    table = _create_table(columns, title)
    for row in rows:
        table.add_row(*[str(row.get(key, "N/A")) for key, _, _, _ in columns])
    footer = markup_text(f"\n[dim]Total {len(rows)} items[/dim]")
    return Group(table, footer)


def _handle_json_output(items: list[Any], rows: list[dict[str, Any]]) -> None:
    """Handle JSON output format."""
    data = rows if rows else [it.to_dict() if hasattr(it, "to_dict") else it for it in items]
    click.echo(json.dumps(data, indent=2, default=str))


def _handle_plain_output(rows: list[dict[str, Any]], title: str, columns: list[tuple]) -> None:
    """Handle plain text output format."""
    _render_plain_list(rows, title, columns)


def _handle_markdown_output(rows: list[dict[str, Any]], title: str, columns: list[tuple]) -> None:
    """Handle markdown output format."""
    _render_markdown_list(rows, title, columns)


def _handle_empty_items(title: str) -> None:
    """Handle case when no items are found."""
    console.print(markup_text(f"[{WARNING_STYLE}]No {title.lower()} found.[/]"))


def _should_use_fuzzy_picker() -> bool:
    """Return True when the interactive fuzzy picker can be shown."""
    return console.is_terminal and _is_tty(1)


def _try_fuzzy_pick(rows: list[dict[str, Any]], columns: list[tuple], title: str) -> dict[str, Any] | None:
    """Best-effort fuzzy selection; returns None if the picker fails."""
    if not _should_use_fuzzy_picker():
        return None

    try:
        return _fuzzy_pick(rows, columns, title)
    except Exception:
        logger.debug("Fuzzy picker failed; falling back to table output", exc_info=True)
        return None


def _resource_tip_command(title: str) -> str | None:
    """Resolve the follow-up command hint for the given table title."""
    title_lower = title.lower()
    mapping = {
        "agent": ("agents get", "agents"),
        "tool": ("tools get", None),
        "mcp": ("mcps get", None),
        "model": ("models list", None),  # models only ship a list command
    }
    for keyword, (cli_command, slash_command) in mapping.items():
        if keyword in title_lower:
            return command_hint(cli_command, slash_command=slash_command)
    return command_hint("agents get", slash_command="agents")


def _print_selection_tip(title: str) -> None:
    """Print the contextual follow-up tip after a fuzzy selection."""
    tip_cmd = _resource_tip_command(title)
    if tip_cmd:
        console.print(markup_text(f"\n[dim]Tip: use `{tip_cmd} <ID>` for details[/dim]"))


def _handle_fuzzy_pick_selection(rows: list[dict[str, Any]], columns: list[tuple], title: str) -> bool:
    """Handle fuzzy picker selection.

    Returns:
        True if a resource was selected and displayed,
        False if cancelled/no selection.
    """
    picked = _try_fuzzy_pick(rows, columns, title)
    if picked is None:
        return False

    table = _create_table(columns, title)
    table.add_row(*[str(picked.get(key, "N/A")) for key, _, _, _ in columns])
    console.print(table)
    _print_selection_tip(title)
    return True


def _handle_table_output(
    rows: list[dict[str, Any]],
    columns: list[tuple],
    title: str,
    *,
    use_pager: bool | None = None,
) -> None:
    """Handle table output with paging."""
    content = _build_table_group(rows, columns, title)
    should_page = (
        pager._should_page_output(len(rows), console.is_terminal and _is_tty(1)) if use_pager is None else use_pager
    )

    if should_page:
        ansi = pager._render_ansi(content)
        if not pager._page_with_system_pager(ansi):
            with console.pager(styles=True):
                console.print(content)
    else:
        console.print(content)


def output_list(
    ctx: Any,
    items: list[Any],
    title: str,
    columns: list[tuple[str, str, str, int | None]],
    transform_func: Callable | None = None,
    *,
    skip_picker: bool = False,
    use_pager: bool | None = None,
) -> None:
    """Display a list with optional fuzzy palette for quick selection."""
    fmt = _get_view(ctx)
    rows = _normalise_rows(items, transform_func)
    rows = masking.mask_rows(rows)

    if fmt == "json":
        _handle_json_output(items, rows)
        return

    if fmt == "plain":
        _handle_plain_output(rows, title, columns)
        return

    if fmt == "md":
        _handle_markdown_output(rows, title, columns)
        return

    if not items:
        _handle_empty_items(title)
        return

    if _should_sort_rows(rows):
        try:
            rows = sorted(rows, key=lambda r: str(r.get("name", "")).lower())
        except Exception:
            pass

    if not skip_picker and _handle_fuzzy_pick_selection(rows, columns, title):
        return

    _handle_table_output(rows, columns, title, use_pager=use_pager)


def coerce_to_row(item: Any, keys: list[str]) -> dict[str, Any]:
    """Coerce an item (dict or object) to a row dict with specified keys.

    Args:
        item: The item to coerce (dict or object with attributes)
        keys: List of keys/attribute names to extract

    Returns:
        Dict with the extracted values, "N/A" for missing values
    """
    result = {}
    for key in keys:
        if isinstance(item, dict):
            value = item.get(key, "N/A")
        else:
            value = getattr(item, key, "N/A")
        result[key] = str(value) if value is not None else "N/A"
    return result


def _resolve_by_id(ref: str, get_by_id: Callable) -> Any | None:
    """Resolve resource by UUID if ref is a valid UUID."""
    if is_uuid(ref):
        return get_by_id(ref)
    return None


def _resolve_by_name_multiple_with_select(matches: list[Any], select: int) -> Any:
    """Resolve multiple matches using select parameter."""
    idx = int(select) - 1
    if not (0 <= idx < len(matches)):
        raise click.ClickException(f"--select must be 1..{len(matches)}")
    return matches[idx]


def _resolve_by_name_multiple_fuzzy(ctx: Any, ref: str, matches: list[Any], label: str) -> Any:
    """Resolve multiple matches preferring the fuzzy picker interface."""
    return handle_ambiguous_resource(ctx, label.lower(), ref, matches, interface_preference="fuzzy")


def _resolve_by_name_multiple_questionary(ctx: Any, ref: str, matches: list[Any], label: str) -> Any:
    """Resolve multiple matches preferring the questionary interface."""
    return handle_ambiguous_resource(ctx, label.lower(), ref, matches, interface_preference="questionary")


def resolve_resource(
    ctx: Any,
    ref: str,
    *,
    get_by_id: Callable,
    find_by_name: Callable,
    label: str,
    select: int | None = None,
    interface_preference: str = "fuzzy",
    status_indicator: Any | None = None,
) -> Any | None:
    """Resolve resource reference (ID or name) with ambiguity handling.

    Args:
        ctx: Click context
        ref: Resource reference (ID or name)
        get_by_id: Function to get resource by ID
        find_by_name: Function to find resources by name
        label: Resource type label for error messages
        select: Optional selection index for ambiguity resolution
        interface_preference: "fuzzy" for fuzzy picker, "questionary" for up/down list
        status_indicator: Optional Rich status indicator for wait animations

    Returns:
        Resolved resource object
    """
    spinner = status_indicator
    _spinner_update(spinner, f"[bold blue]Resolving {label}…[/bold blue]")

    # Try to resolve by ID first
    _spinner_update(spinner, f"[bold blue]Fetching {label} by ID…[/bold blue]")
    result = _resolve_by_id(ref, get_by_id)
    if result is not None:
        _spinner_update(spinner, f"[{SUCCESS_STYLE}]{label} found[/]")
        return result

    # If get_by_id returned None, the resource doesn't exist
    if is_uuid(ref):
        _spinner_stop(spinner)
        raise click.ClickException(f"{label} '{ref}' not found")

    # Find resources by name
    _spinner_update(spinner, f"[bold blue]Searching {label}s matching '{ref}'…[/bold blue]")
    matches = find_by_name(name=ref)
    if not matches:
        _spinner_stop(spinner)
        raise click.ClickException(f"{label} '{ref}' not found")

    if len(matches) == 1:
        _spinner_update(spinner, f"[{SUCCESS_STYLE}]{label} found[/]")
        return matches[0]

    # Multiple matches found, handle ambiguity
    if select:
        _spinner_stop(spinner)
        return _resolve_by_name_multiple_with_select(matches, select)

    # Choose interface based on preference
    _spinner_stop(spinner)
    preference = (interface_preference or "fuzzy").lower()
    if preference not in {"fuzzy", "questionary"}:
        preference = "fuzzy"
    if preference == "fuzzy":
        return _resolve_by_name_multiple_fuzzy(ctx, ref, matches, label)
    else:
        return _resolve_by_name_multiple_questionary(ctx, ref, matches, label)


def _handle_json_view_ambiguity(matches: list[Any]) -> Any:
    """Handle ambiguity in JSON view by returning first match."""
    return matches[0]


def _handle_questionary_ambiguity(resource_type: str, ref: str, matches: list[Any]) -> Any:
    """Handle ambiguity using questionary interactive interface."""
    questionary_module, choice_cls = _load_questionary_module()
    if not (questionary_module and os.getenv("TERM") and _is_tty(0) and _is_tty(1)):
        raise click.ClickException("Interactive selection not available")

    # Escape special characters for questionary
    safe_resource_type = resource_type.replace("{", "{{").replace("}", "}}")
    safe_ref = ref.replace("{", "{{").replace("}", "}}")

    picked_idx = questionary_module.select(
        f"Multiple {safe_resource_type}s match '{safe_ref}'. Pick one:",
        choices=[
            _make_questionary_choice(
                choice_cls,
                title=(
                    f"{getattr(m, 'name', '—').replace('{', '{{').replace('}', '}}')} — "
                    f"{getattr(m, 'id', '').replace('{', '{{').replace('}', '}}')}"
                ),
                value=i,
            )
            for i, m in enumerate(matches)
        ],
        use_indicator=True,
        qmark="🧭",
        instruction="↑/↓ to select • Enter to confirm",
    ).ask()
    if picked_idx is None:
        raise click.ClickException("Selection cancelled")
    return matches[picked_idx]


def _handle_fallback_numeric_ambiguity(resource_type: str, ref: str, matches: list[Any]) -> Any:
    """Handle ambiguity using numeric prompt fallback."""
    # Escape special characters for display
    safe_resource_type = resource_type.replace("{", "{{").replace("}", "}}")
    safe_ref = ref.replace("{", "{{").replace("}", "}}")

    console.print(markup_text(f"[{WARNING_STYLE}]Multiple {safe_resource_type}s found matching '{safe_ref}':[/]"))
    table = AIPTable(
        title=f"Select {safe_resource_type.title()}",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("ID", style="dim", width=36)
    table.add_column("Name", style=ACCENT_STYLE)
    for i, m in enumerate(matches, 1):
        table.add_row(str(i), str(getattr(m, "id", "")), str(getattr(m, "name", "")))
    console.print(table)
    choice_str = click.prompt(
        f"Select {safe_resource_type} (1-{len(matches)})",
    )
    try:
        choice = int(choice_str)
    except ValueError as err:
        raise click.ClickException("Invalid selection") from err
    if 1 <= choice <= len(matches):
        return matches[choice - 1]
    raise click.ClickException("Invalid selection")


def _should_fallback_to_numeric_prompt(exception: Exception) -> bool:
    """Determine if we should fallback to numeric prompt for this exception."""
    # Re-raise cancellation - user explicitly cancelled
    if "Selection cancelled" in str(exception):
        return False

    # Fall back to numeric prompt for other exceptions
    return True


def _normalize_interface_preference(preference: str) -> str:
    """Normalize and validate interface preference."""
    normalized = (preference or "questionary").lower()
    return normalized if normalized in {"fuzzy", "questionary"} else "questionary"


def _get_interface_order(preference: str) -> tuple[str, str]:
    """Get the ordered interface preferences."""
    interface_orders = {
        "fuzzy": ("fuzzy", "questionary"),
        "questionary": ("questionary", "fuzzy"),
    }
    return interface_orders.get(preference, ("questionary", "fuzzy"))


def _try_fuzzy_selection(
    resource_type: str,
    ref: str,
    matches: list[Any],
) -> Any | None:
    """Try fuzzy interface selection."""
    picked = _fuzzy_pick_for_resources(matches, resource_type, ref)
    return picked if picked else None


def _try_questionary_selection(
    resource_type: str,
    ref: str,
    matches: list[Any],
) -> Any | None:
    """Try questionary interface selection."""
    try:
        return _handle_questionary_ambiguity(resource_type, ref, matches)
    except Exception as exc:
        if not _should_fallback_to_numeric_prompt(exc):
            raise
        return None


def _try_interface_selection(
    interface_order: tuple[str, str],
    resource_type: str,
    ref: str,
    matches: list[Any],
) -> Any | None:
    """Try interface selection in order, return result or None if all failed."""
    interface_handlers = {
        "fuzzy": _try_fuzzy_selection,
        "questionary": _try_questionary_selection,
    }

    for interface in interface_order:
        handler = interface_handlers.get(interface)
        if handler:
            result = handler(resource_type, ref, matches)
            if result:
                return result

    return None


def handle_ambiguous_resource(
    ctx: Any,
    resource_type: str,
    ref: str,
    matches: list[Any],
    *,
    interface_preference: str = "questionary",
) -> Any:
    """Handle multiple resource matches gracefully."""
    if _get_view(ctx) == "json":
        return _handle_json_view_ambiguity(matches)

    preference = _normalize_interface_preference(interface_preference)
    interface_order = _get_interface_order(preference)

    result = _try_interface_selection(interface_order, resource_type, ref, matches)

    if result is not None:
        return result

    return _handle_fallback_numeric_ambiguity(resource_type, ref, matches)
