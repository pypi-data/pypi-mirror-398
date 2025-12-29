"""Utilities for inspecting and cleaning cached agent run transcripts.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glaip_sdk.cli.config import load_config
from glaip_sdk.cli.transcript.cache import (  # Reuse helpers even if marked private
    MANIFEST_FILENAME,
    _compute_duration_seconds,  # type: ignore[attr-defined]
    _timestamp_to_iso,  # type: ignore[attr-defined]
    ensure_cache_dir,
    load_manifest_entries,
    manifest_path,
    transcript_path_candidates,
    write_manifest,
)
from glaip_sdk.cli.utils import parse_json_line
from glaip_sdk.utils.datetime_helpers import coerce_datetime

DEFAULT_HISTORY_LIMIT = 10
MAX_HISTORY_LIMIT = 200
LEGACY_MANIFEST_KEYS: tuple[str, ...] = ("created_at", "source", "server_run_id")
UTC_MIN = datetime.min.replace(tzinfo=timezone.utc)


def coerce_sortable_datetime(value: datetime | None) -> datetime:
    """Return a timezone-aware datetime for sorting, using UTC minimum as fallback."""
    if value is None:
        return UTC_MIN
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _safe_resolve(path: Path) -> Path:
    """Resolve a path while tolerating filesystem errors."""
    try:
        return path.resolve()
    except OSError:
        return path


@dataclass(slots=True)
class HistoryEntry:
    """Normalised entry describing a cached transcript run."""

    run_id: str
    agent_name: str | None
    agent_id: str | None
    api_url: str | None
    started_at: datetime | None
    started_at_iso: str | None
    finished_at: datetime | None
    finished_at_iso: str | None
    duration_seconds: int | None
    size_bytes: int | None
    filename: str | None
    status: str
    warning: str | None
    migration_notice: str | None
    is_current_session: bool
    expected_path: Path | None
    resolved_path: Path | None
    manifest: dict[str, Any]


@dataclass(slots=True)
class NormalizedEntry:
    """Internal representation of a manifest row post normalisation."""

    persisted: dict[str, Any]
    history: HistoryEntry
    changed: bool
    warnings: list[str]
    resolved_path: Path | None


@dataclass(slots=True)
class TimelineInfo:
    """Computed timestamp snapshot for a manifest entry."""

    started_iso: str | None
    finished_iso: str | None
    started_source: Any
    finished_source: Any
    changed: bool


@dataclass(slots=True)
class HistorySnapshot:
    """Collection of history entries and aggregate stats for presentation."""

    manifest_path: Path
    entries: list[HistoryEntry]
    total_entries: int
    cached_entries: int
    total_size_bytes: int
    index: dict[str, HistoryEntry]
    warnings: list[str]
    migration_summary: str | None
    limit_requested: int
    limit_applied: int
    limit_clamped: bool


@dataclass(slots=True)
class ClearResult:
    """Result of clearing cached transcripts from disk and manifest."""

    manifest_path: Path
    removed_entries: list[HistoryEntry]
    not_found: list[str]
    warnings: list[str]
    reclaimed_bytes: int
    cache_empty: bool


def _dedupe_run_id(run_id: str, existing: set[str]) -> str:
    """Ensure run identifiers remain unique when synthesising orphan entries."""
    candidate = run_id or "run"
    if candidate not in existing:
        existing.add(candidate)
        return candidate

    base = candidate
    counter = 2
    while True:
        candidate = f"{base}-{counter}"
        if candidate not in existing:
            existing.add(candidate)
            return candidate
        counter += 1


def _load_transcript_meta(path: Path) -> dict[str, Any] | None:
    """Read the metadata header from a cached transcript file."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            line = fh.readline()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    payload = parse_json_line(line)
    if payload and payload.get("type") == "meta":
        return payload
    return None


def _to_int(value: Any) -> int | None:
    """Safely coerce numeric-like values to integers."""
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _resolve_cached_paths(entry: dict[str, Any], directory: Path) -> tuple[Path | None, Path | None]:
    """Return (resolved, expected) transcript paths for a manifest entry."""
    candidates = transcript_path_candidates(entry, directory)
    resolved = next((path for path in candidates if path.exists()), None)
    expected = candidates[0] if candidates else None
    return resolved, expected


