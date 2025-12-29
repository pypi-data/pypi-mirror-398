#!/usr/bin/env python3
"""Export utilities for remote agent run transcripts.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from glaip_sdk.models.agent_runs import RunWithOutput, RunOutputChunk


def export_remote_transcript_jsonl(
    run: RunWithOutput,
    destination: Path,
    *,
    overwrite: bool = False,
    agent_name: str | None = None,
    model: str | None = None,
) -> Path:
    """Export a remote run transcript to JSONL format compatible with local transcript viewers.

    Args:
        run: RunWithOutput instance to export
        destination: Target file path for JSONL export
        overwrite: Whether to overwrite existing file
        agent_name: Optional agent name for metadata
        model: Optional model name for metadata (extracted from run.config if not provided)

    Returns:
        Path to the exported file

    Raises:
        FileExistsError: If destination exists and overwrite is False
        OSError: If file cannot be written
    """
    if destination.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {destination}")

    # Ensure parent directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    model_name = model or _extract_model(run)
    final_output_text = _extract_final_output(run.output) or ""

    meta_payload = _build_meta_payload(run, agent_name, model_name)
    meta_record = _build_meta_record(run, agent_name, model_name, final_output_text, meta_payload)

    _write_jsonl_file(destination, meta_record, run.output)

    return destination


def _build_meta_payload(run: RunWithOutput, agent_name: str | None, model_name: str | None) -> dict[str, Any]:
    """Build the meta payload dictionary."""
    return {
        "agent_name": agent_name,
        "model": model_name,
        "input_message": run.input,
        "status": run.status,
        "run_type": run.run_type,
        "schedule_id": str(run.schedule_id) if run.schedule_id else None,
        "config": run.config or {},
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        "event_count": len(run.output),
    }


def _build_meta_record(
    run: RunWithOutput,
    agent_name: str | None,
    model_name: str | None,
    final_output_text: str,
    meta_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the meta record dictionary."""
    return {
        "type": "meta",
        "run_id": str(run.id),
        "agent_id": str(run.agent_id),
        "agent_name": agent_name,
        "model": model_name,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "default_output": final_output_text,
        "final_output": final_output_text,
        "server_run_id": str(run.id),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.completed_at.isoformat() if run.completed_at else None,
        "meta": meta_payload,
        "source": "remote_history",
        # Back-compat fields used by older tooling
        "run_type": run.run_type,
        "schedule_id": str(run.schedule_id) if run.schedule_id else None,
        "status": run.status,
        "input": run.input,
        "config": run.config or {},
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }


def _write_jsonl_file(destination: Path, meta_record: dict[str, Any], events: list[RunOutputChunk]) -> None:
    """Write the JSONL file with meta and event records."""
    records: list[dict[str, Any]] = [meta_record]
    records.extend({"type": "event", "event": event} for event in events)

    with destination.open("w", encoding="utf-8") as fh:
        for idx, record in enumerate(records):
            json.dump(record, fh, ensure_ascii=False, indent=2, default=_json_default)
            fh.write("\n")
            if idx != len(records) - 1:
                fh.write("\n")


def _extract_model(run: RunWithOutput) -> str | None:
    """Best-effort extraction of the model name from run metadata."""
    config = run.config or {}
    if isinstance(config, dict):
        model = config.get("model") or config.get("llm", {}).get("model")
        if isinstance(model, str):
            return model
    return None


def _extract_final_output(events: list[RunOutputChunk]) -> str | None:
    """Return the final response content from the event stream."""
    for chunk in reversed(events):
        content = chunk.get("content")
        if not content:
            continue
        if chunk.get("event_type") == "final_response" or chunk.get("final"):
            return str(content)
    return None


def _json_default(obj: Any) -> Any:
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
