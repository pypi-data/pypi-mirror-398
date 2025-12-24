"""Common TypedDict definitions shared across Pylon tool outputs."""

from typing_extensions import TypedDict


class PaginationInfo(TypedDict, total=False):
    """Pagination information for paginated tool outputs."""

    has_next_page: bool
    """Whether more results are available."""

    cursor: str | None
    """Cursor for fetching next page of results."""


class UserSummary(TypedDict, total=False):
    """User summary in tool outputs."""

    id: str
    """User's unique identifier."""

    email: str
    """User's email address."""

    name: str | None
    """User's display name."""


class TeamSummary(TypedDict, total=False):
    """Team summary in tool outputs."""

    id: str
    """Team's unique identifier."""

    name: str
    """Team's name."""


class AccountSummary(TypedDict, total=False):
    """Account (company/organization) summary."""

    id: str
    """Account's unique identifier."""


class IssueSummary(TypedDict, total=False):
    """Issue summary for list views."""

    id: str
    """Issue's unique identifier."""

    number: int
    """Human-readable issue number."""

    title: str
    """Issue title."""

    state: str
    """Current issue state."""

    source: str
    """Channel source (slack, email, chat, api)."""

    created_at: str
    """ISO 8601 timestamp in UTC when created."""

    link: str
    """URL to view issue in Pylon."""

    assignee: UserSummary | None
    """Currently assigned user."""

    team: TeamSummary | None
    """Assigned team."""


class FuzzySuggestion(TypedDict, total=False):
    """Suggestion for fuzzy match."""

    id: str
    """Entity ID."""

    name: str
    """Entity name."""

    confidence: float
    """Match confidence score (0.0 to 1.0)."""
