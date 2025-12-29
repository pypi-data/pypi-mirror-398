"""CLI core modules for glaip-sdk.

This package contains focused modules extracted from the monolithic cli/utils.py:
- context: Click context helpers, config loading, credential resolution
- prompting: prompt_toolkit + questionary wrappers, validators
- rendering: Rich console helpers, viewer launchers, renderer builders
- output: Table/console output utilities, list rendering

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""  # pylint: disable=duplicate-code

from __future__ import annotations

# Re-export all public APIs from submodules for convenience
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
    handle_resource_export,
    output_list,
    output_result,
    parse_json_line,
    resolve_resource,
    handle_ambiguous_resource,
    sdk_version,
)
from glaip_sdk.cli.core.prompting import (
    _fuzzy_pick_for_resources,
    prompt_export_choice_questionary,
    questionary_safe_ask,
)
from glaip_sdk.cli.core.rendering import (
    build_renderer,
    spinner_context,
    stop_spinner,
    update_spinner,
    with_client_and_spinner,
)

__all__ = [
    # Context
    "bind_slash_session_context",
    "get_client",
    "handle_best_effort_check",
    "restore_slash_session_context",
    # Prompting
    "_fuzzy_pick_for_resources",
    "prompt_export_choice_questionary",
    "questionary_safe_ask",
    # Rendering
    "build_renderer",
    "spinner_context",
    "stop_spinner",
    "update_spinner",
    "with_client_and_spinner",
    # Output
    "coerce_to_row",
    "detect_export_format",
    "fetch_resource_for_export",
    "format_datetime_fields",
    "format_size",
    "handle_resource_export",
    "output_list",
    "output_result",
    "parse_json_line",
    "resolve_resource",
    "handle_ambiguous_resource",
    "sdk_version",
]
