"""Fuzzy matching utilities for Linear toolkit."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError
from rapidfuzz import fuzz, process

from arcade_linear.constants import (
    DISABLE_AUTO_ACCEPT_THRESHOLD,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    FUZZY_MATCH_THRESHOLD,
    MAX_DISPLAY_SUGGESTIONS,
    MAX_FUZZY_SUGGESTIONS,
)


@dataclass
class FuzzyMatch:
    """Result of a fuzzy match."""

    id: str
    name: str
    confidence: float


@dataclass
class FuzzyResult:
    """Complete fuzzy matching result."""

    exact_match: bool
    best_match: FuzzyMatch | None
    suggestions: list[FuzzyMatch]


def fuzzy_match_entity(
    query: str,
    candidates: Sequence[Mapping[str, Any]],
    name_key: str = "name",
    id_key: str = "id",
) -> FuzzyResult:
    """Match a query string against candidate entities using fuzzy matching.

    Returns exact matches immediately. For fuzzy matches, returns candidates
    sorted by confidence score.
    """
    if not query or not candidates:
        return FuzzyResult(exact_match=False, best_match=None, suggestions=[])

    query_lower = query.lower().strip()

    # Check for exact match first
    for candidate in candidates:
        candidate_name = candidate.get(name_key, "")
        if candidate_name and candidate_name.lower() == query_lower:
            return FuzzyResult(
                exact_match=True,
                best_match=FuzzyMatch(
                    id=candidate[id_key],
                    name=candidate_name,
                    confidence=1.0,
                ),
                suggestions=[],
            )

    # Use rapidfuzz for fuzzy matching
    names = [c.get(name_key, "") for c in candidates]
    results: list[tuple[str, float, int]] = process.extract(
        query, names, scorer=fuzz.WRatio, limit=MAX_FUZZY_SUGGESTIONS
    )

    suggestions = []
    for name, score, idx in results:
        normalized_score = score / 100.0
        if normalized_score >= FUZZY_MATCH_THRESHOLD:
            suggestions.append(
                FuzzyMatch(
                    id=candidates[idx][id_key],
                    name=name,
                    confidence=normalized_score,
                )
            )

    suggestions.sort(key=lambda x: x.confidence, reverse=True)
    best_match = suggestions[0] if suggestions else None

    return FuzzyResult(
        exact_match=False,
        best_match=best_match,
        suggestions=suggestions,
    )


def resolve_entity_by_name(
    query: str,
    candidates: Sequence[Mapping[str, Any]],
    entity_type: str,
    auto_accept_matches: bool = False,
    name_key: str = "name",
    id_key: str = "id",
) -> str:
    """Resolve an entity name to its ID using fuzzy matching.

    Raises RetryableToolError with suggestions if no auto-accept and no exact match.
    """
    result = fuzzy_match_entity(query, candidates, name_key, id_key)

    if result.exact_match and result.best_match:
        return result.best_match.id

    threshold = (
        FUZZY_AUTO_ACCEPT_CONFIDENCE if auto_accept_matches else DISABLE_AUTO_ACCEPT_THRESHOLD
    )

    if result.best_match and result.best_match.confidence >= threshold:
        return result.best_match.id

    if not result.suggestions:
        raise ToolExecutionError(
            message=f"No {entity_type} found matching '{query}'",
            developer_message=(
                f"No candidates matched query '{query}' with threshold {FUZZY_MATCH_THRESHOLD}"
            ),
        )

    suggestions_text = "\n".join(
        f"  - {s.name} (confidence: {s.confidence:.0%})"
        for s in result.suggestions[:MAX_DISPLAY_SUGGESTIONS]
    )

    raise RetryableToolError(
        message=f"Multiple {entity_type}s match '{query}'. Please select one.",
        developer_message=f"Fuzzy match for '{query}' returned multiple candidates",
        retry_after_ms=0,
        additional_prompt_content=(
            f"Found similar {entity_type}s:\n{suggestions_text}\n\n"
            f"Please retry with the exact name or set auto_accept_matches=True "
            f"to automatically accept matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence."
        ),
    )


def try_fuzzy_match_by_name(
    entities: Sequence[Mapping[str, Any]],
    name: str,
    auto_accept_matches: bool,
    name_key: str = "name",
    id_key: str = "id",
) -> tuple[list[Mapping[str, Any]], dict[str, Any] | None]:
    """Generic fuzzy matching for entities by name.

    Returns:
        Tuple of (matched_entities, fuzzy_match_info)
        - If exact match or auto_accept with high confidence: returns single match, None
        - If suggestions needed: returns empty list, fuzzy_info with suggestions
        - If no match: returns empty list, None
    """
    if not name or not entities:
        return [], None

    fuzzy_result = fuzzy_match_entity(name, entities, name_key, id_key)

    if fuzzy_result.exact_match and fuzzy_result.best_match:
        matched = [e for e in entities if e.get(id_key) == fuzzy_result.best_match.id]
        return matched, None

    if not fuzzy_result.suggestions:
        return [], None

    if (
        auto_accept_matches
        and fuzzy_result.best_match
        and fuzzy_result.best_match.confidence >= FUZZY_AUTO_ACCEPT_CONFIDENCE
    ):
        matched = [e for e in entities if e.get(id_key) == fuzzy_result.best_match.id]
        return matched, None

    fuzzy_info = {
        "query": name,
        "suggestions": [
            {"id": s.id, "name": s.name, "confidence": round(s.confidence, 2)}
            for s in fuzzy_result.suggestions[:MAX_FUZZY_SUGGESTIONS]
        ],
        "message": f"Multiple matches found for '{name}'. Please select one or be more specific.",
    }
    return [], fuzzy_info