def _ensure_filename_field(entry: dict[str, Any], resolved: Path | None, expected: Path | None) -> bool:
    """Ensure manifest rows include a filename pointing at the cached transcript."""
    filename = entry.get("filename")
    target = filename
    if resolved is not None:
        target = resolved.name
    elif expected is not None:
        target = expected.name
    if target and target != filename:
        entry["filename"] = target
        return True
    return False


def _normalise_cache_path(entry: dict[str, Any], *, directory: Path, resolved: Path | None) -> bool:
    """Ensure cache_path points to fallback locations outside the active cache directory."""
    cache_path = entry.get("cache_path")
    changed = False

    target_path: Path | None = resolved
    if target_path is None and cache_path:
        target_path = Path(str(cache_path)).expanduser()

    if target_path is None:
        if cache_path is not None:
            entry.pop("cache_path", None)
            return True
        return False

    directory_root = _safe_resolve(directory)
    target_root = _safe_resolve(target_path.parent)

    should_keep_cache_path = True
    try:
        should_keep_cache_path = not directory_root.samefile(target_root)
    except (OSError, AttributeError):
        should_keep_cache_path = directory_root != target_root

    if should_keep_cache_path:
        cache_value = str(target_path)
        if cache_value != cache_path:
            entry["cache_path"] = cache_value
            changed = True
    elif cache_path is not None:
        entry.pop("cache_path", None)
        changed = True

    if not entry.get("filename"):
        entry["filename"] = target_path.name
        changed = True

    return changed


def _prune_legacy_fields(entry: dict[str, Any]) -> bool:
    """Remove legacy manifest keys after migrations complete."""
    removed = False
    for key in LEGACY_MANIFEST_KEYS:
        if entry.pop(key, None) is not None:
            removed = True
    return removed


def _select_meta_value(entry: dict[str, Any], meta: dict[str, Any] | None, key: str) -> Any:
    """Return the preferred value for a manifest key from meta or entry data."""
    if meta and meta.get(key) not in (None, ""):
        return meta[key]
    return entry.get(key)


def _normalise_timestamps(entry: dict[str, Any], meta: dict[str, Any] | None) -> TimelineInfo:
    """Normalise started/finished timestamps and return a timeline snapshot."""
    changed = False

    started_source = _select_meta_value(entry, meta, "started_at") or entry.get("created_at")
    started_iso = _timestamp_to_iso(started_source) if started_source is not None else None
    if started_iso is None:
        created_fallback = entry.get("created_at")
        started_iso = _timestamp_to_iso(created_fallback)
        if started_iso is None and isinstance(created_fallback, str):
            started_iso = created_fallback
    if started_iso and started_iso != entry.get("started_at"):
        entry["started_at"] = started_iso
        changed = True

    finished_source = _select_meta_value(entry, meta, "finished_at")
    finished_iso = _timestamp_to_iso(finished_source) if finished_source is not None else None
    if finished_iso and finished_iso != entry.get("finished_at"):
        entry["finished_at"] = finished_iso
        changed = True

    return TimelineInfo(
        started_iso=entry.get("started_at"),
        finished_iso=entry.get("finished_at"),
        started_source=started_source if started_source is not None else entry.get("started_at"),
        finished_source=finished_source if finished_source is not None else entry.get("finished_at"),
        changed=changed,
    )


def _ensure_duration(entry: dict[str, Any], timeline: TimelineInfo) -> bool:
    """Populate duration_seconds when both timestamps are available."""
    duration = entry.get("duration_seconds")
    if duration not in (None, "", 0):
        return False
    computed = _compute_duration_seconds(timeline.started_source, timeline.finished_source)
    if computed is None:
        return False
    entry["duration_seconds"] = computed
    return True


