"""Pager-related helpers for CLI output.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import importlib
import io
import os
import platform
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from typing import Any

from rich.console import Console

from glaip_sdk.cli.constants import PAGER_HEADER_ENABLED, PAGER_MODE, PAGER_WRAP_LINES

__all__ = [
    "console",
    "_prepare_pager_env",
    "_render_ansi",
    "_pager_header",
    "_should_use_pager",
    "_resolve_pager_command",
    "_run_less_pager",
    "_run_more_pager",
    "_run_pager_with_temp_file",
    "_page_with_system_pager",
    "_should_page_output",
]

console: Console | None = None


def _get_console() -> Console:
    """Return the active console instance.

    Returns:
        Console: The active Rich console instance
    """
    global console
    try:
        cli_utils = importlib.import_module("glaip_sdk.cli.utils")
    except Exception:  # pragma: no cover - fallback during import cycles
        cli_utils = None

    current_console = getattr(cli_utils, "console", None) if cli_utils else None
    if current_console is not None and current_console is not console:
        console = current_console

    if console is None:
        console = Console()
    return console


def _prepare_pager_env(clear_on_exit: bool = True) -> None:
    """Configure LESS flags for a predictable, high-quality UX.

    Sets sensible defaults for the system pager:
      -R  : pass ANSI color escapes
      -S  : chop long lines (horizontal scroll with ←/→)
    (No -F, no -X) so we open a full-screen pager and clear on exit.
    Toggle wrapping via `PAGER_WRAP_LINES` (True drops -S).

    Args:
        clear_on_exit: Whether to clear the pager on exit (default: True)

    Returns:
        None
    """
    os.environ.pop("LESSSECURE", None)
    if os.getenv("LESS") is None:
        base = "-R" if PAGER_WRAP_LINES else "-RS"
        default_flags = base if clear_on_exit else (base + "FX")
        os.environ["LESS"] = default_flags


def _render_ansi(renderable: Any) -> str:
    """Render a Rich renderable to an ANSI string suitable for piping to 'less'.

    Args:
        renderable: Any Rich-compatible renderable object

    Returns:
        str: ANSI string representation of the renderable
    """
    active_console = _get_console()
    buf = io.StringIO()
    tmp_console = Console(
        file=buf,
        force_terminal=True,
        color_system=active_console.color_system or "auto",
        width=active_console.size.width or 100,
        legacy_windows=False,
        soft_wrap=False,
        record=False,
    )
    tmp_console.print(renderable)
    return buf.getvalue()


def _pager_header() -> str:
    """Generate pager header with navigation instructions.

    Returns:
        str: Header text containing navigation help, or empty string if disabled
    """
    if not PAGER_HEADER_ENABLED:
        return ""
    return "\n".join(
        [
            "TABLE VIEW — ↑/↓ PgUp/PgDn, ←/→ horiz scroll (with -S), /search, n/N next/prev, h help, q quit",
            "───────────────────────────────────────────────────────────────────────────────────────────────",
            "",
        ]
    )


def _should_use_pager() -> bool:
    """Check if we should attempt to use a system pager.

    Returns:
        bool: True if we should use a pager, False otherwise
    """
    active_console = _get_console()
    if not (active_console.is_terminal and os.isatty(1)):
        return False
    if (os.getenv("TERM") or "").lower() == "dumb":
        return False
    return True


def _resolve_pager_command() -> tuple[list[str] | None, str | None]:
    """Resolve the pager command and path to use.

    Returns:
        tuple[list[str] | None, str | None]: A tuple containing:
            - list[str] | None: The pager command parts if PAGER is set to less, None otherwise
            - str | None: The path to the less executable if found, None otherwise
    """
    pager_cmd = None
    pager_env = os.getenv("PAGER")
    if pager_env:
        parts = shlex.split(pager_env)
        if parts and os.path.basename(parts[0]).lower() == "less":
            pager_cmd = parts

    less_path = shutil.which("less")
    return pager_cmd, less_path


def _run_less_pager(pager_cmd: list[str] | None, less_path: str | None, tmp_path: str) -> None:
    """Run less pager with appropriate command and flags.

    Args:
        pager_cmd: Custom pager command parts if PAGER is set to less, None otherwise
        less_path: Path to the less executable, None if not found
        tmp_path: Path to temporary file containing content to display

    Returns:
        None
    """
    if pager_cmd:
        subprocess.run([*pager_cmd, tmp_path], check=False)
    else:
        flags = os.getenv("LESS", "-RS").split()
        subprocess.run([less_path, *flags, tmp_path], check=False)


def _run_more_pager(tmp_path: str) -> None:
    """Run more pager as fallback.

    Args:
        tmp_path: Path to temporary file containing content to display

    Returns:
        None

    Raises:
        FileNotFoundError: If more command is not found
    """
    more_path = shutil.which("more")
    if more_path:
        subprocess.run([more_path, tmp_path], check=False)
    else:
        raise FileNotFoundError("more command not found")


def _run_pager_with_temp_file(pager_runner: Callable[[str], None], ansi_text: str) -> bool:
    """Run a pager using a temporary file containing the content.

    Args:
        pager_runner: Function that takes a temp file path and runs the pager
        ansi_text: ANSI-formatted text content to display

    Returns:
        bool: True if pager executed successfully, False if there was an exception
    """
    _prepare_pager_env(clear_on_exit=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        tmp.write(_pager_header())
        tmp.write(ansi_text)
        tmp_path = tmp.name
    try:
        pager_runner(tmp_path)
        return True
    except Exception:
        return False
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _page_with_system_pager(ansi_text: str) -> bool:
    """Prefer 'less' with a temp file so stdin remains the TTY.

    Args:
        ansi_text: ANSI-formatted text content to display in the pager

    Returns:
        bool: True if pager was executed successfully, False otherwise
    """
    if not _should_use_pager():
        return False

    pager_cmd, less_path = _resolve_pager_command()

    if pager_cmd or less_path:
        return _run_pager_with_temp_file(lambda tmp_path: _run_less_pager(pager_cmd, less_path, tmp_path), ansi_text)

    if platform.system().lower().startswith("win"):
        return False

    return _run_pager_with_temp_file(_run_more_pager, ansi_text)


def _should_page_output(row_count: int, is_tty: bool) -> bool:
    """Determine if output should be paginated based on content size and terminal.

    Args:
        row_count: Number of rows in the content to display
        is_tty: Whether the output is going to a terminal

    Returns:
        bool: True if output should be paginated, False otherwise
    """
    active_console = _get_console()
    pager_mode = (PAGER_MODE or "auto").lower()
    if pager_mode in ("0", "off", "false"):
        return False
    if pager_mode in ("1", "on", "true"):
        return is_tty
    try:
        term_h = active_console.size.height or 24
        approx_lines = 5 + row_count
        return is_tty and (approx_lines >= term_h * 0.5)
    except Exception:
        return is_tty
