"""CLI prompting utilities: prompt_toolkit + questionary wrappers, validators.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from glaip_sdk.icons import ICON_AGENT
from rich.console import Console

questionary = None  # type: ignore[assignment]

# Optional interactive deps (fuzzy palette)
try:
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.completion import Completion
    from prompt_toolkit.patch_stdout import patch_stdout as pt_patch_stdout
    from prompt_toolkit.selection import SelectionType
    from prompt_toolkit.shortcuts import PromptSession, prompt

    _HAS_PTK = True
except Exception:  # pragma: no cover - optional dependency
    Buffer = None  # type: ignore[assignment]
    SelectionType = None  # type: ignore[assignment]
    PromptSession = None  # type: ignore[assignment]
    prompt = None  # type: ignore[assignment]
    pt_patch_stdout = None  # type: ignore[assignment]
    _HAS_PTK = False

logger = logging.getLogger("glaip_sdk.cli.core.prompting")


def _load_questionary_module() -> tuple[Any | None, Any | None]:
    """Return the questionary module and Choice class if available."""
    module = questionary
    if module is not None:
        return module, getattr(module, "Choice", None)

    try:  # pragma: no cover - optional dependency
        module = __import__("questionary")
    except ImportError:
        return None, None

    return module, getattr(module, "Choice", None)


def _make_questionary_choice(choice_cls: Any | None, **kwargs: Any) -> Any:
    """Create a questionary Choice instance or lightweight fallback."""
    if choice_cls is None:
        return kwargs
    return choice_cls(**kwargs)


def prompt_export_choice_questionary(
    default_path: Path,
    default_display: str,
) -> tuple[str, Path | None] | None:
    """Prompt user for export destination using questionary with numeric shortcuts.

    Args:
        default_path: Default export path.
        default_display: Formatted display string for default path.

    Returns:
        Tuple of (choice, path) or None if cancelled/unavailable.
        Choice can be "default", "custom", or "cancel".
    """
    questionary_module, choice_cls = _load_questionary_module()
    if questionary_module is None or choice_cls is None:
        return None

    try:
        question = questionary_module.select(
            "Export transcript",
            choices=[
                _make_questionary_choice(
                    choice_cls,
                    title=f"Save to default ({default_display})",
                    value=("default", default_path),
                    shortcut_key="1",
                ),
                _make_questionary_choice(
                    choice_cls,
                    title="Choose a different path",
                    value=("custom", None),
                    shortcut_key="2",
                ),
                _make_questionary_choice(
                    choice_cls,
                    title="Cancel",
                    value=("cancel", None),
                    shortcut_key="3",
                ),
            ],
            use_shortcuts=True,
            instruction="Press 1-3 (or arrows) then Enter.",
        )
        answer = questionary_safe_ask(question)
    except Exception:
        return None

    if answer is None:
        return ("cancel", None)
    return answer


def questionary_safe_ask(question: Any, *, patch_stdout: bool = False) -> Any:
    """Run `questionary.Question` safely even when an asyncio loop is active."""
    ask_fn = getattr(question, "unsafe_ask", None)
    if not callable(ask_fn):
        raise RuntimeError("Questionary prompt is missing unsafe_ask()")

    if not _asyncio_loop_running():
        return ask_fn(patch_stdout=patch_stdout)

    return _run_questionary_in_thread(question, patch_stdout=patch_stdout)


def _asyncio_loop_running() -> bool:
    """Return True when an asyncio event loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _run_questionary_in_thread(question: Any, *, patch_stdout: bool = False) -> Any:
    """Execute a questionary prompt in a background thread."""
    if getattr(question, "should_skip_question", False):
        return getattr(question, "default", None)

    application = getattr(question, "application", None)
    run_callable = getattr(application, "run", None) if application is not None else None
    if callable(run_callable):
        try:
            if patch_stdout and pt_patch_stdout is not None:
                with pt_patch_stdout():
                    return run_callable(in_thread=True)
            return run_callable(in_thread=True)
        except TypeError:
            pass

    return question.unsafe_ask(patch_stdout=patch_stdout)


def _basic_prompt(
    message: str,
    completer: Any,
) -> str | None:
    """Fallback prompt handler when PromptSession is unavailable or fails."""
    if prompt is None:  # pragma: no cover - optional dependency path
        return None

    try:
        return prompt(
            message=message,
            completer=completer,
            complete_in_thread=True,
            complete_while_typing=True,
        )
    except (KeyboardInterrupt, EOFError):
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Fallback prompt failed: %s", exc)
        return None


