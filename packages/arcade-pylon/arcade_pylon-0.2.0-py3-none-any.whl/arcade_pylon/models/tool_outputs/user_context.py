"""Tool output types for user context."""

from typing_extensions import TypedDict


class WhoAmIOutput(TypedDict, total=False):
    """Output for who_am_i tool."""

    id: str
    """User's unique identifier."""

    name: str | None
    """User's display name."""
