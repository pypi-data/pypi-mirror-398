"""Issue tools for Pylon toolkit."""

from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import (
    BM25_AUTO_ACCEPT_THRESHOLD,
    BM25_DEFAULT_TOP_K,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    PYLON_API_TOKEN,
)
from arcade_pylon.models.enums import IssueLookupMethod, IssueState, UserLookupMethod
from arcade_pylon.models.mappers import (
    map_issue_detail,
    map_issue_summary,
    map_pagination,
    map_user,
)
from arcade_pylon.models.tool_outputs.issues import (
    AssignIssueOutput,
    GetIssueOutput,
    ListIssuesOutput,
    SearchIssuesOutput,
    UpdateIssueStatusOutput,
)
from arcade_pylon.utils import issue_utils
from arcade_pylon.utils.bm25_utils import format_bm25_suggestions, try_bm25_search
from arcade_pylon.utils.date_utils import get_default_date_range, validate_date_range
from arcade_pylon.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_issues
# API Calls: 1
# APIs Used: GET /issues (REST) + client-side filtering
# Response Complexity: MEDIUM - array of issue summaries
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Issues"
#   readOnlyHint: true      - Only reads issue data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def list_issues(
    context: Context,
    state: Annotated[
        IssueState | None,
        "Filter by issue state. Default is None (all states).",
    ] = None,
    assignee_id: Annotated[
        str | None,
        "Filter by assignee user ID. Default is None (all assignees).",
    ] = None,
    team_id: Annotated[
        str | None,
        "Filter by team ID. Default is None (all teams).",
    ] = None,
    tags: Annotated[
        list[str] | None,
        "Filter by tags (issues must have all listed tags). Default is None.",
    ] = None,
    start_time: Annotated[
        str | None,
        "Start of date range in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ). Default is 7 days ago.",
    ] = None,
    end_time: Annotated[
        str | None,
        "End of date range in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ). Default is now.",
    ] = None,
    cursor: Annotated[
        str | None,
        "Pagination cursor from previous response. Default is None.",
    ] = None,
) -> Annotated[ListIssuesOutput, "List of issues matching the filters."]:
    """List Pylon issues with optional filtering by state, assignee, team, and tags."""
    if start_time is None or end_time is None:
        default_start, default_end = get_default_date_range()
        start_time = start_time or default_start
        end_time = end_time or default_end

    validate_date_range(start_time, end_time)

    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        response = await client.get_issues(
            start_time=start_time,
            end_time=end_time,
            cursor=cursor,
        )

    issues_data = response.get("data") or []

    if state:
        issues_data = [i for i in issues_data if i.get("state") == state.value]
    if assignee_id:
        issues_data = [i for i in issues_data if (i.get("assignee") or {}).get("id") == assignee_id]
    if team_id:
        issues_data = [i for i in issues_data if (i.get("team") or {}).get("id") == team_id]
    if tags:
        issues_data = [
            i
            for i in issues_data
            if all(t in issue_utils.get_issue_tag_names(dict[str, Any](i)) for t in tags)
        ]
    issues = [map_issue_summary(issue) for issue in issues_data]

    result: ListIssuesOutput = {
        "issues": issues,
        "items_returned": len(issues),
        "pagination": map_pagination(response.get("pagination")),
        "date_range": {"start_time": start_time, "end_time": end_time},
    }

    return cast(ListIssuesOutput, remove_none_values_recursive(result))


