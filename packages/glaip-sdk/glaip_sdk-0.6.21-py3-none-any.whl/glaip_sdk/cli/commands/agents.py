"""Agent CLI commands for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from glaip_sdk.branding import (
    ACCENT_STYLE,
    ERROR_STYLE,
    HINT_PREFIX_STYLE,
    INFO,
    SUCCESS,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.agent_config import (
    merge_agent_config_with_cli_args as merge_import_with_cli_args,
)
from glaip_sdk.cli.agent_config import (
    resolve_agent_language_model_selection as resolve_language_model_selection,
)
from glaip_sdk.cli.agent_config import (
    sanitize_agent_config_for_cli as sanitize_agent_config,
)
from glaip_sdk.cli.constants import DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT
from glaip_sdk.cli.context import get_ctx_value, output_flags
from glaip_sdk.cli.display import (
    build_resource_result_data,
    display_agent_run_suggestions,
    display_confirmation_prompt,
    display_creation_success,
    display_deletion_success,
    display_update_success,
    handle_json_output,
    handle_rich_output,
    print_api_error,
)
from glaip_sdk.cli.hints import in_slash_mode
from glaip_sdk.cli.io import (
    fetch_raw_resource_details,
)
from glaip_sdk.cli.io import (
    load_resource_from_file_with_validation as load_resource_from_file,
)
from glaip_sdk.cli.resolution import resolve_resource_reference
from glaip_sdk.cli.rich_helpers import markup_text, print_markup
from glaip_sdk.cli.transcript import (
    maybe_launch_post_run_viewer,
    store_transcript_for_session,
)
from glaip_sdk.cli.utils import (
    _fuzzy_pick_for_resources,
    build_renderer,
    coerce_to_row,
    get_client,
    handle_resource_export,
    output_list,
    output_result,
    spinner_context,
    with_client_and_spinner,
)
from glaip_sdk.cli.validators import (
    validate_agent_instruction_cli as validate_agent_instruction,
)
from glaip_sdk.cli.validators import (
    validate_agent_name_cli as validate_agent_name,
)
from glaip_sdk.cli.validators import (
    validate_timeout_cli as validate_timeout,
)
from glaip_sdk.config.constants import AGENT_CONFIG_FIELDS, DEFAULT_AGENT_RUN_TIMEOUT, DEFAULT_MODEL
from glaip_sdk.exceptions import AgentTimeoutError
from glaip_sdk.icons import ICON_AGENT
from glaip_sdk.utils import format_datetime, is_uuid
from glaip_sdk.utils.agent_config import normalize_agent_config_for_import
from glaip_sdk.utils.import_export import convert_export_to_import_format
from glaip_sdk.utils.rendering.renderer.toggle import TranscriptToggleController
from glaip_sdk.utils.validation import coerce_timeout

console = Console()

# Error message constants
AGENT_NOT_FOUND_ERROR = "Agent not found"

# Instruction preview controls


def _safe_agent_attribute(agent: Any, name: str) -> Any:
    """Return attribute value for ``name`` while filtering Mock sentinels."""
    try:
        value = getattr(agent, name)
    except Exception:
        return None

    if hasattr(value, "_mock_name"):
        return None
    return value


def _coerce_mapping_candidate(candidate: Any) -> dict[str, Any] | None:
    """Convert a mapping-like candidate to a plain dict when possible."""
    if candidate is None:
        return None
    if isinstance(candidate, Mapping):
        return dict(candidate)
    return None


def _call_agent_method(agent: Any, method_name: str) -> dict[str, Any] | None:
    """Attempt to call the named method and coerce its output to a dict."""
    method = getattr(agent, method_name, None)
    if not callable(method):
        return None
    try:
        candidate = method()
    except Exception:
        return None
    return _coerce_mapping_candidate(candidate)


def _coerce_agent_via_methods(agent: Any) -> dict[str, Any] | None:
    """Try standard serialisation helpers to produce a mapping."""
    for attr in ("model_dump", "dict", "to_dict"):
        mapping = _call_agent_method(agent, attr)
        if mapping is not None:
            return mapping
    return None


def _build_fallback_agent_mapping(agent: Any) -> dict[str, Any]:
    """Construct a minimal mapping from well-known agent attributes."""
    fallback_fields = (
        "id",
        "name",
        "instruction",
        "description",
        "model",
        "agent_config",
        *[field for field in AGENT_CONFIG_FIELDS if field not in ("name", "instruction", "model")],
        "tool_configs",
    )

    fallback: dict[str, Any] = {}
    for field in fallback_fields:
        value = _safe_agent_attribute(agent, field)
        if value is not None:
            fallback[field] = value

    return fallback or {"name": str(agent)}


def _prepare_agent_output(agent: Any) -> dict[str, Any]:
    """Build a JSON-serialisable mapping for CLI output."""
    method_mapping = _coerce_agent_via_methods(agent)
    if method_mapping is not None:
        return method_mapping

    intrinsic = _coerce_mapping_candidate(agent)
    if intrinsic is not None:
        return intrinsic

    return _build_fallback_agent_mapping(agent)


def _fetch_full_agent_details(client: Any, agent: Any) -> Any | None:
    """Fetch full agent details by ID to ensure all fields are populated."""
    try:
        agent_id = str(getattr(agent, "id", "")).strip()
        if agent_id:
            return client.agents.get_agent_by_id(agent_id)
    except Exception:
        # If fetching full details fails, continue with the resolved object
        pass
    return agent


def _normalise_model_name(value: Any) -> str | None:
    """Return a cleaned model name or None when not usable."""
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, bool):
        return None
    return str(value)


def _model_from_config(agent: Any) -> str | None:
    """Extract a usable model name from an agent's configuration mapping."""
    config = getattr(agent, "agent_config", None)
    if not config or not isinstance(config, dict):
        return None

    for key in ("lm_name", "model"):
        normalised = _normalise_model_name(config.get(key))
        if normalised:
            return normalised
    return None


