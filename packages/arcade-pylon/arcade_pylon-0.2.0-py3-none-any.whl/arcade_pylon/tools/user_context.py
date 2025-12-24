"""User context tools for Pylon toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import PYLON_API_TOKEN
from arcade_pylon.models.mappers import map_who_am_i
from arcade_pylon.models.tool_outputs import WhoAmIOutput
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# who_am_i
# API Calls: 1
# APIs Used: GET /me (REST)
# Response Complexity: LOW - user profile
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Who Am I"
#   readOnlyHint: true       - Only reads user data, no modifications
#   openWorldHint: true      - Interacts with Pylon's external API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def who_am_i(
    context: Context,
) -> Annotated[WhoAmIOutput, "Authenticated user's profile."]:
    """Get the authenticated user's profile.

    NOTE: This returns the API token owner (service account), not the human user.
    """
    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        me_data = await client.get_me()

    result = map_who_am_i(me_data)
    return cast(WhoAmIOutput, remove_none_values_recursive(result))
