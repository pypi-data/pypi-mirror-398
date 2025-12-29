"""Custom Rich components with copy-friendly defaults.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class AIPPanel(Panel):
    """Rich Panel configured without vertical borders by default."""

    def __init__(self, *args, **kwargs):
        """Initialize AIPPanel with default settings for horizontal borders and padding.

        Args:
            *args: Positional arguments passed to Panel
            **kwargs: Keyword arguments passed to Panel
        """
        kwargs.setdefault("box", box.HORIZONTALS)
        kwargs.setdefault("padding", (0, 1))
        super().__init__(*args, **kwargs)


class AIPTable(Table):
    """Rich Table configured without vertical borders by default."""

    def __init__(self, *args, **kwargs):
        """Initialize AIPTable with default settings for horizontal borders and no edge padding.

        Args:
            *args: Positional arguments passed to Table
            **kwargs: Keyword arguments passed to Table
        """
        kwargs.setdefault("box", box.HORIZONTALS)
        kwargs.setdefault("show_edge", False)
        kwargs.setdefault("pad_edge", False)
        super().__init__(*args, **kwargs)


class AIPGrid(Table):
    """Table-based grid with GL AIP defaults for layout blocks."""

    def __init__(
        self,
        *,
        expand: bool = True,
        padding: tuple[int, int] = (0, 1),
        collapse_padding: bool = True,
    ):
        """Initialize AIPGrid with zero-edge borders and optional expansion.

        Args:
            expand: Whether the grid should expand to fill available width.
            padding: Cell padding for the grid (row, column).
            collapse_padding: Collapse padding between renderables.
        """
        super().__init__(
            show_header=False,
            show_edge=False,
            pad_edge=False,
            box=None,
            expand=expand,
            padding=padding,
            collapse_padding=collapse_padding,
        )


class RemoteRunsTable(AIPTable):
    """Rich Table for displaying remote agent runs with pagination support."""

    def __init__(self, *args, **kwargs):
        """Initialize RemoteRunsTable with columns for run display.

        Args:
            *args: Positional arguments passed to AIPTable
            **kwargs: Keyword arguments passed to AIPTable
        """
        kwargs.setdefault("row_styles", ("dim", "none"))
        kwargs.setdefault("show_header", True)
        super().__init__(*args, **kwargs)
        # Add columns for run display
        self.add_column("", width=2, no_wrap=True)  # Selection gutter
        self.add_column("Run UUID", style="cyan", width=36, no_wrap=True)
        self.add_column("Type", style="yellow", width=8, no_wrap=True)
        self.add_column("Status", style="magenta", width=12, no_wrap=True)
        self.add_column("Started (UTC)", style="dim", width=20, no_wrap=True)
        self.add_column("Completed (UTC)", style="dim", width=20, no_wrap=True)
        self.add_column("Duration", style="green", width=10, no_wrap=True)
        self.add_column("Input Preview", style="white", width=40, overflow="ellipsis")

    def add_run_row(
        self,
        run_uuid: str,
        run_type: str,
        status: str,
        started: str,
        completed: str,
        duration: str,
        preview: str,
        *,
        selected: bool = False,
    ) -> None:
        """Append a run row with optional selection styling."""
        gutter = Text("› ", style="bold bright_cyan") if selected else Text("  ")
        row_style = "reverse" if selected else None
        self.add_row(
            gutter,
            run_uuid,
            run_type,
            status,
            started,
            completed,
            duration,
            preview,
            style=row_style,
        )


__all__ = ["AIPPanel", "AIPTable", "AIPGrid", "RemoteRunsTable"]