# =============================================================================
# get_issue
# API Calls: 1 (direct) or 1+ (search)
# APIs Used: GET /issues/{id}, GET /issues (REST)
# Response Complexity: HIGH - full issue with all fields
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Issue"
#   readOnlyHint: true      - Only reads issue data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def get_issue(
    context: Context,
    lookup_by: Annotated[
        IssueLookupMethod,
        "How to find the issue: 'id' for direct lookup, 'search' for keyword search.",
    ],
    value: Annotated[
        str,
        "Issue ID/number (if lookup_by=id) or search keywords (if lookup_by=search). "
        "For search: use word stems like 'auth' or 'config' for broader matches.",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept search matches above {BM25_AUTO_ACCEPT_THRESHOLD:.0%} confidence gap. "
        "Only used with lookup_by=search. Default is False.",
    ] = False,
) -> Annotated[GetIssueOutput, "Detailed issue information."]:
    """Get detailed information about a Pylon issue.

    For search: uses BM25 ranking. Use word stems ('auth', 'config') and AND/OR/NOT operators.
    """
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        issue_data = await issue_utils.resolve_issue(client, lookup_by, value, auto_accept_matches)

    issue = map_issue_detail(issue_data)
    result: GetIssueOutput = {"issue": issue}

    return cast(GetIssueOutput, remove_none_values_recursive(result))


