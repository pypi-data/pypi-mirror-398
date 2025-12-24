"""Fuzzy matching utilities for Pylon toolkit."""

from typing import Any

from rapidfuzz import fuzz

from arcade_pylon.constants import (
    DISABLE_AUTO_ACCEPT_THRESHOLD,
    EXACT_MATCH_CONFIDENCE,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    FUZZY_MATCH_THRESHOLD,
    MAX_DISPLAY_SUGGESTIONS,
    MAX_FUZZY_SUGGESTIONS,
)


def fuzzy_match_entities(
    entities: list[dict[str, Any]],
    query: str,
    name_key: str = "name",
) -> list[tuple[dict[str, Any], float]]:
    """Find entities matching query using fuzzy matching.

    Uses weighted combination of exact ratio and partial ratio for better
    matching of partial names (e.g., "John" matches "John Doe").

    Args:
        entities: List of entity dictionaries to search.
        query: Search query string.
        name_key: Key in entity dict containing the name to match.

    Returns:
        List of (entity, confidence_score) tuples, sorted by confidence descending.
    """
    matches: list[tuple[dict[str, Any], float]] = []

    for entity in entities:
        name = entity.get(name_key, "")
        if not name:
            continue

        query_lower = query.lower()
        name_lower = name.lower()
        exact_score = fuzz.ratio(query_lower, name_lower) / 100.0
        partial_score = fuzz.partial_ratio(query_lower, name_lower) / 100.0
        score = max(exact_score, partial_score * 0.95)

        if score >= FUZZY_MATCH_THRESHOLD:
            matches.append((entity, score))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:MAX_FUZZY_SUGGESTIONS]


def try_fuzzy_match_by_name(
    entities: list[dict[str, Any]],
    query: str,
    auto_accept_matches: bool,
    name_key: str = "name",
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    """Try to find entities by name using fuzzy matching.

    Args:
        entities: List of entities to search.
        query: Name to search for.
        auto_accept_matches: Whether to auto-accept high confidence matches.
        name_key: Key in entity dict containing the name.

    Returns:
        Tuple of (matched_entities, fuzzy_info).
        - If exact match found: ([matched_entity], None)
        - If auto_accept and high confidence: ([matched_entity], None)
        - If suggestions available: (None, {"suggestions": [...], "query": ...})
        - If no matches: (None, None)
    """
    if not query:
        return None, None

    matches = fuzzy_match_entities(entities, query, name_key)

    if not matches:
        return None, None

    best_match, best_score = matches[0]

    if best_score == EXACT_MATCH_CONFIDENCE:
        return [best_match], None

    auto_accept_threshold = (
        FUZZY_AUTO_ACCEPT_CONFIDENCE if auto_accept_matches else DISABLE_AUTO_ACCEPT_THRESHOLD
    )

    if best_score >= auto_accept_threshold:
        return [best_match], None

    suggestions = [
        {
            "id": entity.get("id"),
            "name": entity.get(name_key),
            "confidence": round(score, 2),
        }
        for entity, score in matches[:MAX_DISPLAY_SUGGESTIONS]
    ]

    return None, {
        "query": query,
        "suggestions": suggestions,
        "message": f"No exact match for '{query}'. Did you mean one of these?",
    }
