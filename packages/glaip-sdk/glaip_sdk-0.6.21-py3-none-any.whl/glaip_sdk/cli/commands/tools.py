"""Tool management commands.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
import re
from pathlib import Path
from typing import Any

import click
from glaip_sdk.branding import (
    ACCENT_STYLE,
    ERROR_STYLE,
    INFO,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.context import get_ctx_value, output_flags
from glaip_sdk.cli.display import (
    display_api_error,
    display_confirmation_prompt,
    display_creation_success,
    display_deletion_success,
    display_update_success,
    handle_json_output,
    handle_rich_output,
)
from glaip_sdk.cli.io import fetch_raw_resource_details
from glaip_sdk.cli.io import (
    load_resource_from_file_with_validation as load_resource_from_file,
)
from glaip_sdk.cli.resolution import resolve_resource_reference
from glaip_sdk.cli.rich_helpers import markup_text, print_markup
from glaip_sdk.cli.utils import (
    coerce_to_row,
    format_datetime_fields,
    get_client,
    handle_best_effort_check,
    handle_resource_export,
    output_list,
    output_result,
    spinner_context,
)
from glaip_sdk.icons import ICON_TOOL
from glaip_sdk.utils.import_export import merge_import_with_cli_args
from rich.console import Console

console = Console()


@click.group(name="tools", no_args_is_help=True)
def tools_group() -> None:
    """Tool management operations."""
    pass


def _resolve_tool(ctx: Any, client: Any, ref: str, select: int | None = None) -> Any | None:
    """Resolve a tool by ID or name, handling ambiguous matches interactively.

    This function provides tool-specific resolution logic. It uses
    resolve_resource_reference to find tools by UUID or name, with interactive
    selection when multiple matches are found.

    Args:
        ctx: Click context for CLI operations.
        client: API client instance.
        ref: Tool reference (UUID string or name).
        select: Pre-selected index for non-interactive mode (1-based).

    Returns:
        Tool object if found, None otherwise.
    """
    # Configure tool-specific resolution with standard fuzzy matching
    get_by_id = client.get_tool
    find_by_name = client.find_tools
    return resolve_resource_reference(
        ctx,
        client,
        ref,
        "tool",
        get_by_id,
        find_by_name,
        "Tool",
        select=select,
    )


# ----------------------------- Helpers --------------------------------- #


def _extract_internal_name(code: str) -> str:
    """Extract plugin class name attribute from tool code."""
    m = re.search(r'^\s*name\s*:\s*str\s*=\s*"([^"]+)"', code, re.M)
    if not m:
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', code, re.M)
    if not m:
        raise click.ClickException(
            "Could not find plugin 'name' attribute in the tool file. "
            'Ensure your plugin class defines e.g. name: str = "my_tool".'
        )
    return m.group(1)


def _validate_name_match(provided: str | None, internal: str) -> str:
    """Validate provided --name against internal name; return effective name."""
    if provided and provided != internal:
        raise click.ClickException(
            f"--name '{provided}' does not match plugin internal name '{internal}'. "
            "Either update the code or pass a matching --name."
        )
    return provided or internal


def _check_duplicate_name(client: Any, tool_name: str) -> None:
    """Raise if a tool with the same name already exists."""

    def _check_duplicate() -> None:
        existing = client.find_tools(name=tool_name)
        if existing:
            raise click.ClickException(
                f"A tool named '{tool_name}' already exists. "
                "Please change your plugin's 'name' to a unique value, then re-run."
            )

    handle_best_effort_check(_check_duplicate)


def _parse_tags(tags: str | None) -> list[str]:
    """Return a cleaned list of tag strings from a comma-separated input."""
    return [t.strip() for t in (tags.split(",") if tags else []) if t.strip()]


def _handle_import_file(
    import_file: str | None,
    name: str | None,
    description: str | None,
    tags: tuple[str, ...] | None,
) -> dict[str, Any]:
    """Handle import file logic and merge with CLI arguments."""
    if import_file:
        import_data = load_resource_from_file(Path(import_file), "tool")

        # Merge CLI args with imported data
        cli_args = {
            "name": name,
            "description": description,
            "tags": tags,
        }

        return merge_import_with_cli_args(import_data, cli_args)
    else:
        # No import file - use CLI args directly
        return {
            "name": name,
            "description": description,
            "tags": tags,
        }


def _create_tool_from_file(
    client: Any,
    file_path: str,
    name: str | None,
    description: str | None,
    tags: str | None,
) -> Any:
    """Create tool from file upload."""
    with open(file_path, encoding="utf-8") as f:
        code_content = f.read()

    internal_name = _extract_internal_name(code_content)
    tool_name = _validate_name_match(name, internal_name)
    _check_duplicate_name(client, tool_name)

    # Upload the plugin code as-is (no rewrite)
    return client.create_tool_from_code(
        name=tool_name,
        code=code_content,
        framework="langchain",  # Always langchain
        description=description,
        tags=_parse_tags(tags) if tags else None,
    )


def _validate_creation_parameters(
    file: str | None,
    import_file: str | None,
) -> None:
    """Validate required parameters for tool creation."""
    if not file and not import_file:
        raise click.ClickException("A tool file must be provided. Use --file to specify the tool file to upload.")


@tools_group.command(name="list")
@output_flags()
@click.option(
    "--type",
    "tool_type",
    help="Filter tools by type (e.g., custom, native)",
    type=str,
    required=False,
)
@click.pass_context
def list_tools(ctx: Any, tool_type: str | None) -> None:
    """List all tools."""
    try:
        client = get_client(ctx)
        with spinner_context(
            ctx,
            "[bold blue]Fetching tools…[/bold blue]",
            console_override=console,
        ):
            tools = client.list_tools(tool_type=tool_type)

        # Define table columns: (data_key, header, style, width)
        columns = [
            ("id", "ID", "dim", 36),
            ("name", "Name", ACCENT_STYLE, None),
            ("framework", "Framework", INFO, None),
        ]

        # Transform function for safe dictionary access
        def transform_tool(tool: Any) -> dict[str, Any]:
            """Transform a tool object to a display row dictionary.

            Args:
                tool: Tool object to transform.

            Returns:
                Dictionary with id, name, and framework fields.
            """
            row = coerce_to_row(tool, ["id", "name", "framework"])
            # Ensure id is always a string
            row["id"] = str(row["id"])
            return row

        output_list(ctx, tools, f"{ICON_TOOL} Available Tools", columns, transform_tool)

    except Exception as e:
        raise click.ClickException(str(e)) from e


@tools_group.command()
@click.argument("file_arg", required=False, type=click.Path(exists=True))
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="Tool file to upload",
)
@click.option(
    "--name",
    help="Tool name (extracted from script if file provided)",
)
@click.option(
    "--description",
    help="Tool description (extracted from script if file provided)",
)
@click.option(
    "--tags",
    help="Comma-separated tags for the tool",
)
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Import tool configuration from JSON file",
)
@output_flags()
@click.pass_context
def create(
    ctx: Any,
    file_arg: str | None,
    file: str | None,
    name: str | None,
    description: str | None,
    tags: tuple[str, ...] | None,
    import_file: str | None,
) -> None:
    r"""Create a new tool.

    \b
    Examples:
        aip tools create tool.py  # Create from file
        aip tools create --import tool.json  # Create from exported configuration
    """
    try:
        client = get_client(ctx)

        # Allow positional file argument for better DX (matches examples)
        if not file and file_arg:
            file = file_arg

        # Handle import file and merge with CLI arguments
        merged_data = _handle_import_file(import_file, name, description, tags)

        # Extract merged values
        name = merged_data.get("name")
        description = merged_data.get("description")
        tags = merged_data.get("tags")

        # Validate required parameters
        _validate_creation_parameters(file, import_file)

        # Create tool from file (either direct file or import file)
        with spinner_context(
            ctx,
            "[bold blue]Creating tool…[/bold blue]",
            console_override=console,
        ):
            tool = _create_tool_from_file(client, file, name, description, tags)

        # Handle JSON output
        handle_json_output(ctx, tool.model_dump())

        # Handle Rich output
        creation_method = "file upload (custom)"
        rich_panel = display_creation_success(
            "Tool",
            tool.name,
            tool.id,
            Framework=getattr(tool, "framework", "N/A"),
            Type=getattr(tool, "tool_type", "N/A"),
            Description=getattr(tool, "description", "No description"),
            Method=creation_method,
        )
        handle_rich_output(ctx, rich_panel)

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "tool creation")
        raise click.ClickException(str(e)) from e


@tools_group.command()
@click.argument("tool_ref")
@click.option("--select", type=int, help="Choose among ambiguous matches (1-based)")
@click.option(
    "--export",
    type=click.Path(dir_okay=False, writable=True),
    help="Export complete tool configuration to file (format auto-detected from .json/.yaml extension)",
)
@output_flags()
@click.pass_context
def get(ctx: Any, tool_ref: str, select: int | None, export: str | None) -> None:
    r"""Get tool details.

    \b
    Examples:
        aip tools get my-tool
        aip tools get my-tool --export tool.json    # Exports complete configuration as JSON
        aip tools get my-tool --export tool.yaml    # Exports complete configuration as YAML
    """
    try:
        client = get_client(ctx)

        # Resolve tool with ambiguity handling
        tool = _resolve_tool(ctx, client, tool_ref, select)

        # Handle export option
        if export:
            handle_resource_export(
                ctx,
                tool,
                Path(export),
                resource_type="tool",
                get_by_id_func=client.get_tool_by_id,
                console_override=console,
            )

        # Try to fetch raw API data first to preserve ALL fields
        with spinner_context(
            ctx,
            "[bold blue]Fetching detailed tool data…[/bold blue]",
            console_override=console,
        ):
            raw_tool_data = fetch_raw_resource_details(client, tool, "tools")

        if raw_tool_data:
            # Use raw API data - this preserves ALL fields
            # Format dates for better display (minimal postprocessing)
            formatted_data = format_datetime_fields(raw_tool_data)

            # Display using output_result with raw data
            output_result(
                ctx,
                formatted_data,
                title="Tool Details",
                panel_title=f"{ICON_TOOL} {raw_tool_data.get('name', 'Unknown')}",
            )
        else:
            # Fall back to original method if raw fetch fails
            console.print(f"[{WARNING_STYLE}]Falling back to Pydantic model data[/]")

            # Create result data with all available fields from backend
            result_data = {
                "id": str(getattr(tool, "id", "N/A")),
                "name": getattr(tool, "name", "N/A"),
                "tool_type": getattr(tool, "tool_type", "N/A"),
                "framework": getattr(tool, "framework", "N/A"),
                "version": getattr(tool, "version", "N/A"),
                "description": getattr(tool, "description", "N/A"),
            }

            output_result(
                ctx,
                result_data,
                title="Tool Details",
                panel_title=f"{ICON_TOOL} {tool.name}",
            )

    except Exception as e:
        raise click.ClickException(str(e)) from e


@tools_group.command()
@click.argument("tool_id")
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="New tool file for code update (custom tools only)",
)
@click.option("--description", help="New description")
@click.option("--tags", help="Comma-separated tags")
@output_flags()
@click.pass_context
def update(
    ctx: Any,
    tool_id: str,
    file: str | None,
    description: str | None,
    tags: tuple[str, ...] | None,
) -> None:
    """Update a tool (code or metadata)."""
    try:
        client = get_client(ctx)

        # Get tool by ID (no ambiguity handling needed)
        try:
            with spinner_context(
                ctx,
                "[bold blue]Fetching tool…[/bold blue]",
                console_override=console,
            ):
                tool = client.get_tool_by_id(tool_id)
        except Exception as e:
            raise click.ClickException(f"Tool with ID '{tool_id}' not found: {e}") from e

        # Prepare update data
        update_data = {}
        if description:
            update_data["description"] = description
        if tags:
            update_data["tags"] = [tag.strip() for tag in tags.split(",")]

        if file:
            # Update code via file upload (custom tools only)
            if tool.tool_type != "custom":
                raise click.ClickException(
                    "File updates are only supported for custom tools. "
                    f"Tool '{tool.name}' is of type '{tool.tool_type}'."
                )
            with spinner_context(
                ctx,
                "[bold blue]Uploading new tool code…[/bold blue]",
                console_override=console,
            ):
                updated_tool = client.tools.update_tool_via_file(tool.id, file, framework=tool.framework)
            handle_rich_output(
                ctx,
                markup_text(f"[{SUCCESS_STYLE}]✓[/] Tool code updated from {file}"),
            )
        elif update_data:
            # Update metadata only (native tools only)
            if tool.tool_type != "native":
                raise click.ClickException(
                    "Metadata updates are only supported for native tools. "
                    f"Tool '{tool.name}' is of type '{tool.tool_type}'."
                )
            with spinner_context(
                ctx,
                "[bold blue]Updating tool metadata…[/bold blue]",
                console_override=console,
            ):
                updated_tool = tool.update(**update_data)
            handle_rich_output(ctx, markup_text(f"[{SUCCESS_STYLE}]✓[/] Tool metadata updated"))
        else:
            handle_rich_output(ctx, markup_text(f"[{WARNING_STYLE}]No updates specified[/]"))
            return

        handle_json_output(ctx, updated_tool.model_dump())
        handle_rich_output(ctx, display_update_success("Tool", updated_tool.name))

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "tool update")
        raise click.ClickException(str(e)) from e


@tools_group.command()
@click.argument("tool_id")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@output_flags()
@click.pass_context
def delete(ctx: Any, tool_id: str, yes: bool) -> None:
    """Delete a tool."""
    try:
        client = get_client(ctx)

        # Get tool by ID (no ambiguity handling needed)
        try:
            with spinner_context(
                ctx,
                "[bold blue]Fetching tool…[/bold blue]",
                console_override=console,
            ):
                tool = client.get_tool_by_id(tool_id)
        except Exception as e:
            raise click.ClickException(f"Tool with ID '{tool_id}' not found: {e}") from e

        # Confirm deletion via centralized display helper
        if not yes and not display_confirmation_prompt("Tool", tool.name):
            return

        with spinner_context(
            ctx,
            "[bold blue]Deleting tool…[/bold blue]",
            console_override=console,
        ):
            tool.delete()

        handle_json_output(
            ctx,
            {
                "success": True,
                "message": f"Tool '{tool.name}' deleted",
            },
        )
        handle_rich_output(ctx, display_deletion_success("Tool", tool.name))

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "tool deletion")
        raise click.ClickException(str(e)) from e


@tools_group.command("script")
@click.argument("tool_id")
@output_flags()
@click.pass_context
def script(ctx: Any, tool_id: str) -> None:
    """Get tool script content."""
    try:
        client = get_client(ctx)
        with spinner_context(
            ctx,
            "[bold blue]Fetching tool script…[/bold blue]",
            console_override=console,
        ):
            script_content = client.get_tool_script(tool_id)

        if get_ctx_value(ctx, "view") == "json":
            click.echo(json.dumps({"script": script_content}, indent=2))
        else:
            console.print(f"[{SUCCESS_STYLE}]📜 Tool Script for '{tool_id}':[/]")
            console.print(script_content)

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            print_markup(f"[{ERROR_STYLE}]Error getting tool script: {e}[/]", console=console)
        raise click.ClickException(str(e)) from e
