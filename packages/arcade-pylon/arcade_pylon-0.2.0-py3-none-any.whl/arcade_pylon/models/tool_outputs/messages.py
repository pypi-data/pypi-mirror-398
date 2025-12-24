"""Tool output types for message operations."""

from typing_extensions import TypedDict


class MessageAuthor(TypedDict, total=False):
    """Message author information."""

    id: str
    """Author's unique identifier."""

    email: str | None
    """Author's email address."""

    type: str
    """Author type: 'user' or 'contact'."""


class MessageOutput(TypedDict, total=False):
    """Message information."""

    id: str
    """Message's unique identifier."""

    issue_id: str
    """ID of the issue this message belongs to."""

    body_html: str
    """Message content in HTML."""

    created_at: str
    """ISO 8601 timestamp in UTC when created."""

    is_internal: bool
    """Whether this is an internal note."""

    author: MessageAuthor | None
    """Message author."""


class AddMessageOutput(TypedDict, total=False):
    """Output for add_message tool."""

    message: MessageOutput
    """Created message details."""


class AddInternalNoteOutput(TypedDict, total=False):
    """Output for add_internal_note tool."""

    message: MessageOutput
    """Created note details."""