# =============================================================================
# assign_issue
# API Calls: 1-3 (varies by lookup method)
# APIs Used: GET /issues/{id}, GET /issues, GET /users, PATCH /issues/{id} (REST)
# Response Complexity: MEDIUM - updated issue
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Assign Issue"
#   readOnlyHint: false     - Modifies issue
#   destructiveHint: false  - Assignment is reversible
#   idempotentHint: true    - Same assignment = same result
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def assign_issue(
    context: Context,
    issue_lookup_by: Annotated[
        IssueLookupMethod,
        "How to find the issue: 'id' for direct lookup, 'search' for keyword search.",
    ],
    issue_value: Annotated[
        str,
        "Issue ID/number (if issue_lookup_by=id) or search keywords (if issue_lookup_by=search).",
    ],
    user_lookup_by: Annotated[
        UserLookupMethod,
        "How to find the user: 'id' for direct lookup, 'name' for fuzzy name search.",
    ],
    user_value: Annotated[
        str,
        "User ID (if user_lookup_by=id) or user name (if user_lookup_by=name).",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy/BM25 matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[AssignIssueOutput, "Updated issue with assignment details."]:
    """Assign a Pylon issue to a user.

    For issue search: uses BM25 ranking. Use word stems ('auth', 'config') and AND/OR/NOT.
    For user search: uses fuzzy name matching.
    """
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        current_issue = await issue_utils.resolve_issue(
            client, issue_lookup_by, issue_value, auto_accept_matches
        )
        resolved_issue_id = str(current_issue.get("id", ""))
        previous_assignee = current_issue.get("assignee")

        assignee_id: str | None = None
        if user_lookup_by == UserLookupMethod.ID:
            assignee_id = user_value
        else:
            users_response = await client.get_users()
            users = cast(list[dict[str, Any]], users_response.get("data", []))

            matched, fuzzy_info = try_fuzzy_match_by_name(
                users, user_value, auto_accept_matches, name_key="name"
            )

            if fuzzy_info:
                suggestions = fuzzy_info["suggestions"]
                suggestions_text = ", ".join(
                    f"{s['name']} (ID: {s['id']}, {s['confidence']:.0%})" for s in suggestions
                )
                raise RetryableToolError(
                    message=fuzzy_info["message"],
                    additional_prompt_content=(
                        f"Suggestions: {suggestions_text}. "
                        "Use user_lookup_by='id' with user ID or set auto_accept_matches=True."
                    ),
                )

            if not matched:
                raise ToolExecutionError(message=f"User not found: {user_value}")

            assignee_id = matched[0]["id"]

        updated_issue = await client.update_issue(resolved_issue_id, {"assignee_id": assignee_id})

    result: AssignIssueOutput = {
        "issue": map_issue_summary(updated_issue),
        "previous_assignee": map_user(previous_assignee) if previous_assignee else None,
        "new_assignee": map_user(updated_issue.get("assignee")),
    }

    return cast(AssignIssueOutput, remove_none_values_recursive(result))


# =============================================================================
# update_issue_status
# API Calls: 1 (direct) or 2+ (search)
# APIs Used: GET /issues/{id}, GET /issues, PATCH /issues/{id} (REST)
# Response Complexity: MEDIUM - updated issue
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Update Issue Status"
#   readOnlyHint: false     - Modifies issue
#   destructiveHint: false  - Status change is reversible
#   idempotentHint: true    - Same status = same result
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def update_issue_status(
    context: Context,
    state: Annotated[
        IssueState,
        "The new state for the issue.",
    ],
    lookup_by: Annotated[
        IssueLookupMethod,
        "How to find the issue: 'id' for direct lookup, 'search' for keyword search.",
    ],
    value: Annotated[
        str,
        "Issue ID/number (if lookup_by=id) or search keywords (if lookup_by=search).",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept BM25 search matches above {BM25_AUTO_ACCEPT_THRESHOLD:.0%} confidence gap. "
        "Default is False.",
    ] = False,
) -> Annotated[UpdateIssueStatusOutput, "Updated issue with state change details."]:
    """Change the state of a Pylon issue.

    For search: uses BM25 ranking. Use word stems ('auth', 'config') and AND/OR/NOT operators.
    """
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        current_issue = await issue_utils.resolve_issue(
            client, lookup_by, value, auto_accept_matches
        )
        resolved_issue_id = str(current_issue.get("id", ""))
        previous_state = current_issue.get("state", "unknown")

        updated_issue = await client.update_issue(resolved_issue_id, {"state": state.value})

    result: UpdateIssueStatusOutput = {
        "issue": map_issue_summary(updated_issue),
        "previous_state": previous_state,
        "new_state": updated_issue.get("state", state.value),
    }

    return cast(UpdateIssueStatusOutput, remove_none_values_recursive(result))


# =============================================================================
# search_issues
# API Calls: 1+ (fetches up to 400 issues for search indexing via parallel requests)
# APIs Used: GET /issues (REST)
# Response Complexity: MEDIUM - search results with scores
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Search Issues"
#   readOnlyHint: true      - Only reads issue data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def search_issues(
    context: Context,
    query: Annotated[
        str,
        "Keywords to search in issue titles and descriptions. "
        "Use word stems like 'auth' or 'config' for broader matches. "
        "Supports AND, OR, NOT operators.",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept high-confidence matches above {BM25_AUTO_ACCEPT_THRESHOLD:.0%} score gap. "
        "Default is False.",
    ] = False,
) -> Annotated[SearchIssuesOutput, "Search results or matched issue."]:
    """Search issues recently created by keywords in title and description.

    Note: This indexes up to 400 issues from the last 30 days.

    Uses BM25 ranking. Use word stems ('auth', 'config') and AND/OR/NOT operators.
    """
    if not query or not query.strip():
        raise ToolExecutionError(message="Search query cannot be empty.")

    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        issues = await client.get_latest_issues()

    if not issues:
        raise ToolExecutionError(
            message="No issues found in the last 30 days to search.",
        )

    issues_as_dicts = cast(list[dict[str, Any]], issues)
    matched_issue, suggestions = try_bm25_search(
        issues_as_dicts, query, auto_accept_matches, top_k=BM25_DEFAULT_TOP_K
    )

    if matched_issue:
        result: SearchIssuesOutput = {
            "issue": map_issue_detail(matched_issue),
            "results_count": 1,
            "query": query,
        }
        return cast(SearchIssuesOutput, remove_none_values_recursive(result))

    if suggestions:
        raise RetryableToolError(
            message=f"Multiple issues match '{query}'. Select one by ID or number.",
            additional_prompt_content=(
                f"Top {len(suggestions)} matches:\n{format_bm25_suggestions(suggestions)}\n\n"
                "Use get_issue, assign_issue, or update_issue_status with lookup_by='id'."
            ),
        )

    raise ToolExecutionError(
        message=f"No issues found matching '{query}'.",
        developer_message=f"BM25 search returned no results for query: {query}",
    )
