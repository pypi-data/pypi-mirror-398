"""Utility functions for cycle tools."""

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, cast

from arcade_linear.models.mappers import map_team_summary
from arcade_linear.models.tool_outputs.cycles import CycleOutput
from arcade_linear.utils.date_utils import parse_date_string


def find_team_id(teams: Sequence[Mapping[str, Any]], team_input: str) -> str | None:
    """Find team ID from a list of teams by ID, key, or name."""
    for t in teams:
        if t.get("id") == team_input:
            return t.get("id")
        key = t.get("key")
        if key and key.lower() == team_input.lower():
            return t.get("id")
        name = t.get("name")
        if name and name.lower() == team_input.lower():
            return t.get("id")
    return None


def is_cycle_active(starts_at: str | None, ends_at: str | None) -> bool:
    """Check if cycle is currently active based on dates."""
    if not starts_at or not ends_at:
        return False
    start = parse_date_string(starts_at)
    end = parse_date_string(ends_at)
    if not start or not end:
        return False
    now = datetime.now(timezone.utc)
    return start <= now <= end


def map_cycle(api_data: Mapping[str, Any]) -> CycleOutput:
    """Map API cycle response to CycleOutput."""
    starts_at = api_data.get("startsAt", "")
    ends_at = api_data.get("endsAt", "")

    return cast(
        CycleOutput,
        {
            "id": api_data.get("id"),
            "number": api_data.get("number"),
            "name": api_data.get("name"),
            "description": api_data.get("description"),
            "starts_at": starts_at,
            "ends_at": ends_at,
            "completed_at": api_data.get("completedAt"),
            "progress": api_data.get("progress", 0.0),
            "is_active": is_cycle_active(starts_at, ends_at),
            "team": map_team_summary(api_data.get("team")) if api_data.get("team") else None,
        },
    )
