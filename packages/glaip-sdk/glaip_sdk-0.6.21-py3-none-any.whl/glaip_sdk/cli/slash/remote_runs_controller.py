"""Remote runs controller for browsing agent run history.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
from rich.console import Group
from rich.text import Text

try:  # pragma: no cover - optional dependency
    import questionary
    from questionary import Choice
except Exception:  # pragma: no cover - optional dependency
    questionary = None  # type: ignore[assignment]
    Choice = None  # type: ignore[assignment]

from glaip_sdk.branding import (
    ERROR_STYLE,
    INFO_STYLE,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.constants import DEFAULT_REMOTE_RUNS_PAGE_LIMIT
from glaip_sdk.cli.slash.tui.remote_runs_app import RemoteRunsTUICallbacks, run_remote_runs_textual
from glaip_sdk.cli.utils import prompt_export_choice_questionary, questionary_safe_ask
from glaip_sdk.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    TimeoutError,
    ValidationError,
)
from glaip_sdk.rich_components import RemoteRunsTable
from glaip_sdk.utils.export import export_remote_transcript_jsonl
from glaip_sdk.utils.rendering import render_remote_sse_transcript

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from glaip_sdk.cli.slash.session import SlashSession


class RemoteRunsController:
    """Controller for browsing remote agent run history."""

    def __init__(self, session: SlashSession) -> None:
        """Initialize the remote runs controller.

        Args:
            session: The slash session context.
        """
        self.session = session
        self.console = session.console
        self.ctx = session.ctx

        self._snapshot_notice_shown = False

    def handle_runs_command(self, args: list[str]) -> bool:
        """Handle the /runs command for browsing remote agent run history.

        Args:
            args: Command arguments (optional run_id for detail view).

        Returns:
            True to continue session.
        """
        current_agent = getattr(self.session, "_current_agent", None)
        if not current_agent:
            self.console.print(
                f"[{WARNING_STYLE}]Open /agents and select an agent first to browse remote run history.[/]"
            )
            return self._continue_session()

        agent_id = str(getattr(current_agent, "id", ""))
        if not agent_id:
            self.console.print(f"[{ERROR_STYLE}]Invalid agent context.[/]")
            return self._continue_session()

        if args:
            run_id = args[0]
            self.show_run_detail(agent_id, run_id)
            return self._continue_session()

        client = self._get_client_or_fail()
        if not client:
            return self._continue_session()

        agent_name = getattr(current_agent, "name", "") or None
        self.open_remote_runs_browser(client, agent_id, agent_name=agent_name)
        return self._continue_session()

    def open_remote_runs_browser(self, client: Any, agent_id: str, *, agent_name: str | None = None) -> None:
        """Fetch and render the remote runs table for the current agent.

        Args:
            client: API client instance.
            agent_id: UUID of the agent.
            agent_name: Optional display name for the agent.
        """
        state = self._get_runs_state(agent_id)
        runs_page = self._fetch_remote_runs_page(client, agent_id, state)
        if runs_page is None:
            return

        state["page"] = runs_page.page
        state["limit"] = runs_page.limit
        cursor = state.get("cursor", 0)
        if runs_page.data:
            cursor = max(0, min(cursor, len(runs_page.data) - 1))
        state["cursor"] = cursor

        if self._should_use_textual_browser():
            self._run_textual_browser(client, agent_id, runs_page, state, agent_name=agent_name)
            return

        if not self._snapshot_notice_shown:
            self.console.print(
                f"[{INFO_STYLE}]Interactive remote history requires a TTY. Showing the latest snapshot instead.[/]"
            )
            self._snapshot_notice_shown = True
        self._render_runs_table(runs_page, agent_id, cursor_idx=cursor)

    def _get_runs_state(self, agent_id: str) -> dict[str, Any]:
        """Return the persisted pagination state for an agent.

        Args:
            agent_id: UUID of the agent.

        Returns:
            Dictionary with page, limit, and cursor state.
        """
        pagination_state = getattr(self.session, "_runs_pagination_state", {})
        state = pagination_state.setdefault(
            agent_id,
            {"page": 1, "limit": DEFAULT_REMOTE_RUNS_PAGE_LIMIT, "cursor": 0},
        )
        state.setdefault("page", 1)
        state.setdefault("limit", DEFAULT_REMOTE_RUNS_PAGE_LIMIT)
        state.setdefault("cursor", 0)
        return state

    def _fetch_remote_runs_page(
        self,
        client: Any,
        agent_id: str,
        state: dict[str, Any],
        *,
        allow_reset: bool = True,
    ) -> Any | None:
        """Fetch a RunsPage while handling common error flows.

        Args:
            client: API client instance.
            agent_id: UUID of the agent.
            state: Pagination state dictionary.
            allow_reset: Whether to reset pagination on validation errors.

        Returns:
            RunsPage instance or None on error.
        """
        try:
            return client.agents.runs.list_runs(agent_id, limit=state["limit"], page=state["page"])
        except AuthenticationError:
            self.console.print(f"[{ERROR_STYLE}]Authentication failed. Run /login to refresh credentials.[/]")
        except ForbiddenError as exc:
            self.console.print(f"[{ERROR_STYLE}]Access denied: {exc}[/]")
        except NotFoundError:
            self.console.print(
                f"[{WARNING_STYLE}]Agent not found or access revoked. Re-open /agents to select again.[/]"
            )
            pagination_state = getattr(self.session, "_runs_pagination_state", {})
            pagination_state.pop(agent_id, None)
        except TimeoutError:
            ctx_obj = self.ctx.obj if isinstance(self.ctx.obj, dict) else {}
            timeout_seconds = ctx_obj.get("timeout", 30)
            self.console.print(
                f"[{WARNING_STYLE}]Remote history timed out after {timeout_seconds}s. Press Enter to retry.[/]"
            )
        except ValidationError:
            if allow_reset:
                self.console.print(
                    f"[{WARNING_STYLE}]Invalid pagination request (page {state['page']}, limit {state['limit']}). "
                    "Resetting to defaults.[/]"
                )
                state["page"] = 1
                state["limit"] = DEFAULT_REMOTE_RUNS_PAGE_LIMIT
                return self._fetch_remote_runs_page(client, agent_id, state, allow_reset=False)
            self.console.print(f"[{ERROR_STYLE}]Pagination request rejected by backend.[/]")
        except Exception as exc:  # pragma: no cover - unexpected API failure
            self.console.print(f"[{ERROR_STYLE}]Error fetching runs: {exc}[/]")
        return None

    def _build_runs_table_renderable(
        self,
        runs_page: Any,
        agent_id: str,
        *,
        cursor_idx: int = 0,
    ) -> Group:
        """Build the Rich renderable for the runs table view."""
        current_agent = getattr(self.session, "_current_agent", None)
        agent_label = getattr(current_agent, "name", agent_id) if current_agent else agent_id
        total_pages = 1
        if runs_page.limit:
            total_pages = max(1, math.ceil(runs_page.total / runs_page.limit))
        header = (
            f"[dim]Agent: {agent_label} ({agent_id}) · Limit={runs_page.limit} · "
            f"Page {runs_page.page}/{total_pages} (use ←/→ to paginate)[/]"
        )
        renderables: list[Any] = [Text.from_markup(f"\n{header}")]

        if runs_page.total == 0:
            renderables.append(
                Text.from_markup(f"[{WARNING_STYLE}]No remote runs yet. Trigger `/agents run` to create a run.[/]")
            )
            return Group(*renderables)

        table = RemoteRunsTable(title="Remote Runs — ↑/↓ rows · ←/→ pages · q/Esc exit")
        for idx, run in enumerate(runs_page.data):
            run_type_str = run.run_type.title()
            status_str = run.status.upper()
            started_str = run.started_at.strftime("%Y-%m-%d %H:%M:%S") if run.started_at else "—"
            completed_str = run.completed_at.strftime("%Y-%m-%d %H:%M:%S") if run.completed_at else "—"
            duration_str = run.duration_formatted()
            input_preview = run.input_preview()
            table.add_run_row(
                str(run.id),
                run_type_str,
                status_str,
                started_str,
                completed_str,
                duration_str,
                input_preview,
                selected=idx == cursor_idx,
            )

        renderables.append(table)
        renderables.append(Text.from_markup("[dim]Enter detail · e export JSONL · q/Esc exit[/]"))
        return Group(*renderables)

    def _render_runs_table(self, runs_page: Any, agent_id: str, *, cursor_idx: int = 0) -> None:
        """Render runs table with pagination info."""
        renderable = self._build_runs_table_renderable(
            runs_page,
            agent_id,
            cursor_idx=cursor_idx,
        )
        self.console.print(renderable)

    def _should_use_textual_browser(self) -> bool:
        """Return True when Textual-based navigation can be used."""
        ctx_obj = getattr(self.session.ctx, "obj", {})
        interactive = bool(getattr(self.session, "_interactive", False))
        if not interactive and isinstance(ctx_obj, dict) and ctx_obj.get("tty"):
            interactive = True
        if not interactive:
            return False
        try:
            stdin_tty = sys.stdin.isatty()
            stdout_tty = sys.stdout.isatty()
        except Exception:
            return False
        return bool(stdin_tty and stdout_tty)

    def _run_textual_browser(
        self,
        client: Any,
        agent_id: str,
        runs_page: Any,
        state: dict[str, Any],
        *,
        agent_name: str | None = None,
    ) -> None:
        """Launch the Textual UI for browsing runs."""

        def fetch_page(page: int, limit: int) -> Any | None:
            fetch_state = {"page": page, "limit": limit}
            return self._fetch_remote_runs_page(client, agent_id, fetch_state)

        def fetch_detail(run_id: str) -> Any | None:
            return self._load_run_detail(client, agent_id, run_id)

        def export_run(run_id: str, detail: Any | None) -> bool:
            return self.export_remote_run(agent_id, run_id, client, detail)

        callbacks = RemoteRunsTUICallbacks(
            fetch_page=fetch_page,
            fetch_detail=fetch_detail,
            export_run=export_run,
        )
        page, limit, cursor = run_remote_runs_textual(
            runs_page,
            state.get("cursor", 0),
            callbacks,
            agent_name=agent_name,
            agent_id=agent_id,
        )
        state["page"] = page
        state["limit"] = limit
        state["cursor"] = cursor

    def _load_run_detail(self, client: Any, agent_id: str, run_id: str) -> Any | None:
        """Return detailed run payload, handling errors."""
        try:
            return client.agents.runs.get_run(agent_id, run_id)
        except AuthenticationError:
            self.console.print(f"[{ERROR_STYLE}]Authentication failed while loading run detail.[/]")
        except NotFoundError:
            self.console.print(f"[{WARNING_STYLE}]Run no longer exists. It may have been cleaned up.[/]")
        except TimeoutError:
            self.console.print(f"[{WARNING_STYLE}]Fetching remote transcript timed out. Try again.[/]")
        except Exception as exc:  # pragma: no cover - unexpected API failure
            self.console.print(f"[{ERROR_STYLE}]Error fetching run detail: {exc}[/]")
        return None

    def show_run_detail(self, agent_id: str, run_id: str) -> Any | None:
        """Show detailed run information with SSE events.

        Args:
            agent_id: UUID of the agent.
            run_id: UUID of the run.

        Returns:
            RunWithOutput instance or None on error.
        """
        client = self._get_client_or_fail()
        if not client:
            return None

        run_detail = self._load_run_detail(client, agent_id, run_id)
        if run_detail is None:
            return None

        self.console.print()
        render_remote_sse_transcript(run_detail, self.console, show_metadata=True)
        return run_detail

    def export_remote_run(
        self,
        agent_id: str,
        run_id: str,
        client: Any,
        detail: Any | None,
    ) -> bool:
        """Export the selected remote run to JSONL.

        Args:
            agent_id: UUID of the agent.
            run_id: UUID of the run.
            client: API client instance.
            detail: Cached RunWithOutput instance or None.
        """
        run_detail = detail or self._load_run_detail(client, agent_id, run_id)
        if run_detail is None:
            return False

        destination = self._prompt_remote_export_path(run_id)
        if destination is None:
            self.console.print("[dim]Export cancelled.[/]")
            return False

        overwrite = False
        if destination.exists():
            if not click.confirm(f"{destination} already exists. Overwrite?", default=False):
                self.console.print("[dim]Export cancelled.[/]")
                return False
            overwrite = True

        try:
            agent_label = self._resolve_agent_name()
            exported = export_remote_transcript_jsonl(
                run_detail,
                destination,
                overwrite=overwrite,
                agent_name=agent_label,
            )
            self.console.print(f"[{SUCCESS_STYLE}]Remote transcript exported to {exported}[/]")
            return True
        except FileExistsError:
            self.console.print(f"[{WARNING_STYLE}]File already exists and overwrite was disabled: {destination}[/]")
        except Exception as exc:  # pragma: no cover - unexpected IO failures
            self.console.print(f"[{ERROR_STYLE}]Failed to export transcript: {exc}[/]")
        return False

    def _resolve_agent_name(self) -> str | None:
        """Return the friendly agent name for the active session if available."""
        current_agent = getattr(self.session, "_current_agent", None)
        if current_agent is None:
            return None
        return getattr(current_agent, "name", None) or getattr(current_agent, "display_name", None)

    def _prompt_remote_export_path(self, run_id: str) -> Path | None:
        """Prompt the operator for an export destination.

        Args:
            run_id: UUID of the run.

        Returns:
            Path object or None if cancelled.
        """
        # Default to current working directory for exports (user can override via prompt).
        # This is safe as the user explicitly initiates the export operation.
        default_path = Path.cwd() / f"run_{run_id}.jsonl"  # noqa: S108
        try:
            result = self._handle_questionary_export_prompt(default_path)
            if result is not None:
                return result
            return None
        except RuntimeError:
            pass

        is_terminal = bool(getattr(self.console, "is_terminal", False))
        if not is_terminal:
            return default_path

        return self._prompt_cli_export_choice(default_path)

    def _handle_questionary_export_prompt(self, default_path: Path) -> Path | None:
        """Handle questionary-based export prompt with error handling.

        Args:
            default_path: Default export path.

        Returns:
            Selected path or None if cancelled.

        Raises:
            RuntimeError: If questionary prompt is unavailable or fails.
        """
        selection = self._prompt_questionary_export_choice(default_path)
        if selection is None:
            return None

        choice, _ = selection
        if choice == "default":
            return default_path

        if choice == "custom":
            return self._prompt_questionary_custom_destination(default_path)

        # choice == "cancel" or any other value
        return None

    def _prompt_questionary_export_choice(self, default_path: Path) -> tuple[str, Path | None] | None:
        """Render the questionary export menu and return the selected action."""
        display_path = self._format_export_display_path(default_path)
        result = prompt_export_choice_questionary(default_path, display_path)
        if result is None:
            raise RuntimeError("Questionary prompt unavailable")
        return result

    def _prompt_questionary_custom_destination(self, default_path: Path) -> Path | None:
        """Prompt for a custom destination using questionary path picker."""
        if questionary is None:
            raise RuntimeError("Questionary prompt unavailable")

        try:
            prompt = questionary.path(
                "Destination path (Tab to autocomplete):",
                default="",
                only_directories=False,
            )
            response = questionary_safe_ask(prompt)
        except Exception as exc:  # pragma: no cover - questionary failure
            raise RuntimeError("Questionary path prompt failed") from exc

        return self._resolve_export_path(response, default_path, allow_default=False)

    def _prompt_cli_export_choice(self, default_path: Path) -> Path | None:
        """Render a click-based export menu when questionary isn't available."""
        display_path = self._format_export_display_path(default_path)
        self.console.print()
        self.console.print("Remote export options:")
        self.console.print(f"  1. Save to default ({display_path})")
        self.console.print("  2. Choose a different path")
        self.console.print("  3. Cancel")
        try:
            selection = click.prompt(
                "Select an option",
                type=click.Choice(["1", "2", "3"]),
                default="1",
                show_choices=False,
            )
        except (click.Abort, EOFError, KeyboardInterrupt):
            return None

        if selection == "1":
            return default_path
        if selection == "2":
            return self._prompt_click_export_path(default_path)
        return None

    def _prompt_click_export_path(self, default_path: Path) -> Path | None:
        """Prompt for a custom export destination using click only."""
        default_ref = self._format_export_display_path(default_path)
        self.console.print(
            f"[dim]Enter a custom destination path. Leave blank to cancel. Default reference: {default_ref}[/]"
        )
        try:
            response = click.prompt(
                "Custom path",
                default="",
                show_default=False,
            )
        except (click.Abort, EOFError, KeyboardInterrupt):
            return None

        return self._resolve_export_path(response, default_path, allow_default=False)

    def _resolve_export_path(self, response: str | None, default_path: Path, *, allow_default: bool) -> Path | None:
        """Normalise export path input into a Path instance."""
        value = (response or "").strip()
        if not value:
            return default_path if allow_default else None

        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            # Resolve relative paths against current working directory.
            # This is safe as the user explicitly provided this path via prompt.
            candidate = Path.cwd() / candidate  # noqa: S108
        return candidate

    def _format_export_display_path(self, path: Path) -> str:
        """Return a user-friendly string for default export paths."""
        cwd = Path.cwd()
        try:
            relative = path.relative_to(cwd)
            return str(Path(".") / relative)
        except ValueError:
            pass

        home = Path.home()
        try:
            relative_home = path.relative_to(home)
            suffix = f"/{relative_home}" if relative_home.parts else ""
            return f"~{suffix}"
        except ValueError:
            pass

        return str(path)

    def _get_client_or_fail(self) -> Any:
        """Get client or handle failure and return None.

        Returns:
            API client instance or None on error.
        """
        try:
            return self.session._get_client()
        except click.ClickException as exc:
            self.console.print(f"[{ERROR_STYLE}]{exc}[/]")
            return None

    def _continue_session(self) -> bool:
        """Signal that the slash session should remain active.

        Returns:
            True to continue session.
        """
        return not getattr(self.session, "_should_exit", False)