def _get_agent_model_name(agent: Any) -> str | None:
    """Extract model name from agent configuration."""
    config_model = _model_from_config(agent)
    if config_model:
        return config_model

    normalised_attr = _normalise_model_name(getattr(agent, "model", None))
    if normalised_attr:
        return normalised_attr

    return DEFAULT_MODEL


def _resolve_resources_by_name(
    _client: Any, items: tuple[str, ...], resource_type: str, find_func: Any, label: str
) -> list[str]:
    """Resolve resource names/IDs to IDs, handling ambiguity.

    Args:
        client: API client
        items: Tuple of resource names/IDs
        resource_type: Type of resource ("tool" or "agent")
        find_func: Function to find resources by name
        label: Label for error messages

    Returns:
        List of resolved resource IDs
    """
    out = []
    for ref in items or ():
        if is_uuid(ref):
            out.append(ref)
            continue

        matches = find_func(name=ref)
        if not matches:
            raise click.ClickException(f"{label} not found: {ref}")
        if len(matches) > 1:
            raise click.ClickException(f"Multiple {resource_type}s named '{ref}'. Use ID instead.")
        out.append(str(matches[0].id))
    return out


def _fetch_and_format_raw_agent_data(client: Any, agent: Any) -> dict | None:
    """Fetch raw agent data and format it for display."""
    try:
        raw_agent_data = fetch_raw_resource_details(client, agent, "agents")
        if not raw_agent_data:
            return None

        # Format dates for better display
        formatted_data = raw_agent_data.copy()
        if "created_at" in formatted_data:
            formatted_data["created_at"] = format_datetime(formatted_data["created_at"])
        if "updated_at" in formatted_data:
            formatted_data["updated_at"] = format_datetime(formatted_data["updated_at"])

        return formatted_data
    except Exception:
        return None


def _format_fallback_agent_data(client: Any, agent: Any) -> dict:
    """Format fallback agent data using Pydantic model."""
    full_agent = _fetch_full_agent_details(client, agent)

    # Define fields to extract
    fields = [
        "id",
        "name",
        "type",
        "framework",
        "version",
        "description",
        "instruction",
        "created_at",
        "updated_at",
        "metadata",
        "language_model_id",
        "agent_config",
        "tools",
        "agents",
        "mcps",
        "a2a_profile",
        "tool_configs",
    ]

    result_data = build_resource_result_data(full_agent, fields)

    # Handle missing instruction
    if result_data.get("instruction") in ["N/A", None, ""]:
        result_data["instruction"] = "-"

    # Format dates for better display
    for date_field in ["created_at", "updated_at"]:
        if result_data.get(date_field) and result_data[date_field] not in ["N/A", None]:
            result_data[date_field] = format_datetime(result_data[date_field])

    return result_data


def _clamp_instruction_preview_limit(limit: int | None) -> int:
    """Normalise preview limit; 0 disables trimming."""
    default = DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT
    if limit is None:  # pragma: no cover
        return default
    try:
        limit_value = int(limit)
    except (TypeError, ValueError):  # pragma: no cover - defensive parsing
        return default

    if limit_value <= 0:
        return 0

    return limit_value


def _build_instruction_preview(value: Any, limit: int) -> tuple[Any, bool]:
    """Return a trimmed preview for long instruction strings."""
    if not isinstance(value, str) or limit <= 0:  # pragma: no cover
        return value, False

    if len(value) <= limit:
        return value, False

    trimmed_value = value[:limit].rstrip()
    preview = f"{trimmed_value}\n\n... (preview trimmed)"
    return preview, True


def _prepare_agent_details_payload(
    data: dict[str, Any],
    *,
    instruction_preview_limit: int,
) -> tuple[dict[str, Any], bool]:
    """Return payload ready for rendering plus trim indicator."""
    payload = deepcopy(data)
    trimmed = False
    if instruction_preview_limit > 0:
        preview, trimmed = _build_instruction_preview(payload.get("instruction"), instruction_preview_limit)
        if trimmed:
            payload["instruction"] = preview
    return payload, trimmed


def _show_instruction_trim_hint(
    ctx: Any,
    *,
    trimmed: bool,
    preview_limit: int,
) -> None:
    """Render hint describing how to expand or collapse the instruction preview."""
    if not trimmed or preview_limit <= 0:
        return

    view = get_ctx_value(ctx, "view", "rich") if ctx is not None else "rich"
    if view != "rich":  # pragma: no cover - non-rich view handling
        return

    suffix = f"[dim](preview: {preview_limit:,} chars)[/]"
    if in_slash_mode(ctx):
        console.print(
            f"[{HINT_PREFIX_STYLE}]Tip:[/] Use '/details' again to toggle between trimmed and full prompts {suffix}"
        )
        return

    console.print(  # pragma: no cover - fallback hint rendering
        f"[{HINT_PREFIX_STYLE}]Tip:[/] Run 'aip agents get <agent> --instruction-preview <n>' "
        f"to control prompt preview length {suffix}"
    )


