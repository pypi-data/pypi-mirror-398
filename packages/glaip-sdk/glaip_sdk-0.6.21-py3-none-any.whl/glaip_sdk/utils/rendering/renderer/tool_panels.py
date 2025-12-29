"""Tool panel controller logic extracted from the renderer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from time import monotonic
from typing import Any, TYPE_CHECKING

from rich.console import Console

from glaip_sdk.utils.rendering.layout.panels import create_tool_panel
from glaip_sdk.utils.rendering.layout.progress import format_tool_title, is_delegation_tool
from glaip_sdk.utils.rendering.layout.transcript import DEFAULT_TRANSCRIPT_THEME
from glaip_sdk.utils.rendering.models import Step
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.steps import StepManager

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from glaip_sdk.utils.rendering.renderer.stream import StreamProcessor


class ToolPanelController:
    """Encapsulates tool panel lifecycle management."""

    OUTPUT_PREFIX = "**Output:**\n"

    def __init__(
        self,
        *,
        steps: StepManager,
        stream_processor: StreamProcessor,
        console: Console,
        cfg: RendererConfig,
        step_server_start_times: dict[str, float],
        output_prefix: str | None = None,
    ) -> None:
        """Initialize the tool panel controller.

        Args:
            steps: Step manager instance for tracking steps
            stream_processor: Stream processor for handling events
            console: Rich console instance for rendering
            cfg: Renderer configuration
            step_server_start_times: Dictionary mapping step IDs to server start times
            output_prefix: Optional prefix for tool output (defaults to OUTPUT_PREFIX)
        """
        self._steps = steps
        self._stream_processor = stream_processor
        self._console = console
        self._cfg = cfg
        self._step_server_start_times = step_server_start_times
        self.panels: dict[str, dict[str, Any]] = {}
        self._panel_output_prefix = output_prefix or self.OUTPUT_PREFIX

    # Public API -------------------------------------------------------
    def update_console(self, console: Console) -> None:
        """Update the console reference used for snapshot printing."""
        self._console = console

    def update_config(self, cfg: RendererConfig) -> None:
        """Update configuration reference (useful when overrides occur)."""
        self._cfg = cfg

    def finish_all_panels(self) -> None:
        """Mark all panels as finished (used during cleanup/finalization)."""
        try:
            items = list(self.panels.items())
        except Exception:  # pragma: no cover - defensive guard
            return

        for _sid, meta in items:
            if meta.get("status") != "finished":
                meta["status"] = "finished"

    def handle_agent_step(
        self,
        event: dict[str, Any],
        tool_name: str | None,
        tool_args: Any,
        _tool_out: Any,
        tool_calls_info: list[tuple[str, Any, Any]],
        *,
        tracked_step: Step | None = None,
    ) -> None:
        """Handle agent step tool bookkeeping."""
        metadata = event.get("metadata", {})
        task_id = event.get("task_id") or metadata.get("task_id")
        context_id = event.get("context_id") or metadata.get("context_id")
        content = event.get("content", "")

        if tool_name:
            tool_sid = self._ensure_tool_panel(tool_name, tool_args, task_id, context_id)
            self._start_tool_step(
                task_id,
                context_id,
                tool_name,
                tool_args,
                tool_sid,
                tracked_step=tracked_step,
            )

        self._process_additional_tool_calls(tool_calls_info, tool_name, task_id, context_id)

        (
            is_tool_finished,
            finished_tool_name,
            finished_tool_output,
        ) = self._detect_tool_completion(metadata, content)

        if not (is_tool_finished and finished_tool_name):
            return

        self._finish_tool_panel(finished_tool_name, finished_tool_output, task_id, context_id)
        self._finish_tool_step(
            finished_tool_name,
            finished_tool_output,
            task_id,
            context_id,
            tracked_step=tracked_step,
        )
        self._create_tool_snapshot(finished_tool_name, task_id, context_id)

    # Internal helpers -------------------------------------------------
    def _ensure_tool_panel(self, name: str, args: Any, task_id: str, context_id: str) -> str:
        formatted_title = format_tool_title(name)
        is_delegation = is_delegation_tool(name)
        tool_sid = self._session_id(name, task_id, context_id)

        if tool_sid not in self.panels:
            self.panels[tool_sid] = {
                "title": formatted_title,
                "status": "running",
                "started_at": monotonic(),
                "server_started_at": self._stream_processor.server_elapsed_time,
                "chunks": [],
                "args": args or {},
                "output": None,
                "is_delegation": is_delegation,
            }
            if args:
                try:
                    args_content = "**Args:**\n```json\n" + json.dumps(args, indent=2) + "\n```\n\n"
                except Exception:
                    args_content = f"**Args:**\n{args}\n\n"
                self.panels[tool_sid]["chunks"].append(args_content)

        return tool_sid

    def _start_tool_step(
        self,
        task_id: str,
        context_id: str,
        tool_name: str,
        tool_args: Any,
        _tool_sid: str,
        *,
        tracked_step: Step | None = None,
    ) -> Step | None:
        if tracked_step is not None:
            return tracked_step

        if is_delegation_tool(tool_name):
            step = self._steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="delegate",
                name=tool_name,
                args=tool_args,
            )
        else:
            step = self._steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="tool",
                name=tool_name,
                args=tool_args,
            )

        if step and self._stream_processor.server_elapsed_time is not None:
            self._step_server_start_times[step.step_id] = self._stream_processor.server_elapsed_time

        return step

    def _process_additional_tool_calls(
        self,
        tool_calls_info: list[tuple[str, Any, Any]],
        tool_name: str | None,
        task_id: str,
        context_id: str,
    ) -> None:
        for call_name, call_args, _ in tool_calls_info or []:
            if call_name and call_name != tool_name:
                self._process_single_tool_call(call_name, call_args, task_id, context_id)

    def _process_single_tool_call(self, call_name: str, call_args: Any, task_id: str, context_id: str) -> None:
        self._ensure_tool_panel(call_name, call_args, task_id, context_id)
        step = self._create_step_for_tool_call(call_name, call_args, task_id, context_id)
        if step and self._stream_processor.server_elapsed_time is not None:
            self._step_server_start_times[step.step_id] = self._stream_processor.server_elapsed_time

    def _create_step_for_tool_call(self, call_name: str, call_args: Any, task_id: str, context_id: str) -> Any:
        if is_delegation_tool(call_name):
            return self._steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="delegate",
                name=call_name,
                args=call_args,
            )
        return self._steps.start_or_get(
            task_id=task_id,
            context_id=context_id,
            kind="tool",
            name=call_name,
            args=call_args,
        )

    def _detect_tool_completion(self, metadata: dict[str, Any], content: str) -> tuple[bool, str | None, Any]:
        tool_info = metadata.get("tool_info", {}) if isinstance(metadata, dict) else {}

        if tool_info.get("status") == "finished" and tool_info.get("name"):
            return True, tool_info.get("name"), tool_info.get("output")
        if content and isinstance(content, str) and content.startswith("Completed "):
            tool_name = content.replace("Completed ", "").strip()
            if tool_name:
                output = tool_info.get("output") if tool_info.get("name") == tool_name else None
                return True, tool_name, output
        if metadata.get("status") == "finished" and tool_info.get("name"):
            return True, tool_info.get("name"), tool_info.get("output")
        return False, None, None

    def _finish_tool_panel(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
    ) -> None:
        tool_sid = self._session_id(finished_tool_name, task_id, context_id)
        if tool_sid not in self.panels:
            return

        meta = self.panels[tool_sid]
        self._mark_panel_as_finished(meta, tool_sid)
        self._add_tool_output_to_panel(meta, finished_tool_output, finished_tool_name)

    def _finish_tool_step(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
        *,
        tracked_step: Step | None = None,
    ) -> None:
        if tracked_step is not None:
            return

        duration = self._get_step_duration(finished_tool_name, task_id, context_id)
        if is_delegation_tool(finished_tool_name):
            self._steps.finish(
                task_id=task_id,
                context_id=context_id,
                kind="delegate",
                name=finished_tool_name,
                output=finished_tool_output,
                duration_raw=duration,
            )
            return

        self._steps.finish(
            task_id=task_id,
            context_id=context_id,
            kind="tool",
            name=finished_tool_name,
            output=finished_tool_output,
            duration_raw=duration,
        )

    def _mark_panel_as_finished(self, meta: dict[str, Any], tool_sid: str) -> None:
        if meta.get("status") != "finished":
            meta["status"] = "finished"
            dur = self._calculate_tool_duration(meta)
            self._update_tool_metadata(meta, dur)
        self._stream_processor.current_event_finished_panels.add(tool_sid)

    def _calculate_tool_duration(self, meta: dict[str, Any]) -> float | None:
        started_at = meta.get("server_started_at")
        finished_at = (
            self._stream_processor.server_elapsed_time
            if isinstance(self._stream_processor.server_elapsed_time, (int, float))
            else None
        )
        if not isinstance(started_at, (int, float)) or finished_at is None:
            started_at = meta.get("started_at")
            finished_at = meta.get("finished_at")
        try:
            if isinstance(started_at, (int, float)) and isinstance(finished_at, (int, float)):
                return max(0.0, float(finished_at) - float(started_at))
        except Exception:
            return None
        return None

    def _update_tool_metadata(self, meta: dict[str, Any], dur: float | None) -> None:
        if dur is not None:
            meta["duration_seconds"] = dur
            meta["server_finished_at"] = (
                self._stream_processor.server_elapsed_time
                if isinstance(self._stream_processor.server_elapsed_time, (int, float))
                else None
            )
            meta["finished_at"] = monotonic()

    def _add_tool_output_to_panel(
        self, meta: dict[str, Any], finished_tool_output: Any, finished_tool_name: str
    ) -> None:
        if finished_tool_output is None:
            return
        meta.setdefault("chunks", []).append(self._format_output_block(finished_tool_output, finished_tool_name))
        meta["output"] = finished_tool_output

    def _get_step_duration(self, finished_tool_name: str, task_id: str, context_id: str) -> float | None:
        tool_sid = self._session_id(finished_tool_name, task_id, context_id)
        return self.panels.get(tool_sid, {}).get("duration_seconds")

    def _should_create_snapshot(self, tool_sid: str) -> bool:
        return self._cfg.append_finished_snapshots and not self.panels.get(tool_sid, {}).get("snapshot_printed")

    def _create_tool_snapshot(self, finished_tool_name: str, task_id: str, context_id: str) -> None:
        tool_sid = self._session_id(finished_tool_name, task_id, context_id)
        if not self._should_create_snapshot(tool_sid):
            return

        meta = self.panels[tool_sid]
        adjusted_title = self._get_snapshot_title(meta, finished_tool_name)
        body_text = "".join(meta.get("chunks") or [])
        body_text = self._clamp_snapshot_body(body_text)

        snapshot_panel = create_tool_panel(
            title=adjusted_title,
            content=body_text or "(no output)",
            status="finished",
            theme=self._panel_theme(),
            is_delegation=is_delegation_tool(finished_tool_name),
        )
        self._console.print(snapshot_panel)
        self.panels[tool_sid]["snapshot_printed"] = True

    def _get_snapshot_title(self, meta: dict[str, Any], finished_tool_name: str) -> str:
        adjusted_title = meta.get("title") or finished_tool_name
        dur = meta.get("duration_seconds")
        if isinstance(dur, (int, float)):
            elapsed = self._format_snapshot_duration(dur)
            adjusted_title = f"{adjusted_title}  · {elapsed}"
        return adjusted_title

    def _format_snapshot_duration(self, dur: int | float) -> str:
        try:
            if not isinstance(dur, (int, float)):
                return "<1ms"
            if dur >= 1:
                return f"{dur:.2f}s"
            if int(dur * 1000) > 0:
                return f"{int(dur * 1000)}ms"
            return "<1ms"
        except (TypeError, ValueError, OverflowError):
            return "<1ms"

    def _clamp_snapshot_body(self, body_text: str) -> str:
        max_lines = int(self._cfg.snapshot_max_lines or 0)
        lines = body_text.splitlines()
        if max_lines > 0 and len(lines) > max_lines:
            lines = lines[:max_lines] + ["… (truncated)"]
            body_text = "\n".join(lines)

        max_chars = int(self._cfg.snapshot_max_chars or 0)
        if max_chars > 0 and len(body_text) > max_chars:
            suffix = "\n… (truncated)"
            body_text = body_text[: max_chars - len(suffix)] + suffix

        return body_text

    def _session_id(self, tool_name: str, task_id: str, context_id: str) -> str:
        return f"tool_{tool_name}_{task_id}_{context_id}"

    # Output formatting helpers ---------------------------------------
    def _format_output_block(self, output_value: Any, tool_name: str | None) -> str:
        if isinstance(output_value, (dict, list)):
            return self._format_dict_or_list_output(output_value)
        if isinstance(output_value, str):
            return self._format_string_output(output_value, tool_name)
        return self._format_other_output(output_value)

    def _format_dict_or_list_output(self, output_value: dict | list) -> str:
        try:
            return self._panel_output_prefix + "```json\n" + json.dumps(output_value, indent=2) + "\n```\n"
        except Exception:
            return self._panel_output_prefix + str(output_value) + "\n"

    def _format_string_output(self, output: str, tool_name: str | None) -> str:
        s = output.strip()
        s = self._clean_sub_agent_prefix(s, tool_name)
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            return self._format_json_string_output(s)
        return self._panel_output_prefix + s + "\n"

    def _format_other_output(self, output_value: Any) -> str:
        try:
            return self._panel_output_prefix + json.dumps(output_value, indent=2) + "\n"
        except Exception:
            return self._panel_output_prefix + str(output_value) + "\n"

    def _format_json_string_output(self, output: str) -> str:
        try:
            parsed = json.loads(output)
            return self._panel_output_prefix + "```json\n" + json.dumps(parsed, indent=2) + "\n```\n"
        except Exception:
            return self._panel_output_prefix + output + "\n"

    def _clean_sub_agent_prefix(self, output: str, tool_name: str | None) -> str:
        if not (tool_name and is_delegation_tool(tool_name)):
            return output

        sub = tool_name
        if tool_name.startswith("delegate_to_"):
            sub = tool_name.replace("delegate_to_", "")
        elif tool_name.startswith("delegate_"):
            sub = tool_name.replace("delegate_", "")
        prefix = f"[{sub}]"
        if output.startswith(prefix):
            return output[len(prefix) :].lstrip()
        return output

    def _panel_theme(self) -> str:
        return DEFAULT_TRANSCRIPT_THEME


__all__ = ["ToolPanelController"]