def _merge_meta_fields(entry: dict[str, Any], meta: dict[str, Any] | None, keys: tuple[str, ...]) -> bool:
    """Overlay metadata attributes from the transcript header."""
    if not meta:
        return False
    changed = False
    for key in keys:
        value = meta.get(key)
        if value is None:
            continue
        if entry.get(key) != value:
            entry[key] = value
            changed = True
    return changed


def _resolve_size(entry: dict[str, Any], resolved: Path | None) -> tuple[int, bool]:
    """Return (size_bytes, changed) for a manifest entry."""
    try:
        size_bytes = resolved.stat().st_size if resolved else _to_int(entry.get("size_bytes")) or 0
    except OSError:
        size_bytes = _to_int(entry.get("size_bytes")) or 0

    current = _to_int(entry.get("size_bytes"))
    return size_bytes, current != size_bytes


def _resolve_entry_warning(
    entry: dict[str, Any], resolved: Path | None, expected: Path | None
) -> tuple[str | None, list[str]]:
    """Determine warning code and text for manifest anomalies."""
    if resolved is not None:
        return None, []
    warnings = []
    if expected is not None:
        run_label = entry.get("run_id") or "?"
        hint = entry.get("run_id") or "<RUN_ID>"
        warnings.append(
            f"Transcript file missing for run {run_label} (expected {expected}). "
            f"Run `aip transcripts clear --id {hint}` or `aip transcripts clear --all` to remove stale entries."
        )
    return "transcript_missing", warnings


def _build_history_entry(
    entry: dict[str, Any],
    *,
    resolved: Path | None,
    expected: Path | None,
    warning: str | None,
    current_run_id: str | None,
    timeline: TimelineInfo,
) -> HistoryEntry:
    """Create a HistoryEntry from normalised manifest data."""
    started_iso = timeline.started_iso
    finished_iso = timeline.finished_iso
    return HistoryEntry(
        run_id=str(entry.get("run_id") or ""),
        agent_name=entry.get("agent_name"),
        agent_id=entry.get("agent_id"),
        api_url=entry.get("api_url"),
        started_at=coerce_datetime(started_iso),
        started_at_iso=str(started_iso) if started_iso is not None else None,
        finished_at=coerce_datetime(finished_iso),
        finished_at_iso=str(finished_iso) if finished_iso is not None else None,
        duration_seconds=_to_int(entry.get("duration_seconds")),
        size_bytes=_to_int(entry.get("size_bytes")),
        filename=entry.get("filename"),
        status="cached" if resolved is not None else "missing",
        warning=warning,
        migration_notice=entry.get("migration_notice"),
        is_current_session=bool(current_run_id and history_run_id_eq(entry, current_run_id)),
        expected_path=expected,
        resolved_path=resolved,
        manifest=entry,
    )


def _normalise_entry(
    entry: dict[str, Any],
    *,
    directory: Path,
    current_run_id: str | None,
) -> NormalizedEntry:
    """Normalise an existing manifest entry against on-disk metadata."""
    persisted = dict(entry)
    warnings: list[str] = []
    changed = False

    resolved_path, expected_path = _resolve_cached_paths(persisted, directory)
    if _ensure_filename_field(persisted, resolved_path, expected_path):
        changed = True
    if _normalise_cache_path(persisted, directory=directory, resolved=resolved_path):
        changed = True

    meta = _load_transcript_meta(resolved_path) if resolved_path else None

    timeline = _normalise_timestamps(persisted, meta)
    if timeline.changed:
        changed = True
    if _ensure_duration(persisted, timeline):
        changed = True
    if _merge_meta_fields(persisted, meta, ("agent_id", "agent_name", "model")):
        changed = True

    size_bytes, size_changed = _resolve_size(persisted, resolved_path)
    if size_changed:
        persisted["size_bytes"] = size_bytes
        changed = True

    if "retained" in persisted:
        retained = bool(persisted.get("retained", True))
        if retained != persisted.get("retained"):
            persisted["retained"] = retained
            changed = True
    else:
        persisted["retained"] = True

    warning, warning_messages = _resolve_entry_warning(persisted, resolved_path, expected_path)
    warnings.extend(warning_messages)

    if _prune_legacy_fields(persisted):
        changed = True

    history = _build_history_entry(
        persisted,
        resolved=resolved_path,
        expected=expected_path,
        warning=warning,
        current_run_id=current_run_id,
        timeline=timeline,
    )

    return NormalizedEntry(
        persisted=persisted,
        history=history,
        changed=changed,
        warnings=warnings,
        resolved_path=resolved_path,
    )