def _display_agent_details(
    ctx: Any,
    client: Any,
    agent: Any,
    *,
    instruction_preview_limit: int | None = None,
) -> None:
    """Display full agent details using raw API data to preserve ALL fields."""
    if agent is None:
        handle_rich_output(ctx, markup_text(f"[{ERROR_STYLE}]❌ No agent provided[/]"))
        return

    preview_limit = _clamp_instruction_preview_limit(instruction_preview_limit)
    trimmed_instruction = False

    # Try to fetch and format raw agent data first
    with spinner_context(
        ctx,
        "[bold blue]Loading agent details…[/bold blue]",
        console_override=console,
    ):
        formatted_data = _fetch_and_format_raw_agent_data(client, agent)

    if formatted_data:
        # Use raw API data - this preserves ALL fields including account_id
        panel_title = f"{ICON_AGENT} {formatted_data.get('name', 'Unknown')}"
        payload, trimmed_instruction = _prepare_agent_details_payload(
            formatted_data,
            instruction_preview_limit=preview_limit,
        )
        output_result(
            ctx,
            payload,
            title=panel_title,
        )
    else:
        # Fall back to Pydantic model data if raw fetch fails
        handle_rich_output(
            ctx,
            markup_text(f"[{WARNING_STYLE}]Falling back to Pydantic model data[/]"),
        )

        with spinner_context(
            ctx,
            "[bold blue]Preparing fallback agent details…[/bold blue]",
            console_override=console,
        ):
            result_data = _format_fallback_agent_data(client, agent)

        # Display using output_result
        payload, trimmed_instruction = _prepare_agent_details_payload(
            result_data,
            instruction_preview_limit=preview_limit,
        )
        output_result(
            ctx,
            payload,
            title="Agent Details",
        )

    _show_instruction_trim_hint(
        ctx,
        trimmed=trimmed_instruction,
        preview_limit=preview_limit,
    )


@click.group(name="agents", no_args_is_help=True)
def agents_group() -> None:
    """Agent management operations."""
    pass


def _resolve_agent(
    ctx: Any,
    client: Any,
    ref: str,
    select: int | None = None,
    interface_preference: str = "fuzzy",
) -> Any | None:
    """Resolve an agent by ID or name, supporting fuzzy and questionary interfaces.

    This function provides agent-specific resolution with flexible UI options.
    It wraps resolve_resource_reference with agent-specific configuration, allowing
    users to choose between fuzzy search and traditional questionary selection.

    Args:
        ctx: Click context for CLI command execution.
        client: AIP SDK client instance.
        ref: Agent identifier (UUID or name string).
        select: Pre-selected index for non-interactive resolution (1-based).
        interface_preference: UI preference - "fuzzy" for search or "questionary" for list.

    Returns:
        Agent object when found, None when resolution fails.
    """
    # Configure agent-specific resolution parameters
    resolution_config = {
        "resource_type": "agent",
        "get_by_id": client.agents.get_agent_by_id,
        "find_by_name": client.agents.find_agents,
        "label": "Agent",
    }
    # Use agent-specific resolution with flexible interface preference
    return resolve_resource_reference(
        ctx,
        client,
        ref,
        resolution_config["resource_type"],
        resolution_config["get_by_id"],
        resolution_config["find_by_name"],
        resolution_config["label"],
        select=select,
        interface_preference=interface_preference,
    )


@agents_group.command(name="list")
@click.option("--simple", is_flag=True, help="Show simple table without interactive picker")
@click.option("--type", "agent_type", help="Filter by agent type (config, code, a2a, langflow)")
@click.option("--framework", help="Filter by framework (langchain, langgraph, google_adk)")
@click.option("--name", help="Filter by partial name match (case-insensitive)")
@click.option("--version", help="Filter by exact version match")
@click.option(
    "--sync-langflow",
    is_flag=True,
    help="Sync with LangFlow server before listing (only applies when filtering by langflow type)",
)
@output_flags()
@click.pass_context
def list_agents(
    ctx: Any,
    simple: bool,
    agent_type: str | None,
    framework: str | None,
    name: str | None,
    version: str | None,
    sync_langflow: bool,
) -> None:
    """List agents with optional filtering."""
    try:
        with with_client_and_spinner(
            ctx,
            "[bold blue]Fetching agents…[/bold blue]",
            console_override=console,
        ) as client:
            # Query agents with specified filters
            filter_params = {
                "agent_type": agent_type,
                "framework": framework,
                "name": name,
                "version": version,
                "sync_langflow_agents": sync_langflow,
            }
            agents = client.agents.list_agents(**filter_params)

        # Define table columns: (data_key, header, style, width)
        columns = [
            ("id", "ID", "dim", 36),
            ("name", "Name", ACCENT_STYLE, None),
            ("type", "Type", WARNING_STYLE, None),
            ("framework", "Framework", INFO, None),
            ("version", "Version", SUCCESS, None),
        ]

        # Transform function for safe attribute access
        def transform_agent(agent: Any) -> dict[str, Any]:
            """Transform an agent object to a display row dictionary.

            Args:
                agent: Agent object to transform.

            Returns:
                Dictionary with id, name, type, framework, and version fields.
            """
            row = coerce_to_row(agent, ["id", "name", "type", "framework", "version"])
            # Ensure id is always a string
            row["id"] = str(row["id"])
            return row

        # Use fuzzy picker for interactive agent selection and details (default behavior)
        # Skip if --simple flag is used, a name filter is applied, or non-rich output is requested
        ctx_obj = ctx.obj if isinstance(getattr(ctx, "obj", None), dict) else {}
        current_view = ctx_obj.get("view")
        interactive_enabled = (
            not simple
            and name is None
            and current_view not in {"json", "plain", "md"}
            and console.is_terminal
            and os.isatty(1)
            and len(agents) > 0
        )

        # Track picker attempt so the fallback table doesn't re-open the palette
        picker_attempted = False
        if interactive_enabled:
            picker_attempted = True
            picked_agent = _fuzzy_pick_for_resources(agents, "agent", "")
            if picked_agent:
                _display_agent_details(ctx, client, picked_agent)
                # Show run suggestions via centralized display helper
                handle_rich_output(ctx, display_agent_run_suggestions(picked_agent))
                return

        # Show simple table (either --simple flag or non-interactive)
        output_list(
            ctx,
            agents,
            f"{ICON_AGENT} Available Agents",
            columns,
            transform_agent,
            skip_picker=(
                not interactive_enabled
                or picker_attempted
                or simple
                or any(param is not None for param in (agent_type, framework, name, version))
            ),
            use_pager=False,
        )

    except Exception as e:
        raise click.ClickException(str(e)) from e


