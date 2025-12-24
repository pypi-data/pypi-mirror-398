"""User tools for Pylon toolkit."""

import base64
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import (
    DEFAULT_PAGE_SIZE,
    EXACT_MATCH_CONFIDENCE,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_DISPLAY_SUGGESTIONS,
    PYLON_API_TOKEN,
)
from arcade_pylon.models.mappers import map_user_detail
from arcade_pylon.models.tool_outputs.users import (
    ListUsersOutput,
    SearchUsersOutput,
)
from arcade_pylon.utils.fuzzy_utils import fuzzy_match_entities
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_users
# API Calls: 1
# APIs Used: GET /users (REST)
# Response Complexity: MEDIUM - array of users
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Users"
#   readOnlyHint: true      - Only reads user data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def list_users(
    context: Context,
    cursor: Annotated[
        str | None,
        "Pagination cursor from previous response. Default is None.",
    ] = None,
    limit: Annotated[
        int,
        f"Maximum number of users to return. Default is {DEFAULT_PAGE_SIZE}.",
    ] = DEFAULT_PAGE_SIZE,
) -> Annotated[ListUsersOutput, "List of users in the workspace."]:
    """List all users/team members in the Pylon workspace."""
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        response = await client.get_users()

    all_users = response.get("data") or []

    start_idx = 0
    if cursor:
        start_idx = int(base64.b64decode(cursor).decode("utf-8"))

    end_idx = start_idx + limit
    users_page = all_users[start_idx:end_idx]
    users = [map_user_detail(dict[str, Any](user)) for user in users_page]

    has_next = end_idx < len(all_users)
    next_cursor = (
        base64.b64encode(str(end_idx).encode("utf-8")).decode("utf-8") if has_next else None
    )

    result: ListUsersOutput = {
        "users": users,
        "items_returned": len(users),
        "total_count": len(all_users),
        "pagination": {"has_next_page": has_next, "cursor": next_cursor},
    }

    return cast(ListUsersOutput, remove_none_values_recursive(result))


# =============================================================================
# search_users
# API Calls: 1
# APIs Used: GET /users (REST) + client-side fuzzy matching
# Response Complexity: MEDIUM - filtered user list with match info
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Search Users"
#   readOnlyHint: true      - Only reads user data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def search_users(
    context: Context,
    query: Annotated[
        str,
        "The name or partial name to search for.",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[SearchUsersOutput, "Users matching the search query."]:
    """Search for users by name using fuzzy matching."""
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        response = await client.get_users()

    users_data = response.get("data") or []
    if not users_data:
        return cast(SearchUsersOutput, {"matches": [], "query": query})

    users_list = [dict[str, Any](u) for u in users_data]
    matches = fuzzy_match_entities(users_list, query, name_key="name")

    if not matches:
        return cast(SearchUsersOutput, {"matches": [], "query": query})

    best_entity, best_score = matches[0]

    if best_score == EXACT_MATCH_CONFIDENCE or (
        auto_accept_matches and best_score >= FUZZY_AUTO_ACCEPT_CONFIDENCE
    ):
        return cast(
            SearchUsersOutput,
            remove_none_values_recursive({
                "matches": [{"user": map_user_detail(best_entity), "confidence": best_score}],
                "query": query,
            }),
        )

    suggestions = [
        {"id": entity.get("id"), "name": entity.get("name"), "confidence": round(score, 2)}
        for entity, score in matches[:MAX_DISPLAY_SUGGESTIONS]
    ]
    return cast(
        SearchUsersOutput,
        {
            "fuzzy_info": {
                "query": query,
                "suggestions": suggestions,
                "message": f"Multiple users match '{query}'. Use auto_accept_matches=True.",
            },
            "query": query,
            "matches": [],
        },
    )
