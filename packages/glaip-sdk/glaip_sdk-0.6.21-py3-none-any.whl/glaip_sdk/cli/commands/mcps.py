"""MCP management commands.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from glaip_sdk.branding import (
    ACCENT_STYLE,
    INFO,
    SUCCESS,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.context import detect_export_format, get_ctx_value, output_flags
from glaip_sdk.cli.display import (
    display_api_error,
    display_confirmation_prompt,
    display_creation_success,
    display_deletion_success,
    display_update_success,
    handle_json_output,
    handle_rich_output,
)
from glaip_sdk.cli.io import (
    fetch_raw_resource_details,
    load_resource_from_file_with_validation,
)
from glaip_sdk.cli.mcp_validators import (
    validate_mcp_auth_structure,
    validate_mcp_config_structure,
)
from glaip_sdk.cli.parsers.json_input import parse_json_input
from glaip_sdk.cli.resolution import resolve_resource_reference
from glaip_sdk.cli.rich_helpers import print_markup
from glaip_sdk.cli.utils import (
    coerce_to_row,
    fetch_resource_for_export,
    format_datetime_fields,
    get_client,
    output_list,
    output_result,
    spinner_context,
    with_client_and_spinner,
)
from glaip_sdk.config.constants import (
    DEFAULT_MCP_TYPE,
)
from glaip_sdk.icons import ICON_TOOL
from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.import_export import convert_export_to_import_format
from glaip_sdk.utils.serialization import (
    build_mcp_export_payload,
    write_resource_export,
)

console = Console()
MAX_DESCRIPTION_LEN = 50


def _is_sensitive_data(val: Any) -> bool:
    """Check if value contains sensitive authentication data.

    Args:
        val: Value to check for sensitive information

    Returns:
        True if the value appears to contain sensitive data
    """
    if not isinstance(val, dict):
        return False

    sensitive_patterns = {"token", "password", "secret", "key", "credential"}
    return any(pattern in str(k).lower() for k in val.keys() for pattern in sensitive_patterns)


def _redact_sensitive_dict(val: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive fields from a dictionary.

    Args:
        val: Dictionary to redact

    Returns:
        Redacted dictionary
    """
    redacted = val.copy()
    sensitive_patterns = {"token", "password", "secret", "key", "credential"}
    for k in redacted.keys():
        if any(pattern in k.lower() for pattern in sensitive_patterns):
            redacted[k] = "<REDACTED>"
    return redacted


def _format_dict_value(val: dict[str, Any]) -> str:
    """Format a dictionary value for display.

    Args:
        val: Dictionary to format

    Returns:
        Formatted string representation
    """
    if _is_sensitive_data(val):
        redacted = _redact_sensitive_dict(val)
        return json.dumps(redacted, indent=2)
    return json.dumps(val, indent=2)


def _format_preview_value(val: Any) -> str:
    """Format a value for display in update preview with sensitive data redaction.

    Args:
        val: Value to format

    Returns:
        Formatted string representation of the value
    """
    if val is None:
        return "[dim]None[/dim]"
    if isinstance(val, dict):
        return _format_dict_value(val)
    if isinstance(val, str):
        return f'"{val}"' if val else '""'
    return str(val)


def _build_empty_override_warnings(empty_fields: list[str]) -> list[str]:
    """Build warning lines for empty CLI overrides.

    Args:
        empty_fields: List of field names with empty string overrides

    Returns:
        List of formatted warning lines
    """
    if not empty_fields:
        return []

    warnings = ["\n[yellow]⚠️  Warning: Empty values provided via CLI will override import values[/yellow]"]
    warnings.extend(f"- [yellow]{field}: will be set to empty string[/yellow]" for field in empty_fields)
    return warnings


def _validate_import_payload_fields(import_payload: dict[str, Any]) -> bool:
    """Validate that import payload contains updatable fields.

    Args:
        import_payload: Import payload to validate

    Returns:
        True if payload has updatable fields, False otherwise
    """
    updatable_fields = {"name", "transport", "description", "config", "authentication"}
    has_updatable = any(field in import_payload for field in updatable_fields)

    if not has_updatable:
        available_fields = set(import_payload.keys())
        print_markup(
            "[yellow]⚠️  No updatable fields found in import file.[/yellow]\n"
            f"[dim]Found fields: {', '.join(sorted(available_fields))}[/dim]\n"
            f"[dim]Updatable fields: {', '.join(sorted(updatable_fields))}[/dim]"
        )
    return has_updatable