@agents_group.command()
@click.argument("agent_ref")
@click.option("--select", type=int, help="Choose among ambiguous matches (1-based)")
@click.option(
    "--export",
    type=click.Path(dir_okay=False, writable=True),
    help="Export complete agent configuration to file (format auto-detected from .json/.yaml extension)",
)
@click.option(
    "--instruction-preview",
    type=int,
    default=0,
    show_default=True,
    help="Instruction preview length when printing instructions (0 shows full prompt).",
)
@output_flags()
@click.pass_context
def get(
    ctx: Any,
    agent_ref: str,
    select: int | None,
    export: str | None,
    instruction_preview: int,
) -> None:
    r"""Get agent details.

    \b
    Examples:
        aip agents get my-agent
        aip agents get my-agent --export agent.json    # Exports complete configuration as JSON
        aip agents get my-agent --export agent.yaml    # Exports complete configuration as YAML
    """
    try:
        # Initialize API client for agent retrieval
        api_client = get_client(ctx)

        # Resolve agent reference using questionary interface for better UX
        agent = _resolve_agent(ctx, api_client, agent_ref, select, interface_preference="questionary")

        if not agent:
            raise click.ClickException(f"Agent '{agent_ref}' not found")

        # Handle export option if requested
        if export:
            handle_resource_export(
                ctx,
                agent,
                Path(export),
                resource_type="agent",
                get_by_id_func=api_client.agents.get_agent_by_id,
                console_override=console,
            )

        # Display full agent details using the standardized helper
        _display_agent_details(
            ctx,
            api_client,
            agent,
            instruction_preview_limit=instruction_preview,
        )

        # Show run suggestions via centralized display helper
        handle_rich_output(ctx, display_agent_run_suggestions(agent))

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e)) from e


def _validate_run_input(input_option: str | None, input_text: str | None) -> str:
    """Validate and determine the final input text for agent run."""
    final_input_text = input_option if input_option else input_text

    if not final_input_text:
        raise click.ClickException("Input text is required. Use either positional argument or --input option.")

    return final_input_text


def _parse_chat_history(chat_history: str | None) -> list[dict[str, Any]] | None:
    """Parse chat history JSON if provided."""
    if not chat_history:
        return None

    try:
        return json.loads(chat_history)
    except json.JSONDecodeError as err:
        raise click.ClickException("Invalid JSON in chat history") from err


def _setup_run_renderer(ctx: Any, save: str | None, verbose: bool) -> Any:
    """Set up renderer and working console for agent run."""
    tty_enabled = bool(get_ctx_value(ctx, "tty", True))
    return build_renderer(
        ctx,
        save_path=save,
        verbose=verbose,
        _tty_enabled=tty_enabled,
    )


def _maybe_attach_transcript_toggle(ctx: Any, renderer: Any) -> None:
    """Attach transcript toggle controller when interactive TTY is available."""
    if renderer is None:
        return

    console_obj = getattr(renderer, "console", None)
    if console_obj is None or not getattr(console_obj, "is_terminal", False):
        return

    tty_enabled = bool(get_ctx_value(ctx, "tty", True))
    if not tty_enabled:
        return

    controller = TranscriptToggleController(enabled=True)
    renderer.transcript_controller = controller


def _prepare_run_kwargs(
    agent: Any,
    final_input_text: str,
    files: list[str] | None,
    parsed_chat_history: list[dict[str, Any]] | None,
    renderer: Any,
    tty_enabled: bool,
) -> dict[str, Any]:
    """Prepare kwargs for agent run."""
    run_kwargs = {
        "agent_id": agent.id,
        "message": final_input_text,
        "files": list(files),
        "agent_name": agent.name,
        "tty": tty_enabled,
    }

    if parsed_chat_history:
        run_kwargs["chat_history"] = parsed_chat_history

    if renderer is not None:
        run_kwargs["renderer"] = renderer

    return run_kwargs


def _handle_run_output(ctx: Any, result: Any, renderer: Any) -> None:
    """Handle output formatting for agent run results."""
    printed_by_renderer = bool(renderer)
    selected_view = get_ctx_value(ctx, "view", "rich")

    if not printed_by_renderer:
        if selected_view == "json":
            handle_json_output(ctx, {"output": result})
        elif selected_view == "md":
            click.echo(f"# Assistant\n\n{result}")
        elif selected_view == "plain":
            click.echo(result)


