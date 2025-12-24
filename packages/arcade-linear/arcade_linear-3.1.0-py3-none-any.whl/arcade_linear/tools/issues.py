"""Issue-related tools for Linear toolkit."""

from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.constants import FUZZY_AUTO_ACCEPT_CONFIDENCE
from arcade_linear.models.enums import IssuePriority
from arcade_linear.models.mappers import map_issue, map_issue_details, map_pagination
from arcade_linear.models.tool_outputs.issues import IssueDetailsOutput, IssueSearchOutput
from arcade_linear.utils.date_utils import get_current_timestamp
from arcade_linear.utils.issue_utils import (
    build_create_issue_input,
    build_update_issue_input,
    resolve_create_issue_entities,
    resolve_labels_for_update,
    resolve_update_issue_entities,
    validate_and_resolve_state,
)
from arcade_linear.utils.response_utils import remove_none_values_recursive
from arcade_linear.utils.search_utils import build_issue_filter


# =============================================================================
# list_issues
# API Calls: 1
# APIs Used: issues query with filter (GraphQL)
# Response Complexity: MEDIUM - returns summary issue data, no nested details
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Issues"
#   readOnlyHint: true      - Only reads issue data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_issues(
    context: Context,
    keywords: Annotated[
        str | None,
        "Search keywords to match in issue titles and descriptions. Default is None.",
    ] = None,
    team: Annotated[
        str | None,
        "Filter by team name or key. Default is None (all teams).",
    ] = None,
    state: Annotated[
        str | None,
        "Filter by workflow state name. Default is None (all states).",
    ] = None,
    assignee: Annotated[
        str | None,
        "Filter by assignee. Use '@me' for current user. Default is None.",
    ] = None,
    priority: Annotated[
        IssuePriority | None,
        "Filter by priority level. Default is None.",
    ] = None,
    label: Annotated[
        str | None,
        "Filter by label name. Default is None.",
    ] = None,
    project: Annotated[
        str | None,
        "Filter by project name. Default is None.",
    ] = None,
    created_after: Annotated[
        str | None,
        "Filter issues created after this date in ISO format (YYYY-MM-DD). Default is None.",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of issues to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[IssueSearchOutput, "Issues matching the filters"]:
    """List Linear issues, optionally filtered by keywords and other criteria.

    Returns all issues when no filters provided, or filtered results when
    keywords or other filters are specified.
    """
    limit = max(1, min(limit, 50))

    issue_filter = build_issue_filter(
        keywords=keywords,
        team=team,
        state=state,
        assignee=assignee,
        priority=priority.value if priority else None,
        label=label,
        project=project,
        created_after=created_after,
    )

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        search_response = await client.search_issues(
            issue_filter=issue_filter if issue_filter else None,
            first=limit,
            after=end_cursor,
        )

    issues = search_response.get("nodes", [])
    page_info = search_response.get("pageInfo", {})

    mapped_issues = [map_issue(issue) for issue in issues]

    filters_applied: dict[str, Any] = {}
    if keywords:
        filters_applied["keywords"] = keywords
    if team:
        filters_applied["team"] = team
    if state:
        filters_applied["state"] = state
    if assignee:
        filters_applied["assignee"] = assignee
    if priority:
        filters_applied["priority"] = priority.value
    if label:
        filters_applied["label"] = label
    if project:
        filters_applied["project"] = project
    if created_after:
        filters_applied["created_after"] = created_after

    response: IssueSearchOutput = {
        "issues": mapped_issues,
        "items_returned": len(mapped_issues),
        "pagination": map_pagination(page_info),
        "filters": filters_applied if filters_applied else None,
    }

    return cast(IssueSearchOutput, remove_none_values_recursive(response))


# =============================================================================
# get_issue
# API Calls: 1
# APIs Used: issue query (GraphQL)
# Response Complexity: HIGH - includes comments, attachments, relations, children
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Issue"
#   readOnlyHint: true      - Only reads issue data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_issue(
    context: Context,
    issue_id: Annotated[
        str,
        "The Linear issue ID or identifier (like TOO-123).",
    ],
    include_comments: Annotated[
        bool,
        "Include comments in the response. Default is True.",
    ] = True,
    include_attachments: Annotated[
        bool,
        "Include attachments in the response. Default is True.",
    ] = True,
    include_relations: Annotated[
        bool,
        "Include issue relations (blocks, dependencies). Default is True.",
    ] = True,
    include_children: Annotated[
        bool,
        "Include sub-issues in the response. Default is True.",
    ] = True,
) -> Annotated[dict[str, Any], "Complete issue details with related data"]:
    """Get detailed information about a specific Linear issue.

    Accepts either the issue UUID or the human-readable identifier (like TOO-123).
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await client.get_issue_by_id(issue_id)
        if not issue_data:
            raise ToolExecutionError(message=f"Issue not found: {issue_id}")

    cleaned_issue: IssueDetailsOutput = map_issue_details(issue_data)

    if not include_comments:
        cleaned_issue.pop("comments", None)

    if not include_attachments:
        cleaned_issue.pop("attachments", None)

    if not include_relations:
        cleaned_issue.pop("relations", None)

    if not include_children:
        cleaned_issue.pop("children", None)

    retrieved_at = get_current_timestamp()

    result = {
        "issue": cleaned_issue,
        "retrieved_at": retrieved_at,
    }

    return cast(dict[str, Any], remove_none_values_recursive(result))


# =============================================================================
# create_issue
# API Calls: 2-5 (validation + create, +1 if @me assignee, +1 if parent_issue, +1 if attachment)
# APIs Used: issue_validation_data, viewer, team_issues, issueCreate, attachmentLinkURL (GraphQL)
# Response Complexity: MEDIUM - returns created issue data
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Create Issue"
#   readOnlyHint: false     - Creates new issue in Linear
#   destructiveHint: false  - Additive operation, creates new resource
#   idempotentHint: false   - Each call creates a new issue
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["issues:create"]))
async def create_issue(
    context: Context,
    team: Annotated[
        str,
        "Team name, key, or ID. Required.",
    ],
    title: Annotated[
        str,
        "Issue title. Required.",
    ],
    description: Annotated[
        str | None,
        "Issue description in Markdown format. Default is None.",
    ] = None,
    assignee: Annotated[
        str | None,
        "Assignee name or email. Use '@me' for current user. Must be a team member. "
        "Default is '@me' (assigns to current user).",
    ] = "@me",
    labels_to_add: Annotated[
        list[str] | None,
        "Labels to add by name or ID. Default is None.",
    ] = None,
    priority: Annotated[
        IssuePriority | None,
        "Issue priority. Default is None (no priority).",
    ] = None,
    state: Annotated[
        str | None,
        "Initial workflow state name. Default is team's default state.",
    ] = None,
    project: Annotated[
        str | None,
        "Project name, slug, or ID to link. Default is None.",
    ] = None,
    cycle: Annotated[
        str | None,
        "Cycle name or number to link. Default is None.",
    ] = None,
    parent_issue: Annotated[
        str | None,
        "Parent issue identifier to make this a sub-issue. Default is None.",
    ] = None,
    estimate: Annotated[
        int | None,
        "Effort estimate in points. Default is None.",
    ] = None,
    due_date: Annotated[
        str | None,
        "Due date in YYYY-MM-DD format. Default is None.",
    ] = None,
    attachment_url: Annotated[
        str | None,
        "URL to attach to the issue. Default is None.",
    ] = None,
    attachment_title: Annotated[
        str | None,
        "Title for the attached URL. Default is None (URL used as title).",
    ] = None,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Created issue details"]:
    """Create a new Linear issue with validation.

    When assignee is None or '@me', the issue is assigned to the authenticated user.
    All entity references (team, assignee, labels, state, project, cycle, parent)
    are validated before creation. If an entity is not found, suggestions are
    returned to help correct the input.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        validation_data = await client.get_issue_validation_data()

        resolved = await resolve_create_issue_entities(
            client,
            validation_data,
            team,
            assignee,
            labels_to_add,
            state,
            project,
            cycle,
            parent_issue,
            auto_accept_matches,
        )

        input_data = build_create_issue_input(
            team_id=resolved["team_id"],
            title=title,
            description=description,
            assignee_id=resolved.get("assignee_id"),
            label_ids=resolved.get("label_ids"),
            priority_value=priority.to_numeric() if priority else None,
            state_id=resolved.get("state_id"),
            project_id=resolved.get("project_id"),
            cycle_id=resolved.get("cycle_id"),
            parent_id=resolved.get("parent_id"),
            estimate=estimate,
            due_date=due_date,
        )

        created_issue = await client.create_issue(input_data)

        attachment_linked = False
        if attachment_url:
            await client.link_url_to_issue(
                str(created_issue.get("id", "")), attachment_url, attachment_title
            )
            attachment_linked = True

    result: dict[str, Any] = {"issue": map_issue(created_issue), "created": True}
    if attachment_linked:
        result["attachment_url"] = attachment_url
    return cast(dict[str, Any], result)


