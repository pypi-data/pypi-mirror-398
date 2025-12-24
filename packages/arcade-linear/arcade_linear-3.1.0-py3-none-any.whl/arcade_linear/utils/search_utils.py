"""Search utilities for Linear toolkit.

Provides utilities for building filters that work with Linear's GraphQL API.
"""

from typing import Any


def build_issue_filter(
    keywords: str | None = None,
    team: str | None = None,
    state: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    label: str | None = None,
    project: str | None = None,
    created_after: str | None = None,
) -> dict[str, Any]:
    """Build a Linear IssueFilter object from structured parameters.

    Returns a filter dict compatible with Linear's GraphQL IssueFilter type.
    """
    issue_filter: dict[str, Any] = {}

    if keywords:
        issue_filter["searchableContent"] = {"contains": keywords}
    if team:
        issue_filter["team"] = {"name": {"containsIgnoreCase": team}}
    if state:
        issue_filter["state"] = {"name": {"containsIgnoreCase": state}}
    if assignee:
        issue_filter["assignee"] = _build_assignee_filter(assignee)
    if priority:
        issue_filter["priority"] = _build_priority_filter(priority)
    if label:
        issue_filter["labels"] = {"name": {"containsIgnoreCase": label}}
    if project:
        issue_filter["project"] = {"name": {"containsIgnoreCase": project}}
    if created_after:
        issue_filter["createdAt"] = {"gte": f"{created_after}T00:00:00Z"}

    return issue_filter


def _build_assignee_filter(assignee: str) -> dict[str, Any]:
    """Build assignee filter clause."""
    if assignee == "@me":
        return {"isMe": {"eq": True}}
    return {"name": {"containsIgnoreCase": assignee}}


def _build_priority_filter(priority: str) -> dict[str, Any]:
    """Build priority filter clause.

    Raises:
        ValueError: If priority is not a valid value.
    """
    priority_map = {"urgent": 1, "high": 2, "medium": 3, "low": 4, "none": 0}
    priority_value = priority_map.get(priority.lower())
    if priority_value is None:
        valid = ", ".join(priority_map.keys())
        raise ValueError(f"Invalid priority '{priority}'. Valid values: {valid}")
    return {"eq": priority_value}
