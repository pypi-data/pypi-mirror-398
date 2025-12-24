"""Team-related tools for Linear toolkit."""

from collections.abc import Mapping
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.constants import DEFAULT_PAGE_SIZE, FUZZY_AUTO_ACCEPT_CONFIDENCE
from arcade_linear.models.enums import TeamLookupBy
from arcade_linear.models.mappers import map_pagination
from arcade_linear.utils import team_utils
from arcade_linear.utils.date_utils import parse_date_string, validate_date_format
from arcade_linear.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# get_team
# API Calls: 1-2 (ID: 1 call, KEY: 1 call, NAME: 1-2 calls if fuzzy match auto-accepts)
# APIs Used: team query, teams query (GraphQL)
# Response Complexity: HIGH - includes nested members array
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Team"
#   readOnlyHint: true      - Only reads team data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_team(
    context: Context,
    value: Annotated[
        str,
        "The value to look up (ID, key, or name depending on lookup_by).",
    ],
    lookup_by: Annotated[
        TeamLookupBy,
        "How to look up the team. Default is id.",
    ] = TeamLookupBy.ID,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Only used when lookup_by is name. Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Team details with member information"]:
    """Get detailed information about a specific Linear team.

    Supports lookup by ID, key (like TOO, ENG), or name (with fuzzy matching).
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        if lookup_by == TeamLookupBy.NAME:
            teams_response = await client.get_teams(first=DEFAULT_PAGE_SIZE)
            teams = teams_response.get("nodes", [])

            if teams:
                matched, fuzzy_info = try_fuzzy_match_by_name(teams, value, auto_accept_matches)

                if fuzzy_info:
                    return cast(dict[str, Any], {"fuzzy_matches": fuzzy_info})

                if matched:
                    team_data = await client.get_team_by_id(matched[0]["id"])
                    if team_data:
                        cleaned_team = team_utils.clean_team_data(team_data)
                        return cast(
                            dict[str, Any],
                            remove_none_values_recursive({"team": cleaned_team}),
                        )

            raise ToolExecutionError(message=f"Team not found: {value}")

        if lookup_by == TeamLookupBy.KEY:
            teams_response = await client.get_teams(first=DEFAULT_PAGE_SIZE)
            teams = teams_response.get("nodes", [])
            team_data = next((t for t in teams if t.get("key", "").upper() == value.upper()), {})
            if not team_data:
                raise ToolExecutionError(message=f"Team not found: {value}")
            cleaned_team = team_utils.clean_team_data(team_data)
            return cast(dict[str, Any], remove_none_values_recursive({"team": cleaned_team}))

        team_data = await client.get_team_by_id(value)
        if not team_data:
            raise ToolExecutionError(message=f"Team not found: {value}")

        cleaned_team = team_utils.clean_team_data(team_data)
        return cast(dict[str, Any], remove_none_values_recursive({"team": cleaned_team}))


# =============================================================================
# list_teams
# API Calls: 1
# APIs Used: teams query (GraphQL)
# Response Complexity: HIGH - includes nested members array per team
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Teams"
#   readOnlyHint: true      - Only reads team data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_teams(
    context: Context,
    keywords: Annotated[
        str | None,
        "Search keywords to match in team names. Default is None (all teams).",
    ] = None,
    include_archived: Annotated[
        bool,
        "Include archived teams in results. Default is False.",
    ] = False,
    created_after: Annotated[
        str | None,
        "Filter teams created after this date in ISO format (YYYY-MM-DD). "
        "Default is None (all time).",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of teams to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[dict[str, Any], "Teams matching the filters"]:
    """List Linear teams, optionally filtered by keywords and other criteria.

    Returns all teams when no filters provided, or filtered results when
    keywords or other filters are specified.
    """
    limit = max(1, min(limit, 50))

    created_after_date = None
    if created_after:
        validate_date_format("created_after", created_after)
        created_after_date = parse_date_string(created_after)

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        teams_response = await client.get_teams(
            first=limit,
            after=end_cursor,
            include_archived=include_archived,
            name_filter=keywords,
        )

    teams = cast(list[Mapping[str, Any]], teams_response.get("nodes", []))

    items_before_filter = len(teams)
    if created_after_date:
        teams = team_utils.filter_teams_by_date(teams, created_after_date)

    cleaned_teams = [team_utils.clean_team_data(team) for team in teams]

    filters_applied: dict[str, Any] = {}
    if keywords:
        filters_applied["keywords"] = keywords
    if include_archived:
        filters_applied["include_archived"] = include_archived
    if created_after:
        filters_applied["created_after"] = created_after

    filtering_note = None
    if created_after_date and len(cleaned_teams) < items_before_filter:
        filtering_note = (
            f"Results filtered locally by created_after. "
            f"Requested {limit}, API returned {items_before_filter}, "
            f"after filtering: {len(cleaned_teams)}. "
            f"Use pagination to fetch more if needed."
        )

    response: dict[str, Any] = {
        "teams": cleaned_teams,
        "items_returned": len(cleaned_teams),
        "pagination": map_pagination(teams_response.get("pageInfo")),
        "filters": filters_applied if filters_applied else None,
        "filtering_note": filtering_note,
    }

    return cast(dict[str, Any], remove_none_values_recursive(response))
