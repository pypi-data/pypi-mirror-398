"""Panel rendering utilities for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations


from rich.align import Align
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

from glaip_sdk.branding import INFO, PRIMARY, SUCCESS, WARNING
from glaip_sdk.rich_components import AIPPanel


def _spinner_renderable(message: str = "Processing...") -> Align:
    """Build a Rich spinner renderable for loading placeholders."""
    spinner = Spinner(
        "dots",
        text=Text(f" {message}", style="dim"),
        style=INFO,
    )
    return Align.left(spinner)


def create_main_panel(content: str, title: str, theme: str = "dark") -> AIPPanel:
    """Create a main content panel.

    Args:
        content: The content to display
        title: Panel title
        theme: Color theme ("dark" or "light")

    Returns:
        Rich Panel instance
    """
    if content.strip():
        return AIPPanel(
            Markdown(content, code_theme=("monokai" if theme == "dark" else "github")),
            title=title,
            border_style=SUCCESS,
        )
    else:
        return AIPPanel(
            _spinner_renderable(),
            title=title,
            border_style=SUCCESS,
        )


def create_tool_panel(
    title: str,
    content: str,
    status: str = "running",
    theme: str = "dark",
    is_delegation: bool = False,
    *,
    spinner_message: str | None = None,
) -> AIPPanel:
    """Create a tool execution panel.

    Args:
        title: Tool name/title
        content: Tool output content
        status: Tool execution status
        theme: Color theme
        is_delegation: Whether this is a delegation tool
        spinner_message: Optional custom message to show alongside the spinner

    Returns:
        Rich Panel instance
    """
    mark = "✓" if status == "finished" else ""
    border_style = WARNING if is_delegation else PRIMARY

    if content:
        body_renderable = Markdown(
            content,
            code_theme=("monokai" if theme == "dark" else "github"),
        )
    elif status == "running":
        body_renderable = _spinner_renderable(spinner_message or f"{title} running...")
    else:
        body_renderable = Text("No output yet.", style="dim")

    title_text = f"{title}  {mark}".rstrip()

    return AIPPanel(
        body_renderable,
        title=title_text,
        border_style=border_style,
    )


def create_context_panel(
    title: str,
    content: str,
    status: str = "running",
    theme: str = "dark",
    is_delegation: bool = False,
) -> AIPPanel:
    """Create a context/sub-agent panel.

    Args:
        title: Context title
        content: Context content
        status: Execution status
        theme: Color theme
        is_delegation: Whether this is a delegation context

    Returns:
        Rich Panel instance
    """
    mark = "✓" if status == "finished" else ""
    border_style = WARNING if is_delegation else INFO

    title_text = f"{title}  {mark}".rstrip()

    return AIPPanel(
        Markdown(
            content,
            code_theme=("monokai" if theme == "dark" else "github"),
        ),
        title=title_text,
        border_style=border_style,
    )


def create_final_panel(content: str, title: str = "Final Result", theme: str = "dark") -> AIPPanel:
    """Create a final result panel.

    Args:
        content: Final result content
        title: Panel title
        theme: Color theme

    Returns:
        Rich Panel instance
    """
    return AIPPanel(
        Markdown(content, code_theme=("monokai" if theme == "dark" else "github")),
        title=title,
        border_style=SUCCESS,
        padding=(0, 1),
    )


__all__ = [
    "create_main_panel",
    "create_tool_panel",
    "create_context_panel",
    "create_final_panel",
]
