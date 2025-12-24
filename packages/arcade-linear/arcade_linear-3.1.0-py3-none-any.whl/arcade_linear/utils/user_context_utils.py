"""User context utilities for Linear toolkit."""

from typing import Any


def build_activity_item(issue: dict[str, Any], activity_type: str) -> dict[str, Any]:
    """Build an activity item from an issue."""
    team = issue.get("team", {})
    timestamp = issue.get("createdAt") if activity_type == "created" else issue.get("updatedAt")

    return {
        "issue_id": issue.get("id"),
        "issue_identifier": issue.get("identifier"),
        "issue_title": issue.get("title"),
        "issue_url": issue.get("url"),
        "activity_type": activity_type,
        "timestamp": timestamp,
        "team_name": team.get("name") if team else None,
    }
