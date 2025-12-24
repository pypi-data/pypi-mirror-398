"""TypedDict definitions for Linear user context tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo, TeamSummary, UserData


class WhoAmIOutput(TypedDict, total=False):
    """Output for the who_am_i tool."""

    id: str
    """Authenticated user's unique identifier."""

    name: str | None
    """User's full name."""

    email: str | None
    """User's email address."""

    display_name: str | None
    """User's display name."""

    avatar_url: str | None
    """URL to user's avatar image."""

    active: bool
    """Whether the user is active."""

    admin: bool
    """Whether the user is an admin."""

    organization_name: str | None
    """Name of the user's organization."""

    teams: list[TeamSummary]
    """Teams the user belongs to."""


class NotificationData(TypedDict, total=False):
    """Individual notification in tool outputs."""

    id: str
    """Notification unique identifier."""

    type: str
    """Notification type (e.g., issueComment, issueMention)."""

    created_at: str
    """ISO 8601 timestamp when notification was created."""

    read_at: str | None
    """ISO 8601 timestamp when notification was read."""

    issue_id: str | None
    """Related issue ID if applicable."""

    issue_identifier: str | None
    """Related issue identifier (e.g., FE-123)."""

    issue_title: str | None
    """Related issue title."""

    actor: UserData | None
    """User who triggered the notification."""


class NotificationsOutput(TypedDict, total=False):
    """Output for the get_notifications tool."""

    notifications: list[NotificationData]
    """List of notifications."""

    items_returned: int
    """Number of notifications returned in this response."""

    unread_count: int
    """Number of unread notifications."""

    pagination: PaginationInfo
    """Pagination information."""


class ActivityItem(TypedDict, total=False):
    """Individual activity item in recent activity output."""

    issue_id: str
    """Issue unique identifier."""

    issue_identifier: str
    """Issue identifier (e.g., FE-123)."""

    issue_title: str
    """Issue title."""

    issue_url: str
    """URL to the issue."""

    activity_type: str
    """Type of activity (created, assigned, commented)."""

    timestamp: str
    """ISO 8601 timestamp of the activity."""

    team_name: str | None
    """Team the issue belongs to."""


class RecentActivityOutput(TypedDict, total=False):
    """Output for the get_recent_activity tool."""

    activities: list[ActivityItem]
    """List of recent activities."""

    items_returned: int
    """Number of activities returned in this response."""

    days_searched: int
    """Number of days searched."""

    created_count: int
    """Number of issues created."""

    assigned_count: int
    """Number of issues assigned."""
