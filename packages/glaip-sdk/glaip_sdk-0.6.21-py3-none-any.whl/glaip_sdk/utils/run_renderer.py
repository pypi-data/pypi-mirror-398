#!/usr/bin/env python3
"""Modern run renderer for agent execution with clean streaming output.

This module provides a modern CLI experience similar to Claude Code and Gemini CLI,
with compact headers, streaming markdown, collapsible tool steps, and clean output.

This is a compatibility shim that re-exports components from the new modular renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

# Configure logger
import logging

from glaip_sdk.utils.rendering.models import RunStats

# Re-export main components from the new modular renderer package
from glaip_sdk.utils.rendering.renderer.base import RichStreamRenderer
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.renderer.console import CapturingConsole

# Legacy imports for backward compatibility
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event
from glaip_sdk.utils.rendering.steps import StepManager

logger = logging.getLogger("glaip_sdk.run_renderer")


# The full implementation has been moved to glaip_sdk.utils.rendering.renderer.base
# This file now serves as a compatibility shim for existing imports.
__all__ = [
    "CapturingConsole",
    "RendererConfig",
    "RichStreamRenderer",
    "RunStats",
    "StepManager",
    "render_debug_event",
]
