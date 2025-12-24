"""Pylon REST API client with HTTP/2 support and connection pooling."""

import asyncio
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, ClassVar, cast

import httpx
from arcade_mcp_server.exceptions import FatalToolError, UpstreamError

from arcade_pylon.constants import (
    BM25_MAX_ISSUES_TO_INDEX,
    LOCK_ACQUIRE_TIMEOUT_SECONDS,
    MAX_DATE_RANGE_DAYS,
    PYLON_API_URL,
    PYLON_MAX_TIMEOUT_SECONDS,
)
from arcade_pylon.models.api_responses import (
    IssueData,
    IssuesListResponse,
    MeResponse,
    MessageData,
    TagsListResponse,
    TeamData,
    TeamsListResponse,
    UserData,
    UsersListResponse,
)
from arcade_pylon.models.api_responses.contacts import (
    ContactData,
    ContactsListResponse,
)
from arcade_pylon.utils.date_utils import get_date_range_for_days


@dataclass
class PylonClient:
    """Client for interacting with Pylon REST API.

    Supports HTTP/2, connection pooling, and retry logic for server errors.
    Use as async context manager:
        async with PylonClient(token) as client:
            result = await client.get_me()
    """

    auth_token: str
    base_url: str = PYLON_API_URL
    timeout_seconds: int = PYLON_MAX_TIMEOUT_SECONDS

    _clients: ClassVar[dict[str, httpx.AsyncClient]] = {}
    _client_locks: ClassVar[dict[str, asyncio.Lock]] = {}
    _global_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    _client: httpx.AsyncClient | None = field(default=None, repr=False)

    async def __aenter__(self) -> "PylonClient":
        """Enter async context - get or create pooled HTTP client."""
        self._client = await self._get_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context - client remains pooled for reuse."""
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create a pooled HTTP client for the base URL (async-safe)."""
        base_url = self.base_url

        try:
            await asyncio.wait_for(
                self._global_lock.acquire(), timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError as e:
            raise FatalToolError(
                f"Timeout acquiring global lock after {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
            ) from e

        try:
            if base_url not in self._client_locks:
                self._client_locks[base_url] = asyncio.Lock()
            lock = self._client_locks[base_url]
        finally:
            self._global_lock.release()

        try:
            await asyncio.wait_for(lock.acquire(), timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS)
        except asyncio.TimeoutError as e:
            raise FatalToolError(
                f"Timeout acquiring client lock after {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
            ) from e

        try:
            if base_url not in self._clients:
                self._clients[base_url] = httpx.AsyncClient(
                    base_url=base_url,
                    http2=True,
                    headers={"Content-Type": "application/json"},
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                    timeout=self.timeout_seconds,
                )
            return self._clients[base_url]
        finally:
            lock.release()

    @classmethod
    async def close_all(cls) -> None:
        """Close all pooled HTTP clients and clear the pool.

        Call this on application shutdown or in tests to properly clean up resources.
        """
        async with cls._global_lock:
            for client in cls._clients.values():
                await client.aclose()
            cls._clients.clear()
            cls._client_locks.clear()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute HTTP request with retry logic for 5xx server errors only.

        4xx client errors are raised immediately without retry.
        """
        if not self._client:
            raise FatalToolError(
                "Client not initialized. Use 'async with PylonClient() as client:'",
            )

        backoff_delays = [0.3, 0.6, 1.2]

        for attempt, delay in enumerate(backoff_delays):
            try:
                response = await self._client.request(
                    method,
                    endpoint,
                    params=params,
                    json=json,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status >= 500:
                    is_last_attempt = attempt == len(backoff_delays) - 1
                    if not is_last_attempt:
                        await asyncio.sleep(delay)
                        continue
                    _handle_server_error(e)
                raise
            except httpx.RequestError as e:
                raise UpstreamError(
                    f"Failed to connect to Pylon API: {e}",
                    developer_message=str(e),
                    status_code=503,
                ) from e

        raise RuntimeError("Retry logic exited unexpectedly without returning or raising.")

    async def get_me(self) -> MeResponse:
        """Get authenticated user information."""
        response = await self._request("GET", "/me")
        data = response.get("data", {})
        return cast(MeResponse, data)

    async def get_users(self) -> UsersListResponse:
        """Get all users in the workspace. API returns all users, no pagination."""
        response = await self._request("GET", "/users")
        return cast(UsersListResponse, response)

    async def get_user_by_id(self, user_id: str) -> UserData:
        """Get a single user by ID."""
        response = await self._request("GET", f"/users/{user_id}")
        return cast(UserData, response.get("data", {}))

    async def get_issues(
        self,
        start_time: str,
        end_time: str,
        cursor: str | None = None,
    ) -> IssuesListResponse:
        """Get issues within a time range."""
        params: dict[str, Any] = {"start_time": start_time, "end_time": end_time}
        if cursor:
            params["cursor"] = cursor
        response = await self._request("GET", "/issues", params=params)
        return cast(IssuesListResponse, response)

    async def get_issue_by_id(self, issue_id: str) -> IssueData:
        """Get a single issue by ID or number."""
        response = await self._request("GET", f"/issues/{issue_id}")
        return cast(IssueData, response.get("data", {}))

    async def update_issue(self, issue_id: str, updates: dict[str, Any]) -> IssueData:
        """Update an issue."""
        response = await self._request("PATCH", f"/issues/{issue_id}", json=updates)
        return cast(IssueData, response.get("data", {}))

    async def create_thread(self, issue_id: str, name: str = "Notes") -> dict[str, Any]:
        """Create a new thread on an issue."""
        payload: dict[str, Any] = {"name": name}
        response = await self._request("POST", f"/issues/{issue_id}/threads", json=payload)
        return cast(dict[str, Any], response.get("data", {}))

    async def get_threads(self, issue_id: str) -> list[dict[str, Any]]:
        """Get threads for an issue."""
        response = await self._request("GET", f"/issues/{issue_id}/threads")
        return cast(list[dict[str, Any]], response.get("data") or [])

    async def create_note(
        self,
        issue_id: str,
        body_html: str,
        thread_id: str | None = None,
        user_id: str | None = None,
    ) -> MessageData:
        """Create an internal note on an issue.

        If thread_id is not provided, creates or reuses a 'Notes' thread.
        """
        if not thread_id:
            threads = await self.get_threads(issue_id)
            notes_thread = next((t for t in threads if t.get("name") == "Notes"), None)
            if notes_thread:
                thread_id = notes_thread.get("id")
            else:
                new_thread = await self.create_thread(issue_id, "Notes")
                thread_id = new_thread.get("id")

        payload: dict[str, Any] = {"body_html": body_html, "thread_id": thread_id}
        if user_id:
            payload["user_id"] = user_id
        response = await self._request("POST", f"/issues/{issue_id}/note", json=payload)
        return cast(MessageData, response.get("data", {}))

    async def get_teams(self, cursor: str | None = None) -> TeamsListResponse:
        """Get list of teams."""
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        response = await self._request("GET", "/teams", params=params)
        return cast(TeamsListResponse, response)

    async def get_team_by_id(self, team_id: str) -> TeamData:
        """Get a single team by ID."""
        response = await self._request("GET", f"/teams/{team_id}")
        return cast(TeamData, response.get("data", {}))

    async def update_team(self, team_id: str, updates: dict[str, Any]) -> TeamData:
        """Update team settings."""
        response = await self._request("PATCH", f"/teams/{team_id}", json=updates)
        return cast(TeamData, response.get("data", {}))

    async def get_tags(self) -> TagsListResponse:
        """Get list of tags."""
        response = await self._request("GET", "/tags")
        return cast(TagsListResponse, response)

    async def search_issues_by_filter(
        self,
        state: str | None = None,
        assignee_id: str | None = None,
        team_id: str | None = None,
        tags: list[str] | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> IssuesListResponse:
        """Search issues with filters using POST /issues/search.

        Args:
            state: Filter by issue state.
            assignee_id: Filter by assignee user ID.
            team_id: Filter by team ID.
            tags: Filter by tags (issues must have all listed tags).
            created_after: RFC3339 timestamp - only issues created after this time.
            created_before: RFC3339 timestamp - only issues created before this time.
            cursor: Pagination cursor.
            limit: Maximum results per page (default 50).

        Returns:
            Paginated list of matching issues.
        """
        filter_obj: dict[str, Any] = {}
        if state:
            filter_obj["state"] = state
        if assignee_id:
            filter_obj["assignee_id"] = assignee_id
        if team_id:
            filter_obj["team_id"] = team_id
        if tags:
            filter_obj["tags"] = tags
        if created_after:
            filter_obj["created_after"] = created_after
        if created_before:
            filter_obj["created_before"] = created_before

        body: dict[str, Any] = {"filter": filter_obj, "limit": limit}
        if cursor:
            body["cursor"] = cursor

        response = await self._request("POST", "/issues/search", json=body)
        return cast(IssuesListResponse, response)

    async def get_latest_issues(self, limit: int = BM25_MAX_ISSUES_TO_INDEX) -> list[IssueData]:
        """Fetch recent issues for search indexing.

        Args:
            limit: Maximum number of issues to fetch (default 400).

        Returns:
            List of issues from the last 30 days.
        """
        start_time, end_time = get_date_range_for_days(MAX_DATE_RANGE_DAYS)
        all_issues: list[IssueData] = []
        cursor: str | None = None

        while len(all_issues) < limit:
            response = await self.get_issues(
                start_time=start_time,
                end_time=end_time,
                cursor=cursor,
            )
            issues = cast(list[IssueData], response.get("data", []))
            all_issues.extend(issues)

            pagination = response.get("pagination", {})
            if not pagination.get("has_next_page", False):
                break
            cursor = pagination.get("cursor")
            if not cursor:
                break

        return all_issues[:limit]

    async def get_contacts(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ContactsListResponse:
        """Get all contacts.

        Args:
            cursor: Pagination cursor.
            limit: Maximum results per page.

        Returns:
            Paginated list of contacts.
        """
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        response = await self._request("GET", "/contacts", params=params or None)
        return cast(ContactsListResponse, response)

    async def get_contact_by_id(self, contact_id: str) -> ContactData:
        """Get a single contact by ID.

        Args:
            contact_id: Contact ID.

        Returns:
            Contact data.
        """
        response = await self._request("GET", f"/contacts/{contact_id}")
        return cast(ContactData, response.get("data", {}))

    async def search_contacts_by_email(
        self,
        email: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> ContactsListResponse:
        """Search contacts by email.

        Args:
            email: Email to search for (supports partial match).
            cursor: Pagination cursor.
            limit: Maximum results (1-1000, default 100).

        Returns:
            Paginated list of matching contacts.
        """
        body: dict[str, Any] = {
            "filter": {"field": "email", "operator": "string_contains", "value": email},
            "limit": limit,
        }
        if cursor:
            body["cursor"] = cursor
        response = await self._request("POST", "/contacts/search", json=body)
        return cast(ContactsListResponse, response)


def _handle_server_error(error: httpx.HTTPStatusError) -> None:
    """Handle 5xx server errors from Pylon API after retry exhaustion."""
    status = error.response.status_code
    try:
        body = error.response.json()
        message = (body.get("error") or {}).get("message", f"HTTP {status}")
    except Exception:
        message = f"HTTP {status}"

    raise UpstreamError(
        f"Pylon API server error: {message}",
        developer_message=f"Pylon API {status}: {error.response.text}",
        status_code=status,
    ) from error