def history_run_id_eq(entry: dict[str, Any], target_run_id: str) -> bool:
    """Return True when the manifest entry represents the target run id."""
    run_id = entry.get("run_id")
    return bool(run_id) and str(run_id) == str(target_run_id)


def _build_orphan_entry(
    path: Path,
    *,
    existing_ids: set[str],
    current_run_id: str | None,
) -> NormalizedEntry:
    """Create a synthetic manifest entry for an orphaned transcript file."""
    meta = _load_transcript_meta(path)
    run_id = None
    if meta and meta.get("run_id"):
        run_id = str(meta.get("run_id"))
    if not run_id:
        stem = path.stem
        run_id = stem.replace("run-", "", 1) if stem.startswith("run-") else stem
    run_id = _dedupe_run_id(run_id, existing_ids)

    try:
        size_bytes = path.stat().st_size
    except OSError:
        size_bytes = 0

    persisted = {
        "run_id": run_id,
        "agent_id": meta.get("agent_id") if meta else None,
        "agent_name": meta.get("agent_name") if meta else None,
        "model": meta.get("model") if meta else None,
        "started_at": meta.get("started_at"),
        "finished_at": meta.get("finished_at"),
        "duration_seconds": meta.get("duration_seconds"),
        "size_bytes": size_bytes,
        "filename": path.name,
        "retained": True,
        "migration_notice": "orphaned_transcript",
    }

    timeline = _normalise_timestamps(persisted, meta)
    _ensure_duration(persisted, timeline)
    _merge_meta_fields(persisted, meta, ("agent_id", "agent_name", "model"))

    history = _build_history_entry(
        persisted,
        resolved=path,
        expected=path,
        warning=None,
        current_run_id=current_run_id,
        timeline=timeline,
    )

    return NormalizedEntry(
        persisted=persisted,
        history=history,
        changed=True,
        warnings=[],
        resolved_path=path,
    )


def _format_migration_summary(counters: dict[str, int]) -> str | None:
    """Summarise any cache migrations performed during snapshot normalisation."""
    parts: list[str] = []
    legacy = counters.get("legacy", 0)
    if legacy:
        parts.append(f"Migrated {legacy} legacy entries")
    orphans = counters.get("orphans", 0)
    if orphans:
        parts.append(f"{orphans} orphan files added from disk")
    missing = counters.get("missing", 0)
    if missing:
        parts.append(f"{missing} stale rows flagged as missing")
    if not parts:
        return None
    return "; ".join(parts) + "."


def _process_manifest_entries(
    raw_entries: list[dict[str, Any]],
    *,
    directory: Path,
    current_run_id: str | None,
) -> tuple[
    list[NormalizedEntry],
    list[dict[str, Any]],
    list[str],
    dict[str, int],
    bool,
    int,
    set[str],
]:
    """Normalise persisted manifest entries and collect aggregate stats."""
    normalized_entries: list[NormalizedEntry] = []
    persisted_entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    counters = {"legacy": 0, "missing": 0, "cached": 0}
    changed = False
    total_bytes = 0
    existing_ids: set[str] = set()

    for entry in raw_entries:
        normalized = _normalise_entry(entry, directory=directory, current_run_id=current_run_id)
        normalized_entries.append(normalized)
        persisted_entries.append(normalized.persisted)
        warnings.extend(normalized.warnings)
        if normalized.changed:
            counters["legacy"] += 1
            changed = True
        if normalized.history.warning == "transcript_missing":
            counters["missing"] += 1
        if normalized.history.status == "cached":
            counters["cached"] += 1
        if normalized.history.size_bytes:
            total_bytes += int(normalized.history.size_bytes or 0)
        run_id = normalized.persisted.get("run_id")
        if run_id:
            existing_ids.add(str(run_id))

    return normalized_entries, persisted_entries, warnings, counters, changed, total_bytes, existing_ids


