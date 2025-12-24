"""Issue resolution utilities for Pylon toolkit."""

from typing import Any, cast

from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import BM25_DEFAULT_TOP_K
from arcade_pylon.models.enums import IssueLookupMethod
from arcade_pylon.utils.bm25_utils import format_bm25_suggestions, try_bm25_search


async def resolve_issue(
    client: PylonClient,
    lookup_by: IssueLookupMethod,
    value: str,
    auto_accept_matches: bool,
) -> dict[str, Any]:
    """Resolve issue by ID or BM25 search.

    Args:
        client: PylonClient instance.
        lookup_by: How to find the issue (ID or search).
        value: Issue ID or search query.
        auto_accept_matches: Auto-accept high confidence matches.

    Returns:
        The resolved issue data.

    Raises:
        ToolExecutionError: If no issues found.
        RetryableToolError: If multiple matches found with suggestions.
    """
    if lookup_by == IssueLookupMethod.ID:
        return cast(dict[str, Any], await client.get_issue_by_id(value))

    issues = await client.get_latest_issues()
    if not issues:
        raise ToolExecutionError(message="No issues found in the last 30 days.")

    issues_as_dicts = cast(list[dict[str, Any]], issues)
    matched_issue, suggestions = try_bm25_search(
        issues_as_dicts, value, auto_accept_matches, top_k=BM25_DEFAULT_TOP_K
    )

    if matched_issue:
        return matched_issue

    if suggestions:
        raise RetryableToolError(
            message=f"Multiple issues match '{value}'. Use lookup_by=id with issue ID.",
            additional_prompt_content=(
                f"Top {len(suggestions)} matches:\n{format_bm25_suggestions(suggestions)}\n\n"
                "Set lookup_by='id' and use issue ID from suggestions."
            ),
        )

    raise ToolExecutionError(message=f"No issues found matching '{value}'.")


def get_issue_tag_names(issue: dict[str, Any]) -> list[str]:
    """Get normalized issue tag names from an issue payload."""
    tags = issue.get("tags") or []
    if not isinstance(tags, list):
        return []

    names: list[str] = []
    for tag in tags:
        if isinstance(tag, dict):
            name = tag.get("name")
            if isinstance(name, str) and name:
                names.append(name)
        elif isinstance(tag, str) and tag:
            names.append(tag)
    return names
