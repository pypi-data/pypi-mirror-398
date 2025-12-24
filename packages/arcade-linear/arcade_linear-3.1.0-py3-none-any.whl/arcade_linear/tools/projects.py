"""Project-related tools for Linear toolkit."""

from collections.abc import Mapping
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError
from gql.transport.exceptions import TransportQueryError

from arcade_linear.client import LinearClient
from arcade_linear.constants import (
    DEFAULT_PAGE_SIZE,
    DESCRIPTION_CHUNK_SIZE,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_DISPLAY_SUGGESTIONS,
    MAX_PAGE_SIZE,
)
from arcade_linear.models.enums import ProjectHealth, ProjectLookupBy, ProjectState
from arcade_linear.models.mappers import map_pagination
from arcade_linear.models.tool_outputs.issues import ArchiveOutput
from arcade_linear.models.tool_outputs.projects import (
    CreateProjectOutput,
    CreateProjectUpdateOutput,
    ProjectDescriptionOutput,
    ProjectSearchOutput,
    ProjectUpdateOutput,
    UpdateProjectOutput,
)
from arcade_linear.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_linear.utils.project_utils import (
    add_basic_update_fields,
    build_create_project_response,
    build_project_filter,
    build_project_response,
    build_update_project_response,
    clean_project_summary,
    filter_projects_by_team,
    resolve_lead,
    resolve_team,
    update_project_teams,
)
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# get_project
# API Calls: 1-2 (1 for ID/slug lookup, 2 if fuzzy matching by name)
# APIs Used: project query, projects query (GraphQL)
# Response Complexity: MEDIUM - includes teams and issues
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Project"
#   readOnlyHint: true      - Only reads project data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_project(
    context: Context,
    value: Annotated[
        str,
        "The value to look up (ID, slug_id, or name depending on lookup_by).",
    ],
    lookup_by: Annotated[
        ProjectLookupBy,
        "How to look up the project. Default is id.",
    ] = ProjectLookupBy.ID,
    include_issues: Annotated[
        bool,
        "Include latest 10 issues (by updated_at) in the response. Default is True.",
    ] = True,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Only used when lookup_by is name. Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Complete project details with teams and issues"]:
    """Get detailed information about a specific Linear project.

    Supports lookup by ID, slug_id, or name (with fuzzy matching for name).
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        if lookup_by == ProjectLookupBy.NAME:
            name_filter = {"name": {"containsIgnoreCase": value}}
            all_projects = await client.search_projects(
                project_filter=name_filter, first=DEFAULT_PAGE_SIZE
            )
            projects = all_projects.get("nodes", [])

            if projects:
                matched, fuzzy_info = try_fuzzy_match_by_name(projects, value, auto_accept_matches)

                if fuzzy_info:
                    return cast(dict[str, Any], {"fuzzy_matches": fuzzy_info})

                if matched:
                    project_data = await client.get_project_by_id(matched[0]["id"])
                    if project_data:
                        return build_project_response(project_data, include_issues)

            raise ToolExecutionError(message=f"Project not found by name: {value}")

        project_data = await client.get_project_by_id(value)
        if not project_data:
            raise ToolExecutionError(message=f"Project not found: {value}")

        return build_project_response(project_data, include_issues)


# =============================================================================
# list_projects
# API Calls: 1
# APIs Used: projects query with filter (GraphQL)
# Response Complexity: MEDIUM - returns summary project data
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Projects"
#   readOnlyHint: true      - Only reads project data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_projects(
    context: Context,
    keywords: Annotated[
        str | None,
        "Search keywords to match in project names. Default is None (all projects).",
    ] = None,
    state: Annotated[
        str | None,
        "Filter by project state. Default is None (all states).",
    ] = None,
    team: Annotated[
        str | None,
        "Filter by team name. Default is None (all teams).",
    ] = None,
    created_after: Annotated[
        str | None,
        "Filter projects created after this date in ISO format (YYYY-MM-DD). "
        "Default is None (all time).",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of projects to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[ProjectSearchOutput, "Projects matching the filters"]:
    """List Linear projects, optionally filtered by keywords and other criteria.

    Returns all projects when no filters provided, or filtered results when
    keywords or other filters are specified.
    """
    limit = max(1, min(limit, 50))

    project_filter = build_project_filter(
        name=keywords,
        state=state,
        created_after=created_after,
    )

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        search_response = await client.search_projects(
            project_filter=project_filter if project_filter else None,
            first=limit,
            after=end_cursor,
        )

    projects = cast(list[Mapping[str, Any]], search_response.get("nodes", []))
    page_info = search_response.get("pageInfo", {})

    items_before_filter = len(projects)
    if team and projects:
        projects = filter_projects_by_team(projects, team)

    mapped_projects = [clean_project_summary(p) for p in projects]

    filters_applied: dict[str, Any] = {}
    if keywords:
        filters_applied["keywords"] = keywords
    if state:
        filters_applied["state"] = state
    if team:
        filters_applied["team"] = team
    if created_after:
        filters_applied["created_after"] = created_after

    filtering_note = None
    if team and len(mapped_projects) < items_before_filter:
        filtering_note = (
            f"Results filtered locally by team. "
            f"Requested {limit}, API returned {items_before_filter}, "
            f"after filtering: {len(mapped_projects)}. "
            f"Use pagination to fetch more if needed."
        )

    response: ProjectSearchOutput = {
        "projects": mapped_projects,
        "items_returned": len(mapped_projects),
        "pagination": map_pagination(page_info),
        "filters": filters_applied if filters_applied else None,
        "filtering_note": filtering_note,
    }

    return cast(ProjectSearchOutput, remove_none_values_recursive(response))


# =============================================================================
# get_project_description
# API Calls: 1
# APIs Used: project query (GraphQL)
# Response Complexity: LOW - returns chunked description text
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Project Description"
#   readOnlyHint: true      - Only reads description, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_project_description(
    context: Context,
    project_id: Annotated[
        str,
        "The project ID or slug_id.",
    ],
    offset: Annotated[
        int,
        "Character offset to start reading from. Default is 0 (start).",
    ] = 0,
    limit: Annotated[
        int,
        f"Maximum characters to return. Default is {DESCRIPTION_CHUNK_SIZE}.",
    ] = DESCRIPTION_CHUNK_SIZE,
) -> Annotated[ProjectDescriptionOutput, "Project description chunk with pagination info"]:
    """Get a project's full description with pagination support.

    Use this tool when you need the complete description of a project that
    was truncated in the get_project response. Supports chunked reading for
    very large descriptions.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        project_data = await client.get_project_by_id(project_id)

    if not project_data:
        raise ToolExecutionError(message=f"Project not found: {project_id}")

    doc_content: dict[str, Any] = project_data.get("documentContent") or {}  # type: ignore[assignment]
    description: str = str(
        doc_content.get("content")
        or project_data.get("content")
        or project_data.get("description")
        or ""
    )
    total_length = len(description)

    chunk_start = max(0, offset)
    chunk_end = min(chunk_start + limit, total_length)
    chunk = description[chunk_start:chunk_end]

    result: ProjectDescriptionOutput = {
        "project_id": project_data.get("id", ""),
        "project_name": project_data.get("name", ""),
        "description": chunk,
        "total_length": total_length,
        "has_more": chunk_end < total_length,
    }

    return result


