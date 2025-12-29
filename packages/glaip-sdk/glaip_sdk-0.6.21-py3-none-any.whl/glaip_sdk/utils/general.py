"""General utility functions for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

import click


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human readable size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_datetime(dt: datetime | str | None) -> str:
    """Format datetime object to readable string.

    Args:
        dt: Datetime object or string to format

    Returns:
        Formatted datetime string or "N/A" if None
    """
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif dt is None:
        return "N/A"
    return str(dt)


def progress_bar(iterable: Iterable[Any], description: str = "Processing") -> Iterator[Any]:
    """Simple progress bar using click.

    Args:
        iterable: Iterable to process
        description: Progress description

    Yields:
        Items from iterable with progress display
    """
    try:
        with click.progressbar(iterable, label=description) as bar:
            yield from bar
    except ImportError:
        # Fallback if click not available
        yield from iterable
