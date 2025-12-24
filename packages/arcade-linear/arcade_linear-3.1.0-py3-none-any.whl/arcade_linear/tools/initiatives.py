"""Initiative-related tools for Linear toolkit."""

from collections.abc import Mapping
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.constants import (
    DEFAULT_PAGE_SIZE,
    DESCRIPTION_CHUNK_SIZE,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_DISPLAY_SUGGESTIONS,
)
from arcade_linear.models.enums import InitiativeLookupBy, InitiativeState
from arcade_linear.models.mappers import map_initiative_summary, map_pagination
from arcade_linear.models.tool_outputs.initiatives import (
    AddProjectToInitiativeOutput,
    CreateInitiativeOutput,
    InitiativeDescriptionOutput,
    ListInitiativesOutput,
    UpdateInitiativeOutput,
)
from arcade_linear.models.tool_outputs.issues import ArchiveOutput
from arcade_linear.utils.fuzzy_utils import try_fuzzy_match_by_name
from arcade_linear.utils.initiative_utils import (
    build_create_initiative_response,
    build_initiative_response,
    build_update_initiative_response,
    filter_initiatives_by_status,
    resolve_initiative_id,
    resolve_project_id,
)
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# get_initiative
# API Calls: 1-2 (1 for ID lookup, 2 if fuzzy matching by name)
# APIs Used: initiative query, initiatives query (GraphQL)
# Response Complexity: MEDIUM - includes linked projects
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Initiative"
#   readOnlyHint: true      - Only reads initiative data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_initiative(
    context: Context,
    value: Annotated[
        str,
        "The value to look up (ID or name depending on lookup_by).",
    ],
    lookup_by: Annotated[
        InitiativeLookupBy,
        "How to look up the initiative. Default is id.",
    ] = InitiativeLookupBy.ID,
    include_projects: Annotated[
        bool,
        "Include linked projects in the response. Default is True.",
    ] = True,
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Only used when lookup_by is name. Default is False.",
    ] = False,
) -> Annotated[dict[str, Any], "Complete initiative details with linked projects"]:
    """Get detailed information about a specific Linear initiative.

    Supports lookup by ID or name (with fuzzy matching for name).
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        if lookup_by == InitiativeLookupBy.NAME:
            all_initiatives = await client.get_initiatives(first=DEFAULT_PAGE_SIZE)
            initiatives = all_initiatives.get("nodes", [])

            if initiatives:
                matched, fuzzy_info = try_fuzzy_match_by_name(
                    initiatives, value, auto_accept_matches
                )

                if fuzzy_info:
                    return cast(dict[str, Any], {"fuzzy_matches": fuzzy_info})

                if matched:
                    initiative_data = await client.get_initiative_by_id(matched[0]["id"])
                    if initiative_data:
                        return build_initiative_response(initiative_data, include_projects)

            raise ToolExecutionError(message=f"Initiative not found: {value}")

        initiative_data = await client.get_initiative_by_id(value)
        if not initiative_data:
            raise ToolExecutionError(message=f"Initiative not found: {value}")

        return build_initiative_response(initiative_data, include_projects)


# =============================================================================
# list_initiatives
# API Calls: 1
# APIs Used: initiatives query (GraphQL)
# Response Complexity: LOW - returns summary initiative data
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Initiatives"
#   readOnlyHint: true      - Only reads initiative data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_initiatives(
    context: Context,
    keywords: Annotated[
        str | None,
        "Search keywords to match in initiative names. Default is None (all initiatives).",
    ] = None,
    state: Annotated[
        InitiativeState | None,
        "Filter by initiative state. Default is None (all states).",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of initiatives to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[ListInitiativesOutput, "Initiatives matching the filters"]:
    """List Linear initiatives, optionally filtered by keywords and other criteria.

    Returns all initiatives when no filters provided, or filtered results when
    keywords or other filters are specified.
    """
    limit = max(1, min(limit, 50))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiatives_response = await client.get_initiatives(
            first=limit,
            after=end_cursor,
        )

    initiatives = cast(list[Mapping[str, Any]], initiatives_response.get("nodes", []))
    page_info = initiatives_response.get("pageInfo", {})

    items_before_filter = len(initiatives)
    local_filters_applied = []

    if keywords:
        keywords_lower = keywords.lower()
        initiatives = [i for i in initiatives if keywords_lower in (i.get("name") or "").lower()]
        local_filters_applied.append("keywords")

    if state:
        initiatives = filter_initiatives_by_status(initiatives, state.value)
        local_filters_applied.append("state")

    mapped_initiatives = [map_initiative_summary(i) for i in initiatives]

    filters_applied: dict[str, Any] = {}
    if keywords:
        filters_applied["keywords"] = keywords
    if state:
        filters_applied["state"] = state.value

    filtering_note = None
    if local_filters_applied and len(mapped_initiatives) < items_before_filter:
        filtering_note = (
            f"Results filtered locally by {', '.join(local_filters_applied)}. "
            f"Requested {limit}, API returned {items_before_filter}, "
            f"after filtering: {len(mapped_initiatives)}. "
            f"Use pagination to fetch more if needed."
        )

    response: ListInitiativesOutput = {
        "initiatives": mapped_initiatives,
        "items_returned": len(mapped_initiatives),
        "pagination": map_pagination(page_info),
        "filters": filters_applied if filters_applied else None,
        "filtering_note": filtering_note,
    }

    return cast(ListInitiativesOutput, remove_none_values_recursive(response))


# =============================================================================
# get_initiative_description
# API Calls: 1
# APIs Used: initiative query (GraphQL)
# Response Complexity: LOW - returns chunked description text
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Initiative Description"
#   readOnlyHint: true      - Only reads description, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def get_initiative_description(
    context: Context,
    initiative_id: Annotated[
        str,
        "The initiative ID.",
    ],
    offset: Annotated[
        int,
        "Character offset to start reading from. Default is 0 (start).",
    ] = 0,
    limit: Annotated[
        int,
        f"Maximum characters to return. Default is {DESCRIPTION_CHUNK_SIZE}.",
    ] = DESCRIPTION_CHUNK_SIZE,
) -> Annotated[InitiativeDescriptionOutput, "Initiative description chunk with pagination info"]:
    """Get an initiative's full description with pagination support.

    Use this tool when you need the complete description of an initiative that
    was truncated in the get_initiative response. Supports chunked reading for
    very large descriptions.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiative_data = await client.get_initiative_by_id(initiative_id)

    if not initiative_data:
        raise ToolExecutionError(message=f"Initiative not found: {initiative_id}")

    document_content: dict[str, Any] = initiative_data.get("documentContent") or {}  # type: ignore[assignment]
    description = document_content.get("content") or initiative_data.get("description") or ""
    total_length = len(description)

    chunk_start = max(0, offset)
    chunk_end = min(chunk_start + limit, total_length)
    chunk = description[chunk_start:chunk_end]

    result: InitiativeDescriptionOutput = {
        "initiative_id": initiative_data.get("id", ""),
        "initiative_name": initiative_data.get("name", ""),
        "description": chunk,
        "total_length": total_length,
        "has_more": chunk_end < total_length,
    }

    return result