# =============================================================================
# create_project_update
# API Calls: 1
# APIs Used: projectUpdateCreate mutation (GraphQL)
# Response Complexity: LOW - returns created update details
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Create Project Update"
#   readOnlyHint: false     - Creates status update post
#   destructiveHint: false  - Additive operation, creates new update
#   idempotentHint: false   - Each call creates a new update
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def create_project_update(
    context: Context,
    project_id: Annotated[
        str,
        "The project ID to create an update for.",
    ],
    body: Annotated[
        str,
        "The update content in Markdown format.",
    ],
    health: Annotated[
        ProjectHealth | None,
        "Project health status. Default is None (no change).",
    ] = None,
) -> Annotated[CreateProjectUpdateOutput, "Created project update details"]:
    """Create a project status update.

    Project updates are posts that communicate progress, blockers, or status
    changes to stakeholders. They appear in the project's Updates tab and
    can include a health status indicator.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        update_data = await client.create_project_update(
            project_id=project_id,
            body=body,
            health=health.value if health else None,
        )

    user_data = update_data.get("user", {})
    project_data = update_data.get("project", {})

    project_update: ProjectUpdateOutput = {
        "id": update_data.get("id", ""),
        "body": update_data.get("body", ""),
        "health": update_data.get("health"),
        "created_at": update_data.get("createdAt", ""),
        "user_name": user_data.get("name") or user_data.get("displayName", ""),
        "project_id": project_data.get("id", ""),
        "project_name": project_data.get("name", ""),
        "project_url": project_data.get("url", ""),
    }

    result: CreateProjectUpdateOutput = {
        "project_update": project_update,
    }

    return cast(CreateProjectUpdateOutput, remove_none_values_recursive(result))


# =============================================================================
# create_project
# API Calls: 2 (1 for validation data, 1 for creation)
# APIs Used: teams query, projectCreate mutation (GraphQL)
# Response Complexity: LOW - returns created project summary
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Create Project"
#   readOnlyHint: false     - Creates new project in Linear
#   destructiveHint: false  - Additive operation, creates new resource
#   idempotentHint: false   - Each call creates a new project
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def create_project(
    context: Context,
    name: Annotated[
        str,
        "Project name. Required.",
    ],
    team: Annotated[
        str,
        "Team name, key, or ID to associate the project with. Required.",
    ],
    description: Annotated[
        str | None,
        "Project description in Markdown format. Default is None.",
    ] = None,
    state: Annotated[
        ProjectState | None,
        "Initial project state. Default is None (uses Linear default).",
    ] = None,
    lead: Annotated[
        str | None,
        "Project lead name or email. Must be a workspace member. Default is None.",
    ] = None,
    start_date: Annotated[
        str | None,
        "Project start date in YYYY-MM-DD format. Default is None.",
    ] = None,
    target_date: Annotated[
        str | None,
        "Target completion date in YYYY-MM-DD format. Default is None.",
    ] = None,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[CreateProjectOutput, "Created project details"]:
    """Create a new Linear project.

    Team is validated before creation. If team is not found, suggestions are
    returned to help correct the input. Lead is validated if provided.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        teams_response = await client.get_teams(first=MAX_PAGE_SIZE)
        teams = teams_response.get("nodes", [])

        team_id = resolve_team(teams, team, auto_accept_matches)

        lead_id = None
        if lead:
            lead_id = await resolve_lead(client, lead, auto_accept_matches)

        input_data: dict[str, Any] = {
            "name": name,
            "teamIds": [team_id],
        }
        if description:
            input_data["description"] = description
        if state:
            input_data["state"] = state.value
        if lead_id:
            input_data["leadId"] = lead_id
        if start_date:
            input_data["startDate"] = start_date
        if target_date:
            input_data["targetDate"] = target_date

        project_data = await client.create_project(input_data)

    return build_create_project_response(project_data)