def _append_orphan_entries(
    directory: Path,
    *,
    current_run_id: str | None,
    existing_ids: set[str],
    normalized_entries: list[NormalizedEntry],
    persisted_entries: list[dict[str, Any]],
    counters: dict[str, int],
    total_bytes: int,
) -> tuple[bool, int]:
    """Add on-disk transcripts that are missing from the manifest."""
    resolved_paths = {entry.resolved_path.resolve() for entry in normalized_entries if entry.resolved_path}
    try:
        files_on_disk = {
            path.resolve(): path
            for path in directory.glob("*.jsonl")
            if path.is_file() and path.name != MANIFEST_FILENAME
        }
    except OSError:
        return False, total_bytes

    changed = False
    for resolved, actual in files_on_disk.items():
        if resolved in resolved_paths:
            continue
        orphan_entry = _build_orphan_entry(
            actual,
            existing_ids=existing_ids,
            current_run_id=current_run_id,
        )
        normalized_entries.append(orphan_entry)
        persisted_entries.append(orphan_entry.persisted)
        counters["orphans"] = counters.get("orphans", 0) + 1
        if orphan_entry.history.status == "cached":
            counters["cached"] = counters.get("cached", 0) + 1
        if orphan_entry.history.size_bytes:
            total_bytes += int(orphan_entry.history.size_bytes or 0)
        changed = True

    return changed, total_bytes


def _normalise_manifest(
    *,
    cache_dir: Path | None,
    current_run_id: str | None,
    include_orphans: bool,
) -> tuple[list[NormalizedEntry], list[dict[str, Any]], list[str], dict[str, int], Path, Path, bool, int]:
    """Return normalised entries plus bookkeeping metadata for a given cache directory."""
    directory = ensure_cache_dir(cache_dir)
    manifest = manifest_path(directory)
    raw_entries = load_manifest_entries(directory)
    (
        normalized_entries,
        persisted_entries,
        warnings,
        counters,
        changed,
        total_bytes,
        existing_ids,
    ) = _process_manifest_entries(
        raw_entries,
        directory=directory,
        current_run_id=current_run_id,
    )

    counters.setdefault("orphans", 0)

    if include_orphans:
        orphan_changed, total_bytes = _append_orphan_entries(
            directory,
            current_run_id=current_run_id,
            existing_ids=existing_ids,
            normalized_entries=normalized_entries,
            persisted_entries=persisted_entries,
            counters=counters,
            total_bytes=total_bytes,
        )
        changed = changed or orphan_changed

    return (
        normalized_entries,
        persisted_entries,
        warnings,
        counters,
        directory,
        manifest,
        changed,
        total_bytes,
    )


def _resolve_history_default_limit() -> int:
    """Return the configured default limit from `aip config`, falling back to the built-in default."""
    try:
        config = load_config()
    except Exception:
        config = {}
    config_limit = _to_int(config.get("history_default_limit"))
    if config_limit is not None:
        return max(0, config_limit)

    return DEFAULT_HISTORY_LIMIT