def _prompt_with_auto_select(
    message: str,
    completer: Any,
    choices: Iterable[str],
) -> str | None:
    """Prompt with fuzzy completer that auto-selects suggested matches."""
    if not _HAS_PTK or PromptSession is None or Buffer is None or SelectionType is None:
        return _basic_prompt(message, completer)

    try:
        session = PromptSession(
            message,
            completer=completer,
            complete_in_thread=True,
            complete_while_typing=True,
            reserve_space_for_menu=8,
        )
    except Exception as exc:  # pragma: no cover - depends on prompt_toolkit
        logger.debug("PromptSession init failed (%s); falling back to basic prompt.", exc)
        return _basic_prompt(message, completer)

    buffer = session.default_buffer
    valid_choices = set(choices)

    def _auto_select(_: Buffer) -> None:
        """Auto-select text when a valid choice is entered."""
        text = buffer.text
        if not text or text not in valid_choices:
            return
        buffer.cursor_position = 0
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
        buffer.cursor_position = len(text)

    handler_attached = False
    try:
        buffer.on_text_changed += _auto_select
        handler_attached = True
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Failed to attach auto-select handler: %s", exc)

    try:
        return session.prompt()
    except (KeyboardInterrupt, EOFError):
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("PromptSession prompt failed (%s); falling back to basic prompt.", exc)
        return _basic_prompt(message, completer)
    finally:
        if handler_attached:
            try:
                buffer.on_text_changed -= _auto_select
            except Exception:  # pragma: no cover - defensive
                pass


class _FuzzyCompleter:
    """Fuzzy completer for prompt_toolkit."""

    def __init__(self, words: list[str]) -> None:
        """Initialize fuzzy completer with word list.

        Args:
            words: List of words to complete from.
        """
        self.words = words

    def get_completions(self, document: Any, _complete_event: Any) -> Any:  # pragma: no cover
        """Get fuzzy completions for the current word, ranked by score.

        Args:
            document: Document object from prompt_toolkit.
            _complete_event: Completion event (unused).

        Yields:
            Completion objects matching the current word, in ranked order.
        """
        # Get the entire buffer text (not just word before cursor)
        buffer_text = document.text_before_cursor
        if not buffer_text or not isinstance(buffer_text, str):
            return

        # Rank labels by fuzzy score
        ranked_labels = _rank_labels(self.words, buffer_text)

        # Yield ranked completions
        for label in ranked_labels:
            # Replace entire buffer text, not just the word before cursor
            # This prevents concatenation issues with hyphenated names
            yield Completion(label, start_position=-len(buffer_text))


def _strip_spaces_for_matching(value: str) -> str:
    """Remove whitespace from a query for consistent fuzzy matching."""
    return re.sub(r"\s+", "", value)


def _is_fuzzy_match(search: Any, target: Any) -> bool:
    """Case-insensitive fuzzy match with optional spaces; returns False for non-string inputs."""
    # Ensure search is a string
    if not isinstance(search, str) or not isinstance(target, str):
        return False

    if not search:
        return True

    # Strip spaces from search query - treat them as optional separators
    # This allows "test agent" to match "test-agent", "test_agent", etc.
    search_no_spaces = _strip_spaces_for_matching(search).lower()
    if not search_no_spaces:
        # If search is only spaces, match everything
        return True

    search_idx = 0
    for char in target.lower():
        if search_idx < len(search_no_spaces) and search_no_spaces[search_idx] == char:
            search_idx += 1
            if search_idx == len(search_no_spaces):
                return True
    return False


def _calculate_exact_match_bonus(search: str, target: str) -> int:
    """Calculate bonus for exact substring matches.

    Spaces in search are treated as optional separators (stripped before matching).
    """
    # Strip spaces from search - treat them as optional separators
    search_no_spaces = _strip_spaces_for_matching(search).lower()
    if not search_no_spaces:
        return 0
    return 100 if search_no_spaces in target.lower() else 0


def _calculate_consecutive_bonus(search: str, target: str) -> int:
    """Case-insensitive consecutive-character bonus."""
    # Strip spaces from search - treat them as optional separators
    search_no_spaces = _strip_spaces_for_matching(search).lower()
    if not search_no_spaces:
        return 0

    consecutive = 0
    max_consecutive = 0
    search_idx = 0

    for char in target.lower():
        if search_idx < len(search_no_spaces) and search_no_spaces[search_idx] == char:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
            search_idx += 1
        else:
            consecutive = 0

    return max_consecutive * 10


