"""API response types for users endpoints."""

from typing_extensions import TypedDict

from arcade_pylon.models.api_responses.common import BaseListResponse, BaseSingleResponse


class UserData(TypedDict, total=False):
    """Raw user data from API."""

    id: str
    email: str
    name: str
    avatar_url: str
    role: str
    status: str


class UsersListResponse(BaseListResponse, total=False):
    """Response from GET /users."""

    data: list[UserData]


class UserSingleResponse(BaseSingleResponse, total=False):
    """Response from GET /users/{id}."""

    data: UserData
