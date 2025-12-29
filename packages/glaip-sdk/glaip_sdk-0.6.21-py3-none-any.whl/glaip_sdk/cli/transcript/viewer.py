"""Interactive viewer for post-run transcript exploration.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click
from rich.console import Console

try:  # pragma: no cover - optional dependency
    import questionary
    from questionary import Choice
except Exception:  # pragma: no cover - optional dependency
    questionary = None  # type: ignore[assignment]
    Choice = None  # type: ignore[assignment]

from glaip_sdk.cli.transcript.cache import suggest_filename
from glaip_sdk.cli.utils import prompt_export_choice_questionary, questionary_safe_ask
from glaip_sdk.utils.rendering.layout.progress import is_delegation_tool
from glaip_sdk.utils.rendering.layout.transcript import DEFAULT_TRANSCRIPT_THEME
from glaip_sdk.utils.rendering.viewer import (
    ViewerContext as PresenterViewerContext,
    prepare_viewer_snapshot as presenter_prepare_viewer_snapshot,
    render_post_run_view as presenter_render_post_run_view,
    render_transcript_events as presenter_render_transcript_events,
    render_transcript_view as presenter_render_transcript_view,
)

EXPORT_CANCELLED_MESSAGE = "[dim]Export cancelled.[/dim]"


ViewerContext = PresenterViewerContext


class PostRunViewer:  # pragma: no cover - interactive flows are not unit tested
    """Simple interactive session for inspecting agent run transcripts."""

    def __init__(
        self,
        console: Console,
        ctx: ViewerContext,
        export_callback: Callable[[Path], Path],
        *,
        initial_view: str = "default",
    ) -> None:
        """Initialize viewer state for a captured transcript."""
        self.console = console
        self.ctx = ctx
        self._export_callback = export_callback
        self._view_mode = initial_view if initial_view in {"default", "transcript"} else "default"

    def run(self) -> None:
        """Enter the interactive loop."""
        if not self.ctx.events and not (self.ctx.default_output or self.ctx.final_output):
            return
        if self._view_mode == "transcript":
            self._render()
        self._print_command_hint()
        self._fallback_loop()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render(self) -> None:
        """Render the transcript viewer interface."""
        try:
            if self.console.is_terminal:
                self.console.clear()
        except Exception:  # pragma: no cover - platform quirks
            pass

        header = f"Agent transcript viewer · run {self.ctx.manifest_entry.get('run_id')}"
        agent_label = self.ctx.manifest_entry.get("agent_name") or "unknown agent"
        model = self.ctx.manifest_entry.get("model") or self.ctx.meta.get("model")
        agent_id = self.ctx.manifest_entry.get("agent_id")
        subtitle_parts = [agent_label]
        if model:
            subtitle_parts.append(str(model))
        if agent_id:
            subtitle_parts.append(agent_id)

        if self._view_mode == "transcript":
            self.console.rule(header)
            if subtitle_parts:
                self.console.print(f"[dim]{' · '.join(subtitle_parts)}[/]")
            self.console.print()

        if self._view_mode == "default":
            presenter_render_post_run_view(self.console, self.ctx)
        else:
            theme = DEFAULT_TRANSCRIPT_THEME
            snapshot, state = presenter_prepare_viewer_snapshot(self.ctx, glyphs=None, theme=theme)
            presenter_render_transcript_view(self.console, snapshot, theme=theme)
            presenter_render_transcript_events(self.console, state.events)

    # ------------------------------------------------------------------
    # Interaction loops
    # ------------------------------------------------------------------
    def _fallback_loop(self) -> None:
        """Fallback interaction loop for non-interactive terminals."""
        while True:
            try:
                ch = click.getchar()
            except (EOFError, KeyboardInterrupt):
                break

            if ch in {"\r", "\n"}:
                break

            if ch == "\x14" or ch.lower() == "t":  # Ctrl+T or t
                self.toggle_view()
                continue

            if ch.lower() == "e":
                self.export_transcript()
                self._print_command_hint()
            else:
                continue

    def _handle_command(self, raw: str) -> bool:
        """Handle a command input.

        Args:
            raw: Raw command string.

        Returns:
            True to continue, False to exit.
        """
        lowered = raw.lower()
        if lowered in {"exit", "quit", "q"}:
            return True
        if lowered in {"export", "e"}:
            self.export_transcript()
            self._print_command_hint()
            return False
        self.console.print("[dim]Commands: export, exit.[/dim]")
        return False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def toggle_view(self) -> None:
        """Switch between default result view and verbose transcript."""
        self._view_mode = "transcript" if self._view_mode == "default" else "default"
        self._render()
        self._print_command_hint()

    def export_transcript(self) -> None:
        """Prompt user for a destination and export the cached transcript."""
        entry = self.ctx.manifest_entry
        default_name = suggest_filename(entry)
        default_path = Path.cwd() / default_name

        def _display_path(path: Path) -> str:
            raw = str(path)
            return raw if len(raw) <= 80 else f"…{raw[-77:]}"

        selection = self._prompt_export_choice(default_path, _display_path(default_path))
        if selection is None:
            self._legacy_export_prompt(default_path, _display_path)
            return

        action, _ = selection
        if action == "cancel":
            self.console.print(EXPORT_CANCELLED_MESSAGE)
            return

        if action == "default":
            destination = default_path
        else:
            destination = self._prompt_custom_destination()
            if destination is None:
                self.console.print(EXPORT_CANCELLED_MESSAGE)
                return

        try:
            target = self._export_callback(destination)
            self.console.print(f"[green]Transcript exported to {target}[/green]")
        except FileNotFoundError as exc:
            self.console.print(f"[red]{exc}[/red]")
        except Exception as exc:  # pragma: no cover - unexpected IO failures
            self.console.print(f"[red]Failed to export transcript: {exc}[/red]")

    def _prompt_export_choice(self, default_path: Path, default_display: str) -> tuple[str, Any] | None:
        """Render interactive export menu with numeric shortcuts."""
        if not self.console.is_terminal:
            return None

        return prompt_export_choice_questionary(default_path, default_display)

    def _prompt_custom_destination(self) -> Path | None:
        """Prompt for custom export path with filesystem completion."""
        if not self.console.is_terminal:
            return None

        try:
            question = questionary.path(
                "Destination path (Tab to autocomplete):",
                default="",
                only_directories=False,
            )
            response = questionary_safe_ask(question)
        except Exception:
            return None

        if not response:
            return None

        candidate = Path(response.strip()).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        return candidate

    def _legacy_export_prompt(self, default_path: Path, formatter: Callable[[Path], str]) -> None:
        """Fallback export workflow when interactive UI is unavailable."""
        self.console.print("[dim]Export options (fallback mode)[/dim]")
        self.console.print(f"  1. Save to default ({formatter(default_path)})")
        self.console.print("  2. Choose a different path")
        self.console.print("  3. Cancel")

        try:
            choice = click.prompt(
                "Select option",
                type=click.Choice(["1", "2", "3"], case_sensitive=False),
                default="1",
                show_choices=False,
            )
        except (EOFError, KeyboardInterrupt):
            self.console.print(EXPORT_CANCELLED_MESSAGE)
            return

        if choice == "3":
            self.console.print(EXPORT_CANCELLED_MESSAGE)
            return

        if choice == "1":
            destination = default_path
        else:
            try:
                destination_str = click.prompt("Enter destination path", default="")
            except (EOFError, KeyboardInterrupt):
                self.console.print(EXPORT_CANCELLED_MESSAGE)
                return
            if not destination_str.strip():
                self.console.print(EXPORT_CANCELLED_MESSAGE)
                return
            destination = Path(destination_str.strip()).expanduser()
            if not destination.is_absolute():
                destination = Path.cwd() / destination

        try:
            target = self._export_callback(destination)
            self.console.print(f"[green]Transcript exported to {target}[/green]")
        except FileNotFoundError as exc:
            self.console.print(f"[red]{exc}[/red]")
        except Exception as exc:  # pragma: no cover - unexpected IO failures
            self.console.print(f"[red]Failed to export transcript: {exc}[/red]")

    def _print_command_hint(self) -> None:
        """Print command hint for user interaction."""
        self.console.print("[dim]Ctrl+T to toggle transcript · type `e` to export · press Enter to exit[/dim]")
        self.console.print()

    @staticmethod
    def _extract_direct_tool(
        tool_info: dict[str, Any],
    ) -> tuple[str, dict[str, Any]] | None:
        """Extract direct tool from tool_info.

        Args:
            tool_info: Tool info dictionary.

        Returns:
            Tuple of (tool_name, tool_info) or None.
        """
        if isinstance(tool_info, dict):
            name = tool_info.get("name")
            if name:
                return name, tool_info
        return None

    @staticmethod
    def _extract_completed_name(event: dict[str, Any]) -> str | None:
        """Extract completed tool name from event content.

        Args:
            event: Event dictionary.

        Returns:
            Tool name or None.
        """
        content = event.get("content") or ""
        if isinstance(content, str) and content.startswith("Completed "):
            name = content.replace("Completed ", "").strip()
            if name:
                return name
        return None

    def _ensure_step_entry(
        self,
        steps: dict[str, dict[str, Any]],
        order: list[str],
        name: str,
    ) -> dict[str, Any]:
        """Ensure step entry exists, creating if needed.

        Args:
            steps: Steps dictionary.
            order: Order list.
            name: Step name.

        Returns:
            Step dictionary.
        """
        if name not in steps:
            steps[name] = {
                "name": name,
                "title": name,
                "is_delegate": is_delegation_tool(name),
                "duration": None,
                "started_at": None,
                "finished": False,
            }
            order.append(name)
        return steps[name]

    def _apply_step_update(
        self,
        step: dict[str, Any],
        metadata: dict[str, Any],
        info: dict[str, Any],
        event: dict[str, Any],
    ) -> None:
        """Apply update to step from event metadata.

        Args:
            step: Step dictionary to update.
            metadata: Event metadata.
            info: Step info dictionary.
            event: Event dictionary.
        """
        status = metadata.get("status")
        event_time = metadata.get("time")

        if status == "running" and step.get("started_at") is None and isinstance(event_time, (int, float)):
            try:
                step["started_at"] = float(event_time)
            except Exception:
                step["started_at"] = None

        if self._is_step_finished(metadata, event):
            step["finished"] = True

        duration = self._compute_step_duration(step, info, metadata)
        if duration is not None:
            step["duration"] = duration


def run_viewer_session(
    console: Console,
    ctx: ViewerContext,
    export_callback: Callable[[Path], Path],
    *,
    initial_view: str = "default",
) -> None:
    """Entry point for creating and running the post-run viewer."""
    viewer = PostRunViewer(console, ctx, export_callback, initial_view=initial_view)
    viewer.run()
