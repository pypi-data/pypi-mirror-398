"""Layout utilities exposed for renderer/viewer consumers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from glaip_sdk.utils.rendering.layout.panels import (
    create_context_panel,
    create_final_panel,
    create_main_panel,
    create_tool_panel,
)
from glaip_sdk.utils.rendering.layout.progress import (
    TrailingSpinnerLine,
    build_progress_footer,
    format_elapsed_time,
    format_tool_title,
    format_working_indicator,
    get_spinner,
    get_spinner_char,
    is_delegation_tool,
)
from glaip_sdk.utils.rendering.layout.transcript import (
    DEFAULT_TRANSCRIPT_THEME,
    TranscriptGlyphs,
    TranscriptRow,
    TranscriptSnapshot,
    build_final_panel,
    build_transcript_snapshot,
    build_transcript_view,
    extract_query_from_meta,
    format_final_panel_title,
    render_final_panel,
)
from glaip_sdk.utils.rendering.layout.summary import render_summary_panels

__all__ = [
    # Panels
    "create_context_panel",
    "create_final_panel",
    "create_main_panel",
    "create_tool_panel",
    "render_summary_panels",
    # Progress
    "TrailingSpinnerLine",
    "build_progress_footer",
    "format_elapsed_time",
    "format_tool_title",
    "format_working_indicator",
    "get_spinner",
    "get_spinner_char",
    "is_delegation_tool",
    # Transcript
    "DEFAULT_TRANSCRIPT_THEME",
    "TranscriptGlyphs",
    "TranscriptRow",
    "TranscriptSnapshot",
    "build_final_panel",
    "build_transcript_snapshot",
    "build_transcript_view",
    "extract_query_from_meta",
    "format_final_panel_title",
    "render_final_panel",
]
