"""Helpers for storing and exporting agent run transcripts.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from glaip_sdk.utils.datetime_helpers import (
    coerce_datetime as _coerce_datetime,
)

DEFAULT_CACHE_ROOT = Path(
    os.getenv(
        "AIP_TRANSCRIPT_CACHE_DIR",
        Path.home() / ".config" / "glaip-sdk" / "transcripts",
    )
)
MANIFEST_FILENAME = "manifest.jsonl"
JSONL_SUFFIX = ".jsonl"
UTC_OFFSET_SUFFIX = "+00:00"

_RUN_ID_PREFIX = "run_"
_RUN_ID_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


@dataclass(slots=True)
class TranscriptPayload:
    """Data bundle representing a captured agent run."""

    events: list[dict[str, Any]]
    default_output: str
    final_output: str
    agent_id: str | None
    agent_name: str | None
    model: str | None
    server_run_id: str | None
    started_at: float | None
    finished_at: float | None
    created_at: datetime
    source: str
    meta: dict[str, Any]
    run_id: str


@dataclass(slots=True)
class TranscriptStoreResult:
    """Result of writing a transcript to the local cache."""

    path: Path
    manifest_entry: dict[str, Any]
    pruned_entries: list[dict[str, Any]]


@dataclass(slots=True)
class TranscriptCacheStats:
    """Lightweight usage snapshot for the transcript cache."""

    cache_dir: Path
    entry_count: int
    total_bytes: int


def generate_run_id(length: int = 6) -> str:
    """Return a short, human-friendly run identifier."""
    length = max(4, min(int(length or 0), 16)) or 6
    return _RUN_ID_PREFIX + "".join(secrets.choice(_RUN_ID_ALPHABET) for _ in range(length))


def _timestamp_to_iso(value: Any) -> str | None:
    """Convert supported timestamp-like values to an ISO8601 string with UTC designator."""
    dt = _coerce_datetime(value)
    if dt is None:
        return None
    if dt.year < 2000:
        return None
    return dt.isoformat().replace(UTC_OFFSET_SUFFIX, "Z")


def _compute_duration_seconds(start: Any, end: Any) -> int | None:
    """Compute whole-second duration between two timestamp-like values."""
    start_dt = _coerce_datetime(start)
    end_dt = _coerce_datetime(end)
    if start_dt is None or end_dt is None:
        return None
    delta = (end_dt - start_dt).total_seconds()
    if delta < 0:
        return None
    return int(round(delta))


def _iter_candidate_paths(entry: dict[str, Any], directory: Path) -> Iterator[Path]:
    """Yield plausible transcript paths for a manifest entry, deduplicated."""
    seen: set[str] = set()

    def _offer(path: Path) -> Iterator[Path]:
        key = str(path)
        if key not in seen:
            seen.add(key)
            yield path

    for candidate in _filename_candidate_paths(entry, directory):
        yield from _offer(candidate)
    for candidate in _cache_path_candidate_paths(entry):
        yield from _offer(candidate)
    for candidate in _run_id_candidate_paths(entry, directory):
        yield from _offer(candidate)


def _filename_candidate_paths(entry: dict[str, Any], directory: Path) -> tuple[Path, ...]:
    """Return possible transcript paths derived from the manifest filename."""
    filename = entry.get("filename")
    if not filename:
        return ()
    candidate = Path(str(filename))
    if not candidate.is_absolute():
        candidate = directory / candidate
    return (candidate,)


def _cache_path_candidate_paths(entry: dict[str, Any]) -> tuple[Path, ...]:
    """Return legacy cache_path-derived transcript candidates."""
    cache_path = entry.get("cache_path")
    if not cache_path:
        return ()
    return (Path(str(cache_path)).expanduser(),)


def _run_id_candidate_paths(entry: dict[str, Any], directory: Path) -> tuple[Path, ...]:
    """Return candidate transcript paths derived from the run id."""
    run_id = entry.get("run_id")
    if not run_id:
        return ()
    paths: list[Path] = []
    for variant in _run_id_variants(str(run_id)):
        name = variant if variant.endswith(JSONL_SUFFIX) else f"{variant}{JSONL_SUFFIX}"
        paths.append(directory / name)
    return tuple(paths)


def _run_id_variants(run_id: str) -> set[str]:
    """Return plausible filename stems derived from a run id."""
    variants = {run_id}
    if run_id.startswith(_RUN_ID_PREFIX):
        suffix = run_id[len(_RUN_ID_PREFIX) :]
        if suffix:
            variants.update({suffix, f"run-{suffix}"})
        variants.add(f"run-{run_id}")
    else:
        variants.update({f"run-{run_id}", _RUN_ID_PREFIX + run_id})
    return variants


def transcript_path_candidates(entry: dict[str, Any], cache_dir: Path | None = None) -> list[Path]:
    """Return possible transcript file locations for a manifest entry."""
    directory = ensure_cache_dir(cache_dir)
    return list(_iter_candidate_paths(entry, directory))


def resolve_transcript_path(entry: dict[str, Any], cache_dir: Path | None = None) -> Path:
    """Resolve the cached transcript path for a manifest entry or raise informative errors."""
    candidates = transcript_path_candidates(entry, cache_dir)
    if not candidates:
        raise FileNotFoundError("Cached transcript path missing from manifest.")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Cached transcript file not found: {candidates[0]}")


def _manifest_sort_key(entry: dict[str, Any]) -> datetime:
    """Return a datetime for ordering manifest rows, defaulting to the distant past."""
    for key in ("started_at", "created_at"):
        dt = _coerce_datetime(entry.get(key))
        if dt is not None:
            return dt
    return datetime.min.replace(tzinfo=timezone.utc)


def ensure_cache_dir(cache_dir: Path | None = None) -> Path:
    """Ensure the cache directory exists and return it."""
    directory = cache_dir or DEFAULT_CACHE_ROOT
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return _fallback_cache_dir()

    if not os.access(directory, os.W_OK):
        return _fallback_cache_dir()

    return directory


def _fallback_cache_dir() -> Path:
    """Return a writable fallback cache directory under the current working tree."""
    fallback = Path.cwd() / ".glaip-transcripts"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def manifest_path(cache_dir: Path | None = None) -> Path:
    """Return the manifest file path."""
    return ensure_cache_dir(cache_dir) / MANIFEST_FILENAME


def _parse_iso(ts: str | None) -> datetime | None:
    """Parse metadata timestamps that may use the legacy Z suffix."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", UTC_OFFSET_SUFFIX))
    except Exception:
        return None


