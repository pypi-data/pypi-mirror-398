"""Cycle tools for Linear toolkit."""

from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.constants import DEFAULT_PAGE_SIZE
from arcade_linear.models.mappers import map_pagination
from arcade_linear.models.tool_outputs.cycles import (
    CycleDetailsOutput,
    ListCyclesOutput,
)
from arcade_linear.utils.cycle_utils import find_team_id, is_cycle_active, map_cycle
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# get_cycle
# API Calls: 1
# APIs Used: cycle query (GraphQL)
# Response Complexity: LOW - single cycle details
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Cycle"
#   readOnlyHint: true      - Only reads cycle data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_cycle(
    context: Context,
    cycle_id: Annotated[
        str,
        "The cycle ID. Required.",
    ],
) -> Annotated[CycleDetailsOutput, "Cycle details"]:
    """Get detailed information about a specific Linear cycle."""
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        cycle_data = await client.get_cycle_by_id(cycle_id)

    if not cycle_data:
        raise ToolExecutionError(message=f"Cycle not found: {cycle_id}")

    result: CycleDetailsOutput = {
        "cycle": map_cycle(cycle_data),
    }

    return cast(CycleDetailsOutput, remove_none_values_recursive(result))


# =============================================================================
# list_cycles
# API Calls: 1-2 (1 for cycles, +1 if team filter provided to resolve team ID)
# APIs Used: cycles query, teams query (GraphQL)
# Response Complexity: LOW - list of cycle summaries
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Cycles"
#   readOnlyHint: true      - Only reads cycle data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_cycles(
    context: Context,
    team: Annotated[
        str | None,
        "Filter by team ID or key. Default is None (all teams).",
    ] = None,
    active_only: Annotated[
        bool,
        "Only return currently active cycles. Default is False.",
    ] = False,
    include_completed: Annotated[
        bool,
        "Include completed cycles. Default is True.",
    ] = True,
    limit: Annotated[
        int,
        "Maximum number of cycles to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[ListCyclesOutput, "Cycles matching the filters"]:
    """List Linear cycles, optionally filtered by team and status.

    Cycles are time-boxed iterations (like sprints) for organizing work.
    """
    limit = max(1, min(limit, 50))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        team_id = None
        if team:
            teams_response = await client.get_teams(first=DEFAULT_PAGE_SIZE, name_filter=team)
            teams = teams_response.get("nodes", [])
            team_id = find_team_id(teams, team)
            if not team_id:
                raise ToolExecutionError(f"Team not found: {team}")

        cycles_response = await client.get_cycles(
            team_id=team_id,
            first=limit,
            after=end_cursor,
        )

    cycles = cycles_response.get("nodes", [])
    page_info = cycles_response.get("pageInfo", {})

    items_before_filter = len(cycles)
    local_filters_applied = []

    if active_only:
        cycles = [c for c in cycles if is_cycle_active(c.get("startsAt"), c.get("endsAt"))]
        local_filters_applied.append("active_only")

    if not include_completed:
        cycles = [c for c in cycles if not c.get("completedAt")]
        local_filters_applied.append("exclude_completed")

    mapped_cycles = [map_cycle(c) for c in cycles]

    filters_applied: dict[str, Any] = {}
    if team:
        filters_applied["team"] = team
    if active_only:
        filters_applied["active_only"] = True
    if not include_completed:
        filters_applied["include_completed"] = False

    filtering_note = None
    if local_filters_applied and len(mapped_cycles) < items_before_filter:
        filtering_note = (
            f"Results filtered locally by {', '.join(local_filters_applied)}. "
            f"Requested {limit}, API returned {items_before_filter}, "
            f"after filtering: {len(mapped_cycles)}. "
            f"Use pagination to fetch more if needed."
        )

    response: ListCyclesOutput = {
        "cycles": mapped_cycles,
        "items_returned": len(mapped_cycles),
        "pagination": map_pagination(page_info),
        "filters": filters_applied if filters_applied else None,
        "filtering_note": filtering_note,
    }

    return cast(ListCyclesOutput, remove_none_values_recursive(response))
