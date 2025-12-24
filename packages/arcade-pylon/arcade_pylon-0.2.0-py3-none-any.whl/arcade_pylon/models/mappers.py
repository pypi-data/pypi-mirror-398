"""Mapper functions to transform Pylon API responses to tool outputs."""

from collections.abc import Mapping
from typing import Any, cast

from arcade_pylon.constants import PYLON_APP_URL
from arcade_pylon.models.tool_outputs.common import (
    AccountSummary,
    IssueSummary,
    PaginationInfo,
    TeamSummary,
    UserSummary,
)
from arcade_pylon.models.tool_outputs.contacts import ContactDetail
from arcade_pylon.models.tool_outputs.issues import IssueDetail
from arcade_pylon.models.tool_outputs.messages import MessageAuthor, MessageOutput
from arcade_pylon.models.tool_outputs.teams import (
    TeamDetail,
    TeamListItem,
    TeamMember,
)
from arcade_pylon.models.tool_outputs.user_context import WhoAmIOutput
from arcade_pylon.models.tool_outputs.users import UserDetail


def map_user(api_data: Mapping[str, Any] | None) -> UserSummary:
    """Map API user response to UserSummary output."""
    if not api_data:
        return cast(UserSummary, {})
    return cast(
        UserSummary,
        {
            "id": api_data.get("id"),
            "email": api_data.get("email"),
            "name": api_data.get("name"),
        },
    )


def map_team(api_data: Mapping[str, Any] | None) -> TeamSummary:
    """Map API team response to TeamSummary output."""
    if not api_data:
        return cast(TeamSummary, {})
    return cast(
        TeamSummary,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
        },
    )


def map_account(api_data: Mapping[str, Any] | None) -> AccountSummary:
    """Map API account response to AccountSummary output."""
    if not api_data:
        return cast(AccountSummary, {})
    return cast(
        AccountSummary,
        {
            "id": api_data.get("id"),
        },
    )


def map_issue_summary(api_data: Mapping[str, Any] | None) -> IssueSummary:
    """Map API issue response to IssueSummary output."""
    if not api_data:
        return cast(IssueSummary, {})
    return cast(
        IssueSummary,
        {
            "id": api_data.get("id"),
            "number": api_data.get("number"),
            "title": api_data.get("title"),
            "state": api_data.get("state"),
            "source": api_data.get("source"),
            "created_at": api_data.get("created_at"),
            "link": api_data.get("link"),
            "assignee": map_user(api_data.get("assignee")),
            "team": map_team(api_data.get("team")),
        },
    )


def map_issue_detail(api_data: Mapping[str, Any] | None) -> IssueDetail:
    """Map API issue response to IssueDetail output."""
    if not api_data:
        return cast(IssueDetail, {})
    return cast(
        IssueDetail,
        {
            "id": api_data.get("id"),
            "number": api_data.get("number"),
            "title": api_data.get("title"),
            "body_html": api_data.get("body_html"),
            "state": api_data.get("state"),
            "source": api_data.get("source"),
            "priority": api_data.get("priority"),
            "created_at": api_data.get("created_at"),
            "resolution_time": api_data.get("resolution_time"),
            "first_response_time": api_data.get("first_response_time"),
            "first_response_seconds": api_data.get("first_response_seconds"),
            "link": api_data.get("link"),
            "assignee": map_user(api_data.get("assignee")),
            "requester": map_user(api_data.get("requester")),
            "team": map_team(api_data.get("team")),
            "account": map_account(api_data.get("account")),
            "tags": api_data.get("tags", []),
            "snoozed_until_time": api_data.get("snoozed_until_time"),
        },
    )


def map_pagination(cursor_data: Mapping[str, Any] | None) -> PaginationInfo:
    """Map cursor-based pagination to PaginationInfo output."""
    if not cursor_data:
        return cast(PaginationInfo, {"has_next_page": False})
    return cast(
        PaginationInfo,
        {
            "has_next_page": cursor_data.get("has_next_page", False),
            "cursor": cursor_data.get("cursor"),
        },
    )


def map_who_am_i(api_data: Mapping[str, Any] | None) -> WhoAmIOutput:
    """Map /me response to WhoAmIOutput."""
    if not api_data:
        return cast(WhoAmIOutput, {})

    return cast(
        WhoAmIOutput,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
        },
    )