# =============================================================================
# update_project
# API Calls: 1-3 (1 for update, +1-2 if resolving lead/team)
# APIs Used: projectUpdate mutation, teams query, users query (GraphQL)
# Response Complexity: LOW - returns updated project summary
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Update Project"
#   readOnlyHint: false     - Modifies existing project
#   destructiveHint: false  - Updates fields, doesn't delete
#   idempotentHint: true    - Same update with same args = same result
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def update_project(
    context: Context,
    project_id: Annotated[
        str,
        "Project ID or slug_id. Required.",
    ],
    name: Annotated[
        str | None,
        "New project name. Only updated if provided.",
    ] = None,
    description: Annotated[
        str | None,
        "New project description in Markdown format. Only updated if provided.",
    ] = None,
    state: Annotated[
        ProjectState | None,
        "New project state. Only updated if provided.",
    ] = None,
    lead: Annotated[
        str | None,
        "New project lead name or email. Only updated if provided.",
    ] = None,
    start_date: Annotated[
        str | None,
        "New start date in YYYY-MM-DD format. Only updated if provided.",
    ] = None,
    target_date: Annotated[
        str | None,
        "New target date in YYYY-MM-DD format. Only updated if provided.",
    ] = None,
    teams_to_add: Annotated[
        list[str] | None,
        "Team names, keys, or IDs to add to the project. Only updated if provided.",
    ] = None,
    teams_to_remove: Annotated[
        list[str] | None,
        "Team names, keys, or IDs to remove from the project. Only updated if provided.",
    ] = None,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[UpdateProjectOutput, "Updated project details"]:
    """Update a Linear project with partial updates.

    Only fields that are explicitly provided will be updated. All entity
    references are validated before update.
    """
    input_data: dict[str, Any] = {}
    fields_updated: list[str] = []

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        add_basic_update_fields(
            input_data, fields_updated, name, description, state, start_date, target_date
        )

        if lead:
            input_data["leadId"] = await resolve_lead(client, lead, auto_accept_matches)
            fields_updated.append("lead")

        needs_current_project = teams_to_add or teams_to_remove
        current_project = (
            await client.get_project_by_id(project_id) if needs_current_project else None
        )

        if teams_to_add or teams_to_remove:
            team_ids, team_fields = await update_project_teams(
                client, current_project, teams_to_add, teams_to_remove, auto_accept_matches
            )
            input_data["teamIds"] = team_ids
            fields_updated.extend(team_fields)

        if not input_data:
            raise ToolExecutionError(message="No fields provided for update")

        project_data = await client.update_project(project_id, input_data)

    return build_update_project_response(project_data, fields_updated)


# =============================================================================
# archive_project
# API Calls: 2 (get project, archive)
# APIs Used: project query, projectArchive mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Archive Project"
#   readOnlyHint: false     - Archives (soft-deletes) project
#   destructiveHint: true   - Hides project from default views
#   idempotentHint: true    - Archiving already-archived = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def archive_project(
    context: Context,
    project: Annotated[str, "Project ID, slug_id, or name to archive."],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[ArchiveOutput, "Archive operation result"]:
    """Archive a project.

    Archived projects are hidden from default views but can be restored.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        project_data: Mapping[str, Any] = {}
        project_id = ""

        try:
            project_data = await client.get_project_by_id(project)
        except TransportQueryError as e:
            if "not found" not in str(e).lower() and "invalid" not in str(e).lower():
                raise

        if project_data.get("id"):
            project_id = str(project_data["id"])
        else:
            projects_response = await client.search_projects(first=DEFAULT_PAGE_SIZE)
            projects = cast(list[Mapping[str, Any]], projects_response.get("nodes", []))
            matched, fuzzy_info = try_fuzzy_match_by_name(projects, project, auto_accept_matches)
            if not matched:
                if fuzzy_info:
                    suggestions = fuzzy_info.get("suggestions", [])
                    suggestions_text = ", ".join(
                        f"{s['name']} ({round(s['confidence'] * 100)}%)"
                        for s in suggestions[:MAX_DISPLAY_SUGGESTIONS]
                    )
                    raise RetryableToolError(
                        message=f"Project not found: {project}",
                        additional_prompt_content=f"Suggestions: {suggestions_text}",
                    )
                raise ToolExecutionError(message=f"Project not found: {project}")
            project_data = matched[0]
            project_id = str(project_data.get("id", ""))

        success = await client.archive_project(project_id)

    return cast(
        ArchiveOutput,
        remove_none_values_recursive({
            "id": project_id,
            "name": project_data.get("name"),
            "entity_type": "project",
            "success": success,
        }),
    )
