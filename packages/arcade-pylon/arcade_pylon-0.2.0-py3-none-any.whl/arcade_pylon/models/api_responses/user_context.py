"""API response types for user context endpoints."""

from typing_extensions import TypedDict


class MeResponse(TypedDict, total=False):
    """Response from GET /me (data field)."""

    id: str
    name: str