def _load_manifest_entries(cache_dir: Path | None = None) -> list[dict[str, Any]]:
    """Read manifest entries from disk, returning an empty list when missing."""
    path = manifest_path(cache_dir)
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def _json_default(value: Any) -> Any:
    """Ensure non-serialisable values degrade to readable strings."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    return repr(value)


def _write_manifest(entries: Iterable[dict[str, Any]], cache_dir: Path | None = None) -> None:
    """Atomically write manifest entries back to disk."""
    path = manifest_path(cache_dir)
    tmp_path = path.with_name(f"{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False, default=_json_default))
            fh.write("\n")
    tmp_path.replace(path)


def load_manifest_entries(cache_dir: Path | None = None) -> list[dict[str, Any]]:
    """Public wrapper around manifest loading for downstream tooling."""
    return _load_manifest_entries(cache_dir)


def write_manifest(entries: Iterable[dict[str, Any]], cache_dir: Path | None = None) -> None:
    """Persist manifest entries atomically."""
    _write_manifest(entries, cache_dir)


def store_transcript(
    payload: TranscriptPayload,
    *,
    cache_dir: Path | None = None,
) -> TranscriptStoreResult:
    """Persist a transcript to disk and update the manifest."""
    directory = ensure_cache_dir(cache_dir)
    filename = _normalise_run_filename(payload.run_id)
    transcript_path = directory / filename

    meta_line = _build_meta_line(payload)
    transcript_path = _write_transcript_file(transcript_path, filename, meta_line, payload.events)
    size_bytes = _safe_file_size(transcript_path)
    manifest_entry = _build_manifest_entry(payload, transcript_path.name, size_bytes)
    if transcript_path.parent != directory:
        manifest_entry["cache_path"] = str(transcript_path)

    existing_entries = _load_manifest_entries(directory)
    existing_entries.append(manifest_entry)
    _write_manifest(existing_entries, directory)

    return TranscriptStoreResult(
        path=transcript_path,
        manifest_entry=manifest_entry,
        pruned_entries=[],
    )


def _normalise_run_filename(run_id: str) -> str:
    """Ensure cached run filenames always end with .jsonl."""
    run_basename = run_id.rstrip()
    if run_basename.endswith(JSONL_SUFFIX):
        run_basename = run_basename[: -len(JSONL_SUFFIX)]
    return f"{run_basename}{JSONL_SUFFIX}"


def _build_meta_line(payload: TranscriptPayload) -> dict[str, Any]:
    """Return the metadata header stored at the top of transcript files."""
    return {
        "type": "meta",
        "run_id": payload.run_id,
        "agent_id": payload.agent_id,
        "agent_name": payload.agent_name,
        "model": payload.model,
        "created_at": payload.created_at.isoformat(),
        "default_output": payload.default_output,
        "final_output": payload.final_output,
        "server_run_id": payload.server_run_id,
        "started_at": payload.started_at,
        "finished_at": payload.finished_at,
        "meta": payload.meta,
        "source": payload.source,
    }


def _write_transcript_file(
    path: Path,
    filename: str,
    meta_line: dict[str, Any],
    events: list[dict[str, Any]],
) -> Path:
    """Persist the transcript JSONL file, falling back to cwd when necessary."""

    def _write(target: Path) -> None:
        with target.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(meta_line, ensure_ascii=False, default=_json_default))
            fh.write("\n")
            for event in events:
                fh.write(
                    json.dumps(
                        {"type": "event", "event": event},
                        ensure_ascii=False,
                        default=_json_default,
                    )
                )
                fh.write("\n")

    try:
        _write(path)
        return path
    except PermissionError:
        fallback_dir = _fallback_cache_dir()
        fallback_path = fallback_dir / filename
        _write(fallback_path)
        return fallback_path


def _safe_file_size(path: Path) -> int:
    """Return the file size, tolerating missing paths."""
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _build_manifest_entry(payload: TranscriptPayload, filename: str, size_bytes: int) -> dict[str, Any]:
    """Generate the manifest row corresponding to a stored transcript."""
    entry: dict[str, Any] = {
        "run_id": payload.run_id,
        "agent_id": payload.agent_id,
        "agent_name": payload.agent_name,
        "started_at": _timestamp_to_iso(payload.started_at) or payload.created_at.isoformat(),
        "finished_at": _timestamp_to_iso(payload.finished_at),
        "duration_seconds": _compute_duration_seconds(payload.started_at, payload.finished_at),
        "size_bytes": size_bytes,
        "filename": filename,
        "retained": True,
        "model": payload.model,
    }

    api_url = payload.meta.get("api_url")
    if api_url:
        entry["api_url"] = api_url

    if entry["duration_seconds"] is None:
        entry["duration_seconds"] = _coerce_duration_hint(payload.meta.get("final_duration_seconds"))

    if entry.get("finished_at") is None and entry.get("started_at") and entry.get("duration_seconds") is not None:
        start_dt = _coerce_datetime(entry["started_at"])
        if start_dt is not None:
            finished_dt = start_dt + timedelta(seconds=int(entry["duration_seconds"]))
            entry["finished_at"] = finished_dt.isoformat().replace(UTC_OFFSET_SUFFIX, "Z")

    return entry


def _coerce_duration_hint(value: Any) -> int | None:
    """Convert loose duration hints to whole seconds."""
    try:
        if value is None:
            return None
        return int(round(float(value)))
    except Exception:
        return None


def latest_manifest_entry(cache_dir: Path | None = None) -> dict[str, Any] | None:
    """Return the most recent manifest entry, if any."""
    entries = _load_manifest_entries(cache_dir)
    if not entries:
        return None
    return max(entries, key=_manifest_sort_key)


def resolve_manifest_entry(
    run_id: str,
    cache_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Find a manifest entry by run id."""
    entries = _load_manifest_entries(cache_dir)
    for entry in entries:
        if entry.get("run_id") == run_id:
            return entry
    return None