def _calculate_length_bonus(search: str, target: str) -> int:
    """Calculate bonus for shorter search terms.

    Spaces in search are treated as optional separators (stripped before calculation).
    """
    # Strip spaces from search - treat them as optional separators
    search_no_spaces = _strip_spaces_for_matching(search)
    if not search_no_spaces:
        return 0
    return max(0, (len(target) - len(search_no_spaces)) * 2)


def _fuzzy_score(search: Any, target: str) -> int:
    """Calculate fuzzy match score.

    Higher score = better match.
    Returns -1 if no match possible.

    Args:
        search: Search string (or any type - non-strings return -1)
        target: Target string to match against
    """
    # Ensure search is a string first
    if not isinstance(search, str):
        return -1

    if not search:
        return 0

    if not _is_fuzzy_match(search, target):
        return -1  # Not a fuzzy match

    # Calculate score based on different factors
    score = 0
    score += _calculate_exact_match_bonus(search, target)
    score += _calculate_consecutive_bonus(search, target)
    score += _calculate_length_bonus(search, target)

    return score


def _extract_id_suffix(label: str) -> str:
    """Extract ID suffix from label for tie-breaking.

    Args:
        label: Display label (e.g., "name • [abc123...]")

    Returns:
        ID suffix string (e.g., "abc123") or empty string if not found
    """
    # Look for pattern like "[abc123...]" or "[abc123]"
    match = re.search(r"\[([^\]]+)\]", label)
    return match.group(1) if match else ""


def _rank_labels(labels: list[str], query: Any) -> list[str]:
    """Rank labels by fuzzy score with deterministic tie-breaks.

    Args:
        labels: List of display labels to rank
        query: Search query string (or any type - non-strings return sorted labels)

    Returns:
        Labels sorted by fuzzy score (descending), then case-insensitive label,
        then id suffix for deterministic ordering.
    """
    suffix_cache = {label: _extract_id_suffix(label) for label in labels}

    if not query:
        # No query: sort by case-insensitive label, then id suffix
        return sorted(labels, key=lambda lbl: (lbl.lower(), suffix_cache[lbl]))

    # Ensure query is a string
    if not isinstance(query, str):
        return sorted(labels, key=lambda lbl: (lbl.lower(), suffix_cache[lbl]))

    query_lower = query.lower()

    # Calculate scores and create tuples for sorting
    scored_labels = []
    for label in labels:
        label_lower = label.lower()
        score = _fuzzy_score(query_lower, label_lower)
        if score >= 0:  # Only include matches
            scored_labels.append((score, label_lower, suffix_cache[label], label))

    if not scored_labels:
        # No fuzzy matches: fall back to deterministic label sorting
        return sorted(labels, key=lambda lbl: (lbl.lower(), suffix_cache[lbl]))

    # Sort by: score (desc), label (case-insensitive), id suffix, original label
    scored_labels.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))

    return [label for _score, _label_lower, _id_suffix, label in scored_labels]


