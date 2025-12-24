"""API response types for contacts."""

from typing import Any

from typing_extensions import TypedDict


class MiniAccountData(TypedDict, total=False):
    """Minimal account info embedded in contact."""

    id: str
    name: str


class ContactData(TypedDict, total=False):
    """Raw contact data from Pylon API."""

    id: str
    name: str
    email: str
    emails: list[str]
    avatar_url: str
    portal_role: str
    account: MiniAccountData
    custom_fields: dict[str, Any]


class ContactsListResponse(TypedDict, total=False):
    """Response from GET /contacts."""

    data: list[ContactData]
    pagination: dict[str, Any]


class ContactSingleResponse(TypedDict, total=False):
    """Response from GET /contacts/{id}."""

    data: ContactData
    request_id: str


class ContactSearchFilter(TypedDict, total=False):
    """Filter for contact search."""

    field: str
    operator: str
    value: Any


class ContactSearchRequest(TypedDict, total=False):
    """Request body for POST /contacts/search."""

    filter: ContactSearchFilter
    cursor: str
    limit: int
