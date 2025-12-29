"""Human-in-the-Loop (HITL) utilities for glaip-sdk.

This package provides utilities for HITL approval workflows in both local
and remote agent execution modes.

For local development, LocalPromptHandler is automatically injected when
agent_config.hitl_enabled is True. No manual setup required.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from glaip_sdk.hitl.local import LocalPromptHandler, PauseResumeCallback

__all__ = ["LocalPromptHandler", "PauseResumeCallback"]
