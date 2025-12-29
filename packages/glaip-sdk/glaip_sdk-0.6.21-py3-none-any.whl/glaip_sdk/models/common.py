"""Common models for AIP SDK.

This module contains common models that don't fit into specific categories.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from pydantic import BaseModel


class LanguageModelResponse(BaseModel):
    """Language model response model."""

    name: str
    provider: str
    description: str | None = None
    capabilities: list[str] | None = None
    max_tokens: int | None = None
    supports_streaming: bool = False


class TTYRenderer:
    """Simple TTY renderer for non-Rich environments."""

    def __init__(self, use_color: bool = True):
        """Initialize the TTY renderer.

        Args:
            use_color: Whether to use color output
        """
        self.use_color = use_color

    def render_message(self, message: str, event_type: str = "message") -> None:
        """Render a message with optional color."""
        if event_type == "error":
            print(f"ERROR: {message}", flush=True)
        elif event_type == "done":
            print(f"\n✅ {message}", flush=True)
        else:
            print(message, flush=True)