def _save_run_transcript(save: str | None, result: Any, working_console: Any) -> None:
    """Save transcript to file if requested."""
    if not save:
        return

    ext = (save.rsplit(".", 1)[-1] or "").lower()
    if ext == "json":
        save_data = {
            "output": result or "",
            "full_debug_output": getattr(working_console, "get_captured_output", lambda: "")(),
            "timestamp": "captured during agent execution",
        }
        content = json.dumps(save_data, indent=2)
    else:
        full_output = getattr(working_console, "get_captured_output", lambda: "")()
        if full_output:
            content = f"# Agent Debug Log\n\n{full_output}\n\n---\n\n## Final Result\n\n{result or ''}\n"
        else:
            content = f"# Assistant\n\n{result or ''}\n"

    with open(save, "w", encoding="utf-8") as f:
        f.write(content)
    print_markup(f"[{SUCCESS_STYLE}]Full debug output saved to: {save}[/]", console=console)


@agents_group.command()
@click.argument("agent_ref")
@click.argument("input_text", required=False)
@click.option("--select", type=int, help="Choose among ambiguous matches (1-based)")
@click.option("--input", "input_option", help="Input text for the agent")
@click.option("--chat-history", help="JSON string of chat history")
@click.option(
    "--timeout",
    default=DEFAULT_AGENT_RUN_TIMEOUT,
    type=int,
    help="Agent execution timeout in seconds (default: 300s)",
)
@click.option(
    "--save",
    type=click.Path(dir_okay=False, writable=True),
    help="Save transcript to file (md or json)",
)
@click.option(
    "--file",
    "files",
    multiple=True,
    type=click.Path(exists=True),
    help="Attach file(s)",
)
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Show detailed SSE events during streaming",
)
@output_flags()
@click.pass_context
def run(
    ctx: Any,
    agent_ref: str,
    select: int | None,
    input_text: str | None,
    input_option: str | None,
    chat_history: str | None,
    timeout: float | None,
    save: str | None,
    files: tuple[str, ...] | None,
    verbose: bool,
) -> None:
    r"""Run an agent with input text.

    Usage: aip agents run <agent_ref> <input_text> [OPTIONS]

    \b
    Examples:
        aip agents run my-agent "Hello world"
        aip agents run agent-123 "Process this data" --timeout 600
        aip agents run my-agent --input "Hello world"  # Legacy style
    """
    final_input_text = _validate_run_input(input_option, input_text)

    if verbose:
        _emit_verbose_guidance(ctx)
        return

    try:
        client = get_client(ctx)
        agent = _resolve_agent(ctx, client, agent_ref, select, interface_preference="fuzzy")

        parsed_chat_history = _parse_chat_history(chat_history)
        renderer, working_console = _setup_run_renderer(ctx, save, verbose)
        _maybe_attach_transcript_toggle(ctx, renderer)

        try:
            client.timeout = float(timeout)
        except Exception:
            pass

        run_kwargs = _prepare_run_kwargs(
            agent,
            final_input_text,
            files,
            parsed_chat_history,
            renderer,
            bool(get_ctx_value(ctx, "tty", True)),
        )

        result = client.agents.run_agent(**run_kwargs, timeout=timeout)

        slash_mode = _running_in_slash_mode(ctx)
        agent_id = str(_safe_agent_attribute(agent, "id") or "") or None
        agent_name = _safe_agent_attribute(agent, "name")
        model_hint = _get_agent_model_name(agent)

        transcript_context = store_transcript_for_session(
            ctx,
            renderer,
            final_result=result,
            agent_id=agent_id,
            agent_name=agent_name,
            model=model_hint,
            source="slash" if slash_mode else "cli",
        )

        _handle_run_output(ctx, result, renderer)
        _save_run_transcript(save, result, working_console)
        maybe_launch_post_run_viewer(
            ctx,
            transcript_context,
            console=console,
            slash_mode=slash_mode,
        )

    except AgentTimeoutError as e:
        error_msg = str(e)
        handle_json_output(ctx, error=Exception(error_msg))
        raise click.ClickException(error_msg) from e
    except Exception as e:
        _handle_command_exception(ctx, e)


def _running_in_slash_mode(ctx: Any) -> bool:
    """Return True if the command is executing inside the slash session."""
    ctx_obj = getattr(ctx, "obj", None)
    return isinstance(ctx_obj, dict) and bool(ctx_obj.get("_slash_session"))


def _emit_verbose_guidance(ctx: Any) -> None:
    """Explain the modern alternative to the deprecated --verbose flag."""
    if _running_in_slash_mode(ctx):
        message = (
            "[dim]Tip:[/] Verbose streaming has been retired in the command palette. Run the agent normally and open "
            "the post-run viewer (Ctrl+T) to inspect the transcript."
        )
    else:
        message = (
            "[dim]Tip:[/] `--verbose` is no longer supported. Re-run without the flag and toggle the post-run viewer "
            "(Ctrl+T) for detailed output."
        )
    handle_rich_output(ctx, markup_text(message))


def _handle_import_file_logic(
    import_file: str,
    model: str | None,
    name: str,
    instruction: str,
    tools: tuple[str, ...],
    agents: tuple[str, ...],
    mcps: tuple[str, ...],
    timeout: float | None,
) -> dict[str, Any]:
    """Handle import file logic and merge with CLI args."""
    import_data = load_resource_from_file(Path(import_file), "agent")
    import_data = convert_export_to_import_format(import_data)
    import_data = normalize_agent_config_for_import(import_data, model)

    cli_args = {
        "name": name,
        "instruction": instruction,
        "model": model,
        "tools": tools or (),
        "agents": agents or (),
        "mcps": mcps or (),
        "timeout": timeout if timeout != DEFAULT_AGENT_RUN_TIMEOUT else None,
    }

    return merge_import_with_cli_args(import_data, cli_args)


