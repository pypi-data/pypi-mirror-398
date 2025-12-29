"""Renderer factory helpers for CLI, SDK, and slash sessions.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import io
from dataclasses import dataclass, is_dataclass, replace
from inspect import signature
from typing import Any
from collections.abc import Callable

from rich.console import Console

from glaip_sdk.utils.rendering.renderer.base import RichStreamRenderer
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.state import TranscriptBuffer


@dataclass(slots=True)
class RendererFactoryOptions:
    """Shared options for renderer factories."""

    console: Console | None = None
    cfg_overrides: dict[str, Any] | None = None
    verbose: bool | None = None
    transcript_buffer: TranscriptBuffer | None = None
    callbacks: dict[str, Any] | None = None

    def build(self, factory: Callable[..., RichStreamRenderer]) -> RichStreamRenderer:
        """Instantiate a renderer using the provided factory and stored options."""
        params = signature(factory).parameters
        kwargs: dict[str, Any] = {}
        if self.console is not None and "console" in params:
            kwargs["console"] = self.console
        if self.cfg_overrides is not None and "cfg_overrides" in params:
            kwargs["cfg_overrides"] = self.cfg_overrides
        if self.verbose is not None and "verbose" in params:
            kwargs["verbose"] = self.verbose
        if self.transcript_buffer is not None and "transcript_buffer" in params:
            kwargs["transcript_buffer"] = self.transcript_buffer
        if self.callbacks is not None and "callbacks" in params:
            kwargs["callbacks"] = self.callbacks
        return factory(**kwargs)


def _build_config(base: RendererConfig, overrides: dict[str, Any] | None = None) -> RendererConfig:
    cfg = replace(base) if is_dataclass(base) else base
    if overrides:
        for key, value in overrides.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
    return cfg


def make_default_renderer(
    *,
    console: Console | None = None,
    cfg_overrides: dict[str, Any] | None = None,
    verbose: bool = False,
    transcript_buffer: TranscriptBuffer | None = None,
    callbacks: dict[str, Any] | None = None,
) -> RichStreamRenderer:
    """Create the default renderer used by SDK and CLI flows."""
    cfg = _build_config(RendererConfig(), cfg_overrides)
    return RichStreamRenderer(
        console=console or Console(),
        cfg=cfg,
        verbose=verbose,
        transcript_buffer=transcript_buffer,
        callbacks=callbacks,
    )


def make_verbose_renderer(
    *,
    console: Console | None = None,
    cfg_overrides: dict[str, Any] | None = None,
    transcript_buffer: TranscriptBuffer | None = None,
    callbacks: dict[str, Any] | None = None,
) -> RichStreamRenderer:
    """Create a verbose renderer with snapshot appending disabled."""
    verbose_cfg = RendererConfig(live=True, append_finished_snapshots=False)
    cfg = _build_config(verbose_cfg, cfg_overrides)
    return RichStreamRenderer(
        console=console or Console(),
        cfg=cfg,
        verbose=True,
        transcript_buffer=transcript_buffer,
        callbacks=callbacks,
    )


def make_minimal_renderer(
    *,
    console: Console | None = None,
    cfg_overrides: dict[str, Any] | None = None,
    transcript_buffer: TranscriptBuffer | None = None,
    callbacks: dict[str, Any] | None = None,
) -> RichStreamRenderer:
    """Create a renderer that prints only essential output."""
    minimal_cfg = RendererConfig(live=False, persist_live=False, render_thinking=False)
    cfg = _build_config(minimal_cfg, cfg_overrides)
    return RichStreamRenderer(
        console=console or Console(),
        cfg=cfg,
        verbose=False,
        transcript_buffer=transcript_buffer,
        callbacks=callbacks,
    )


def make_silent_renderer(
    *,
    console: Console | None = None,
    cfg_overrides: dict[str, Any] | None = None,
    transcript_buffer: TranscriptBuffer | None = None,
    callbacks: dict[str, Any] | None = None,
) -> RichStreamRenderer:
    """Create a renderer that suppresses terminal output for background flows."""
    cfg = _build_config(
        RendererConfig(
            live=False,
            persist_live=False,
            render_thinking=False,
        ),
        cfg_overrides,
    )
    silent_console = console or Console(file=io.StringIO(), force_terminal=False)
    return RichStreamRenderer(
        console=silent_console,
        cfg=cfg,
        verbose=False,
        transcript_buffer=transcript_buffer,
        callbacks=callbacks,
    )
