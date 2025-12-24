"""Tool output types for issue operations."""

from typing_extensions import TypedDict

from arcade_pylon.models.tool_outputs.common import (
    AccountSummary,
    IssueSummary,
    PaginationInfo,
    TeamSummary,
    UserSummary,
)


class DateRange(TypedDict, total=False):
    """Date range used in query."""

    start_time: str
    """Start of date range in RFC3339 format."""

    end_time: str
    """End of date range in RFC3339 format."""


class ListIssuesOutput(TypedDict, total=False):
    """Output for list_issues tool."""

    issues: list[IssueSummary]
    """List of issues matching the criteria."""

    items_returned: int
    """Number of issues in this response."""

    pagination: PaginationInfo
    """Pagination information for fetching more results."""

    date_range: DateRange
    """The date range used for the query."""


class IssueDetail(TypedDict, total=False):
    """Detailed issue information."""

    id: str
    """Issue's unique identifier."""

    number: int
    """Human-readable issue number."""

    title: str
    """Issue title."""

    body_html: str
    """Issue body content in HTML."""

    state: str
    """Current issue state."""

    source: str
    """Channel source (slack, email, chat, api)."""

    priority: str | None
    """Issue priority (urgent, high, medium, low)."""

    created_at: str
    """ISO 8601 timestamp in UTC when created."""

    resolution_time: str | None
    """ISO 8601 timestamp when resolved."""

    first_response_time: str | None
    """ISO 8601 timestamp of first response."""

    first_response_seconds: int | None
    """Seconds until first response."""

    link: str
    """URL to view issue in Pylon."""

    assignee: UserSummary | None
    """Currently assigned user."""

    requester: UserSummary | None
    """User who created the issue."""

    team: TeamSummary | None
    """Assigned team."""

    account: AccountSummary | None
    """Associated account/company."""

    tags: list[str]
    """List of tag names."""

    snoozed_until_time: str | None
    """ISO 8601 timestamp if snoozed."""


class GetIssueOutput(TypedDict, total=False):
    """Output for get_issue tool."""

    issue: IssueDetail
    """Detailed issue information."""


class AssignIssueOutput(TypedDict, total=False):
    """Output for assign_issue tool."""

    issue: IssueSummary
    """Updated issue with new assignee."""

    previous_assignee: UserSummary | None
    """Previously assigned user (if any)."""

    new_assignee: UserSummary
    """Newly assigned user."""


class UpdateIssueStatusOutput(TypedDict, total=False):
    """Output for update_issue_status tool."""

    issue: IssueSummary
    """Updated issue with new state."""

    previous_state: str
    """Previous state before update."""

    new_state: str
    """New state after update."""


class SearchIssuesOutput(TypedDict, total=False):
    """Output for search_issues tool."""

    issue: IssueDetail | None
    """Matched issue if auto-accepted."""

    results_count: int
    """Number of matching issues found."""

    query: str
    """The search query used."""
