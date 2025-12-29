"""Update command for upgrading the glaip-sdk package.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import click
from rich.console import Console

from glaip_sdk.branding import ACCENT_STYLE, ERROR_STYLE, INFO_STYLE, SUCCESS_STYLE

PACKAGE_NAME = "glaip-sdk"


def _is_uv_managed_environment() -> bool:
    """Check if running in a uv-managed tool environment.

    Uses a path-based heuristic against sys.executable, sys.prefix, and UV_TOOL_DIR
    or UV_TOOL_BIN to detect a case-insensitive "uv/tools" segment. Update if uv
    changes its layout.
    """
    if _has_uv_tool_path(sys.executable):
        return True
    if _has_uv_tool_path(sys.prefix):
        return True
    uv_tool_dir = os.environ.get("UV_TOOL_DIR") or os.environ.get("UV_TOOL_BIN")
    if uv_tool_dir and _has_uv_tool_path(uv_tool_dir):
        return True
    return False


def _has_uv_tool_path(path: str) -> bool:
    """Return True when a path contains a case-insensitive uv/tools segment."""
    parts = [part.lower() for part in Path(path).parts]
    for idx, part in enumerate(parts[:-1]):
        if part == "uv" and parts[idx + 1] == "tools":
            return True
    return False


def _is_pip_available() -> bool:
    """Return True when pip can be imported in the current interpreter."""
    return importlib.util.find_spec("pip") is not None


def _build_missing_pip_guidance(
    *,
    include_prerelease: bool,
    package_name: str = PACKAGE_NAME,
    force_reinstall: bool = False,
) -> tuple[str, str]:
    """Return error and troubleshooting guidance when pip is unavailable."""
    manual_cmd = _build_manual_upgrade_command(
        include_prerelease,
        package_name=package_name,
        is_uv=True,
        force_reinstall=force_reinstall,
    )
    error_detail = "pip is not available in this environment."
    troubleshooting = (
        "💡 Troubleshooting:\n"
        f"   • If you installed via uv tool, run: {manual_cmd}\n"
        "   • Otherwise install pip: python -m ensurepip"
    )
    return error_detail, troubleshooting


def _build_command_parts(
    *,
    package_name: str = PACKAGE_NAME,
    is_uv: bool | None = None,
    force_reinstall: bool = False,
    include_prerelease: bool = False,
) -> tuple[list[str], str]:
    """Build the common parts of upgrade commands.

    Returns:
        Tuple of (command parts list, force_reinstall flag name).
        For uv: (["uv", "tool", "install", "--upgrade", package_name], "--reinstall")
        For pip: (["pip", "install", "--upgrade", package_name], "--force-reinstall")
    """
    if is_uv is None:
        is_uv = _is_uv_managed_environment()

    if is_uv:
        command = ["uv", "tool", "install", "--upgrade", package_name]
        reinstall_flag = "--reinstall"
    else:
        command = ["pip", "install", "--upgrade", package_name]
        reinstall_flag = "--force-reinstall"

    if force_reinstall:
        command.insert(-1, reinstall_flag)

    if include_prerelease:
        command.append("--pre")

    return command, reinstall_flag


def _build_upgrade_command(
    include_prerelease: bool,
    *,
    package_name: str = PACKAGE_NAME,
    is_uv: bool | None = None,
    force_reinstall: bool = False,
) -> Sequence[str]:
    """Return the command used to upgrade the SDK (pip or uv tool install)."""
    if is_uv is None:
        is_uv = _is_uv_managed_environment()

    command_parts, _ = _build_command_parts(
        package_name=package_name,
        is_uv=is_uv,
        force_reinstall=force_reinstall,
        include_prerelease=include_prerelease,
    )

    # For pip, prepend sys.executable and -m
    if not is_uv:
        command_parts = [sys.executable, "-m"] + command_parts

    return command_parts


def _build_manual_upgrade_command(
    include_prerelease: bool,
    *,
    package_name: str = PACKAGE_NAME,
    is_uv: bool | None = None,
    force_reinstall: bool = False,
) -> str:
    """Return a manual upgrade command string matching the active environment."""
    command_parts, _ = _build_command_parts(
        package_name=package_name,
        is_uv=is_uv,
        force_reinstall=force_reinstall,
        include_prerelease=include_prerelease,
    )
    return " ".join(command_parts)


@click.command(name="update")
@click.option(
    "--pre",
    "include_prerelease",
    is_flag=True,
    help="Include pre-release versions when upgrading.",
)
def update_command(include_prerelease: bool) -> None:
    """Upgrade the glaip-sdk package using pip or uv tool install."""
    console = Console()
    # Call _is_uv_managed_environment() once and pass explicitly to avoid redundant calls
    is_uv = _is_uv_managed_environment()
    if not is_uv and not _is_pip_available():
        error_detail, troubleshooting = _build_missing_pip_guidance(
            include_prerelease=include_prerelease,
        )
        raise click.ClickException(f"{error_detail}\n{troubleshooting}")
    upgrade_cmd = _build_upgrade_command(include_prerelease, is_uv=is_uv)

    # Determine the appropriate manual command for error messages
    manual_cmd = _build_manual_upgrade_command(include_prerelease, is_uv=is_uv)

    console.print(f"[{ACCENT_STYLE}]Upgrading {PACKAGE_NAME} using[/] [{INFO_STYLE}]{' '.join(upgrade_cmd)}[/]")

    try:
        subprocess.run(upgrade_cmd, check=True)
    except FileNotFoundError as exc:
        if is_uv:
            raise click.ClickException(
                f"Unable to locate uv executable. Please ensure uv is installed and on your PATH.\n"
                f"Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh\n"
                f"Or run manually: {manual_cmd}"
            ) from exc
        raise click.ClickException(
            "Unable to locate Python executable to run pip. Please ensure Python is installed and try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        console.print(f"[{ERROR_STYLE}]Automatic upgrade failed.[/] Please run `{manual_cmd}` manually.")
        raise click.ClickException("Automatic upgrade failed.") from exc

    console.print(f"[{SUCCESS_STYLE}]✅ {PACKAGE_NAME} upgraded successfully.[/]")