def _build_cli_args_data(
    name: str,
    instruction: str,
    model: str | None,
    tools: tuple[str, ...],
    agents: tuple[str, ...],
    mcps: tuple[str, ...],
    timeout: float | None,
) -> dict[str, Any]:
    """Build merged data from CLI arguments."""
    return {
        "name": name,
        "instruction": instruction,
        "model": model,
        "tools": tools or (),
        "agents": agents or (),
        "mcps": mcps or (),
        "timeout": timeout if timeout != DEFAULT_AGENT_RUN_TIMEOUT else None,
    }


def _extract_and_validate_fields(
    merged_data: dict[str, Any],
) -> tuple[str, str, str | None, tuple, tuple, tuple, Any]:
    """Extract and validate required fields from merged data."""
    name = merged_data.get("name")
    instruction = merged_data.get("instruction")
    model = merged_data.get("model")
    tools = tuple(merged_data.get("tools", ()))
    agents = tuple(merged_data.get("agents", ()))
    mcps = tuple(merged_data.get("mcps", ()))
    timeout = merged_data.get("timeout", DEFAULT_AGENT_RUN_TIMEOUT)

    # Validate required fields
    if not name:
        raise click.ClickException("Agent name is required (--name or --import)")
    if not instruction:
        raise click.ClickException("Agent instruction is required (--instruction or --import)")

    return name, instruction, model, tools, agents, mcps, timeout


def _validate_and_coerce_fields(name: str, instruction: str, timeout: Any) -> tuple[str, str, Any]:
    """Validate and coerce field values."""
    name = validate_agent_name(name)
    instruction = validate_agent_instruction(instruction)
    timeout = coerce_timeout(timeout)
    if timeout is not None:
        timeout = validate_timeout(timeout)

    return name, instruction, timeout


def _resolve_resources(client: Any, tools: tuple, agents: tuple, mcps: tuple) -> tuple[list, list, list]:
    """Resolve tool, agent, and MCP references."""
    resolved_tools = _resolve_resources_by_name(client, tools, "tool", client.find_tools, "Tool")
    resolved_agents = _resolve_resources_by_name(client, agents, "agent", client.find_agents, "Agent")
    resolved_mcps = _resolve_resources_by_name(client, mcps, "mcp", client.find_mcps, "MCP")

    return resolved_tools, resolved_agents, resolved_mcps


def _build_create_kwargs(
    name: str,
    instruction: str,
    resolved_tools: list,
    resolved_agents: list,
    resolved_mcps: list,
    timeout: Any,
    merged_data: dict[str, Any],
    model: str | None,
    import_file: str | None,
) -> dict[str, Any]:
    """Build create_agent kwargs with all necessary parameters."""
    create_kwargs = {
        "name": name,
        "instruction": instruction,
        "tools": resolved_tools or None,
        "agents": resolved_agents or None,
        "mcps": resolved_mcps or None,
        "timeout": timeout,
    }

    # Handle language model selection
    lm_selection_dict, should_strip_lm_identity = resolve_language_model_selection(merged_data, model)
    create_kwargs.update(lm_selection_dict)

    # Handle import file specific logic
    if import_file:
        _add_import_file_attributes(create_kwargs, merged_data, should_strip_lm_identity)

    return create_kwargs


def _add_import_file_attributes(
    create_kwargs: dict[str, Any],
    merged_data: dict[str, Any],
    should_strip_lm_identity: bool,
) -> None:
    """Add import file specific attributes to create_kwargs."""
    agent_config_raw = merged_data.get("agent_config")
    if isinstance(agent_config_raw, dict):
        create_kwargs["agent_config"] = sanitize_agent_config(
            agent_config_raw, strip_lm_identity=should_strip_lm_identity
        )

    # Add other attributes from import data
    excluded_fields = {
        "name",
        "instruction",
        "model",
        "language_model_id",
        "tools",
        "agents",
        "timeout",
        "agent_config",
        "id",
        "created_at",
        "updated_at",
        "type",
        "framework",
        "version",
        "mcps",
        "a2a_profile",
    }
    for key, value in merged_data.items():
        if key not in excluded_fields and value is not None:
            create_kwargs[key] = value


def _get_language_model_display_name(agent: Any, model: str | None) -> str:
    """Get display name for the language model."""
    lm_display = getattr(agent, "model", None)
    if not lm_display:
        cfg = getattr(agent, "agent_config", {}) or {}
        lm_display = cfg.get("lm_name") or cfg.get("model") or model or f"{DEFAULT_MODEL} (backend default)"
    return lm_display


def _handle_successful_creation(ctx: Any, agent: Any, model: str | None) -> None:
    """Handle successful agent creation output."""
    handle_json_output(ctx, _prepare_agent_output(agent))

    lm_display = _get_language_model_display_name(agent, model)

    handle_rich_output(
        ctx,
        display_creation_success(
            "Agent",
            agent.name,
            agent.id,
            Model=lm_display,
            Type=getattr(agent, "type", "config"),
            Framework=getattr(agent, "framework", "langchain"),
            Version=getattr(agent, "version", "1.0"),
        ),
    )
    handle_rich_output(ctx, display_agent_run_suggestions(agent))


def _handle_command_exception(ctx: Any, e: Exception) -> None:
    """Handle exceptions during command execution with consistent error handling."""
    if isinstance(e, click.ClickException):
        if get_ctx_value(ctx, "view") == "json":
            handle_json_output(ctx, error=Exception(AGENT_NOT_FOUND_ERROR))
        raise

    handle_json_output(ctx, error=e)
    if get_ctx_value(ctx, "view") != "json":
        print_api_error(e)
    raise click.exceptions.Exit(1) from e


