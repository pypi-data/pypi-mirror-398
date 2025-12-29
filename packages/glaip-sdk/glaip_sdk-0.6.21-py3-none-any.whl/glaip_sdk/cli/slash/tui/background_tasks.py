"""Shared mixin for tracking background asyncio tasks in Textual apps.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any


class BackgroundTaskMixin:
    """Mixin that tracks background tasks and cleans them up on unmount."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize task tracking set for derived Textual apps."""
        super().__init__(*args, **kwargs)
        self._pending_tasks: set[asyncio.Task[Any]] = set()

    def track_task(
        self,
        coro: Coroutine[Any, Any, Any],
        *,
        on_error: Callable[[Exception], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> asyncio.Task[Any]:
        """Create and track a background task with optional error handling."""
        task = asyncio.create_task(coro)
        self._pending_tasks.add(task)

        def _cleanup(finished: asyncio.Task[Any]) -> None:
            self._pending_tasks.discard(finished)
            if finished.cancelled():
                return
            try:
                exc = finished.exception()
            except Exception:
                return
            if exc:
                if on_error:
                    on_error(exc)
                elif logger:
                    logger.debug("Background task failed", exc_info=exc)

        task.add_done_callback(_cleanup)
        return task

    def on_unmount(self) -> None:  # pragma: no cover - UI lifecycle hook
        """Ensure background tasks are cleaned up on exit."""
        pending = [task for task in self._pending_tasks if not task.done()]
        for task in pending:
            try:
                task.cancel()
            except Exception:
                continue
        if pending:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                try:
                    loop.create_task(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
        self._pending_tasks.clear()
        parent_on_unmount = getattr(super(), "on_unmount", None)
        if callable(parent_on_unmount):
            parent_on_unmount()  # type: ignore[misc]