# =============================================================================
# update_issue
# API Calls: 2-5 (issue lookup + validation, +1 if @me, +1 for update, +1 if attachment)
# APIs Used: issue query, issue_validation_data, viewer, issueUpdate, attachmentLinkURL (GraphQL)
# Response Complexity: MEDIUM - returns updated issue data
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Update Issue"
#   readOnlyHint: false     - Modifies existing issue
#   destructiveHint: false  - Updates fields, doesn't delete
#   idempotentHint: true    - Same update with same args = same result
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["issues:create"]))
async def update_issue(
    context: Context,
    issue_id: Annotated[
        str,
        "Issue ID or identifier (like TOO-123). Required.",
    ],
    title: Annotated[
        str | None,
        "New issue title. Only updated if provided.",
    ] = None,
    description: Annotated[
        str | None,
        "New description in Markdown. Only updated if provided.",
    ] = None,
    assignee: Annotated[
        str | None,
        "New assignee name or email. Use '@me' for current user. Must be a team member. "
        "Only updated if provided.",
    ] = None,
    labels_to_add: Annotated[
        list[str] | None,
        "Labels to add by name or ID. Default is None.",
    ] = None,
    labels_to_remove: Annotated[
        list[str] | None,
        "Labels to remove by name or ID. Default is None.",
    ] = None,
    priority: Annotated[
        IssuePriority | None,
        "New priority. Only updated if provided.",
    ] = None,
    state: Annotated[
        str | None,
        "New workflow state name. Only updated if provided.",
    ] = None,
    project: Annotated[
        str | None,
        "Project to link (name, slug, or ID). Only updated if provided.",
    ] = None,
    cycle: Annotated[
        str | None,
        "Cycle to link (name or number). Only updated if provided.",
    ] = None,
    estimate: Annotated[
        int | None,
        "New effort estimate in points. Only updated if provided.",
    ] = None,
    due_date: Annotated[
        str | None,
        "New due date in YYYY-MM-DD format. Only updated if provided.",
    ] = None,
    attachment_url: Annotated[
        str | None,
        "URL to attach to the issue. Default is None.",
    ] = None,
    attachment_title: Annotated[
        str | None,
        "Title for the attached URL. Default is None (URL used as title).",
    ] = None,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Updated issue details"]:
    """Update a Linear issue with partial updates.

    Only fields that are explicitly provided will be updated. All entity
    references are validated before update.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        existing_issue = await client.get_issue_by_id(issue_id)
        if not existing_issue:
            raise ToolExecutionError(message=f"Issue not found: {issue_id}")

        issue_uuid = str(existing_issue.get("id") or "")
        team_data = existing_issue.get("team", {})
        team_id = str(team_data.get("id") or "")
        team_name = str(team_data.get("name") or "")

        validation_data = await client.get_issue_validation_data()

        resolved_assignee = assignee
        if assignee == "@me":
            viewer = await client.get_viewer()
            resolved_assignee = str(viewer.get("id") or "")

        resolved = resolve_update_issue_entities(
            validation_data,
            team_id,
            team_name,
            resolved_assignee if resolved_assignee != "@me" else None,
            state,
            project,
            cycle,
            auto_accept_matches,
        )
        if assignee == "@me" and resolved_assignee:
            resolved["assignee_id"] = resolved_assignee

        current_label_ids = [
            str(lb.get("id")) for lb in existing_issue.get("labels", {}).get("nodes", [])
        ]
        label_ids = resolve_labels_for_update(
            current_label_ids,
            resolved["all_labels"],
            labels_to_add,
            labels_to_remove,
            auto_accept_matches,
        )

        input_data = build_update_issue_input(
            title=title,
            description=description,
            assignee_id=resolved.get("assignee_id"),
            label_ids=label_ids,
            priority_value=priority.to_numeric() if priority else None,
            state_id=resolved.get("state_id"),
            project_id=resolved.get("project_id"),
            cycle_id=resolved.get("cycle_id"),
            estimate=estimate,
            due_date=due_date,
        )

        if not input_data and not attachment_url:
            raise ToolExecutionError(
                message="No fields to update. Provide at least one field to change."
            )

        updated_issue = existing_issue
        if input_data:
            updated_issue = await client.update_issue(issue_uuid, input_data)

        attachment_linked = False
        if attachment_url:
            await client.link_url_to_issue(issue_uuid, attachment_url, attachment_title)
            attachment_linked = True

    result: dict[str, Any] = {
        "issue": map_issue(updated_issue),
        "updated": True,
        "fields_updated": list(input_data.keys()) if input_data else [],
    }
    if attachment_linked:
        result["attachment_url"] = attachment_url
    return cast(dict[str, Any], result)


# =============================================================================
# transition_issue_state
# API Calls: 2-3 (1 for issue lookup, 1 for validation data, 1 for update)
# APIs Used: issue query, issue_validation_data query, issueUpdate mutation
# Response Complexity: LOW - returns transition result
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Transition Issue State"
#   readOnlyHint: false     - Changes issue workflow state
#   destructiveHint: false  - Updates state, doesn't delete
#   idempotentHint: true    - Transitioning to same state = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def transition_issue_state(
    context: Context,
    issue_id: Annotated[
        str,
        "Issue ID or identifier (like TOO-123). Required.",
    ],
    target_state: Annotated[
        str,
        "Target workflow state name. Required.",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Transition result with previous and new state"]:
    """Transition a Linear issue to a new workflow state.

    The target state is validated against the team's available states.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        existing_issue = await client.get_issue_by_id(issue_id)
        if not existing_issue:
            raise ToolExecutionError(message=f"Issue not found: {issue_id}")

        issue_uuid = str(existing_issue.get("id") or "")
        previous_state = existing_issue.get("state", {})
        previous_state_name = str(previous_state.get("name") or "Unknown")
        team_data = existing_issue.get("team", {})
        team_id = str(team_data.get("id") or "")
        team_name = str(team_data.get("name") or "")

        validation_data = await client.get_issue_validation_data()
        teams = validation_data["teams"]

        current_team: dict[str, Any] = next((t for t in teams if t["id"] == team_id), {})
        team_states = current_team.get("states", {}).get("nodes", [])

        state_id = validate_and_resolve_state(
            team_states, target_state, team_name, auto_accept_matches
        )

        await client.update_issue(issue_uuid, {"stateId": state_id})

    new_state: dict[str, Any] = next((s for s in team_states if s["id"] == state_id), {})
    new_state_name = str(new_state.get("name") or target_state)

    return cast(
        dict[str, Any],
        {
            "issue_id": issue_uuid,
            "issue_identifier": existing_issue.get("identifier"),
            "previous_state": previous_state_name,
            "new_state": new_state_name,
            "transitioned": True,
        },
    )
