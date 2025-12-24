"""Team tools for Pylon toolkit."""

from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import FUZZY_AUTO_ACCEPT_CONFIDENCE, PYLON_API_TOKEN
from arcade_pylon.models.enums import TeamLookupMethod
from arcade_pylon.models.mappers import map_pagination, map_team_detail, map_team_list_item
from arcade_pylon.models.tool_outputs.teams import (
    GetTeamOutput,
    ListTeamsOutput,
)
from arcade_pylon.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_teams
# API Calls: 1
# APIs Used: GET /teams (REST)
# Response Complexity: MEDIUM - array of teams
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Teams"
#   readOnlyHint: true      - Only reads team data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def list_teams(
    context: Context,
    cursor: Annotated[
        str | None,
        "Pagination cursor from previous response. Default is None.",
    ] = None,
) -> Annotated[ListTeamsOutput, "List of teams in the workspace."]:
    """List all teams in the Pylon workspace."""
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        response = await client.get_teams(cursor=cursor)

    teams_data = response.get("data") or []
    teams = [map_team_list_item(dict[str, Any](team)) for team in teams_data]

    result: ListTeamsOutput = {
        "teams": teams,
        "items_returned": len(teams),
        "pagination": map_pagination(response.get("pagination")),
    }

    return cast(ListTeamsOutput, remove_none_values_recursive(result))


# =============================================================================
# get_team_and_assignment
# API Calls: 1-2 (1 if ID, 2 if name lookup)
# APIs Used: GET /teams, GET /teams/{id} (REST)
# Response Complexity: HIGH - includes team members
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Team Details"
#   readOnlyHint: true      - Only reads team data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def get_team_and_assignment(
    context: Context,
    lookup_by: Annotated[
        TeamLookupMethod,
        "How to find the team: 'id' for direct lookup, 'name' for fuzzy name search.",
    ],
    value: Annotated[
        str,
        "Team ID (if lookup_by=id) or team name (if lookup_by=name).",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Only used when lookup_by=name. Default is False.",
    ] = False,
) -> Annotated[GetTeamOutput, "Detailed team information."]:
    """Get detailed information about a Pylon team including members."""
    token = context.get_secret(PYLON_API_TOKEN)
    resolved_id: str = value

    async with PylonClient(token) as client:
        if lookup_by == TeamLookupMethod.NAME:
            teams_response = await client.get_teams()
            teams = [dict[str, Any](t) for t in (teams_response.get("data") or [])]

            matched, fuzzy_info = try_fuzzy_match_by_name(teams, value, auto_accept_matches)

            if fuzzy_info:
                return cast(GetTeamOutput, {"fuzzy_info": fuzzy_info})

            if not matched:
                raise ToolExecutionError(message=f"Team not found: {value}")

            resolved_id = matched[0]["id"]

        team_data = await client.get_team_by_id(resolved_id)

    team = map_team_detail(dict[str, Any](team_data))
    result: GetTeamOutput = {"team": team}

    return cast(GetTeamOutput, remove_none_values_recursive(result))