def _handle_creation_exception(ctx: Any, e: Exception) -> None:
    """Handle exceptions during agent creation."""
    _handle_command_exception(ctx, e)


@agents_group.command()
@click.option("--name", help="Agent name")
@click.option("--instruction", help="Agent instruction (prompt)")
@click.option(
    "--model",
    help=f"Language model to use (e.g., {DEFAULT_MODEL}, default: {DEFAULT_MODEL})",
)
@click.option("--tools", multiple=True, help="Tool names or IDs to attach")
@click.option("--agents", multiple=True, help="Sub-agent names or IDs to attach")
@click.option("--mcps", multiple=True, help="MCP names or IDs to attach")
@click.option(
    "--timeout",
    default=DEFAULT_AGENT_RUN_TIMEOUT,
    type=int,
    help="Agent execution timeout in seconds (default: 300s)",
)
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Import agent configuration from JSON file",
)
@output_flags()
@click.pass_context
def create(
    ctx: Any,
    name: str,
    instruction: str,
    model: str | None,
    tools: tuple[str, ...] | None,
    agents: tuple[str, ...] | None,
    mcps: tuple[str, ...] | None,
    timeout: float | None,
    import_file: str | None,
) -> None:
    r"""Create a new agent.

    \b
    Examples:
        aip agents create --name "My Agent" --instruction "You are a helpful assistant"
        aip agents create --import agent.json
    """
    try:
        client = get_client(ctx)

        # Handle import file or CLI args
        if import_file:
            merged_data = _handle_import_file_logic(import_file, model, name, instruction, tools, agents, mcps, timeout)
        else:
            merged_data = _build_cli_args_data(name, instruction, model, tools, agents, mcps, timeout)

        # Extract and validate fields
        (
            name,
            instruction,
            model,
            tools,
            agents,
            mcps,
            timeout,
        ) = _extract_and_validate_fields(merged_data)
        name, instruction, timeout = _validate_and_coerce_fields(name, instruction, timeout)

        # Resolve resources
        resolved_tools, resolved_agents, resolved_mcps = _resolve_resources(client, tools, agents, mcps)

        # Build create kwargs
        create_kwargs = _build_create_kwargs(
            name,
            instruction,
            resolved_tools,
            resolved_agents,
            resolved_mcps,
            timeout,
            merged_data,
            model,
            import_file,
        )

        # Create agent
        agent = client.agents.create_agent(**create_kwargs)

        # Handle successful creation
        _handle_successful_creation(ctx, agent, model)

    except Exception as e:
        _handle_creation_exception(ctx, e)


def _get_agent_for_update(client: Any, agent_id: str) -> Any:
    """Retrieve agent by ID for update operation."""
    try:
        return client.agents.get_agent_by_id(agent_id)
    except Exception as e:
        raise click.ClickException(f"Agent with ID '{agent_id}' not found: {e}") from e


def _handle_update_import_file(
    import_file: str | None,
    name: str | None,
    instruction: str | None,
    tools: tuple[str, ...] | None,
    agents: tuple[str, ...] | None,
    mcps: tuple[str, ...] | None,
    timeout: float | None,
) -> tuple[
    Any | None,
    str | None,
    str | None,
    tuple[str, ...] | None,
    tuple[str, ...] | None,
    tuple[str, ...] | None,
    float | None,
]:
    """Handle import file processing for agent update."""
    if not import_file:
        return None, name, instruction, tools, agents, mcps, timeout

    import_data = load_resource_from_file(Path(import_file), "agent")
    import_data = convert_export_to_import_format(import_data)
    import_data = normalize_agent_config_for_import(import_data, None)

    cli_args = {
        "name": name,
        "instruction": instruction,
        "tools": tools or (),
        "agents": agents or (),
        "mcps": mcps or (),
        "timeout": timeout,
    }

    merged_data = merge_import_with_cli_args(import_data, cli_args)

    return (
        merged_data,
        merged_data.get("name"),
        merged_data.get("instruction"),
        tuple(merged_data.get("tools", ())),
        tuple(merged_data.get("agents", ())),
        tuple(merged_data.get("mcps", ())),
        coerce_timeout(merged_data.get("timeout")),
    )


def _build_update_data(
    name: str | None,
    instruction: str | None,
    tools: tuple[str, ...] | None,
    agents: tuple[str, ...] | None,
    mcps: tuple[str, ...] | None,
    timeout: float | None,
) -> dict[str, Any]:
    """Build the update data dictionary from provided parameters."""
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if instruction is not None:
        update_data["instruction"] = instruction
    if tools:
        update_data["tools"] = list(tools)
    if agents:
        update_data["agents"] = list(agents)
    if mcps:
        update_data["mcps"] = list(mcps)
    if timeout is not None:
        update_data["timeout"] = timeout
    return update_data


def _handle_update_import_config(
    import_file: str | None, merged_data: dict[str, Any], update_data: dict[str, Any]
) -> None:
    """Handle agent config and additional attributes for import-based updates."""
    if not import_file:
        return

    lm_selection, should_strip_lm_identity = resolve_language_model_selection(merged_data, None)
    update_data.update(lm_selection)

    raw_cfg = merged_data.get("agent_config") if isinstance(merged_data, dict) else None
    if isinstance(raw_cfg, dict):
        update_data["agent_config"] = sanitize_agent_config(raw_cfg, strip_lm_identity=should_strip_lm_identity)

    excluded_fields = {
        "name",
        "instruction",
        "tools",
        "agents",
        "timeout",
        "agent_config",
        "language_model_id",
        "id",
        "created_at",
        "updated_at",
        "type",
        "framework",
        "version",
        "a2a_profile",
    }
    for key, value in merged_data.items():
        if key not in excluded_fields and value is not None:
            update_data[key] = value


