"""TypedDict definitions for user tool outputs."""

from typing import Any

from typing_extensions import TypedDict

from arcade_pylon.models.tool_outputs.common import PaginationInfo


class UserDetail(TypedDict, total=False):
    """Detailed user information."""

    id: str
    """User's unique identifier."""

    email: str | None
    """User's email address."""

    name: str | None
    """User's display name."""

    avatar_url: str | None
    """URL to user's avatar image."""

    url: str | None
    """URL to user profile in Pylon app."""


class ListUsersOutput(TypedDict, total=False):
    """Output for list_users tool."""

    users: list[UserDetail]
    """List of users in the workspace."""

    items_returned: int
    """Number of users in this response."""

    total_count: int
    """Total number of users available."""

    pagination: PaginationInfo
    """Pagination information for fetching more results."""


class UserMatchResult(TypedDict, total=False):
    """User with match confidence."""

    user: UserDetail
    """User information."""

    confidence: float
    """Match confidence score (0.0 to 1.0)."""


class SearchUsersOutput(TypedDict, total=False):
    """Output for search_users tool."""

    matches: list[UserMatchResult]
    """Users matching the search query, sorted by confidence."""

    query: str
    """The search query used."""

    fuzzy_info: dict[str, Any] | None
    """Fuzzy match suggestions if no auto-accept."""