# =============================================================================
# create_initiative
# API Calls: 1
# APIs Used: initiativeCreate mutation (GraphQL)
# Response Complexity: LOW - returns created initiative summary
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Create Initiative"
#   readOnlyHint: false     - Creates new initiative in Linear
#   destructiveHint: false  - Additive operation, creates new resource
#   idempotentHint: false   - Each call creates a new initiative
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def create_initiative(
    context: Context,
    name: Annotated[
        str,
        "Initiative name. Required.",
    ],
    description: Annotated[
        str | None,
        "Initiative description in Markdown format. Default is None.",
    ] = None,
    status: Annotated[
        InitiativeState | None,
        "Initial initiative status. Default is None (uses Linear default).",
    ] = None,
    target_date: Annotated[
        str | None,
        "Target completion date in YYYY-MM-DD format. Default is None.",
    ] = None,
) -> Annotated[CreateInitiativeOutput, "Created initiative details"]:
    """Create a new Linear initiative.

    Initiatives are high-level strategic goals that group related projects.
    """
    input_data: dict[str, Any] = {"name": name}

    if description:
        input_data["description"] = description
    if status:
        input_data["status"] = status.value
    if target_date:
        input_data["targetDate"] = target_date

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiative_data = await client.create_initiative(input_data)

    return build_create_initiative_response(initiative_data)


# =============================================================================
# update_initiative
# API Calls: 1
# APIs Used: initiativeUpdate mutation (GraphQL)
# Response Complexity: LOW - returns updated initiative summary
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Update Initiative"
#   readOnlyHint: false     - Modifies existing initiative
#   destructiveHint: false  - Updates fields, doesn't delete
#   idempotentHint: true    - Same update with same args = same result
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def update_initiative(
    context: Context,
    initiative_id: Annotated[
        str,
        "Initiative ID. Required.",
    ],
    name: Annotated[
        str | None,
        "New initiative name. Only updated if provided.",
    ] = None,
    description: Annotated[
        str | None,
        "New initiative description in Markdown format. Only updated if provided.",
    ] = None,
    status: Annotated[
        InitiativeState | None,
        "New initiative status. Only updated if provided.",
    ] = None,
    target_date: Annotated[
        str | None,
        "New target date in YYYY-MM-DD format. Only updated if provided.",
    ] = None,
) -> Annotated[UpdateInitiativeOutput, "Updated initiative details"]:
    """Update a Linear initiative with partial updates.

    Only fields that are explicitly provided will be updated.
    """
    input_data: dict[str, Any] = {}
    fields_updated: list[str] = []

    if name:
        input_data["name"] = name
        fields_updated.append("name")
    if description is not None:
        input_data["description"] = description
        fields_updated.append("description")
    if status:
        input_data["status"] = status.value
        fields_updated.append("status")
    if target_date:
        input_data["targetDate"] = target_date
        fields_updated.append("target_date")

    if not input_data:
        raise ToolExecutionError(message="No fields provided for update")

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiative_data = await client.update_initiative(initiative_id, input_data)

    return build_update_initiative_response(initiative_data, fields_updated)


