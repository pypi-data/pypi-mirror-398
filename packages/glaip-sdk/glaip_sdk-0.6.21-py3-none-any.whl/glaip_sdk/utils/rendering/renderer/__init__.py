"""Renderer package for modular streaming output.

This package provides modular components for rendering agent execution streams,
with clean separation of concerns between configuration, console handling,
debug output, panel rendering, progress tracking, and event routing.
"""

from rich.console import Console

from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.rendering.renderer.base import RichStreamRenderer
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.renderer.console import CapturingConsole
from glaip_sdk.utils.rendering.renderer.factory import (
    RendererFactoryOptions,
    make_default_renderer,
    make_minimal_renderer,
    make_silent_renderer,
    make_verbose_renderer,
)


def print_panel(
    content: str,
    *,
    title: str | None = None,
    border_style: str = "blue",
    padding: tuple[int, int] = (1, 2),
    console: Console | None = None,
) -> None:
    """Print boxed content using Rich without exposing Console/Panel at call site.

    Args:
        content: The text to display inside the panel.
        title: Optional title for the panel.
        border_style: Rich style string for the border color.
        padding: (vertical, horizontal) padding inside the panel.
        console: Optional Rich Console to print to; created if not provided.
    """
    c = console or Console()
    c.print(AIPPanel(content, title=title, border_style=border_style, padding=padding))


__all__ = [
    # Main classes
    "RichStreamRenderer",
    "RendererConfig",
    "CapturingConsole",
    "RendererFactoryOptions",
    "make_silent_renderer",
    "make_minimal_renderer",
    "make_default_renderer",
    "make_verbose_renderer",
    "print_panel",
]
