"""Agent-specific interaction loop for the command palette.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import click

from glaip_sdk.branding import ERROR_STYLE, HINT_PREFIX_STYLE
from glaip_sdk.cli.commands.agents import get as agents_get_command
from glaip_sdk.cli.commands.agents import run as agents_run_command
from glaip_sdk.cli.constants import DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT
from glaip_sdk.cli.hints import format_command_hint
from glaip_sdk.cli.slash.prompt import _HAS_PROMPT_TOOLKIT, FormattedText
from glaip_sdk.cli.utils import bind_slash_session_context

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from glaip_sdk.cli.slash.session import SlashSession


class AgentRunSession:
    """Per-agent execution context for the command palette."""

    def __init__(self, session: SlashSession, agent: Any) -> None:
        """Initialize the agent run session.

        Args:
            session: The slash session context
            agent: The agent to interact with
        """
        self.session = session
        self.agent = agent
        self.console = session.console
        self._agent_id = str(getattr(agent, "id", ""))
        self._agent_name = getattr(agent, "name", "") or self._agent_id
        self._prompt_placeholder: str = (
            "Chat with this agent here; use / for shortcuts. "
            "Alt+Enter inserts a newline. Ctrl+T opens the last transcript."
        )
        self._contextual_completion_help: dict[str, str] = {
            "details": "Show this agent's configuration (+ expands prompt).",
            "help": "Display this context-aware menu.",
            "runs": "✨ NEW · Browse remote run history for this agent.",
            "exit": "Return to the command palette.",
            "q": "Return to the command palette.",
        }
        self._instruction_preview_limit = DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT

    def run(self) -> None:
        """Run the interactive agent session loop."""
        self.session.set_contextual_commands(self._contextual_completion_help, include_global=False)
        previous_agent = getattr(self.session, "_current_agent", None)
        self.session._current_agent = self.agent
        clear_ready = getattr(self.session, "clear_agent_transcript_ready", None)
        if callable(clear_ready):
            clear_ready(self._agent_id)
        try:
            self._display_agent_info()
            self._run_agent_loop()
        finally:
            self.session.set_contextual_commands(None)
            self.session._current_agent = previous_agent

    def _display_agent_info(self) -> None:
        """Display agent information and summary."""
        self.session._render_header(self.agent, focus_agent=True)

    def _run_agent_loop(self) -> None:
        """Run the main agent interaction loop."""
        while True:
            raw = self._get_user_input()
            if raw is None:
                return

            raw = raw.strip()
            if not raw:
                continue

            if raw.startswith("/"):
                if not self._handle_slash_command(raw, self._agent_id):
                    return
                continue

            self._run_agent(self._agent_id, raw)

    def _get_user_input(self) -> str | None:
        """Get user input with proper error handling."""
        try:

            def _prompt_message() -> Any:
                """Get formatted prompt message for agent session."""
                prompt_prefix = f"{self._agent_name} ({self._agent_id}) "

                # Use FormattedText if prompt_toolkit is available, otherwise use simple string
                if _HAS_PROMPT_TOOLKIT and FormattedText is not None:
                    segments = [
                        ("class:prompt", prompt_prefix),
                        ("class:prompt", "\n› "),
                    ]
                    return FormattedText(segments)

                return f"{prompt_prefix}\n› "

            raw = self.session._prompt(
                _prompt_message,
                placeholder=self._prompt_placeholder,
            )
            if self._prompt_placeholder:
                # Show the guidance once, then fall back to a clean prompt.
                self._prompt_placeholder = ""
            return raw
        except EOFError:
            self.console.print("\nExiting agent context.")
            return None
        except KeyboardInterrupt:
            self.console.print("")
            return ""

    def _handle_slash_command(self, raw: str, agent_id: str) -> bool:
        """Handle slash commands in agent context. Returns False if should exit."""
        # Handle simple commands first
        if raw == "/":
            return self._handle_help_command()

        if raw in {"/exit", "/back", "/q"}:
            return self._handle_exit_command()

        if raw == "/details":
            return self._handle_details_command(agent_id)

        if raw in {"/help", "/?"}:
            return self._handle_help_command()

        # Handle other commands through the main session
        return self._handle_other_command(raw)

    def _handle_help_command(self) -> bool:
        """Handle help command."""
        self.session._cmd_help([], True)
        return True

    def _handle_exit_command(self) -> bool:
        """Handle exit command."""
        self.console.print("[dim]Returning to the main prompt.[/dim]")
        return False

    def _handle_details_command(self, agent_id: str) -> bool:
        """Handle details command."""
        self._show_details(agent_id)
        return True

    def _handle_other_command(self, raw: str) -> bool:
        """Handle other commands through the main session."""
        self.session.handle_command(raw, invoked_from_agent=True)
        return not self.session._should_exit

    def _show_details(self, agent_id: str, *, enable_prompt: bool = True) -> None:
        """Render the agent's configuration export inside the command palette."""
        try:
            self.session.ctx.invoke(
                agents_get_command,
                agent_ref=agent_id,
                instruction_preview=self._instruction_preview_limit,
            )
            if enable_prompt:
                self._prompt_instruction_view_toggle(agent_id)
                self.console.print(
                    f"[{HINT_PREFIX_STYLE}]Tip:[/] Continue the conversation in this prompt, or use "
                    f"{format_command_hint('/help') or '/help'} for shortcuts."
                )
        except click.ClickException as exc:
            self.console.print(f"[{ERROR_STYLE}]{exc}[/]")

    def _prompt_instruction_view_toggle(self, agent_id: str) -> None:
        """Offer a prompt to expand or collapse the instruction preview after details."""
        if not getattr(self.console, "is_terminal", False):
            return

        while True:
            mode = "expanded" if self._instruction_preview_limit == 0 else "trimmed"
            self.console.print(f"[dim]Instruction view is {mode}. Press Ctrl+T to toggle, Enter to continue.[/dim]")
            try:
                ch = click.getchar()
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - defensive guard
                return

            if not self._handle_instruction_toggle_input(agent_id, ch):
                break

        if self._instruction_preview_limit == 0:
            self._instruction_preview_limit = DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT
        self.console.print("")

    def _handle_instruction_toggle_input(self, agent_id: str, ch: str) -> bool:
        """Process a single toggle keypress; return False when the loop should exit."""
        if ch in {"\r", "\n"}:
            return False

        lowered = ch.lower()
        if lowered == "t" or ch == "\x14":  # support literal 't' or Ctrl+T
            self._instruction_preview_limit = (
                DEFAULT_AGENT_INSTRUCTION_PREVIEW_LIMIT if self._instruction_preview_limit == 0 else 0
            )
            self._show_details(agent_id, enable_prompt=False)
            return True

        # Ignore other keys and continue prompting.
        return True

    def _after_agent_run(self) -> None:
        """Handle transcript viewer behaviour after a successful run."""
        payload, manifest = self.session._get_last_transcript()
        if not self._transcript_matches(payload, manifest):
            return
        run_id = str(manifest.get("run_id") or "")
        mark_ready = getattr(self.session, "mark_agent_transcript_ready", None)
        if callable(mark_ready):
            mark_ready(self._agent_id, run_id)
        if self._open_transcript_viewer():
            return
        self.console.print("[dim]Transcript viewer is unavailable in this environment.[/dim]")

    def _transcript_matches(self, payload: Any, manifest: Any) -> bool:
        """Return True when the latest transcript belongs to this agent."""
        if not payload or not isinstance(manifest, dict):
            return False
        if not manifest.get("run_id"):
            return False
        return manifest.get("agent_id") == self._agent_id

    def _open_transcript_viewer(self) -> bool:
        """Launch the transcript viewer when terminal support is available."""
        if not getattr(self.console, "is_terminal", False):
            return False
        try:
            current_agent = getattr(self.session, "_current_agent", None)
            self.session.open_transcript_viewer(announce=True)
            if getattr(self.session.console, "is_terminal", False):
                try:
                    self.session.console.clear()
                except Exception:  # pragma: no cover - defensive cleanup
                    pass
                if current_agent is not None:  # pragma: no cover - UI refresh best effort
                    try:
                        self.session._render_header(current_agent, focus_agent=True)
                    except Exception:  # pragma: no cover - defensive cleanup
                        pass
            return True
        except Exception:  # pragma: no cover - defensive cleanup
            return False

    @contextmanager
    def _bind_session_context(self) -> Any:
        """Temporarily attach this slash session to the Click context."""
        with bind_slash_session_context(self.session.ctx, self.session):
            yield

    def _run_agent(self, agent_id: str, message: str) -> None:
        """Execute the agents run command for the active agent."""
        if not message:
            return

        try:
            self.session.notify_agent_run_started()
            with self._bind_session_context():
                self.session.ctx.invoke(
                    agents_run_command,
                    agent_ref=agent_id,
                    input_text=message,
                    verbose=False,
                )
            self.session.last_run_input = message
            self._after_agent_run()
        except click.ClickException as exc:
            self.console.print(f"[{ERROR_STYLE}]{exc}[/]")
        finally:
            try:
                self.session.notify_agent_run_finished()
            except Exception:
                pass
