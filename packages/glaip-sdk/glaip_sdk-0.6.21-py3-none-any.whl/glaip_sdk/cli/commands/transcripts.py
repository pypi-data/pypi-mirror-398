"""Transcript commands for inspecting cached agent transcripts.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from glaip_sdk.branding import (
    INFO_STYLE,
    SUCCESS_STYLE,
    WARNING_STYLE,
)
from glaip_sdk.cli.transcript.cache import (
    export_transcript as export_cached_transcript,
)
from glaip_sdk.cli.transcript.history import (
    ClearResult,
    HistoryEntry,
    HistorySnapshot,
    clear_cached_runs,
    coerce_sortable_datetime,
    load_history_snapshot,
)
from glaip_sdk.cli.transcript.viewer import ViewerContext, run_viewer_session
from glaip_sdk.cli.utils import format_size, get_ctx_value, parse_json_line
from glaip_sdk.rich_components import AIPTable
from glaip_sdk.utils.rendering.layout.panels import create_final_panel
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event

console = Console()


def _format_duration(seconds: int | None) -> str:
    """Format elapsed seconds as HH:MM:SS."""
    if seconds is None:
        return "—"
    seconds = int(max(0, seconds))
    delta = timedelta(seconds=seconds)
    total = int(delta.total_seconds())
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_timestamp(value: datetime | None) -> str:
    """Render datetimes in UTC display format."""
    if value is None:
        return "—"
    try:
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def _row_label(entry: HistoryEntry) -> str:
    """Build a run id label with warning markers."""
    suffix = ""
    if entry.warning:
        suffix += " !"
    return f"{entry.run_id}{suffix}"


def _should_use_transcript_viewer(ctx: click.Context | None, target_console: Console, *, force: bool = False) -> bool:
    """Return True if the interactive transcript viewer should be launched."""
    if not target_console.is_terminal:
        return False
    if force:
        return True

    selected_view = get_ctx_value(ctx, "view", "rich") if ctx else "rich"
    if selected_view != "rich":
        return False
    if ctx is not None and not bool(get_ctx_value(ctx, "tty", True)):
        return False
    try:
        return bool(sys.stdin.isatty() and sys.stdout.isatty())
    except Exception:
        return False


def _coerce_timestamp_to_float(value: Any) -> float | None:
    """Convert assorted timestamp formats to epoch seconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return None
    if isinstance(value, datetime):
        try:
            return value.timestamp()
        except Exception:
            return None
    if isinstance(value, str):
        try:
            text = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
            return parsed.timestamp()
        except ValueError:
            return None
    return None


def _build_viewer_context(
    entry: HistoryEntry, meta: dict[str, Any] | None, events: list[dict[str, Any]]
) -> ViewerContext:
    """Create a ViewerContext payload for the cached transcript."""
    manifest_entry = dict(entry.manifest or {})
    if entry.run_id and not manifest_entry.get("run_id"):
        manifest_entry["run_id"] = entry.run_id

    meta_payload = dict(meta or {})
    default_output = str(meta_payload.get("default_output") or meta_payload.get("renderer_output") or "")
    final_output = str(meta_payload.get("final_output") or "")

    started_hint = meta_payload.get("started_at") or entry.started_at or entry.started_at_iso
    stream_started_at = _coerce_timestamp_to_float(started_hint)

    return ViewerContext(
        manifest_entry=manifest_entry,
        events=list(events),
        default_output=default_output,
        final_output=final_output,
        stream_started_at=stream_started_at,
        meta=meta_payload,
    )


def _launch_transcript_viewer(
    entry: HistoryEntry,
    meta: dict[str, Any] | None,
    events: list[dict[str, Any]],
    *,
    console_override: Console | None = None,
    initial_view: str = "default",
) -> bool:
    """Launch the transcript viewer for a cached run."""
    if not entry.run_id:
        return False

    target_console = console_override or console
    viewer_ctx = _build_viewer_context(entry, meta, events)

    def _export(destination: Path) -> Path:
        """Export cached transcript to destination.

        Args:
            destination: Path to export transcript to.

        Returns:
            Path to exported transcript file.
        """
        return export_cached_transcript(destination=destination, run_id=entry.run_id)

    run_viewer_session(target_console, viewer_ctx, _export, initial_view=initial_view)
    return True


