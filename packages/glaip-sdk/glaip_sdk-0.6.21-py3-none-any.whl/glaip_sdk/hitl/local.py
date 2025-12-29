"""Local HITL prompt handler with interactive console support.

Author:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import os
from typing import Any

try:
    from aip_agents.agent.hitl.prompt.base import BasePromptHandler
    from aip_agents.schema.hitl import ApprovalDecision, ApprovalDecisionType, ApprovalRequest
except ImportError as e:
    raise ImportError("aip_agents is required for local HITL. Install with: pip install 'glaip-sdk[local]'") from e

from rich.console import Console
from rich.prompt import Prompt


class LocalPromptHandler(BasePromptHandler):
    """Local HITL prompt handler with interactive console prompts.

    Experimental local HITL implementation with known limitations:
    - Timeouts are not enforced (interactive prompts wait indefinitely)
    - Relies on private renderer methods for pause/resume
    - Only supports interactive terminal environments

    The key insight from Rich documentation is that Live must be stopped before
    using Prompt/input(), otherwise the input won't render properly.

    Environment variables:
        GLAIP_HITL_AUTO_APPROVE: Set to "true" (case-insensitive) to auto-approve
            all requests without user interaction. Useful for integration tests and CI.
    """

    def __init__(self, *, pause_resume_callback: Any | None = None) -> None:
        """Initialize the prompt handler.

        Args:
            pause_resume_callback: Optional callable with pause() and resume() methods
                to control the live renderer during prompts. This is needed because
                Rich Live interferes with Prompt/input().
        """
        super().__init__()
        self._pause_resume = pause_resume_callback
        self._console = Console()

    async def prompt_for_decision(
        self,
        request: ApprovalRequest,
        timeout_seconds: int,
        context_keys: list[str] | None = None,
    ) -> ApprovalDecision:
        """Prompt for approval decision with live renderer pause/resume.

        Supports auto-approval via GLAIP_HITL_AUTO_APPROVE environment variable
        for integration testing and CI environments. Set to "true" (case-insensitive) to enable.
        """
        _ = (timeout_seconds, context_keys)  # Suppress unused parameter warnings.

        # Check for auto-approve mode (for integration tests/CI)
        auto_approve = os.getenv("GLAIP_HITL_AUTO_APPROVE", "").lower() == "true"

        if auto_approve:
            # Auto-approve without user interaction
            return ApprovalDecision(
                request_id=request.request_id,
                decision=ApprovalDecisionType.APPROVED,
                operator_input="auto-approved",
            )

        # Pause the live renderer if callback is available
        if self._pause_resume:
            self._pause_resume.pause()

        try:
            # POC/MVP: Show what we're approving (still auto-approve for now)
            self._print_request_info(request)

            # POC/MVP: For testing, we can do actual input here
            # Uncomment to enable real prompting:
            response = Prompt.ask(
                "\n[yellow]Approve this tool call?[/yellow] [dim](y/n/s)[/dim]",
                console=self._console,
                default="y",
            )
            response = response.lower().strip()

            if response in ("y", "yes"):
                decision = ApprovalDecisionType.APPROVED
            elif response in ("n", "no"):
                decision = ApprovalDecisionType.REJECTED
            else:
                decision = ApprovalDecisionType.SKIPPED

            return ApprovalDecision(
                request_id=request.request_id,
                decision=decision,
                operator_input=response if decision != ApprovalDecisionType.SKIPPED else None,
            )
        finally:
            # Always resume the live renderer
            if self._pause_resume:
                self._pause_resume.resume()

    def _print_request_info(self, request: ApprovalRequest) -> None:
        """Print the approval request information."""
        self._console.print()
        self._console.rule("[yellow]HITL Approval Request[/yellow]", style="yellow")

        tool_name = request.tool_name or "unknown"
        self._console.print(f"[cyan]Tool:[/cyan] {tool_name}")

        if hasattr(request, "arguments_preview") and request.arguments_preview:
            self._console.print(f"[cyan]Arguments:[/cyan] {request.arguments_preview}")

        if request.context:
            self._console.print(f"[dim]Context: {request.context}[/dim]")


class PauseResumeCallback:
    """Simple callback object for pausing/resuming the live renderer.

    This allows the LocalPromptHandler to control the renderer without
    directly coupling to the renderer implementation.
    """

    def __init__(self) -> None:
        """Initialize the callback."""
        self._renderer: Any | None = None

    def set_renderer(self, renderer: Any) -> None:
        """Set the renderer instance.

        Args:
            renderer: RichStreamRenderer instance with pause_live() and resume_live() methods.
        """
        self._renderer = renderer

    def pause(self) -> None:
        """Pause the live renderer before prompting."""
        if self._renderer and hasattr(self._renderer, "_shutdown_live"):
            self._renderer._shutdown_live()

    def resume(self) -> None:
        """Resume the live renderer after prompting."""
        if self._renderer and hasattr(self._renderer, "_ensure_live"):
            self._renderer._ensure_live()


__all__ = ["LocalPromptHandler", "PauseResumeCallback"]
