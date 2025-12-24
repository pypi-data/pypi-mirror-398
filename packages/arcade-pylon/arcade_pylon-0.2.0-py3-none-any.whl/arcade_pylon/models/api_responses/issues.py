"""API response types for issues endpoints."""

from typing import Any

from typing_extensions import TypedDict

from arcade_pylon.models.api_responses.common import (
    AccountRef,
    BaseListResponse,
    BaseSingleResponse,
    ChatWidgetInfo,
    CSATResponse,
    CustomFieldValue,
    ExternalIssueRef,
    FollowerRef,
    SlackInfo,
    TeamRef,
    UserRef,
)


class IssueData(TypedDict, total=False):
    """Raw issue data from API."""

    id: str
    number: int
    title: str
    body_html: str
    state: str
    source: str
    type: str
    created_at: str
    latest_message_time: str
    first_response_time: str
    first_response_seconds: int
    business_hours_first_response_seconds: int
    resolution_time: str
    resolution_seconds: int
    business_hours_resolution_seconds: int
    number_of_touches: int
    link: str
    snoozed_until_time: str
    customer_portal_visible: bool
    assignee: UserRef
    requester: UserRef
    team: TeamRef
    account: AccountRef
    tags: list[str]
    custom_fields: dict[str, CustomFieldValue]
    external_issues: list[ExternalIssueRef]
    attachment_urls: list[str]
    csat_responses: list[CSATResponse]
    slack: SlackInfo
    chat_widget_info: ChatWidgetInfo


class IssuesListResponse(BaseListResponse, total=False):
    """Response from GET /issues and POST /issues/search."""

    data: list[IssueData]


class IssueSingleResponse(BaseSingleResponse, total=False):
    """Response from GET/POST/PATCH /issues/{id}."""

    data: IssueData


class FollowersListResponse(BaseSingleResponse, total=False):
    """Response from GET /issues/{id}/followers."""

    data: list[FollowerRef]


class IssueSearchFilter(TypedDict, total=False):
    """Filter for POST /issues/search request body."""

    state: str
    assignee_id: str
    team_id: str
    tags: list[str]
    created_after: str
    created_before: str


class IssueSearchRequest(TypedDict, total=False):
    """Request body for POST /issues/search."""

    filter: IssueSearchFilter | dict[str, Any]
    cursor: str
    limit: int