def _get_config_transport(
    transport: str | None,
    import_payload: dict[str, Any] | None,
    mcp: Any,
) -> str | None:
    """Get the transport value for config validation.

    Args:
        transport: CLI transport flag
        import_payload: Optional import payload
        mcp: Current MCP object

    Returns:
        Transport value or None
    """
    if import_payload:
        return transport or import_payload.get("transport")
    return transport or getattr(mcp, "transport", None)


def _build_update_data_from_sources(
    import_payload: dict[str, Any] | None,
    mcp: Any,
    name: str | None,
    transport: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
) -> dict[str, Any]:
    """Build update data from import payload and CLI flags.

    Args:
        import_payload: Optional import payload
        mcp: Current MCP object
        name: CLI name flag
        transport: CLI transport flag
        description: CLI description flag
        config: CLI config flag
        auth: CLI auth flag

    Returns:
        Dictionary with update data
    """
    update_data = {}

    # Start with import data if available
    if import_payload:
        updatable_fields = [
            "name",
            "transport",
            "description",
            "config",
            "authentication",
        ]
        for field in updatable_fields:
            if field in import_payload:
                update_data[field] = import_payload[field]

    # CLI flags override import values
    if name is not None:
        update_data["name"] = name
    if transport is not None:
        update_data["transport"] = transport
    if description is not None:
        update_data["description"] = description
    if config is not None:
        parsed_config = parse_json_input(config)
        config_transport = _get_config_transport(transport, import_payload, mcp)
        update_data["config"] = validate_mcp_config_structure(
            parsed_config,
            transport=config_transport,
            source="--config",
        )
    if auth is not None:
        parsed_auth = parse_json_input(auth)
        update_data["authentication"] = validate_mcp_auth_structure(parsed_auth, source="--auth")

    return update_data


def _collect_cli_overrides(
    name: str | None,
    transport: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
) -> dict[str, Any]:
    """Collect CLI flags that were explicitly provided.

    Args:
        name: CLI name flag
        transport: CLI transport flag
        description: CLI description flag
        config: CLI config flag
        auth: CLI auth flag

    Returns:
        Dictionary of provided CLI overrides
    """
    cli_overrides = {}
    if name is not None:
        cli_overrides["name"] = name
    if transport is not None:
        cli_overrides["transport"] = transport
    if description is not None:
        cli_overrides["description"] = description
    if config is not None:
        cli_overrides["config"] = config
    if auth is not None:
        cli_overrides["auth"] = auth
    return cli_overrides


def _handle_cli_error(ctx: Any, error: Exception, operation: str) -> None:
    """Render CLI error once and exit with non-zero status."""
    handle_json_output(ctx, error=error)
    if get_ctx_value(ctx, "view") != "json":
        display_api_error(error, operation)
    ctx.exit(1)


@click.group(name="mcps", no_args_is_help=True)
def mcps_group() -> None:
    """MCP management operations.

    Provides commands for creating, listing, updating, deleting, and managing
    Model Context Protocol (MCP) configurations.
    """
    pass


def _resolve_mcp(ctx: Any, client: Any, ref: str, select: int | None = None) -> Any | None:
    """Resolve an MCP server by ID or name, with interactive selection support.

    This function provides MCP-specific resolution logic. It delegates to
    resolve_resource_reference for MCP-specific resolution, supporting UUID
    lookups and name-based fuzzy matching.

    Args:
        ctx: Click context for command execution.
        client: API client for backend operations.
        ref: MCP identifier (UUID or name string).
        select: Optional selection index when multiple MCPs match (1-based).

    Returns:
        MCP instance if resolution succeeds, None if not found.

    Raises:
        click.ClickException: When resolution fails or selection is invalid.
    """
    # Configure MCP-specific resolution functions
    mcp_client = client.mcps
    get_by_id_func = mcp_client.get_mcp_by_id
    find_by_name_func = mcp_client.find_mcps
    # Use MCP-specific resolution with standard fuzzy matching
    return resolve_resource_reference(
        ctx,
        client,
        ref,
        "mcp",
        get_by_id_func,
        find_by_name_func,
        "MCP",
        select=select,
    )


def _strip_server_only_fields(import_data: dict[str, Any]) -> dict[str, Any]:
    """Remove fields that should not be forwarded during import-driven creation.

    Args:
        import_data: Raw import payload loaded from disk.

    Returns:
        A shallow copy of the data with server-managed fields removed.
    """
    cleaned = dict(import_data)
    for key in (
        "id",
        "type",
        "status",
        "connection_status",
        "created_at",
        "updated_at",
    ):
        cleaned.pop(key, None)
    return cleaned


