"""CLI display utilities for success/failure panels and Rich renderers.

This module handles all display-related functionality for CLI commands,
including success messages, error handling, and output formatting.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from glaip_sdk.branding import ERROR_STYLE, SUCCESS, SUCCESS_STYLE, WARNING_STYLE
from glaip_sdk.cli.hints import command_hint, format_command_hint, in_slash_mode
from glaip_sdk.cli.rich_helpers import markup_text
from glaip_sdk.icons import ICON_AGENT, ICON_TOOL
from glaip_sdk.rich_components import AIPPanel

console = Console()


def display_creation_success(
    resource_type: str, resource_name: str, resource_id: str, **additional_fields: Any
) -> Panel:
    """Create standardized success message for resource creation.

    Args:
        resource_type: Type of resource (e.g., "Agent", "Tool", "MCP")
        resource_name: Name of the created resource
        resource_id: ID of the created resource
        **additional_fields: Additional fields to display

    Returns:
        Rich Panel object for display
    """
    # Build additional fields display
    fields_display = ""
    if additional_fields:
        fields_display = "\n" + "\n".join(f"{key}: {value}" for key, value in additional_fields.items())

    return AIPPanel(
        f"[{SUCCESS_STYLE}]✅ {resource_type} '{resource_name}' created successfully![/]\n\n"
        f"ID: {resource_id}{fields_display}",
        title=f"{ICON_AGENT} {resource_type} Created",
        border_style=SUCCESS,
        padding=(0, 1),
    )


def display_update_success(resource_type: str, resource_name: str) -> Text:
    """Create standardized success message for resource update.

    Args:
        resource_type: Type of resource (e.g., "Agent", "Tool", "MCP")
        resource_name: Name of the updated resource

    Returns:
        Rich Text object for display
    """
    return markup_text(f"[{SUCCESS_STYLE}]✅ {resource_type} '{resource_name}' updated successfully[/]")


def display_deletion_success(resource_type: str, resource_name: str) -> Text:
    """Create standardized success message for resource deletion.

    Args:
        resource_type: Type of resource (e.g., "Agent", "Tool", "MCP")
        resource_name: Name of the deleted resource

    Returns:
        Rich Text object for display
    """
    return markup_text(f"[{SUCCESS_STYLE}]✅ {resource_type} '{resource_name}' deleted successfully[/]")


def display_api_error(error: Exception, operation: str = "operation") -> None:
    """Display standardized API error message.

    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
    """
    error_type = type(error).__name__
    error_message = markup_text(f"[{ERROR_STYLE}]Error during {operation}: {error}[/]")
    error_message.no_wrap = True
    error_message.overflow = "ignore"
    console.print(error_message)

    error_type_message = markup_text(f"[dim]Error type: {error_type}[/dim]")
    error_type_message.no_wrap = True
    error_type_message.overflow = "ignore"
    console.print(error_type_message)


def print_api_error(e: Exception) -> None:
    """Print API error with consistent formatting for both JSON and Rich views.

    Args:
        e: The exception to format and display

    Notes:
        - Extracts status_code, error_type, and payload from APIError exceptions
        - Provides consistent error reporting across CLI commands
        - Handles both JSON and Rich output formats
        - Special handling for validation errors with detailed field-level errors
    """
    if not hasattr(e, "__dict__"):
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        return

    if not hasattr(e, "status_code"):
        console.print(f"[{ERROR_STYLE}]Error: {e}[/]")
        return

    error_text = str(e).strip()
    if not error_text:
        error_text = "Unknown error"
    if "\n" in error_text:
        error_text = error_text.splitlines()[0]
    console.print(f"[{ERROR_STYLE}]API Error: {error_text}[/]")
    status_code = getattr(e, "status_code", None)
    if status_code is not None:
        console.print(f"[{WARNING_STYLE}]Status: {status_code}[/]")

    payload = getattr(e, "payload", _MISSING)
    if payload is _MISSING:
        return

    if payload:
        if not _print_structured_payload(payload):
            console.print(f"[{WARNING_STYLE}]Details: {payload}[/]")
    else:
        console.print(f"[{WARNING_STYLE}]Details: {payload}[/]")


def _print_structured_payload(payload: Any) -> bool:
    """Print structured payloads with enhanced formatting. Returns True if handled."""
    if not isinstance(payload, dict):
        return False

    if "detail" in payload and _print_validation_details(payload["detail"]):
        return True

    if "details" in payload and _print_details_field(payload["details"]):
        return True

    return False


def _print_validation_details(detail: Any) -> bool:
    """Render FastAPI-style validation errors."""
    if not isinstance(detail, list) or not detail:
        return False

    console.print(f"[{ERROR_STYLE}]Validation Errors:[/]")
    for error in detail:
        if isinstance(error, dict):
            loc = " -> ".join(str(x) for x in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            error_type = error.get("type", "unknown")
            location = loc if loc else "field"
            console.print(f"  [{WARNING_STYLE}]• {location}:[/] {msg}")
            if error_type != "unknown":
                console.print(f"    [dim]({error_type})[/dim]")
        else:
            console.print(f"  [{WARNING_STYLE}]•[/] {error}")
    return True


def _print_details_field(details: Any) -> bool:
    """Render custom error details from API payloads."""
    if not details:
        return False

    console.print(f"[{ERROR_STYLE}]Error Details:[/]")
    if isinstance(details, str):
        console.print(f"  [{WARNING_STYLE}]•[/] {details}")
    elif isinstance(details, list):
        for detail in details:
            console.print(f"  [{WARNING_STYLE}]•[/] {detail}")
    else:
        console.print(f"  [{WARNING_STYLE}]•[/] {details}")
    return True


_MISSING = object()


def build_resource_result_data(resource: Any, fields: list[str]) -> dict[str, Any]:
    """Return a normalized mapping of ``fields`` extracted from ``resource``."""
    result: dict[str, Any] = {}
    for field in fields:
        try:
            value = getattr(resource, field)
        except AttributeError:
            value = _MISSING
        except Exception:
            value = _MISSING

        result[field] = _normalise_field_value(field, value)

    return result


def _normalise_field_value(field: str, value: Any) -> Any:
    """Convert special sentinel values into display-friendly text."""
    if value is _MISSING:
        return "N/A"
    if hasattr(value, "_mock_name"):
        return "N/A"
    if field == "id":
        return str(value)
    return value


def _get_context_object(ctx: Any) -> dict[str, Any]:
    """Get context object safely."""
    ctx_obj = getattr(ctx, "obj", {}) if ctx is not None else {}
    return ctx_obj if isinstance(ctx_obj, dict) else {}


def _should_output_json(ctx_obj: dict[str, Any]) -> bool:
    """Check if output should be in JSON format."""
    return ctx_obj.get("view") == "json"


def _build_error_output_data(error: Exception) -> dict[str, Any]:
    """Build error output data with additional error details."""
    output_data = {"error": str(error)}

    # Add additional error details if available
    if hasattr(error, "status_code"):
        output_data["status_code"] = error.status_code
    if hasattr(error, "error_type"):
        output_data["error_type"] = error.error_type
    if hasattr(error, "payload"):
        output_data["details"] = error.payload

    return output_data


def _build_success_output_data(data: Any) -> dict[str, Any]:
    """Build success output data."""
    return data if data is not None else {"success": True}


def handle_json_output(ctx: Any, data: Any = None, error: Exception = None) -> None:
    """Handle JSON output format for CLI commands.

    Args:
        ctx: Click context
        data: Data to output (for successful operations)
        error: Error to output (for failed operations)
    """
    ctx_obj = _get_context_object(ctx)

    if _should_output_json(ctx_obj):
        if error:
            output_data = _build_error_output_data(error)
        else:
            output_data = _build_success_output_data(data)

        click.echo(json.dumps(output_data, indent=2, default=str))


def handle_rich_output(ctx: Any, rich_content: Any = None) -> None:
    """Handle Rich output format for CLI commands.

    Args:
        ctx: Click context
        rich_content: Rich content to display
    """
    ctx_obj = getattr(ctx, "obj", {}) if ctx is not None else {}
    if not isinstance(ctx_obj, dict):
        ctx_obj = {}

    if ctx_obj.get("view") != "json" and rich_content:
        console.print(rich_content)


def display_confirmation_prompt(resource_type: str, resource_name: str) -> bool:
    """Display standardized confirmation prompt for destructive operations.

    Args:
        resource_type: Type of resource (e.g., "Agent", "Tool", "MCP")
        resource_name: Name of the resource

    Returns:
        True if user confirms, False otherwise
    """
    if not click.confirm(f"Are you sure you want to delete {resource_type.lower()} '{resource_name}'?"):
        if console.is_terminal:
            console.print(Text("Deletion cancelled."))
        return False
    return True


def display_agent_run_suggestions(agent: Any) -> Panel:
    """Return a panel with post-creation suggestions for an agent."""
    agent_id = getattr(agent, "id", "")
    agent_name = getattr(agent, "name", "")
    slash_mode = in_slash_mode()
    run_hint_id = command_hint(
        f'agents run {agent_id} "Your message here"',
        slash_command=None,
    )
    run_hint_name = command_hint(
        f'agents run "{agent_name}" "Your message here"',
        slash_command=None,
    )

    content_parts: list[str] = ["[bold blue]💡 Next Steps:[/bold blue]\n\n"]

    if slash_mode:
        slash_shortcuts = "\n".join(
            f"   {format_command_hint(command, description) or command}"
            for command, description in (
                ("/details", "Show configuration (toggle preview)"),
                ("/help", "Show command palette menu"),
                ("/exit", "Return to the palette"),
            )
        )
        content_parts.append(
            f"🚀 Start chatting with [bold]{agent_name}[/bold] right here:\n"
            f"   Type your message below and press Enter to run it immediately.\n\n"
            f"{ICON_TOOL} Slash shortcuts:\n"
            f"{slash_shortcuts}"
        )
    else:
        cli_hint_lines = [format_command_hint(hint) or hint for hint in (run_hint_id, run_hint_name) if hint]
        if cli_hint_lines:
            joined_hints = "\n".join(f"   {hint}" for hint in cli_hint_lines)
            content_parts.append(f"🚀 Run this agent from the CLI:\n{joined_hints}\n\n")
        content_parts.append(
            f"{ICON_TOOL} Available options:\n"
            f"   [dim]--chat-history[/dim]  Include previous conversation\n"
            f"   [dim]--file[/dim]          Attach files\n"
            f"   [dim]--input[/dim]         Alternative input method\n"
            f"   [dim]--timeout[/dim]       Set execution timeout\n"
            f"   [dim]--save[/dim]          Save transcript to file\n"
            f"   [dim]--verbose[/dim]       Show detailed execution\n\n"
            f"💡 [dim]Input text can be positional OR use --input flag (both work!)[/dim]"
        )

    return AIPPanel(
        "".join(content_parts),
        title=f"{ICON_AGENT} Ready to Run Agent",
        border_style="blue",
        padding=(0, 1),
    )