@agents_group.command()
@click.argument("agent_id")
@click.option("--name", help="New agent name")
@click.option("--instruction", help="New instruction")
@click.option("--tools", multiple=True, help="New tool names or IDs")
@click.option("--agents", multiple=True, help="New sub-agent names")
@click.option("--mcps", multiple=True, help="New MCP names or IDs")
@click.option("--timeout", type=int, help="New timeout value")
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Import agent configuration from JSON file",
)
@output_flags()
@click.pass_context
def update(
    ctx: Any,
    agent_id: str,
    name: str | None,
    instruction: str | None,
    tools: tuple[str, ...] | None,
    agents: tuple[str, ...] | None,
    mcps: tuple[str, ...] | None,
    timeout: float | None,
    import_file: str | None,
) -> None:
    r"""Update an existing agent.

    \b
    Examples:
        aip agents update my-agent --instruction "New instruction"
        aip agents update my-agent --import agent.json
    """
    try:
        client = get_client(ctx)
        agent = _get_agent_for_update(client, agent_id)

        # Handle import file processing
        (
            merged_data,
            name,
            instruction,
            tools,
            agents,
            mcps,
            timeout,
        ) = _handle_update_import_file(import_file, name, instruction, tools, agents, mcps, timeout)

        update_data = _build_update_data(name, instruction, tools, agents, mcps, timeout)

        if merged_data:
            _handle_update_import_config(import_file, merged_data, update_data)
            # Ensure instruction from import file is included if not already set via CLI
            # This handles the case where instruction is None in CLI args but exists in import file
            if import_file and (instruction is None or "instruction" not in update_data):
                import_instruction = merged_data.get("instruction")
                if import_instruction is not None:
                    update_data["instruction"] = import_instruction

        if not update_data:
            raise click.ClickException("No update fields specified")

        updated_agent = client.agents.update_agent(agent.id, **update_data)

        handle_json_output(ctx, _prepare_agent_output(updated_agent))
        handle_rich_output(ctx, display_update_success("Agent", updated_agent.name))
        handle_rich_output(ctx, display_agent_run_suggestions(updated_agent))

    except click.ClickException:
        # Handle JSON output for ClickExceptions if view is JSON
        if get_ctx_value(ctx, "view") == "json":
            handle_json_output(ctx, error=Exception(AGENT_NOT_FOUND_ERROR))
        # Re-raise ClickExceptions without additional processing
        raise
    except Exception as e:
        _handle_command_exception(ctx, e)


@agents_group.command()
@click.argument("agent_id")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@output_flags()
@click.pass_context
def delete(ctx: Any, agent_id: str, yes: bool) -> None:
    """Delete an agent."""
    try:
        client = get_client(ctx)

        # Get agent by ID (no ambiguity handling needed)
        try:
            agent = client.agents.get_agent_by_id(agent_id)
        except Exception as e:
            raise click.ClickException(f"Agent with ID '{agent_id}' not found: {e}") from e

        # Confirm deletion when not forced
        if not yes and not display_confirmation_prompt("Agent", agent.name):
            return

        client.agents.delete_agent(agent.id)

        handle_json_output(
            ctx,
            {
                "success": True,
                "message": f"Agent '{agent.name}' deleted",
            },
        )
        handle_rich_output(ctx, display_deletion_success("Agent", agent.name))

    except click.ClickException:
        # Handle JSON output for ClickExceptions if view is JSON
        if get_ctx_value(ctx, "view") == "json":
            handle_json_output(ctx, error=Exception(AGENT_NOT_FOUND_ERROR))
        # Re-raise ClickExceptions without additional processing
        raise
    except Exception as e:
        _handle_command_exception(ctx, e)


@agents_group.command()
@click.option(
    "--base-url",
    help="Custom LangFlow server base URL (overrides LANGFLOW_BASE_URL env var)",
)
@click.option("--api-key", help="Custom LangFlow API key (overrides LANGFLOW_API_KEY env var)")
@output_flags()
@click.pass_context
def sync_langflow(ctx: Any, base_url: str | None, api_key: str | None) -> None:
    r"""Sync agents with LangFlow server flows.

    This command fetches all flows from the configured LangFlow server and
    creates/updates corresponding agents in the platform.

    The LangFlow server configuration can be provided via:
    - Command options (--base-url, --api-key)
    - Environment variables (LANGFLOW_BASE_URL, LANGFLOW_API_KEY)

    \b
    Examples:
        aip agents sync-langflow
        aip agents sync-langflow --base-url https://my-langflow.com --api-key my-key
    """
    try:
        client = get_client(ctx)

        # Perform the sync
        result = client.sync_langflow_agents(base_url=base_url, api_key=api_key)

        # Handle output format
        handle_json_output(ctx, result)

        # Show success message for non-JSON output
        if get_ctx_value(ctx, "view") != "json":
            # Extract some useful info from the result
            success_count = result.get("data", {}).get("created_count", 0) + result.get("data", {}).get(
                "updated_count", 0
            )
            total_count = result.get("data", {}).get("total_processed", 0)

            handle_rich_output(
                ctx,
                markup_text(
                    f"[{SUCCESS_STYLE}]✅ Successfully synced {success_count} LangFlow agents "
                    f"({total_count} total processed)[/]"
                ),
            )

    except Exception as e:
        _handle_command_exception(ctx, e)
