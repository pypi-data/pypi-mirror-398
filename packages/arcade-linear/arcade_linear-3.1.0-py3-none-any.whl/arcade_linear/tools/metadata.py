"""Metadata tools for Linear toolkit - labels and workflow states."""

from collections.abc import Mapping
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear

from arcade_linear.client import LinearClient
from arcade_linear.models.enums import IssueStateType
from arcade_linear.models.mappers import map_pagination, map_team_summary
from arcade_linear.models.tool_outputs.metadata import (
    LabelOutput,
    ListLabelsOutput,
    ListWorkflowStatesOutput,
    WorkflowStateOutput,
)
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_labels
# API Calls: 1
# APIs Used: issueLabels query (GraphQL)
# Response Complexity: LOW - simple label data
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Labels"
#   readOnlyHint: true      - Only reads label data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_labels(
    context: Context,
    limit: Annotated[
        int,
        "Maximum number of labels to return. Min 1, max 100. Default is 50.",
    ] = 50,
) -> Annotated[ListLabelsOutput, "Available issue labels"]:
    """List available issue labels in the workspace.

    Returns labels that can be applied to issues. Use label IDs or names
    when creating or updating issues.
    """
    limit = max(1, min(limit, 100))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        labels_response = await client.get_labels(first=limit)

    labels_nodes = labels_response.get("nodes", [])
    page_info = labels_response.get("pageInfo", {})

    labels: list[LabelOutput] = [
        {
            "id": label.get("id", ""),
            "name": label.get("name", ""),
            "color": label.get("color", ""),
            "description": label.get("description"),
        }
        for label in labels_nodes
    ]

    response: ListLabelsOutput = {
        "labels": labels,
        "items_returned": len(labels),
        "pagination": map_pagination(page_info),
    }

    return cast(ListLabelsOutput, remove_none_values_recursive(response))


# =============================================================================
# list_workflow_states
# API Calls: 1
# APIs Used: workflowStates query (GraphQL)
# Response Complexity: LOW - simple state data with team info
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Workflow States"
#   readOnlyHint: true      - Only reads workflow state data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_workflow_states(
    context: Context,
    team: Annotated[
        str | None,
        "Filter by team name or key. Default is None (all teams).",
    ] = None,
    state_type: Annotated[
        IssueStateType | None,
        "Filter by state type. Default is None (all types).",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of states to return. Min 1, max 100. Default is 50.",
    ] = 50,
) -> Annotated[ListWorkflowStatesOutput, "Available workflow states"]:
    """List available workflow states in the workspace.

    Returns workflow states that can be used for issue transitions.
    States are team-specific and have different types.
    """
    limit = max(1, min(limit, 100))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        states_response = await client.get_workflow_states(first=limit)

    states_nodes = states_response.get("nodes", [])
    page_info = states_response.get("pageInfo", {})

    items_before_filter = len(states_nodes)
    local_filters_applied = []

    if team:
        team_lower = team.lower()

        def get_team_field(state: Mapping[str, Any], field: str) -> str:
            team_data = cast(Mapping[str, Any] | None, state.get("team"))
            return str(team_data.get(field) or "") if team_data else ""

        states_nodes = [
            s
            for s in states_nodes
            if team_lower in get_team_field(s, "name").lower()
            or team_lower == get_team_field(s, "key").lower()
        ]
        local_filters_applied.append("team")

    if state_type:
        states_nodes = [s for s in states_nodes if s.get("type", "") == state_type.value]
        local_filters_applied.append("state_type")

    states: list[WorkflowStateOutput] = [
        {
            "id": state.get("id", ""),
            "name": state.get("name", ""),
            "type": state.get("type", ""),
            "team": map_team_summary(cast(Mapping[str, Any] | None, state.get("team")))
            if state.get("team")
            else None,
        }
        for state in states_nodes
    ]

    filters_applied: dict[str, Any] = {}
    if team:
        filters_applied["team"] = team
    if state_type:
        filters_applied["state_type"] = state_type.value

    filtering_note = None
    if local_filters_applied and len(states) < items_before_filter:
        filtering_note = (
            f"Results filtered locally by {', '.join(local_filters_applied)}. "
            f"Requested {limit}, API returned {items_before_filter}, "
            f"after filtering: {len(states)}. "
            f"Use pagination to fetch more if needed."
        )

    response: ListWorkflowStatesOutput = {
        "states": states,
        "items_returned": len(states),
        "pagination": map_pagination(page_info),
        "filters": filters_applied if filters_applied else None,
        "filtering_note": filtering_note,
    }

    return cast(ListWorkflowStatesOutput, remove_none_values_recursive(response))
