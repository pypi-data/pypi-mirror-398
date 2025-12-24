"""API response types for teams endpoints."""

from typing_extensions import TypedDict

from arcade_pylon.models.api_responses.common import (
    AssignmentConfig,
    BaseListResponse,
    BaseSingleResponse,
    UserRef,
    UserSchedule,
)


class TeamData(TypedDict, total=False):
    """Raw team data from API."""

    id: str
    name: str
    members: list[UserRef]
    assignment_strategy: str
    timezone: str
    assignment_config: AssignmentConfig
    assignment_schedule: list[UserSchedule]


class TeamsListResponse(BaseListResponse, total=False):
    """Response from GET /teams."""

    data: list[TeamData]


class TeamSingleResponse(BaseSingleResponse, total=False):
    """Response from GET /teams/{id} and PATCH /teams/{id}."""

    data: TeamData
