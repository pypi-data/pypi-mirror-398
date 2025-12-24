"""Message tools for Pylon toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import PYLON_API_TOKEN
from arcade_pylon.models.mappers import map_message
from arcade_pylon.models.tool_outputs.messages import AddInternalNoteOutput
from arcade_pylon.utils.html_utils import escape_html_if_needed
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# add_internal_note
# API Calls: 1
# APIs Used: POST /issues/{id}/note (REST)
# Response Complexity: LOW - created message
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Add Internal Note to Issue"
#   readOnlyHint: false     - Creates new message
#   destructiveHint: false  - Additive operation
#   idempotentHint: false   - Each call creates new message
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def add_internal_note(
    context: Context,
    issue_id: Annotated[
        str,
        "The issue ID (UUID) or issue number to add message to.",
    ],
    body: Annotated[
        str,
        "The message content to add.",
    ],
    as_html: Annotated[
        bool,
        "Whether body is already HTML formatted. Default is False (plain text).",
    ] = False,
) -> Annotated[AddInternalNoteOutput, "Created internal note details."]:
    """Add an internal note to a Pylon issue."""
    body_html = escape_html_if_needed(body, as_html)

    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        message_data = await client.create_note(
            issue_id=issue_id,
            body_html=body_html,
        )

    result: AddInternalNoteOutput = {
        "message": map_message(message_data),
    }

    return cast(AddInternalNoteOutput, remove_none_values_recursive(result))
