"""Team-related utilities for Linear toolkit."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from arcade_linear.models.mappers import map_user
from arcade_linear.utils.date_utils import parse_date_string
from arcade_linear.utils.response_utils import remove_none_values


def clean_team_data(team_data: Mapping[str, Any]) -> dict[str, Any]:
    """Clean and format team API data for output."""
    if not team_data:
        return {}

    cleaned: dict[str, Any] = {
        "id": team_data.get("id"),
        "key": team_data.get("key"),
        "name": team_data.get("name"),
        "description": team_data.get("description"),
        "private": team_data.get("private"),
        "archived_at": team_data.get("archivedAt"),
        "created_at": team_data.get("createdAt"),
        "updated_at": team_data.get("updatedAt"),
        "icon": team_data.get("icon"),
        "color": team_data.get("color"),
    }

    members_conn = team_data.get("members", {})
    members_data = members_conn.get("nodes", []) if members_conn else []
    if members_data:
        cleaned["members"] = [map_user(member) for member in members_data if member]

    return remove_none_values(cleaned)


def filter_teams_by_date(
    teams: Sequence[Mapping[str, Any]], created_after_date: datetime
) -> list[Mapping[str, Any]]:
    """Filter teams by creation date."""
    filtered: list[Mapping[str, Any]] = []
    for team in teams:
        team_created_at = parse_date_string(team.get("createdAt", ""))
        if team_created_at and team_created_at >= created_after_date:
            filtered.append(team)
    return filtered
