"""API response types for messages endpoints."""

from typing_extensions import TypedDict

from arcade_pylon.models.api_responses.common import AuthorRef, BaseListResponse, BaseSingleResponse


class MessageData(TypedDict, total=False):
    """Raw message data from API."""

    id: str
    issue_id: str
    body_html: str
    created_at: str
    author: AuthorRef
    is_internal: bool
    attachment_urls: list[str]


class MessagesListResponse(BaseListResponse, total=False):
    """Response from GET /messages."""

    data: list[MessageData]


class MessageSingleResponse(BaseSingleResponse, total=False):
    """Response from POST /messages."""

    data: MessageData
