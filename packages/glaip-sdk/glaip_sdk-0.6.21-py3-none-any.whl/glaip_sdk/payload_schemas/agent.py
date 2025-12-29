"""Agent payload schema metadata derived from agent_payloads.md.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)

This module encodes which agent fields are mutable, server-managed, or require
additional sanitisation so that CLI and SDK flows can share the same rules.
"""

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Literal

AgentImportOperation = Literal["create", "update"]


@dataclass(frozen=True)
class FieldRule:
    """Schema rule defining how a field should be treated."""

    server_only: bool = False
    cli_managed_create: bool = False
    cli_managed_update: bool = False
    requires_sanitization: bool = False


@dataclass(frozen=True)
class ImportFieldPlan:
    """Plan for how an import pipeline should treat a specific field."""

    copy: bool
    sanitize: bool = False


_DEFAULT_RULE = FieldRule()


AGENT_FIELD_RULES: Mapping[str, FieldRule] = {
    # Server-provided metadata (never send back)
    "id": FieldRule(server_only=True),
    "created_at": FieldRule(server_only=True),
    "updated_at": FieldRule(server_only=True),
    "deleted_at": FieldRule(server_only=True),
    "success": FieldRule(server_only=True),
    "message": FieldRule(server_only=True),
    # Fields handled explicitly by CLI/SDK helpers for language model selection
    "language_model_id": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "provider": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "model_name": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "model": FieldRule(cli_managed_create=True, cli_managed_update=True),
    # Fields collected via CLI flags / explicit logic
    "name": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "instruction": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "tools": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "agents": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "mcps": FieldRule(cli_managed_create=True, cli_managed_update=True),
    "timeout": FieldRule(cli_managed_create=True, cli_managed_update=True),
    # Fields requiring sanitisation before sending to the API
    "agent_config": FieldRule(requires_sanitization=True),
}


def get_import_field_plan(field_name: str, operation: AgentImportOperation) -> ImportFieldPlan:
    """Return the import handling plan for ``field_name`` under ``operation``.

    Unknown fields default to being copied as-is so new API fields propagate
    without additional code changes.
    """
    rule = AGENT_FIELD_RULES.get(field_name, _DEFAULT_RULE)

    if rule.server_only:
        return ImportFieldPlan(copy=False)

    if operation == "create" and rule.cli_managed_create:
        return ImportFieldPlan(copy=False)

    if operation == "update" and rule.cli_managed_update:
        return ImportFieldPlan(copy=False)

    return ImportFieldPlan(copy=True, sanitize=rule.requires_sanitization)


def list_server_only_fields() -> Collection[str]:
    """Expose the set of server-only fields for other tooling."""
    return {name for name, rule in AGENT_FIELD_RULES.items() if rule.server_only}
