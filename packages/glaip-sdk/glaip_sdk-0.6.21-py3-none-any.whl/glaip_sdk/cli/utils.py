"""CLI utilities for glaip-sdk (facade for backward compatibility).

This module is a backward-compatible facade that re-exports functions from
glaip_sdk.cli.core.* modules. New code should import directly from the core modules.
The facade is deprecated and will be removed after consumers migrate to core modules;
see docs/specs/refactor/cli-core-modularization.md for the migration plan.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""  # pylint: disable=duplicate-code

from __future__ import annotations

import threading
import warnings

# Re-export from core modules
from glaip_sdk.cli.core.context import (
    bind_slash_session_context,
    get_client,
    handle_best_effort_check,
    restore_slash_session_context,
)
from glaip_sdk.cli.core.output import (
    coerce_to_row,
    detect_export_format,
    fetch_resource_for_export,
    format_datetime_fields,
    format_size,
    handle_ambiguous_resource,
    handle_resource_export,
    output_list,
    output_result,
    parse_json_line,
    resolve_resource,
    sdk_version,
    # Private functions for backward compatibility (used in tests)
    _build_table_group,
    _build_yaml_renderable,
    _coerce_result_payload,
    _create_table,
    _ensure_displayable,
    _format_yaml_text,
    _get_interface_order,
    _handle_empty_items,
    _handle_fallback_numeric_ambiguity,
    _handle_fuzzy_pick_selection,
    _handle_json_output,
    _handle_json_view_ambiguity,
    _handle_markdown_output,
    _handle_plain_output,
    _handle_questionary_ambiguity,
    _handle_table_output,
    _literal_str_representer,
    _normalise_rows,
    _normalize_interface_preference,
    _print_selection_tip,
    _render_markdown_list,
    _render_markdown_output,
    _render_plain_list,
    _resolve_by_id,
    _resolve_by_name_multiple_fuzzy,
    _resolve_by_name_multiple_questionary,
    _resolve_by_name_multiple_with_select,
    _resource_tip_command,
    _should_fallback_to_numeric_prompt,
    _should_sort_rows,
    _should_use_fuzzy_picker,
    _try_fuzzy_pick,
    _try_fuzzy_selection,
    _try_interface_selection,
    _try_questionary_selection,
    _LiteralYamlDumper,
)
from glaip_sdk.cli.core.prompting import (
    _FuzzyCompleter,  # Private class for backward compatibility (used in tests)
    _fuzzy_pick_for_resources,
    prompt_export_choice_questionary,
    questionary_safe_ask,
    # Private functions for backward compatibility (used in tests)
    _asyncio_loop_running,
    _basic_prompt,
    _build_resource_labels,
    _build_display_parts,
    _build_primary_parts,
    _build_unique_labels,
    _calculate_consecutive_bonus,
    _calculate_exact_match_bonus,
    _calculate_length_bonus,
    _check_fuzzy_pick_requirements,
    _extract_display_fields,
    _extract_fallback_values,
    _extract_id_suffix,
    _get_fallback_columns,
    _fuzzy_pick,
    _fuzzy_score,
    _is_fuzzy_match,
    _is_standard_field,
    _load_questionary_module,
    _make_questionary_choice,
    _perform_fuzzy_search,
    _prompt_with_auto_select,
    _rank_labels,
    _row_display,
    _run_questionary_in_thread,
    _strip_spaces_for_matching,
)
from glaip_sdk.cli.core.rendering import (
    build_renderer,
    spinner_context,
    stop_spinner,
    update_spinner,
    with_client_and_spinner,
    # Private functions for backward compatibility (used in tests)
    _can_use_spinner,
    _register_renderer_with_session,
    _spinner_stop,
    _spinner_update,
    _stream_supports_tty,
)

# Re-export from other modules for backward compatibility
from glaip_sdk.cli.context import get_ctx_value
from glaip_sdk.cli.hints import command_hint
from glaip_sdk.utils import is_uuid

# Re-export module-level variables for backward compatibility
# Note: console is re-exported from output.py since that's where _handle_table_output uses it
from glaip_sdk.cli.core.output import console
import logging

logger = logging.getLogger("glaip_sdk.cli.utils")
questionary = None  # type: ignore[assignment]

_warn_lock = threading.Lock()
_warned = False


def _warn_once() -> None:
    """Emit the deprecation warning once in a thread-safe way."""
    global _warned
    if _warned:
        return
    with _warn_lock:
        if _warned:
            return
        warnings.warn(
            "Importing from glaip_sdk.cli.utils is deprecated. Use glaip_sdk.cli.core.* modules instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        _warned = True


_warn_once()

# Re-export everything for backward compatibility
__all__ = [
    # Context
    "bind_slash_session_context",
    "get_client",
    "get_ctx_value",  # Re-exported from context module
    "handle_best_effort_check",
    "restore_slash_session_context",
    # Prompting
    "_FuzzyCompleter",  # Private class for backward compatibility (used in tests)
    "_asyncio_loop_running",  # Private function for backward compatibility (used in tests)
    "_basic_prompt",  # Private function for backward compatibility (used in tests)
    "_build_display_parts",  # Private function for backward compatibility (used in tests)
    "_build_primary_parts",  # Private function for backward compatibility (used in tests)
    "_build_resource_labels",  # Private function for backward compatibility (used in tests)
    "_build_unique_labels",  # Private function for backward compatibility (used in tests)
    "_calculate_consecutive_bonus",  # Private function for backward compatibility (used in tests)
    "_calculate_exact_match_bonus",  # Private function for backward compatibility (used in tests)
    "_calculate_length_bonus",  # Private function for backward compatibility (used in tests)
    "_check_fuzzy_pick_requirements",  # Private function for backward compatibility (used in tests)
    "_extract_display_fields",  # Private function for backward compatibility (used in tests)
    "_extract_fallback_values",  # Private function for backward compatibility (used in tests)
    "_extract_id_suffix",  # Private function for backward compatibility (used in tests)
    "_fuzzy_pick",  # Private function for backward compatibility (used in tests)
    "_fuzzy_pick_for_resources",
    "_fuzzy_score",  # Private function for backward compatibility (used in tests)
    "_get_fallback_columns",  # Private function for backward compatibility (used in tests)
    "_is_fuzzy_match",  # Private function for backward compatibility (used in tests)
    "_is_standard_field",  # Private function for backward compatibility (used in tests)
    "_load_questionary_module",  # Private function for backward compatibility (used in tests)
    "_make_questionary_choice",  # Private function for backward compatibility (used in tests)
    "_perform_fuzzy_search",  # Private function for backward compatibility (used in tests)
    "_prompt_with_auto_select",  # Private function for backward compatibility (used in tests)
    "_rank_labels",  # Private function for backward compatibility (used in tests)
    "_row_display",  # Private function for backward compatibility (used in tests)
    "_run_questionary_in_thread",  # Private function for backward compatibility (used in tests)
    "_strip_spaces_for_matching",  # Private function for backward compatibility (used in tests)
    "prompt_export_choice_questionary",
    "questionary_safe_ask",
    # Rendering
    "_can_use_spinner",  # Private function for backward compatibility (used in tests)
    "_register_renderer_with_session",  # Private function for backward compatibility (used in tests)
    "_spinner_stop",  # Private function for backward compatibility (used in tests)
    "_spinner_update",  # Private function for backward compatibility (used in tests)
    "_stream_supports_tty",  # Private function for backward compatibility (used in tests)
    "build_renderer",
    "console",  # Module-level variable for backward compatibility
    "logger",  # Module-level variable for backward compatibility
    "questionary",  # Module-level variable for backward compatibility
    "spinner_context",
    "stop_spinner",
    "update_spinner",
    "with_client_and_spinner",
    # Output
    "_LiteralYamlDumper",  # Private class for backward compatibility (used in tests)
    "_build_table_group",  # Private function for backward compatibility (used in tests)
    "_build_yaml_renderable",  # Private function for backward compatibility (used in tests)
    "_coerce_result_payload",  # Private function for backward compatibility (used in tests)
    "_create_table",  # Private function for backward compatibility (used in tests)
    "_ensure_displayable",  # Private function for backward compatibility (used in tests)
    "_format_yaml_text",  # Private function for backward compatibility (used in tests)
    "_get_interface_order",  # Private function for backward compatibility (used in tests)
    "_handle_empty_items",  # Private function for backward compatibility (used in tests)
    "_handle_fallback_numeric_ambiguity",  # Private function for backward compatibility (used in tests)
    "_handle_fuzzy_pick_selection",  # Private function for backward compatibility (used in tests)
    "_handle_json_output",  # Private function for backward compatibility (used in tests)
    "_handle_json_view_ambiguity",  # Private function for backward compatibility (used in tests)
    "_handle_markdown_output",  # Private function for backward compatibility (used in tests)
    "_handle_plain_output",  # Private function for backward compatibility (used in tests)
    "_handle_questionary_ambiguity",  # Private function for backward compatibility (used in tests)
    "_handle_table_output",  # Private function for backward compatibility (used in tests)
    "_literal_str_representer",  # Private function for backward compatibility (used in tests)
    "_normalise_rows",  # Private function for backward compatibility (used in tests)
    "_normalize_interface_preference",  # Private function for backward compatibility (used in tests)
    "_print_selection_tip",  # Private function for backward compatibility (used in tests)
    "_render_markdown_list",  # Private function for backward compatibility (used in tests)
    "_render_markdown_output",  # Private function for backward compatibility (used in tests)
    "_render_plain_list",  # Private function for backward compatibility (used in tests)
    "_resolve_by_id",  # Private function for backward compatibility (used in tests)
    "_resolve_by_name_multiple_fuzzy",  # Private function for backward compatibility (used in tests)
    "_resolve_by_name_multiple_questionary",  # Private function for backward compatibility (used in tests)
    "_resolve_by_name_multiple_with_select",  # Private function for backward compatibility (used in tests)
    "_resource_tip_command",  # Private function for backward compatibility (used in tests)
    "_should_fallback_to_numeric_prompt",  # Private function for backward compatibility (used in tests)
    "_should_sort_rows",  # Private function for backward compatibility (used in tests)
    "_should_use_fuzzy_picker",  # Private function for backward compatibility (used in tests)
    "_try_fuzzy_pick",  # Private function for backward compatibility (used in tests)
    "_try_fuzzy_selection",  # Private function for backward compatibility (used in tests)
    "_try_interface_selection",  # Private function for backward compatibility (used in tests)
    "_try_questionary_selection",  # Private function for backward compatibility (used in tests)
    "coerce_to_row",
    "command_hint",  # Re-exported from hints module
    "detect_export_format",
    "fetch_resource_for_export",
    "format_datetime_fields",
    "format_size",
    "handle_ambiguous_resource",
    "handle_resource_export",
    "output_list",
    "output_result",
    "parse_json_line",
    "resolve_resource",
    "sdk_version",
    # Utils
    "is_uuid",  # Re-exported from glaip_sdk.utils for backward compatibility
]
