"""Contact tools for Pylon toolkit."""

from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_pylon.client import PylonClient
from arcade_pylon.constants import (
    DEFAULT_PAGE_SIZE,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_CONTACTS_PAGE_SIZE,
    PYLON_API_TOKEN,
)
from arcade_pylon.models.mappers import map_contact, map_pagination
from arcade_pylon.models.tool_outputs.contacts import (
    ListContactsOutput,
    SearchContactsOutput,
)
from arcade_pylon.utils import contacts_utils
from arcade_pylon.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_contacts
# API Calls: 1
# APIs Used: GET /contacts (REST)
# Response Complexity: MEDIUM - list of contacts with accounts
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Contacts"
#   readOnlyHint: true      - Only reads contact data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def list_contacts(
    context: Context,
    cursor: Annotated[
        str | None,
        "Pagination cursor from previous response. Default is None (first page).",
    ] = None,
    limit: Annotated[
        int,
        f"Maximum number of contacts to return per page. Default is {DEFAULT_PAGE_SIZE}.",
    ] = DEFAULT_PAGE_SIZE,
) -> Annotated[ListContactsOutput, "List of contacts with pagination."]:
    """List contacts in Pylon."""
    if limit < 1 or limit > MAX_CONTACTS_PAGE_SIZE:
        raise ToolExecutionError(
            message=f"limit must be between 1 and {MAX_CONTACTS_PAGE_SIZE}.",
        )

    token = context.get_secret(PYLON_API_TOKEN)
    async with PylonClient(token) as client:
        response = await client.get_contacts(cursor=cursor, limit=limit)

    contacts_data = response.get("data") or []
    contacts = [map_contact(dict[str, Any](c)) for c in contacts_data]

    result: ListContactsOutput = {
        "contacts": contacts,
        "items_returned": len(contacts),
        "pagination": map_pagination(response.get("pagination")),
    }

    return cast(ListContactsOutput, remove_none_values_recursive(result))


# =============================================================================
# search_contacts
# API Calls: 1-10 (up to max_pages pages for email or name search)
# APIs Used: POST /contacts/search, GET /contacts (REST)
# Response Complexity: MEDIUM - matched contacts with confidence
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Search Contacts"
#   readOnlyHint: true      - Only reads contact data
#   openWorldHint: true     - Interacts with Pylon API
# =============================================================================
@tool(requires_secrets=[PYLON_API_TOKEN])
async def search_contacts(
    context: Context,
    query: Annotated[str, "Name or email to search for."],
    auto_accept_matches: Annotated[
        bool,
        (
            f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE} "
            "confidence. Default is False."
        ),
    ] = False,
    max_pages: Annotated[
        int,
        "Maximum pages to scan when searching contacts. Default is 10.",
    ] = 10,
) -> Annotated[SearchContactsOutput, "Matching contacts with confidence scores."]:
    """Search for contacts by name or email using fuzzy matching."""
    if max_pages < 1:
        raise ToolExecutionError(message="max_pages must be at least 1.")

    token = context.get_secret(PYLON_API_TOKEN)
    is_email_search = "@" in query

    async with PylonClient(token) as client:
        if is_email_search:
            contacts, truncated = await contacts_utils.fetch_contacts_by_email(
                client,
                email_query=query,
                max_pages=max_pages,
            )
        else:
            contacts, truncated = await contacts_utils.fetch_contacts_for_name_search(
                client,
                max_pages=max_pages,
            )

    output = contacts_utils.build_search_contacts_output(
        query=query,
        contacts=contacts,
        is_email_search=is_email_search,
        auto_accept_matches=auto_accept_matches,
        truncated=truncated,
        max_pages=max_pages,
    )
    return cast(SearchContactsOutput, output)