def export_transcript(
    *,
    destination: Path,
    run_id: str | None = None,
    cache_dir: Path | None = None,
) -> Path:
    """Copy a cached transcript to the requested destination path."""
    directory = ensure_cache_dir(cache_dir)
    entry = resolve_manifest_entry(run_id, directory) if run_id else latest_manifest_entry(directory)
    if entry is None:
        raise FileNotFoundError("No cached transcripts available for export.")

    try:
        cache_file = resolve_transcript_path(entry, directory)
    except FileNotFoundError as exc:
        raise FileNotFoundError(str(exc)) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        lines = cache_file.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
    except json.JSONDecodeError as exc:
        raise FileNotFoundError(f"Cached transcript file is corrupted: {cache_file}") from exc

    with destination.open("w", encoding="utf-8") as fh:
        for idx, record in enumerate(records):
            json.dump(record, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            if idx != len(records) - 1:
                fh.write("\n")

    return destination


def suggest_filename(entry: dict[str, Any] | None = None) -> str:
    """Return a friendly filename suggestion for exporting a transcript."""
    run_id = entry.get("run_id") if entry else None
    if not run_id:
        run_id = generate_run_id()

    timestamp_source = None
    if entry:
        timestamp_source = entry.get("started_at") or entry.get("created_at")

    if not timestamp_source:
        timestamp_source = datetime.now(timezone.utc).isoformat()

    timestamp = str(timestamp_source).replace(":", "").replace("-", "").replace("T", "_").split("+")[0]
    safe_run_id = str(run_id).replace("/", "-").replace(" ", "-")
    return f"aip-run-{timestamp}-{safe_run_id}{JSONL_SUFFIX}"


def build_payload(
    *,
    events: list[dict[str, Any]],
    renderer_output: str,
    final_output: str,
    agent_id: str | None,
    agent_name: str | None,
    model: str | None,
    server_run_id: str | None,
    started_at: float | None,
    finished_at: float | None,
    meta: dict[str, Any],
    source: str,
) -> TranscriptPayload:
    """Factory helper to prepare payload objects consistently."""
    return TranscriptPayload(
        events=events,
        default_output=renderer_output,
        final_output=final_output,
        agent_id=agent_id,
        agent_name=agent_name,
        model=model,
        server_run_id=server_run_id,
        started_at=started_at,
        finished_at=finished_at,
        created_at=datetime.now(timezone.utc),
        source=source,
        meta=meta,
        run_id=generate_run_id(),
    )


def get_transcript_cache_stats(
    cache_dir: Path | None = None,
) -> TranscriptCacheStats:
    """Return basic usage information about the transcript cache."""
    directory = ensure_cache_dir(cache_dir)
    entries = _load_manifest_entries(directory)

    total_bytes = 0
    for entry in entries:
        try:
            total_bytes += int(entry.get("size_bytes") or 0)
        except Exception:
            continue

    return TranscriptCacheStats(
        cache_dir=directory,
        entry_count=len(entries),
        total_bytes=total_bytes,
    )