def _perform_fuzzy_search(answer: str, labels: list[str], by_label: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Perform fuzzy search fallback and return best match.

    Returns:
        Selected resource dict or None if cancelled/no match.
    """
    # Exact label match
    if answer in by_label:
        return by_label[answer]

    # Fuzzy search fallback using ranked labels
    # Check if query actually matches anything before ranking
    query_lower = answer.lower()
    has_match = False
    for label in labels:
        if _fuzzy_score(query_lower, label.lower()) >= 0:
            has_match = True
            break

    if not has_match:
        return None

    ranked_labels = _rank_labels(labels, answer)
    if ranked_labels:
        # Return the top-ranked match
        best_match = ranked_labels[0]
        if best_match in by_label:
            return by_label[best_match]

    return None


def _check_fuzzy_pick_requirements() -> bool:
    """Check if fuzzy picking requirements are met."""
    console = Console()
    return _HAS_PTK and console.is_terminal and os.isatty(1)


def _extract_display_fields(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Extract display fields from row data."""
    name = str(row.get("name", "")).strip()
    _id = str(row.get("id", "")).strip()
    type_ = str(row.get("type", "")).strip()
    fw = str(row.get("framework", "")).strip()
    return name, _id, type_, fw


def _build_primary_parts(name: str, type_: str, fw: str) -> list[str]:
    """Build primary display parts from name, type, and framework."""
    parts = []
    if name:
        parts.append(name)
    if type_:
        parts.append(type_)
    if fw:
        parts.append(fw)
    return parts


def _get_fallback_columns(columns: list[tuple]) -> list[tuple]:
    """Get first two visible columns for fallback display."""
    return columns[:2]


def _is_standard_field(k: str) -> bool:
    """Check if field is a standard field to skip."""
    return k in ("id", "name", "type", "framework")


def _extract_fallback_values(row: dict[str, Any], columns: list[tuple]) -> list[str]:
    """Extract fallback values from columns."""
    fallback_parts = []
    for k, _hdr, _style, _w in columns:
        if _is_standard_field(k):
            continue
        val = str(row.get(k, "")).strip()
        if val:
            fallback_parts.append(val)
        if len(fallback_parts) >= 2:
            break
    return fallback_parts


def _build_display_parts(
    name: str, _id: str, type_: str, fw: str, row: dict[str, Any], columns: list[tuple]
) -> list[str]:
    """Build complete display parts list."""
    parts = _build_primary_parts(name, type_, fw)

    if not parts:
        # Use fallback columns
        fallback_columns = _get_fallback_columns(columns)
        parts.extend(_extract_fallback_values(row, fallback_columns))

    if _id:
        parts.append(f"[{_id}]")

    return parts


def _row_display(row: dict[str, Any], columns: list[tuple]) -> str:
    """Build a compact text label for the palette.

    Prefers: name • type • framework • [id] (when available)
    Falls back to first 2 columns + [id].
    """
    name, _id, type_, fw = _extract_display_fields(row)
    parts = _build_display_parts(name, _id, type_, fw, row, columns)
    return " • ".join(parts) if parts else (_id or "(row)")


def _build_unique_labels(
    rows: list[dict[str, Any]], columns: list[tuple]
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Build unique display labels and reverse mapping."""
    labels = []
    by_label: dict[str, dict[str, Any]] = {}

    for r in rows:
        label = _row_display(r, columns)
        # Ensure uniqueness: if duplicate, suffix with …#n
        if label in by_label:
            i = 2
            base = label
            while f"{base} #{i}" in by_label:
                i += 1
            label = f"{base} #{i}"
        labels.append(label)
        by_label[label] = r

    return labels, by_label


def _fuzzy_pick(
    rows: list[dict[str, Any]], columns: list[tuple], title: str
) -> dict[str, Any] | None:  # pragma: no cover - requires interactive prompt toolkit
    """Open a minimal fuzzy palette using prompt_toolkit.

    Returns the selected row (dict) or None if cancelled/missing deps.
    """
    if not _check_fuzzy_pick_requirements():
        return None

    # Build display labels and mapping
    labels, by_label = _build_unique_labels(rows, columns)

    # Create fuzzy completer
    completer = _FuzzyCompleter(labels)
    singular_title = title[:-1] if title.endswith("s") else title
    answer = _prompt_with_auto_select(
        f"Find {singular_title}: ",
        completer,
        labels,
    )
    if answer is None:
        return None

    return _perform_fuzzy_search(answer, labels, by_label) if answer else None


def _build_resource_labels(resources: list[Any]) -> tuple[list[str], dict[str, Any]]:
    """Build unique display labels for resources."""
    labels = []
    by_label: dict[str, Any] = {}

    for resource in resources:
        name = getattr(resource, "name", "Unknown")
        _id = getattr(resource, "id", "Unknown")

        # Create display label
        label_parts = []
        if name and name != "Unknown":
            label_parts.append(name)
        label_parts.append(f"[{_id[:8]}...]")  # Show first 8 chars of ID
        label = " • ".join(label_parts)

        # Ensure uniqueness
        if label in by_label:
            i = 2
            base = label
            while f"{base} #{i}" in by_label:
                i += 1
            label = f"{base} #{i}"

        labels.append(label)
        by_label[label] = resource

    return labels, by_label


def _fuzzy_pick_for_resources(
    resources: list[Any], resource_type: str, _search_term: str
) -> Any | None:  # pragma: no cover - interactive selection helper
    """Fuzzy picker for resource objects, similar to _fuzzy_pick but without column dependencies.

    Args:
        resources: List of resource objects to choose from
        resource_type: Type of resource (e.g., "agent", "tool")
        search_term: The search term that led to multiple matches

    Returns:
        Selected resource object or None if cancelled/no selection
    """
    if not _check_fuzzy_pick_requirements():
        return None

    # Build labels and mapping
    labels, by_label = _build_resource_labels(resources)

    # Create fuzzy completer
    completer = _FuzzyCompleter(labels)
    answer = _prompt_with_auto_select(
        f"Find {ICON_AGENT} {resource_type.title()}: ",
        completer,
        labels,
    )
    if answer is None:
        return None

    return _perform_fuzzy_search(answer, labels, by_label) if answer else None
