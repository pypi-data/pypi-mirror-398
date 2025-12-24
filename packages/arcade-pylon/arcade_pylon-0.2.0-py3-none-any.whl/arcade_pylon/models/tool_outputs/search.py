"""Tool output types for search operations."""

from typing_extensions import TypedDict


class BM25SearchResult(TypedDict, total=False):
    """BM25 search result for an issue."""

    issue_id: str
    """Issue's unique identifier."""

    issue_number: int
    """Human-readable issue number."""

    title: str
    """Issue title."""

    score: float
    """BM25 relevance score (higher = more relevant)."""

    link: str
    """URL to view issue in Pylon."""