def map_message_author(api_data: Mapping[str, Any] | None) -> MessageAuthor:
    """Map API message author to MessageAuthor output."""
    if not api_data:
        return cast(MessageAuthor, {})
    return cast(
        MessageAuthor,
        {
            "id": api_data.get("id"),
            "email": api_data.get("email"),
            "type": api_data.get("type"),
        },
    )


def map_message(api_data: Mapping[str, Any] | None) -> MessageOutput:
    """Map API message response to MessageOutput."""
    if not api_data:
        return cast(MessageOutput, {})
    return cast(
        MessageOutput,
        {
            "id": api_data.get("id"),
            "issue_id": api_data.get("issue_id"),
            "body_html": api_data.get("body_html"),
            "created_at": api_data.get("created_at"),
            "is_internal": api_data.get("is_internal", False),
            "author": map_message_author(api_data.get("author")),
        },
    )


def map_user_detail(api_data: Mapping[str, Any] | None) -> UserDetail:
    """Map API user to UserDetail output."""
    if not api_data:
        return cast(UserDetail, {})
    user_id = api_data.get("id")
    return cast(
        UserDetail,
        {
            "id": user_id,
            "email": api_data.get("email"),
            "name": api_data.get("name"),
            "avatar_url": api_data.get("avatar_url"),
            "url": f"{PYLON_APP_URL}/settings/users/{user_id}" if user_id else None,
        },
    )


def map_contact(api_data: Mapping[str, Any] | None) -> ContactDetail:
    """Map raw contact data to ContactDetail output."""
    if not api_data:
        return cast(ContactDetail, {})
    contact_id = api_data.get("id", "")
    account = api_data.get("account") or {}
    result: ContactDetail = {
        "id": contact_id,
        "name": api_data.get("name", ""),
        "email": api_data.get("email", ""),
        "emails": api_data.get("emails") or [],
        "avatar_url": api_data.get("avatar_url", ""),
        "portal_role": api_data.get("portal_role", ""),
        "url": f"{PYLON_APP_URL}/contacts/{contact_id}" if contact_id else "",
    }
    if account:
        result["account"] = {"id": account.get("id", ""), "name": account.get("name", "")}
    return result


def map_team_list_item(api_data: Mapping[str, Any] | None) -> TeamListItem:
    """Map API team to TeamListItem for list views."""
    if not api_data:
        return cast(TeamListItem, {})
    team_id = api_data.get("id")
    users = api_data.get("users")
    if users is None:
        users = api_data.get("members")
    if not isinstance(users, list):
        users = []
    return cast(
        TeamListItem,
        {
            "id": team_id,
            "name": api_data.get("name"),
            "member_count": len(users) if isinstance(users, list) else 0,
            "url": (
                f"{PYLON_APP_URL}/settings/teams/management/{team_id}?tab=overview"
                if team_id
                else None
            ),
            "assignment_url": (
                f"{PYLON_APP_URL}/settings/teams/management/{team_id}?tab=assignment"
                if team_id
                else None
            ),
        },
    )


def map_team_member(api_data: Mapping[str, Any] | None) -> TeamMember:
    """Map API member to TeamMember."""
    if not api_data:
        return cast(TeamMember, {})
    return cast(
        TeamMember,
        {
            "id": api_data.get("id"),
            "email": api_data.get("email"),
            "name": api_data.get("name"),
        },
    )


def map_team_detail(api_data: Mapping[str, Any] | None) -> TeamDetail:
    """Map API team to TeamDetail."""
    if not api_data:
        return cast(TeamDetail, {})
    team_id = api_data.get("id")
    users = api_data.get("members")
    if users is None:
        users = api_data.get("users")
    if not isinstance(users, list):
        users = []
    return cast(
        TeamDetail,
        {
            "id": team_id,
            "name": api_data.get("name"),
            "members": [map_team_member(m) for m in users] if users else [],
            "member_count": len(users) if isinstance(users, list) else 0,
            "url": (
                f"{PYLON_APP_URL}/settings/teams/management/{team_id}?tab=overview"
                if team_id
                else None
            ),
            "assignment_url": (
                f"{PYLON_APP_URL}/settings/teams/management/{team_id}?tab=assignment"
                if team_id
                else None
            ),
        },
    )