# =============================================================================
# add_project_to_initiative
# API Calls: 3 (initiatives query, projects query, initiativeToProjectCreate mutation)
# APIs Used: initiatives query, projects query, initiativeToProjectCreate mutation (GraphQL)
# Response Complexity: LOW - returns link confirmation
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Add Project to Initiative"
#   readOnlyHint: false     - Creates link between project and initiative
#   destructiveHint: false  - Additive operation, creates association
#   idempotentHint: true    - Linking same project again = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def add_project_to_initiative(
    context: Context,
    initiative: Annotated[
        str,
        "Initiative ID or name to link the project to.",
    ],
    project: Annotated[
        str,
        "Project ID or name to link.",
    ],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[AddProjectToInitiativeOutput, "Confirmation of project-initiative link"]:
    """Link a project to an initiative.

    Both initiative and project can be specified by ID or name.
    If a name is provided, fuzzy matching is used to resolve it.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiatives_response = await client.get_initiatives(first=DEFAULT_PAGE_SIZE)
        initiatives = initiatives_response.get("nodes", [])

        init_id, init_fuzzy = resolve_initiative_id(initiatives, initiative, auto_accept_matches)
        if not init_id:
            if init_fuzzy:
                suggestions = init_fuzzy.get("suggestions", [])
                suggestions_text = ", ".join(
                    f"{s['name']} ({round(s['confidence'] * 100)}%)"
                    for s in suggestions[:MAX_DISPLAY_SUGGESTIONS]
                )
                raise RetryableToolError(
                    message=f"Initiative not found: {initiative}",
                    additional_prompt_content=f"Suggestions: {suggestions_text}",
                )
            raise ToolExecutionError(message=f"Initiative not found: {initiative}")

        projects_response = await client.search_projects(first=DEFAULT_PAGE_SIZE)
        projects = projects_response.get("nodes", [])

        proj_id, proj_fuzzy = resolve_project_id(projects, project, auto_accept_matches)
        if not proj_id:
            if proj_fuzzy:
                suggestions = proj_fuzzy.get("suggestions", [])
                suggestions_text = ", ".join(
                    f"{s['name']} ({round(s['confidence'] * 100)}%)"
                    for s in suggestions[:MAX_DISPLAY_SUGGESTIONS]
                )
                raise RetryableToolError(
                    message=f"Project not found: {project}",
                    additional_prompt_content=f"Suggestions: {suggestions_text}",
                )
            raise ToolExecutionError(message=f"Project not found: {project}")

        await client.add_project_to_initiative(init_id, proj_id)

        resolved_init = cast(
            Mapping[str, Any], next((i for i in initiatives if i.get("id") == init_id), {})
        )
        resolved_proj = cast(
            Mapping[str, Any], next((p for p in projects if p.get("id") == proj_id), {})
        )

    result: AddProjectToInitiativeOutput = {
        "initiative_id": init_id,
        "initiative_name": resolved_init.get("name", ""),
        "project_id": proj_id,
        "project_name": resolved_proj.get("name", ""),
        "project_url": resolved_proj.get("url", ""),
    }

    return cast(AddProjectToInitiativeOutput, remove_none_values_recursive(result))


# =============================================================================
# archive_initiative
# API Calls: 2 (get initiative, archive)
# APIs Used: initiative query, initiativeArchive mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Archive Initiative"
#   readOnlyHint: false     - Archives (soft-deletes) initiative
#   destructiveHint: true   - Hides initiative from default views
#   idempotentHint: true    - Archiving already-archived = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def archive_initiative(
    context: Context,
    initiative: Annotated[str, "Initiative ID or name to archive."],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE:.0%} confidence. "
        "Default is False.",
    ] = False,
) -> Annotated[ArchiveOutput, "Archive operation result"]:
    """Archive an initiative.

    Archived initiatives are hidden from default views but can be restored.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        initiatives_response = await client.get_initiatives(first=DEFAULT_PAGE_SIZE)
        initiatives = initiatives_response.get("nodes", [])

        init_id, init_fuzzy = resolve_initiative_id(initiatives, initiative, auto_accept_matches)
        if not init_id:
            if init_fuzzy:
                suggestions = init_fuzzy.get("suggestions", [])
                suggestions_text = ", ".join(
                    f"{s['name']} ({round(s['confidence'] * 100)}%)"
                    for s in suggestions[:MAX_DISPLAY_SUGGESTIONS]
                )
                raise RetryableToolError(
                    message=f"Initiative not found: {initiative}",
                    additional_prompt_content=f"Suggestions: {suggestions_text}",
                )
            raise ToolExecutionError(message=f"Initiative not found: {initiative}")

        init_data = cast(
            Mapping[str, Any], next((i for i in initiatives if i.get("id") == init_id), {})
        )
        success = await client.archive_initiative(init_id)

    return cast(
        ArchiveOutput,
        remove_none_values_recursive({
            "id": init_id,
            "name": init_data.get("name"),
            "entity_type": "initiative",
            "success": success,
        }),
    )
