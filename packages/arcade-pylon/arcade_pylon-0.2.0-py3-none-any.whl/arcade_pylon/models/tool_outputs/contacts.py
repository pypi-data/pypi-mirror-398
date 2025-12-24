"""Tool output types for contacts."""

from typing import Any

from typing_extensions import TypedDict

from arcade_pylon.models.tool_outputs.common import PaginationInfo


class ContactAccount(TypedDict, total=False):
    """Account info for a contact."""

    id: str
    """Account ID."""

    name: str
    """Account name."""


class ContactDetail(TypedDict, total=False):
    """Contact information."""

    id: str
    """Contact ID."""

    name: str
    """Contact name."""

    email: str
    """Primary email address."""

    emails: list[str]
    """All email addresses."""

    avatar_url: str
    """Avatar URL."""

    portal_role: str
    """Portal access role: no_access, member, or admin."""

    account: ContactAccount
    """Associated account."""

    url: str
    """URL to contact in Pylon app."""


class ListContactsOutput(TypedDict, total=False):
    """Output for list_contacts tool."""

    contacts: list[ContactDetail]
    """List of contacts."""

    items_returned: int
    """Number of contacts in this response."""

    pagination: PaginationInfo
    """Pagination info with cursor and has_next_page."""


class ContactMatchResult(TypedDict, total=False):
    """Fuzzy match result for a contact."""

    id: str
    """Contact ID."""

    name: str
    """Contact name."""

    email: str
    """Primary email."""

    url: str
    """URL to contact in Pylon app."""

    confidence: float
    """Match confidence score."""


class SearchContactsOutput(TypedDict, total=False):
    """Output for search_contacts tool."""

    query: str
    """Search query used."""

    matches: list[ContactMatchResult]
    """Matching contacts with confidence scores."""

    fuzzy_info: dict[str, Any] | None
    """Fuzzy match suggestions if multiple matches found."""