def _load_import_ready_payload(import_file: str) -> dict[str, Any]:
    """Load and normalise an imported MCP definition for create operations.

    Args:
        import_file: Path to an MCP export file (JSON or YAML).

    Returns:
        Normalised import payload ready for CLI/REST usage.

    Raises:
        click.ClickException: If the file cannot be parsed or validated.
    """
    raw_data = load_resource_from_file_with_validation(Path(import_file), "MCP")
    import_data = convert_export_to_import_format(raw_data)
    import_data = _strip_server_only_fields(import_data)

    transport = import_data.get("transport")

    if "config" in import_data:
        import_data["config"] = validate_mcp_config_structure(
            import_data["config"],
            transport=transport,
            source="import file",
        )

    if "authentication" in import_data:
        import_data["authentication"] = validate_mcp_auth_structure(
            import_data["authentication"],
            source="import file",
        )

    return import_data


def _coerce_cli_string(value: str | None) -> str | None:
    """Normalise CLI string values so blanks are treated as missing.

    Args:
        value: User-provided string option.

    Returns:
        The stripped string, or ``None`` when the value is blank/whitespace-only.
    """
    if value is None:
        return None
    trimmed = value.strip()
    # Treat whitespace-only strings as None
    return trimmed if trimmed else None


def _merge_config_field(
    merged_base: dict[str, Any],
    cli_config: str | None,
    final_transport: str | None,
) -> None:
    """Merge config field with validation.

    Args:
        merged_base: Base payload to update in-place.
        cli_config: Raw CLI JSON string for config.
        final_transport: Transport type for validation.

    Raises:
        click.ClickException: If config JSON parsing or validation fails.
    """
    if cli_config is not None:
        parsed_config = parse_json_input(cli_config)
        merged_base["config"] = validate_mcp_config_structure(
            parsed_config,
            transport=final_transport,
            source="--config",
        )
    elif "config" not in merged_base or merged_base["config"] is None:
        merged_base["config"] = {}


def _merge_auth_field(
    merged_base: dict[str, Any],
    cli_auth: str | None,
) -> None:
    """Merge authentication field with validation.

    Args:
        merged_base: Base payload to update in-place.
        cli_auth: Raw CLI JSON string for authentication.

    Raises:
        click.ClickException: If auth JSON parsing or validation fails.
    """
    if cli_auth is not None:
        parsed_auth = parse_json_input(cli_auth)
        merged_base["authentication"] = validate_mcp_auth_structure(
            parsed_auth,
            source="--auth",
        )
    elif "authentication" not in merged_base:
        merged_base["authentication"] = None


