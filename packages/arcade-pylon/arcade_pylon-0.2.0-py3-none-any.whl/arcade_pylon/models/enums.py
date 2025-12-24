"""Enum definitions for Pylon toolkit."""

from enum import Enum


class IssueState(str, Enum):
    """Issue workflow states per Pylon API.

    Settable states: new, waiting_on_you, waiting_on_customer, on_hold, closed.
    Read-only states: open, snoozed (appear in responses but cannot be set via API).
    """

    NEW = "new"
    OPEN = "open"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    WAITING_ON_YOU = "waiting_on_you"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    SNOOZED = "snoozed"


class IssueLookupMethod(str, Enum):
    """Method for finding an issue."""

    ID = "id"
    SEARCH = "search"


class UserLookupMethod(str, Enum):
    """Method for finding a user."""

    ID = "id"
    NAME = "name"


class TeamLookupMethod(str, Enum):
    """Method for finding a team."""

    ID = "id"
    NAME = "name"


class IssueSource(str, Enum):
    """Source channels for issues."""

    SLACK = "slack"
    EMAIL = "email"
    CHAT = "chat"
    API = "api"
    CUSTOMER_PORTAL = "customer_portal"
    DISCORD = "discord"
    MANUAL = "manual"


class IssuePriority(str, Enum):
    """Issue priority levels."""

    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExternalIssueSource(str, Enum):
    """External issue tracker sources."""

    LINEAR = "linear"
    JIRA = "jira"
    GITHUB = "github"
    ASANA = "asana"
