"""User context tools for Linear toolkit."""

import asyncio
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.constants import DEFAULT_PAGE_SIZE
from arcade_linear.models.mappers import map_notification, map_pagination, map_viewer
from arcade_linear.models.tool_outputs.user_context import (
    ActivityItem,
    NotificationsOutput,
    RecentActivityOutput,
    WhoAmIOutput,
)
from arcade_linear.utils.response_utils import remove_none_values_recursive
from arcade_linear.utils.user_context_utils import build_activity_item


# =============================================================================
# who_am_i
# API Calls: 2 (viewer + viewer_teams) - executed in parallel
# APIs Used: viewer query, viewer.teams query (GraphQL)
# Response Complexity: LOW - user profile with team summaries
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Who Am I"
#   readOnlyHint: true      - Only reads user profile, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def who_am_i(
    context: Context,
) -> Annotated[WhoAmIOutput, "Authenticated user's profile and teams"]:
    """Get the authenticated user's profile and team memberships.

    Returns the current user's information including their name, email,
    organization, and the teams they belong to.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        viewer_data, teams_data = await asyncio.gather(
            client.get_viewer(),
            client.get_viewer_teams(first=DEFAULT_PAGE_SIZE),
        )

    result = map_viewer(viewer_data, teams_data)

    return cast(WhoAmIOutput, remove_none_values_recursive(result))


# =============================================================================
# get_notifications
# API Calls: 1
# APIs Used: notifications query (GraphQL)
# Response Complexity: MEDIUM - list of notifications with issue references
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Notifications"
#   readOnlyHint: true      - Only reads notifications, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_notifications(
    context: Context,
    unread_only: Annotated[
        bool,
        "Only return unread notifications. Default is False.",
    ] = False,
    limit: Annotated[
        int,
        "Maximum number of notifications to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[NotificationsOutput, "User's notifications with pagination"]:
    """Get the authenticated user's notifications.

    Returns notifications including issue mentions, comments, assignments,
    and state changes.
    """
    limit = max(1, min(limit, 50))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        notifications_response = await client.get_notifications(
            first=limit,
            after=end_cursor,
        )

    notifications = notifications_response.get("nodes", [])
    page_info = notifications_response.get("pageInfo", {})

    if unread_only:
        notifications = [n for n in notifications if not n.get("readAt")]

    mapped_notifications = [map_notification(n) for n in notifications]
    unread_count = sum(1 for n in notifications if not n.get("readAt"))

    result: NotificationsOutput = {
        "notifications": mapped_notifications,
        "items_returned": len(mapped_notifications),
        "unread_count": unread_count,
        "pagination": map_pagination(page_info),
    }

    return cast(NotificationsOutput, remove_none_values_recursive(result))


# =============================================================================
# get_recent_activity
# API Calls: 3 (viewer + created issues + assigned issues) - issues in parallel
# APIs Used: viewer, issues query with filters (GraphQL)
# Response Complexity: MEDIUM - list of issues with activity metadata
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Recent Activity"
#   readOnlyHint: true      - Only reads activity data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_recent_activity(
    context: Context,
    days: Annotated[
        int,
        "Number of days to look back for activity. Min 1, max 90. Default is 30.",
    ] = 30,
    limit: Annotated[
        int,
        "Maximum number of activities to return. Min 1, max 50. Default is 20.",
    ] = 20,
) -> Annotated[RecentActivityOutput, "User's recent issue activity"]:
    """Get the authenticated user's recent issue activity.

    Returns issues the user has recently created or been assigned to
    within the specified time period.
    """
    from datetime import datetime, timedelta, timezone

    days = max(1, min(days, 90))
    limit = max(1, min(limit, 50))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        viewer_data = await client.get_viewer()
        viewer_id = viewer_data.get("id")

        if not viewer_id:
            raise ToolExecutionError(message="Could not get authenticated user ID")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        created_issues, assigned_issues = await asyncio.gather(
            client.get_user_created_issues(
                user_id=viewer_id,
                created_after=cutoff_iso,
                first=limit,
            ),
            client.get_user_assigned_issues(
                user_id=viewer_id,
                first=limit,
            ),
        )

    activities: list[dict[str, Any]] = []
    created_count = 0
    assigned_count = 0

    for issue in created_issues.get("nodes", []):
        activities.append(build_activity_item(issue, "created"))
        created_count += 1

    for issue in assigned_issues.get("nodes", []):
        issue_updated = issue.get("updatedAt", "")
        issue_id = issue.get("id")
        is_recent = issue_updated >= cutoff_iso
        is_new = not any(a["issue_id"] == issue_id for a in activities)

        if is_recent and is_new:
            activities.append(build_activity_item(issue, "assigned"))
            assigned_count += 1

    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    activities = activities[:limit]

    result: RecentActivityOutput = {
        "activities": cast(list[ActivityItem], activities),
        "items_returned": len(activities),
        "days_searched": days,
        "created_count": created_count,
        "assigned_count": assigned_count,
    }

    return cast(RecentActivityOutput, remove_none_values_recursive(result))