def _merge_import_payload(
    import_data: dict[str, Any] | None,
    *,
    cli_name: str | None,
    cli_transport: str | None,
    cli_description: str | None,
    cli_config: str | None,
    cli_auth: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Merge import data with CLI overrides while tracking missing fields.

    Args:
        import_data: Normalised payload loaded from file (if provided).
        cli_name: Name supplied via CLI option.
        cli_transport: Transport supplied via CLI option.
        cli_description: Description supplied via CLI option.
        cli_config: Raw CLI JSON string for config.
        cli_auth: Raw CLI JSON string for authentication.

    Returns:
        A tuple of (merged_payload, missing_required_fields).

    Raises:
        click.ClickException: If config/auth JSON parsing or validation fails.
    """
    merged_base = import_data.copy() if import_data else {}

    # Merge simple string fields using truthy CLI overrides
    for field, cli_value in (
        ("name", _coerce_cli_string(cli_name)),
        ("transport", _coerce_cli_string(cli_transport)),
        ("description", _coerce_cli_string(cli_description)),
    ):
        if cli_value is not None:
            merged_base[field] = cli_value

    # Determine final transport before validating config
    final_transport = merged_base.get("transport")

    # Merge config and authentication with validation
    _merge_config_field(merged_base, cli_config, final_transport)
    _merge_auth_field(merged_base, cli_auth)

    # Validate required fields
    missing_fields = []
    for required in ("name", "transport"):
        value = merged_base.get(required)
        if not isinstance(value, str) or not value.strip():
            missing_fields.append(required)

    return merged_base, missing_fields


@mcps_group.command(name="list")
@output_flags()
@click.pass_context
def list_mcps(ctx: Any) -> None:
    """List all MCPs in a formatted table.

    Args:
        ctx: Click context containing output format preferences

    Raises:
        ClickException: If API request fails
    """
    try:
        with with_client_and_spinner(
            ctx,
            "[bold blue]Fetching MCPs…[/bold blue]",
            console_override=console,
        ) as client:
            mcps = client.mcps.list_mcps()

        # Define table columns: (data_key, header, style, width)
        columns = [
            ("id", "ID", "dim", 36),
            ("name", "Name", ACCENT_STYLE, None),
            ("config", "Config", INFO, None),
        ]

        # Transform function for safe dictionary access
        def transform_mcp(mcp: Any) -> dict[str, Any]:
            """Transform an MCP object to a display row dictionary.

            Args:
                mcp: MCP object to transform.

            Returns:
                Dictionary with id, name, and config fields.
            """
            row = coerce_to_row(mcp, ["id", "name", "config"])
            # Ensure id is always a string
            row["id"] = str(row["id"])
            # Truncate config field for display
            if row["config"] != "N/A":
                row["config"] = str(row["config"])[:50] + "..." if len(str(row["config"])) > 50 else str(row["config"])
            return row

        output_list(ctx, mcps, "🔌 Available MCPs", columns, transform_mcp)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@mcps_group.command()
@click.option("--name", help="MCP name")
@click.option("--transport", help="MCP transport protocol")
@click.option("--description", help="MCP description")
@click.option(
    "--config",
    help="JSON configuration string or @file reference (e.g., @config.json)",
)
@click.option(
    "--auth",
    "--authentication",
    "auth",
    help="JSON authentication object or @file reference (e.g., @auth.json)",
)
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Import MCP configuration from JSON or YAML export",
)
@output_flags()
@click.pass_context
def create(
    ctx: Any,
    name: str | None,
    transport: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
    import_file: str | None,
) -> None:
    r"""Create a new MCP with specified configuration.

    You can create an MCP by providing all parameters via CLI options, or by
    importing from a file and optionally overriding specific fields.

    Args:
        ctx: Click context containing output format preferences
        name: MCP name (required unless provided via --import)
        transport: MCP transport protocol (required unless provided via --import)
        description: Optional MCP description
        config: JSON configuration string or @file reference
        auth: JSON authentication object or @file reference
        import_file: Optional path to import configuration from export file.
            CLI options override imported values.

    Raises:
        ClickException: If JSON parsing fails or API request fails

    \b
    Examples:
        Create from CLI options:
            aip mcps create --name my-mcp --transport http --config '{"url": "https://api.example.com"}'

        Import from file:
            aip mcps create --import mcp-export.json

        Import with overrides:
            aip mcps create --import mcp-export.json --name new-name --transport sse
    """
    try:
        # Get API client instance for MCP operations
        api_client = get_client(ctx)

        # Process import file if specified, otherwise use None
        import_payload = _load_import_ready_payload(import_file) if import_file is not None else None

        merged_payload, missing_fields = _merge_import_payload(
            import_payload,
            cli_name=name,
            cli_transport=transport,
            cli_description=description,
            cli_config=config,
            cli_auth=auth,
        )

        if missing_fields:
            raise click.ClickException(
                "Missing required fields after combining import and CLI values: " + ", ".join(missing_fields)
            )

        effective_name = merged_payload["name"]
        effective_transport = merged_payload["transport"]
        effective_description = merged_payload.get("description")
        effective_config = merged_payload.get("config") or {}
        effective_auth = merged_payload.get("authentication")

        with spinner_context(
            ctx,
            "[bold blue]Creating MCP…[/bold blue]",
            console_override=console,
        ):
            create_kwargs: dict[str, Any] = {
                "name": effective_name,
                "config": effective_config,
                "transport": effective_transport,
            }

            if effective_description is not None:
                create_kwargs["description"] = effective_description

            if effective_auth:
                create_kwargs["authentication"] = effective_auth

            mcp_metadata = merged_payload.get("mcp_metadata")
            if mcp_metadata is not None:
                create_kwargs["mcp_metadata"] = mcp_metadata

            mcp = api_client.mcps.create_mcp(**create_kwargs)

        # Handle JSON output
        handle_json_output(ctx, mcp.model_dump())

        # Handle Rich output
        rich_panel = display_creation_success(
            "MCP",
            mcp.name,
            mcp.id,
            Type=getattr(mcp, "type", DEFAULT_MCP_TYPE),
            Transport=getattr(mcp, "transport", effective_transport),
            Description=effective_description or "No description",
        )
        handle_rich_output(ctx, rich_panel)

    except Exception as e:
        _handle_cli_error(ctx, e, "MCP creation")


def _handle_mcp_export(
    ctx: Any,
    client: Any,
    mcp: Any,
    export_path: Path,
    no_auth_prompt: bool,
    auth_placeholder: str,
) -> None:
    """Handle MCP export to file with format detection and auth handling.

    Args:
        ctx: Click context for spinner management
        client: API client for fetching MCP details
        mcp: MCP object to export
        export_path: Target file path (format detected from extension)
        no_auth_prompt: Skip interactive secret prompts if True
        auth_placeholder: Placeholder text for missing secrets

    Note:
        Supports JSON (.json) and YAML (.yaml/.yml) export formats.
        In interactive mode, prompts for secret values.
        In non-interactive mode, uses placeholder values.
    """
    # Auto-detect format from file extension
    detected_format = detect_export_format(export_path)

    # Always export comprehensive data - re-fetch with full details

    mcp = fetch_resource_for_export(
        ctx,
        mcp,
        resource_type="MCP",
        get_by_id_func=client.mcps.get_mcp_by_id,
        console_override=console,
    )

    # Determine if we should prompt for secrets
    prompt_for_secrets = not no_auth_prompt and sys.stdin.isatty()

    # Warn user if non-interactive mode forces placeholder usage
    if not no_auth_prompt and not sys.stdin.isatty():
        print_markup(
            f"[{WARNING_STYLE}]⚠️  Non-interactive mode detected. Using placeholder values for secrets.[/]",
            console=console,
        )

    # Build and write export payload
    if prompt_for_secrets:
        # Interactive mode: no spinner during prompts
        export_payload = build_mcp_export_payload(
            mcp,
            prompt_for_secrets=prompt_for_secrets,
            placeholder=auth_placeholder,
            console=console,
        )
        with spinner_context(
            ctx,
            "[bold blue]Writing export file…[/bold blue]",
            console_override=console,
        ):
            write_resource_export(export_path, export_payload, detected_format)
    else:
        # Non-interactive mode: spinner for entire export process
        with spinner_context(
            ctx,
            "[bold blue]Exporting MCP configuration…[/bold blue]",
            console_override=console,
        ):
            export_payload = build_mcp_export_payload(
                mcp,
                prompt_for_secrets=prompt_for_secrets,
                placeholder=auth_placeholder,
                console=console,
            )
            write_resource_export(export_path, export_payload, detected_format)

    print_markup(
        f"[{SUCCESS_STYLE}]✅ Complete MCP configuration exported to: {export_path} (format: {detected_format})[/]",
        console=console,
    )


def _display_mcp_details(ctx: Any, client: Any, mcp: Any) -> None:
    """Display MCP details using raw API data or fallback to Pydantic model.

    Args:
        ctx: Click context containing output format preferences
        client: API client for fetching raw MCP data
        mcp: MCP object to display details for

    Note:
        Attempts to fetch raw API data first to preserve all fields.
        Falls back to Pydantic model data if raw data unavailable.
        Formats datetime fields for better readability.
    """
    # Try to fetch raw API data first to preserve ALL fields
    with spinner_context(
        ctx,
        "[bold blue]Fetching detailed MCP data…[/bold blue]",
        console_override=console,
    ):
        raw_mcp_data = fetch_raw_resource_details(client, mcp, "mcps")

    if raw_mcp_data:
        # Use raw API data - this preserves ALL fields
        formatted_data = format_datetime_fields(raw_mcp_data)

        output_result(
            ctx,
            formatted_data,
            title="MCP Details",
            panel_title=f"🔌 {raw_mcp_data.get('name', 'Unknown')}",
        )
    else:
        # Fall back to Pydantic model data
        console.print(f"[{WARNING_STYLE}]Falling back to Pydantic model data[/]")
        result_data = {
            "id": str(getattr(mcp, "id", "N/A")),
            "name": getattr(mcp, "name", "N/A"),
            "type": getattr(mcp, "type", "N/A"),
            "config": getattr(mcp, "config", "N/A"),
            "status": getattr(mcp, "status", "N/A"),
            "connection_status": getattr(mcp, "connection_status", "N/A"),
        }
        output_result(ctx, result_data, title=f"🔌 {mcp.name}")


@mcps_group.command()
@click.argument("mcp_ref")
@click.option(
    "--export",
    type=click.Path(dir_okay=False, writable=True),
    help="Export complete MCP configuration to file (format auto-detected from .json/.yaml extension)",
)
@click.option(
    "--no-auth-prompt",
    is_flag=True,
    help="Skip interactive secret prompts and use placeholder values.",
)
@click.option(
    "--auth-placeholder",
    default="<INSERT VALUE>",
    show_default=True,
    help="Placeholder text used when secrets are unavailable.",
)
@output_flags()
@click.pass_context
def get(
    ctx: Any,
    mcp_ref: str,
    export: str | None,
    no_auth_prompt: bool,
    auth_placeholder: str,
) -> None:
    r"""Get MCP details and optionally export configuration to file.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        export: Optional file path to export MCP configuration
        no_auth_prompt: Skip interactive secret prompts if True
        auth_placeholder: Placeholder text for missing secrets

    Raises:
        ClickException: If MCP not found or export fails

    \b
    Examples:
        aip mcps get my-mcp
        aip mcps get my-mcp --export mcp.json    # Export as JSON
        aip mcps get my-mcp --export mcp.yaml    # Export as YAML
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Handle export option
        if export:
            _handle_mcp_export(ctx, client, mcp, Path(export), no_auth_prompt, auth_placeholder)

        # Display MCP details
        _display_mcp_details(ctx, client, mcp)

    except Exception as e:
        raise click.ClickException(str(e)) from e


def _get_tools_from_config(ctx: Any, client: Any, config_file: str) -> tuple[list[dict[str, Any]], str]:
    """Get tools from MCP config file.

    Args:
        ctx: Click context
        client: GlaIP client instance
        config_file: Path to config file

    Returns:
        Tuple of (tools list, title string)
    """
    config_data = load_resource_from_file_with_validation(Path(config_file), "MCP config")

    # Validate config structure
    transport = config_data.get("transport")
    if "config" not in config_data:
        raise click.ClickException("Invalid MCP config: missing 'config' section in the file.")
    config_data["config"] = validate_mcp_config_structure(
        config_data["config"],
        transport=transport,
        source=config_file,
    )

    # Get tools from config without saving
    with spinner_context(
        ctx,
        "[bold blue]Fetching tools from config…[/bold blue]",
        console_override=console,
    ):
        tools = client.mcps.get_mcp_tools_from_config(config_data)

    title = f"{ICON_TOOL} Tools from config: {Path(config_file).name}"
    return tools, title


def _get_tools_from_mcp(ctx: Any, client: Any, mcp_ref: str | None) -> tuple[list[dict[str, Any]], str]:
    """Get tools from saved MCP.

    Args:
        ctx: Click context
        client: GlaIP client instance
        mcp_ref: MCP reference (ID or name)

    Returns:
        Tuple of (tools list, title string)
    """
    mcp = _resolve_mcp(ctx, client, mcp_ref)

    with spinner_context(
        ctx,
        "[bold blue]Fetching MCP tools…[/bold blue]",
        console_override=console,
    ):
        tools = client.mcps.get_mcp_tools(mcp.id)

    title = f"{ICON_TOOL} Tools from MCP: {mcp.name}"
    return tools, title


def _output_tool_names(ctx: Any, tools: list[dict[str, Any]]) -> None:
    """Output only tool names.

    Args:
        ctx: Click context
        tools: List of tool dictionaries
    """
    view = get_ctx_value(ctx, "view", "rich")
    tool_names = [tool.get("name", "N/A") for tool in tools]

    if view == "json":
        handle_json_output(ctx, tool_names)
    elif view == "plain":
        if tool_names:
            for name in tool_names:
                console.print(name, markup=False)
            console.print(f"Total: {len(tool_names)} tools", markup=False)
        else:
            console.print("No tools found", markup=False)
    else:
        if tool_names:
            for name in tool_names:
                console.print(name)
            console.print(f"[dim]Total: {len(tool_names)} tools[/dim]")
        else:
            console.print("[yellow]No tools found[/yellow]")


def _transform_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Transform a tool dictionary to a display row dictionary.

    Args:
        tool: Tool dictionary to transform.

    Returns:
        Dictionary with name and description fields.
    """
    description = tool.get("description", "N/A")
    if len(description) > MAX_DESCRIPTION_LEN:
        description = description[: MAX_DESCRIPTION_LEN - 3] + "..."
    return {
        "name": tool.get("name", "N/A"),
        "description": description,
    }


def _output_tools_table(ctx: Any, tools: list[dict[str, Any]], title: str) -> None:
    """Output tools in table format.

    Args:
        ctx: Click context
        tools: List of tool dictionaries
        title: Table title
    """
    columns = [
        ("name", "Name", ACCENT_STYLE, None),
        ("description", "Description", INFO, 50),
    ]

    output_list(
        ctx,
        tools,
        title,
        columns,
        _transform_tool,
    )


def _validate_tool_command_args(mcp_ref: str | None, config_file: str | None) -> None:
    """Validate that exactly one of mcp_ref or config_file is provided.

    Args:
        mcp_ref: MCP reference (ID or name)
        config_file: Path to config file

    Raises:
        ClickException: If validation fails
    """
    if not mcp_ref and not config_file:
        raise click.ClickException(
            "Either MCP_REF or --from-config must be provided.\n"
            "Examples:\n"
            "  aip mcps tools <MCP_ID>\n"
            "  aip mcps tools --from-config mcp-config.json"
        )
    if mcp_ref and config_file:
        raise click.ClickException(
            "Cannot use both MCP_REF and --from-config at the same time.\n"
            "Use either:\n"
            "  aip mcps tools <MCP_ID>\n"
            "  aip mcps tools --from-config mcp-config.json"
        )


@mcps_group.command("tools")
@click.argument("mcp_ref", required=False)
@click.option(
    "--from-config",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Get tools from MCP config file without saving to DB (JSON or YAML)",
)
@click.option(
    "--names-only",
    is_flag=True,
    help="Show only tool names (useful for allowed_tools config)",
)
@output_flags()
@click.pass_context
def list_tools(ctx: Any, mcp_ref: str | None, config_file: str | None, names_only: bool) -> None:
    """List tools available from a specific MCP or config file.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name) - required if --from-config not used
        config_file: Path to MCP config file - alternative to mcp_ref
        names_only: Show only tool names instead of full table

    Raises:
        ClickException: If MCP not found or tools fetch fails

    Examples:
        Get tools from saved MCP:
            aip mcps tools <MCP_ID>

        Get tools from config file (without saving to DB):
            aip mcps tools --from-config mcp-config.json

        Get just tool names for allowed_tools config:
            aip mcps tools <MCP_ID> --names-only
    """
    try:
        _validate_tool_command_args(mcp_ref, config_file)
        client = get_client(ctx)

        if config_file:
            tools, title = _get_tools_from_config(ctx, client, config_file)
        else:
            tools, title = _get_tools_from_mcp(ctx, client, mcp_ref)

        if names_only:
            _output_tool_names(ctx, tools)
        else:
            _output_tools_table(ctx, tools, title)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@mcps_group.command("connect")
@click.option(
    "--from-file",
    "config_file",
    required=True,
    help="MCP config JSON file",
)
@output_flags()
@click.pass_context
def connect(ctx: Any, config_file: str) -> None:
    """Test MCP connection using a configuration file.

    Args:
        ctx: Click context containing output format preferences
        config_file: Path to MCP configuration JSON file

    Raises:
        ClickException: If config file invalid or connection test fails

    Note:
        Loads MCP configuration from JSON file and tests connectivity.
        Displays success or failure with connection details.
    """
    try:
        client = get_client(ctx)

        # Load MCP config from file
        with open(config_file) as f:
            config = json.load(f)

        view = get_ctx_value(ctx, "view", "rich")
        if view != "json":
            print_markup(
                f"[{WARNING_STYLE}]Connecting to MCP with config from {config_file}...[/]",
                console=console,
            )

        # Test connection using config
        with spinner_context(
            ctx,
            "[bold blue]Connecting to MCP…[/bold blue]",
            console_override=console,
        ):
            result = client.mcps.test_mcp_connection_from_config(config)

        view = get_ctx_value(ctx, "view", "rich")
        if view == "json":
            handle_json_output(ctx, result)
        else:
            success_panel = AIPPanel(
                f"[{SUCCESS_STYLE}]✓[/] MCP connection successful!\n\n[bold]Result:[/bold] {result}",
                title="🔌 Connection",
                border_style=SUCCESS,
            )
            console.print(success_panel)

    except Exception as e:
        raise click.ClickException(str(e)) from e


def _generate_update_preview(mcp: Any, update_data: dict[str, Any], cli_overrides: dict[str, Any]) -> str:
    """Generate formatted preview of changes for user confirmation.

    Args:
        mcp: Current MCP object
        update_data: Data that will be sent in update request
        cli_overrides: CLI flags that were explicitly provided

    Returns:
        Formatted preview string showing old→new values
    """
    lines = [f"\n[bold]The following fields will be updated for MCP '{mcp.name}':[/bold]\n"]

    empty_overrides = []

    # Show each field that will be updated
    for field, new_value in update_data.items():
        old_value = getattr(mcp, field, None)

        # Track empty CLI overrides
        if field in cli_overrides and cli_overrides[field] == "":
            empty_overrides.append(field)

        old_display = _format_preview_value(old_value)
        new_display = _format_preview_value(new_value)

        lines.append(f"- [cyan]{field}[/cyan]: {old_display} → {new_display}")

    # Add warnings for empty CLI overrides
    lines.extend(_build_empty_override_warnings(empty_overrides))

    return "\n".join(lines)


@mcps_group.command()
@click.argument("mcp_ref")
@click.option("--name", help="New MCP name")
@click.option("--transport", type=click.Choice(["http", "sse"]), help="New transport protocol")
@click.option("--description", help="New description")
@click.option(
    "--config",
    help="JSON configuration string or @file reference (e.g., @config.json)",
)
@click.option(
    "--auth",
    "--authentication",
    "auth",
    help="JSON authentication object or @file reference (e.g., @auth.json)",
)
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Import MCP configuration from JSON or YAML export",
)
@click.option("-y", is_flag=True, help="Skip confirmation prompt when using --import")
@output_flags()
@click.pass_context
def update(
    ctx: Any,
    mcp_ref: str,
    name: str | None,
    transport: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
    import_file: str | None,
    y: bool,
) -> None:
    r"""Update an existing MCP with new configuration values.

    You can update an MCP by providing individual fields via CLI options, or by
    importing from a file and optionally overriding specific fields.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        name: New MCP name (optional)
        transport: New transport protocol (optional)
        description: New description (optional)
        config: New JSON configuration string or @file reference (optional)
        auth: New JSON authentication object or @file reference (optional)
        import_file: Optional path to import configuration from export file.
            CLI options override imported values.
        y: Skip confirmation prompt when using --import

    Raises:
        ClickException: If MCP not found, JSON invalid, or no fields specified

    Note:
        Must specify either --import OR at least one CLI field.
        CLI options override imported values when both are specified.
        Uses PATCH for import-based updates, PUT/PATCH for CLI-only updates.

    \b
    Examples:
        Update with CLI options:
            aip mcps update my-mcp --name new-name --transport sse

        Import from file:
            aip mcps update my-mcp --import mcp-export.json

        Import with overrides:
            aip mcps update my-mcp --import mcp-export.json --name new-name -y
    """
    try:
        client = get_client(ctx)

        # Validate that at least one update method is provided
        cli_flags_provided = any(v is not None for v in [name, transport, description, config, auth])
        if not import_file and not cli_flags_provided:
            raise click.ClickException(
                "No update fields specified. Use --import or one of: "
                "--name, --transport, --description, --config, --auth"
            )

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Load and validate import data if provided
        import_payload = None
        if import_file:
            import_payload = _load_import_ready_payload(import_file)
            if not _validate_import_payload_fields(import_payload):
                return

        # Build update data from import and CLI flags
        update_data = _build_update_data_from_sources(import_payload, mcp, name, transport, description, config, auth)

        if not update_data:
            raise click.ClickException("No update fields specified")

        # Show confirmation preview for import-based updates (unless -y flag)
        if import_payload and not y:
            cli_overrides = _collect_cli_overrides(name, transport, description, config, auth)
            preview = _generate_update_preview(mcp, update_data, cli_overrides)
            print_markup(preview)

            if not click.confirm("\nContinue with update?", default=False):
                print_markup("[yellow]Update cancelled.[/yellow]")
                return

        # Update MCP
        with spinner_context(
            ctx,
            "[bold blue]Updating MCP…[/bold blue]",
            console_override=console,
        ):
            updated_mcp = client.mcps.update_mcp(mcp.id, **update_data)

        handle_json_output(ctx, updated_mcp.model_dump())
        handle_rich_output(ctx, display_update_success("MCP", updated_mcp.name))

    except Exception as e:
        _handle_cli_error(ctx, e, "MCP update")


@mcps_group.command()
@click.argument("mcp_ref")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@output_flags()
@click.pass_context
def delete(ctx: Any, mcp_ref: str, yes: bool) -> None:
    """Delete an MCP after confirmation.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        yes: Skip confirmation prompt if True

    Raises:
        ClickException: If MCP not found or deletion fails

    Note:
        Requires confirmation unless --yes flag is provided.
        Deletion is permanent and cannot be undone.
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Confirm deletion
        if not yes and not display_confirmation_prompt("MCP", mcp.name):
            return

        with spinner_context(
            ctx,
            "[bold blue]Deleting MCP…[/bold blue]",
            console_override=console,
        ):
            client.mcps.delete_mcp(mcp.id)

        handle_json_output(
            ctx,
            {
                "success": True,
                "message": f"MCP '{mcp.name}' deleted",
            },
        )
        handle_rich_output(ctx, display_deletion_success("MCP", mcp.name))

    except Exception as e:
        _handle_cli_error(ctx, e, "MCP deletion")