def _maybe_launch_transcript_viewer(
    ctx: click.Context | None,
    entry: HistoryEntry,
    meta: dict[str, Any] | None,
    events: list[dict[str, Any]],
    *,
    console_override: Console | None = None,
    force: bool = False,
    initial_view: str = "default",
) -> bool:
    """Launch the transcript viewer when the environment supports it."""
    target_console = console_override or console
    if not _should_use_transcript_viewer(ctx, target_console, force=force):
        return False
    try:
        _launch_transcript_viewer(
            entry,
            meta,
            events,
            console_override=target_console,
            initial_view=initial_view,
        )
        return True
    except Exception:
        return False


def _build_table(entries: Iterable[HistoryEntry]) -> AIPTable:
    """Create the Rich table used by both CLI and slash history commands."""
    table = AIPTable(title="Agent run cache", expand=True)
    table.add_column("Run ID", style="bold")
    table.add_column("Agent")
    table.add_column("Agent ID")
    table.add_column("API URL")
    table.add_column("Started (UTC)")
    table.add_column("Duration")
    table.add_column("Size")

    for entry in entries:
        row_style = WARNING_STYLE if entry.warning else None
        if entry.status == "cached":
            size_value = entry.size_bytes or 0
            size_text = format_size(size_value)
        else:
            size_text = "—"
        table.add_row(
            _row_label(entry),
            entry.agent_name or "—",
            entry.agent_id or "—",
            entry.api_url or "—",
            _format_timestamp(entry.started_at),
            _format_duration(entry.duration_seconds),
            size_text,
            style=row_style,
        )
    return table


def _emit_warnings(snapshot: HistorySnapshot) -> None:
    """Print warning strings associated with a snapshot."""
    for warning in snapshot.warnings:
        console.print(f"[{WARNING_STYLE}]{warning}[/]")


def _abbreviate_path(path: Path | None) -> str:
    """Return a cache path with the home directory abbreviated to `~`."""
    if path is None:
        return "—"

    raw = str(path)
    try:
        home = Path.home()
        home_str = str(home)
    except Exception:
        return raw

    if home_str and raw.startswith(home_str):
        suffix = raw[len(home_str) :]
        if suffix.startswith("/"):
            suffix = suffix[1:]
        return f"~/{suffix}" if suffix else "~"
    return raw


def _parse_transcript_line(raw_line: str) -> dict[str, Any] | None:
    """Parse a JSONL transcript line into a dictionary payload."""
    return parse_json_line(raw_line)