def load_history_snapshot(
    *,
    limit: int | None = None,
    ctx: Any | None = None,
    cache_dir: Path | None = None,
) -> HistorySnapshot:
    """Load cached transcript history applying migrations as needed."""
    ctx_obj = getattr(ctx, "obj", None)
    current_run_id = None
    if isinstance(ctx_obj, dict):
        manifest = ctx_obj.get("_last_transcript_manifest")
        if isinstance(manifest, dict):
            run_id = manifest.get("run_id")
            if run_id:
                current_run_id = str(run_id)

    (
        normalized_entries,
        persisted_entries,
        warnings,
        counters,
        directory,
        manifest_file,
        changed,
        total_bytes,
    ) = _normalise_manifest(cache_dir=cache_dir, current_run_id=current_run_id, include_orphans=True)

    if changed:
        write_manifest(persisted_entries, directory)

    if limit is None or limit == 0:
        requested_limit = _resolve_history_default_limit()
    else:
        requested_limit = max(0, int(limit))

    limit_applied = requested_limit
    limit_clamped = False
    if limit_applied > MAX_HISTORY_LIMIT:
        limit_applied = MAX_HISTORY_LIMIT
        limit_clamped = True

    entries_sorted = sorted(
        (entry.history for entry in normalized_entries),
        key=lambda h: coerce_sortable_datetime(h.started_at),
        reverse=True,
    )

    display_entries = entries_sorted[:limit_applied] if limit_applied else []
    entries_index = {entry.history.run_id: entry.history for entry in normalized_entries if entry.history.run_id}

    migration_summary = _format_migration_summary(counters)

    return HistorySnapshot(
        manifest_path=manifest_file,
        entries=display_entries,
        total_entries=len(entries_sorted),
        cached_entries=counters.get("cached", 0),
        total_size_bytes=total_bytes,
        index=entries_index,
        warnings=warnings,
        migration_summary=migration_summary,
        limit_requested=requested_limit,
        limit_applied=limit_applied,
        limit_clamped=limit_clamped,
    )


def _normalise_run_ids(run_ids: Sequence[str] | None, entries_by_run: dict[str, NormalizedEntry]) -> list[str]:
    """Return a deduplicated list of run ids requested for deletion."""
    if run_ids is None:
        return list(entries_by_run.keys())
    seen: set[str] = set()
    deduped: list[str] = []
    for run_id in run_ids:
        if run_id in seen:
            continue
        seen.add(run_id)
        deduped.append(run_id)
    return deduped


def _purge_entry(entry: NormalizedEntry) -> tuple[HistoryEntry, int, list[str]]:
    """Remove a cached transcript from disk and return bookkeeping information."""
    reclaimed_bytes = 0
    warnings: list[str] = []
    resolved = entry.resolved_path
    if resolved and resolved.exists():
        try:
            reclaimed_bytes = resolved.stat().st_size
            resolved.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            warnings.append(f"Failed to remove {resolved}: {exc}")
    else:
        warnings.append(
            f"Transcript file already missing for run {entry.history.run_id}. Manifest entry will be removed."
        )
    return entry.history, reclaimed_bytes, warnings


def clear_cached_runs(
    run_ids: Sequence[str] | None,
    *,
    cache_dir: Path | None = None,
) -> ClearResult:
    """Remove cached transcripts and update the manifest."""
    (
        normalized_entries,
        persisted_entries,
        warnings,
        _counters,
        directory,
        manifest_file,
        changed,
        _total_bytes,
    ) = _normalise_manifest(cache_dir=cache_dir, current_run_id=None, include_orphans=True)

    # If normalisation changed entries, update manifest before processing deletions
    if changed:
        write_manifest(persisted_entries, directory)

    entries_by_run = {entry.history.run_id: entry for entry in normalized_entries if entry.history.run_id}

    target_run_ids = _normalise_run_ids(run_ids, entries_by_run)
    missing = [run_id for run_id in target_run_ids if run_id not in entries_by_run]
    removable = {run_id for run_id in target_run_ids if run_id in entries_by_run}

    removed_entries: list[HistoryEntry] = []
    reclaimed_bytes = 0
    additional_warnings: list[str] = []
    remaining_entries: list[dict[str, Any]] = []

    for entry in normalized_entries:
        run_id = entry.history.run_id
        if run_id in removable:
            history_entry, reclaimed, warnings_extra = _purge_entry(entry)
            removed_entries.append(history_entry)
            reclaimed_bytes += reclaimed
            additional_warnings.extend(warnings_extra)
        else:
            remaining_entries.append(entry.persisted)

    write_manifest(remaining_entries, directory)

    combined_warnings = warnings + additional_warnings
    cache_empty = len(remaining_entries) == 0

    return ClearResult(
        manifest_path=manifest_file,
        removed_entries=removed_entries,
        not_found=missing,
        warnings=combined_warnings,
        reclaimed_bytes=reclaimed_bytes,
        cache_empty=cache_empty,
    )
