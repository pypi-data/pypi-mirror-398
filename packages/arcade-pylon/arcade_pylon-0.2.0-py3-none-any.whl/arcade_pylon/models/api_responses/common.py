"""Common API response types for Pylon toolkit."""

from typing_extensions import TypedDict


class PaginationResponse(TypedDict, total=False):
    """Pagination in API response."""

    cursor: str
    has_next_page: bool


class UserRef(TypedDict, total=False):
    """User reference in API response (embedded in other objects)."""

    id: str
    email: str
    name: str


class TeamRef(TypedDict, total=False):
    """Team reference in API response."""

    id: str


class AccountRef(TypedDict, total=False):
    """Account reference in API response."""

    id: str


class AuthorRef(TypedDict, total=False):
    """Author reference in message API response."""

    id: str
    email: str
    type: str


class ExternalIssueRef(TypedDict, total=False):
    """External issue link in API response."""

    external_id: str
    link: str
    source: str


class CustomFieldValue(TypedDict, total=False):
    """Custom field value in API response."""

    slug: str
    value: str
    values: list[str]


class CSATResponse(TypedDict, total=False):
    """CSAT response in API response."""

    score: int
    comment: str


class SlackInfo(TypedDict, total=False):
    """Slack channel info in API response."""

    channel_id: str
    message_ts: str
    workspace_id: str


class ChatWidgetInfo(TypedDict, total=False):
    """Chat widget info in API response."""

    page_url: str


class FollowerRef(TypedDict, total=False):
    """Follower reference in API response."""

    id: str
    type: str


class DaySchedule(TypedDict, total=False):
    """Day schedule in assignment schedule."""

    start: str
    end: str


class WeekSchedule(TypedDict, total=False):
    """Week schedule in assignment schedule."""

    sunday: DaySchedule
    monday: DaySchedule
    tuesday: DaySchedule
    wednesday: DaySchedule
    thursday: DaySchedule
    friday: DaySchedule
    saturday: DaySchedule


class UserSchedule(TypedDict, total=False):
    """User assignment schedule in API response."""

    user_id: str
    schedule: WeekSchedule


class AssignmentConfig(TypedDict, total=False):
    """Assignment configuration in team API response."""

    only_active_users: bool
    override_existing_assignee: bool
    capacity_behavior: str


class BaseListResponse(TypedDict, total=False):
    """Base type for paginated list responses."""

    pagination: PaginationResponse
    request_id: str


class BaseSingleResponse(TypedDict, total=False):
    """Base type for single item responses."""

    request_id: str


class TagData(TypedDict, total=False):
    """Raw tag data from API."""

    id: str
    name: str
    color: str


class TagsListResponse(BaseListResponse, total=False):
    """Response from GET /tags."""

    data: list[TagData]
