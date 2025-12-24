"""TypedDict definitions for team tool outputs."""

from typing import Any

from typing_extensions import TypedDict

from arcade_pylon.models.tool_outputs.common import PaginationInfo


class TeamListItem(TypedDict, total=False):
    """Team summary for list views."""

    id: str
    """Team's unique identifier."""

    name: str
    """Team's name."""

    member_count: int
    """Number of members in the team."""

    url: str | None
    """URL to team settings in Pylon app."""

    assignment_url: str | None
    """URL to edit team assignment settings in Pylon app."""


class ListTeamsOutput(TypedDict, total=False):
    """Output for list_teams tool."""

    teams: list[TeamListItem]
    """List of teams in the workspace."""

    items_returned: int
    """Number of teams in this response."""

    pagination: PaginationInfo
    """Pagination information for fetching more results."""


class TeamMember(TypedDict, total=False):
    """Team member information."""

    id: str
    """Member's user ID."""

    email: str | None
    """Member's email address."""

    name: str | None
    """Member's display name."""


class TeamDetail(TypedDict, total=False):
    """Detailed team information."""

    id: str
    """Team's unique identifier."""

    name: str
    """Team's name."""

    members: list[TeamMember]
    """List of team members."""

    member_count: int
    """Number of members in the team."""

    url: str | None
    """URL to team settings in Pylon app."""

    assignment_url: str | None
    """URL to view/edit team assignment settings (strategy, schedule, on-call) in Pylon app."""


class GetTeamOutput(TypedDict, total=False):
    """Output for get_team tool."""

    team: TeamDetail
    """Detailed team information."""

    fuzzy_info: dict[str, Any] | None
    """Fuzzy match suggestions if name lookup used."""