def _decode_transcript(contents: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Decode transcript JSONL contents into meta and event payloads."""
    meta: dict[str, Any] | None = None
    events: list[dict[str, Any]] = []

    for payload in filter(None, (_parse_transcript_line(line) for line in contents.splitlines())):
        kind = payload.get("type")
        if kind == "meta" and meta is None:
            meta = payload
            continue
        if kind == "event":
            event = payload.get("event")
            if isinstance(event, dict):
                events.append(event)

    return meta, events


def _render_transcript_display(
    entry: HistoryEntry,
    manifest_path: Path,
    transcript_path: Path,
    meta: dict[str, Any] | None,
    events: list[dict[str, Any]],
) -> str:
    """Return a Rich-formatted transcript stream similar to transcript mode."""
    buffer = StringIO()
    width = console.width or 120
    view_console = Console(
        file=buffer,
        force_terminal=True,
        color_system=console.color_system,
        width=width,
        soft_wrap=True,
    )

    header = (
        f"[dim]Manifest: {manifest_path} · {entry.run_id or '—'} · "
        f"{_abbreviate_path(transcript_path)} · {len(events)} events[/]"
    )
    view_console.print(header)
    view_console.print()

    final_text = None
    if meta:
        final_text = meta.get("final_output") or meta.get("default_output")
    if final_text:
        view_console.print(create_final_panel(final_text, title="Final Result", theme="dark"))
        view_console.print()

    view_console.print("[bold]Transcript Events[/bold]")
    if not events:
        view_console.print("[dim]No SSE events were captured for this run.[/dim]")
    else:
        view_console.print("[dim]────────────────────────────────────────────────────────[/dim]")
        baseline: datetime | None = None
        for event in events:
            received = _parse_event_received_timestamp(event)
            if baseline is None and received is not None:
                baseline = received
            render_debug_event(event, view_console, received_ts=received, baseline_ts=baseline)
    view_console.print()

    return buffer.getvalue()


def _render_transcript_jsonl(
    entry: HistoryEntry,
    manifest_path: Path,
    transcript_path: Path,
    contents: str,
) -> str:
    """Return a plain-text transcript stream that mirrors the cached JSONL payload."""
    header = f"Manifest: {manifest_path} · {entry.run_id or '—'} · {_abbreviate_path(transcript_path)}"
    normalized = contents if contents.endswith("\n") else contents + "\n"
    return f"{header}\n{normalized}"


def _parse_event_received_timestamp(event: dict[str, Any]) -> datetime | None:
    """Extract received timestamp metadata from an SSE event."""
    metadata = event.get("metadata") or {}
    ts_value = metadata.get("received_at") or event.get("received_at")
    if not ts_value:
        return None
    if isinstance(ts_value, datetime):
        return ts_value if ts_value.tzinfo else ts_value.replace(tzinfo=timezone.utc)
    if isinstance(ts_value, str):
        try:
            text = ts_value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _resolve_transcript_path(entry: HistoryEntry) -> Path:
    """Locate the cached transcript for a manifest entry or raise a helpful error."""
    target = entry.resolved_path or entry.expected_path
    if target is None:
        raise click.ClickException(
            f"Manifest entry for run {entry.run_id or '?'} does not include a transcript filename."
        )
    if not target.exists():
        run_label = entry.run_id or "?"
        hint = entry.run_id or "<RUN_ID>"
        location = _abbreviate_path(target)
        raise click.ClickException(
            f"Transcript file missing for run {run_label} (expected {location}). "
            f"Run `aip transcripts clear --id {hint}` to reconcile the manifest."
        )
    return target


def _load_transcript_text(entry: HistoryEntry) -> tuple[Path, str]:
    """Read the cached transcript file into memory."""
    path = _resolve_transcript_path(entry)
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise click.ClickException(
            f"Transcript file missing for run {entry.run_id or '?'} (expected {path})."
        ) from None
    except OSError as exc:  # Permission problems, etc.
        raise click.ClickException(f"Failed to read cached transcript {path}: {exc}") from exc
    return path, contents


def _transcripts_payload(snapshot: HistorySnapshot) -> dict:
    """Convert a snapshot into the JSON payload returned by `aip transcripts --json`."""
    rows = []
    for entry in snapshot.entries:
        row = {
            "run_id": entry.run_id,
            "started_at": entry.started_at_iso,
            "finished_at": entry.finished_at_iso,
            "agent_name": entry.agent_name,
            "agent_id": entry.agent_id,
            "api_url": entry.api_url,
            "duration_seconds": entry.duration_seconds,
            "size_bytes": entry.size_bytes,
            "status": entry.status,
            "warning": entry.warning,
        }
        rows.append(row)

    return {
        "manifest_path": str(snapshot.manifest_path),
        "limit_requested": snapshot.limit_requested,
        "limit_applied": snapshot.limit_applied,
        "limit_clamped": snapshot.limit_clamped,
        "total_entries": snapshot.total_entries,
        "cached_entries": snapshot.cached_entries,
        "total_size_bytes": snapshot.total_size_bytes,
        "warnings": list(snapshot.warnings),
        "migration_summary": snapshot.migration_summary,
        "rows": rows,
    }


def _print_snapshot(snapshot: HistorySnapshot) -> None:
    """Render the textual history view for the standard CLI."""
    if snapshot.cached_entries == 0:
        console.print(f"[{WARNING_STYLE}]No cached transcripts found. Try running an agent first.[/]")
        console.print(f"[dim]Manifest: {snapshot.manifest_path}[/]")
        if snapshot.total_entries and snapshot.warnings:
            _emit_warnings(snapshot)
        return

    header = (
        f"[dim]Manifest: {snapshot.manifest_path} · {snapshot.total_entries} runs · "
        f"{format_size(snapshot.total_size_bytes)} used"
    )
    if snapshot.limit_applied and snapshot.total_entries > snapshot.limit_applied:
        header += (
            f" · showing {len(snapshot.entries)} of {snapshot.total_entries} runs (limit={snapshot.limit_applied})"
        )
    console.print(header)

    if snapshot.limit_clamped:
        console.print(
            f"[{WARNING_STYLE}]Requested limit exceeded maximum. Showing first {snapshot.limit_applied} runs.[/]"
        )

    if snapshot.migration_summary:
        console.print(f"[{INFO_STYLE}]{snapshot.migration_summary}[/]")

    _emit_warnings(snapshot)

    table = _build_table(snapshot.entries)
    console.print(table)
    console.print("[dim]! Missing transcript[/]")


def _render_detail_view(ctx: click.Context | None, snapshot: HistorySnapshot, run_id: str) -> None:
    """Render the cached transcript for a specific run."""
    entry = snapshot.index.get(run_id)
    if entry is None:
        raise click.ClickException(f"Run id {run_id} was not found in {snapshot.manifest_path}.")

    path, contents = _load_transcript_text(entry)

    meta, events = _decode_transcript(contents)
    if _maybe_launch_transcript_viewer(ctx, entry, meta, events, force=True, initial_view="transcript"):
        if snapshot.migration_summary:
            console.print(f"[{INFO_STYLE}]{snapshot.migration_summary}[/]")
        _emit_warnings(snapshot)
        return

    if snapshot.migration_summary:
        console.print(f"[{INFO_STYLE}]{snapshot.migration_summary}[/]")
    _emit_warnings(snapshot)
    transcript_view = _render_transcript_jsonl(entry, snapshot.manifest_path, path, contents)
    click.echo_via_pager(transcript_view)


def _render_history_overview(snapshot: HistorySnapshot, emit_json: bool) -> None:
    """Render the standard history table or its JSON payload."""
    if emit_json:
        payload = _transcripts_payload(snapshot)
        click.echo(json.dumps(payload, indent=2, default=str))
        for warning in snapshot.warnings:
            click.echo(warning, err=True)
        return

    _print_snapshot(snapshot)


@click.group("transcripts", invoke_without_command=True)
@click.option("--limit", type=int, help="Maximum runs to display (default 10).")
@click.option("--json", "as_json", is_flag=True, help="Return machine-friendly JSON output.")
@click.option("--detail", "detail_run_id", metavar="RUN_ID", help="Show cached transcript details for a run id.")
@click.pass_context
def transcripts_group(ctx: click.Context, limit: int | None, as_json: bool, detail_run_id: str | None) -> None:
    """Inspect and manage cached agent transcripts."""
    if ctx.invoked_subcommand or ctx.resilient_parsing:
        return

    snapshot = load_history_snapshot(limit=limit, ctx=ctx)

    view = None
    ctx_obj = ctx.obj if isinstance(ctx.obj, dict) else {}
    if ctx_obj:
        view = ctx_obj.get("view")

    emit_json = as_json or view == "json"

    if detail_run_id:
        if emit_json:
            raise click.UsageError("--json output is only available for the history table view.")
        _render_detail_view(ctx, snapshot, detail_run_id)
        return

    _render_history_overview(snapshot, emit_json)


@transcripts_group.command("detail")
@click.argument("run_id")
@click.pass_context
def transcripts_detail(ctx: click.Context, run_id: str) -> None:
    """Show cached transcript details for a specific run id."""
    snapshot = load_history_snapshot(ctx=ctx)
    view = ctx.obj.get("view") if isinstance(ctx.obj, dict) else None
    if view == "json":
        raise click.UsageError("`aip transcripts detail` only supports the default view.")
    _render_detail_view(ctx, snapshot, run_id)


def _collect_targets(
    snapshot: HistorySnapshot,
    run_ids: Sequence[str] | None,
    delete_all: bool,
) -> tuple[list[HistoryEntry], list[str]]:
    """Return the HistoryEntry objects that should be deleted plus any missing ids."""
    if delete_all:
        runs = sorted(
            snapshot.index.values(),
            key=lambda entry: coerce_sortable_datetime(entry.started_at),
            reverse=False,
        )
        return runs, []

    ordered: list[str] = []
    seen: set[str] = set()
    for run_id in run_ids or ():
        if run_id in seen:
            continue
        seen.add(run_id)
        ordered.append(run_id)

    found: list[HistoryEntry] = []
    missing: list[str] = []
    for run_id in ordered:
        entry = snapshot.index.get(run_id)
        if entry is None:
            missing.append(run_id)
        else:
            found.append(entry)
    return found, missing


def _build_deletion_preview_payload(entries: Iterable[HistoryEntry]) -> list[dict[str, Any]]:
    """Build the payload list for deletion preview."""
    payload = []
    for entry in entries:
        size_text = format_size(entry.size_bytes or 0) if entry.status == "cached" else "—"
        status_text = "Missing file" if entry.warning else "Cached"
        payload.append(
            {
                "run_id": entry.run_id,
                "agent_name": entry.agent_name or "—",
                "agent_id": entry.agent_id or "—",
                "started_at": _format_timestamp(entry.started_at),
                "size": size_text,
                "status": status_text,
            }
        )
    return payload


def _format_timestamp_display(timestamp_raw: Any) -> str:
    """Format timestamp for display in deletion preview."""
    if timestamp_raw in (None, "—"):
        return "—"
    try:
        timestamp_value = str(timestamp_raw).strip()
    except Exception:
        timestamp_value = str(timestamp_raw)
    return f"{timestamp_value} UTC" if timestamp_value else "—"


def _render_deletion_preview_rich(payload: list[dict[str, Any]], manifest_path: Path) -> None:
    """Render deletion preview in rich format."""
    console.print("Transcripts slated for deletion:")
    console.print(f"[dim]Manifest: {_abbreviate_path(manifest_path)}[/]")
    for row in payload:
        timestamp_display = _format_timestamp_display(row["started_at"])
        status_suffix = " (file missing)" if row["status"] == "Missing file" else ""
        console.print(
            f"  • {row['run_id'] or '—'}  {row['agent_name'] or '—'}  {timestamp_display}  {row['size']}{status_suffix}"
        )


def _render_deletion_preview(
    ctx: click.Context,
    entries: Iterable[HistoryEntry],
    manifest_path: Path,
    *,
    delete_all: bool,
    reclaimed_hint: int,
) -> None:
    """Display a preview of the transcripts that are about to be purged."""
    entry_list = list(entries)
    view = get_ctx_value(ctx, "view", "rich")

    if delete_all:
        summary = {
            "manifest_path": str(manifest_path),
            "delete_all": True,
            "entry_count": len(entry_list),
            "estimated_reclaimed_bytes": reclaimed_hint,
        }
        if view == "json":
            click.echo(json.dumps(summary, indent=2, default=str))
            return

        console.print("Transcripts slated for deletion:")
        console.print(f"[dim]Manifest: {_abbreviate_path(manifest_path)}[/]")
        console.print(
            f"[{WARNING_STYLE}]This will remove ALL cached transcripts ({len(entry_list)} entries, "
            f"{format_size(reclaimed_hint)} reclaimed).[/]"
        )
        console.print("[dim]Use `aip transcripts clear --id <run_id>` to delete specific runs.[/]")
        return

    payload = _build_deletion_preview_payload(entry_list)
    preview = {"manifest_path": str(manifest_path), "transcripts": payload}
    if view == "json":
        click.echo(json.dumps(preview, indent=2, default=str))
    else:
        _render_deletion_preview_rich(payload, manifest_path)


def _confirm_deletion(
    ctx: click.Context,
    entries: list[HistoryEntry],
    reclaimed_hint: int,
    delete_all: bool,
    skip_prompt: bool,
    manifest_path: Path,
) -> bool:
    """Prompt the user for confirmation before deleting transcripts."""
    if skip_prompt:
        return True

    size_text = format_size(reclaimed_hint)
    if delete_all:
        console.print(
            f"[{WARNING_STYLE}]Deleting ALL cached transcripts ({len(entries)} entries, {size_text} reclaimed).[/]"
        )
    else:
        console.print(
            f"[{WARNING_STYLE}]You are about to delete {len(entries)} cached transcript(s) ({size_text} reclaimed).[/]"
        )
    _render_deletion_preview(
        ctx,
        entries,
        manifest_path,
        delete_all=delete_all,
        reclaimed_hint=reclaimed_hint,
    )
    return click.confirm("Proceed?", default=False)


def _handle_clear_result(result: ClearResult) -> None:
    """Summarise the result of a cache sweep."""
    removed_count = len(result.removed_entries)
    reclaimed_text = format_size(result.reclaimed_bytes)
    console.print(f"[{SUCCESS_STYLE}]Deleted {removed_count} transcript(s), reclaimed {reclaimed_text}.[/]")
    if result.not_found:
        console.print(f"[{WARNING_STYLE}]The following run id(s) were not found: {', '.join(result.not_found)}[/]")
    for warning in result.warnings:
        console.print(f"[{WARNING_STYLE}]{warning}[/]")
    if result.cache_empty:
        console.print(f"[{SUCCESS_STYLE}]Cache folder now clean. Future runs will repopulate history.[/]")


def _validate_clear_options(run_ids: tuple[str, ...], delete_all: bool) -> None:
    """Ensure --all/--id input combinations are valid."""
    if delete_all and run_ids:
        raise click.UsageError("Use either --all or --id, not both.")
    if not delete_all and not run_ids:
        raise click.UsageError("Specify --all to delete everything or provide at least one --id.")


def _should_exit_for_targets(
    *,
    delete_all: bool,
    targets: list[HistoryEntry],
    missing: list[str],
) -> bool:
    """Return True when deletion should stop due to empty or invalid selections."""
    if delete_all and not targets:
        console.print(f"[{WARNING_STYLE}]Cache is already empty.[/]")
        return True
    if not delete_all and not targets:
        console.print(f"[{WARNING_STYLE}]No matching transcript ids were found.[/]")
        if missing:
            console.print(f"[{WARNING_STYLE}]Unknown run ids: {', '.join(missing)}[/]")
        return True
    return False


@transcripts_group.command("clear")
@click.argument("run_ids_args", nargs=-1)
@click.option("--id", "run_ids", multiple=True, help="Run ID to delete (repeatable).")
@click.option("--all", "delete_all", is_flag=True, help="Delete all cached transcripts.")
@click.option("--yes", "assume_yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def transcripts_clear(
    ctx: click.Context,
    run_ids_args: tuple[str, ...],
    run_ids: tuple[str, ...],
    delete_all: bool,
    assume_yes: bool,
) -> None:
    """Delete cached transcript files by run id or sweep the entire cache."""
    identifiers = tuple(list(run_ids) + list(run_ids_args))

    _validate_clear_options(identifiers, delete_all)
    snapshot = load_history_snapshot(ctx=ctx)

    targets, missing = _collect_targets(snapshot, identifiers, delete_all)
    if _should_exit_for_targets(delete_all=delete_all, targets=targets, missing=missing):
        return

    total_estimated_bytes = sum(entry.size_bytes or 0 for entry in targets)

    if missing:
        console.print(f"[{WARNING_STYLE}]Unknown run ids: {', '.join(missing)}[/]")

    if not _confirm_deletion(
        ctx,
        targets,
        total_estimated_bytes,
        delete_all,
        assume_yes,
        snapshot.manifest_path,
    ):
        console.print("[dim]Aborted. Cache unchanged.[/]")
        return

    result = clear_cached_runs(None if delete_all else list(identifiers))
    _handle_clear_result(result)
