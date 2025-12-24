"""Contact workflow utilities for Pylon toolkit."""

from collections.abc import Mapping
from typing import Any, cast

from rapidfuzz import fuzz

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import (
    EXACT_MATCH_CONFIDENCE,
    MAX_CONTACTS_PAGE_SIZE,
    MAX_DISPLAY_SUGGESTIONS,
    MAX_FUZZY_SUGGESTIONS,
    PYLON_APP_URL,
)
from arcade_pylon.models.tool_outputs.contacts import ContactMatchResult, SearchContactsOutput
from arcade_pylon.utils.fuzzy_utils import fuzzy_match_entities
from arcade_pylon.utils.response_utils import remove_none_values_recursive


async def fetch_contacts_by_email(
    client: PylonClient,
    email_query: str,
    max_pages: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch contacts matching an email query across pages."""
    contacts: list[dict[str, Any]] = []
    cursor: str | None = None

    for _ in range(max_pages):
        response = await client.search_contacts_by_email(
            email_query,
            cursor=cursor,
            limit=MAX_CONTACTS_PAGE_SIZE,
        )
        contacts.extend(cast(list[dict[str, Any]], response.get("data") or []))

        has_next, cursor = _get_next_page_cursor(response.get("pagination"))
        if not has_next or not cursor:
            return contacts, False

    return contacts, True


async def fetch_contacts_for_name_search(
    client: PylonClient,
    max_pages: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch contacts for name search across pages."""
    contacts: list[dict[str, Any]] = []
    cursor: str | None = None

    for _ in range(max_pages):
        response = await client.get_contacts(cursor=cursor, limit=MAX_CONTACTS_PAGE_SIZE)
        contacts.extend(cast(list[dict[str, Any]], response.get("data") or []))

        has_next, cursor = _get_next_page_cursor(response.get("pagination"))
        if not has_next or not cursor:
            return contacts, False

    return contacts, True


def build_search_contacts_output(
    *,
    query: str,
    contacts: list[dict[str, Any]],
    is_email_search: bool,
    auto_accept_matches: bool,
    truncated: bool,
    max_pages: int,
) -> SearchContactsOutput:
    """Build SearchContactsOutput from contact data."""
    if not contacts:
        empty_output: SearchContactsOutput = {"query": query, "matches": []}
        if truncated:
            empty_output["fuzzy_info"] = _build_truncated_fuzzy_info(max_pages)
        return cast(SearchContactsOutput, remove_none_values_recursive(empty_output))

    results: list[ContactMatchResult]
    if is_email_search:
        results = _build_email_results(query=query, contacts=contacts)
    else:
        matches = fuzzy_match_entities(contacts, query, name_key="name")
        results = [
            {
                "id": entity.get("id", ""),
                "name": entity.get("name", ""),
                "email": entity.get("email", ""),
                "url": f"{PYLON_APP_URL}/contacts/{entity.get('id', '')}",
                "confidence": round(score, 2),
            }
            for entity, score in matches
        ]

    output: SearchContactsOutput = {"query": query, "matches": results[:MAX_FUZZY_SUGGESTIONS]}

    if not auto_accept_matches and len(results) > 1:
        message = "Multiple contacts found. Use contact ID for exact match."
        if truncated:
            message = _append_truncated_notice(message, max_pages)
        output["fuzzy_info"] = {
            "message": message,
            "suggestions": [
                {"id": r["id"], "name": r["name"], "confidence": r["confidence"]}
                for r in results[:MAX_DISPLAY_SUGGESTIONS]
            ],
        }
        return cast(SearchContactsOutput, remove_none_values_recursive(output))

    if truncated:
        output["fuzzy_info"] = _build_truncated_fuzzy_info(max_pages)

    return cast(SearchContactsOutput, remove_none_values_recursive(output))


def _build_email_results(*, query: str, contacts: list[dict[str, Any]]) -> list[ContactMatchResult]:
    query_lower = query.strip().lower()

    results: list[ContactMatchResult] = []
    for contact in contacts:
        email = str(contact.get("email") or "")
        email_lower = email.lower()
        if not email:
            continue

        if email_lower == query_lower:
            confidence = EXACT_MATCH_CONFIDENCE
        else:
            exact_score = fuzz.ratio(query_lower, email_lower) / 100.0
            partial_score = fuzz.partial_ratio(query_lower, email_lower) / 100.0
            confidence = round(max(exact_score, partial_score * 0.95), 2)

        results.append({
            "id": contact.get("id", ""),
            "name": contact.get("name", ""),
            "email": email,
            "url": f"{PYLON_APP_URL}/contacts/{contact.get('id', '')}",
            "confidence": confidence,
        })

    results.sort(key=lambda r: cast(float, r.get("confidence", 0.0)), reverse=True)
    return results


def _build_truncated_fuzzy_info(max_pages: int) -> dict[str, Any]:
    return {
        "message": (
            f"Contact search stopped after {max_pages} pages; results may be incomplete. "
            "Increase max_pages to search further."
        ),
        "suggestions": [],
    }


def _append_truncated_notice(message: str, max_pages: int) -> str:
    return (
        f"{message} Contact search stopped after {max_pages} pages; results may be incomplete. "
        "Increase max_pages to search further."
    )


def _get_next_page_cursor(pagination: Any) -> tuple[bool, str | None]:
    if not isinstance(pagination, Mapping):
        return False, None
    return bool(pagination.get("has_next_page", False)), cast(str | None, pagination.get("cursor"))
