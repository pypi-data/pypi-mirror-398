"""Utility functions for project-related operations."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError

from arcade_linear.constants import (
    DEFAULT_DESCRIPTION_MAX_LENGTH,
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_FUZZY_SUGGESTIONS,
    MAX_PAGE_SIZE,
)
from arcade_linear.models.enums import IssuePriority, ProjectState
from arcade_linear.models.tool_outputs.projects import (
    CreatedProjectOutput,
    CreateProjectOutput,
    ProjectDetailsOutput,
    ProjectIssueOutput,
    ProjectLeadOutput,
    ProjectOutput,
    ProjectSummaryOutput,
    ProjectTeamOutput,
    UpdateProjectOutput,
)
from arcade_linear.utils.fuzzy_utils import fuzzy_match_entity
from arcade_linear.utils.response_utils import remove_none_values_recursive

if TYPE_CHECKING:
    from arcade_linear.client import LinearClient

MAX_PROJECT_ISSUES = 10


def build_project_response(
    project_data: Mapping[str, Any],
    include_issues: bool,
    max_description_length: int | None = DEFAULT_DESCRIPTION_MAX_LENGTH,
) -> dict[str, Any]:
    """Build the project response with optional fields."""
    cleaned_project = clean_project_data(project_data, max_description_length)

    if not include_issues:
        cleaned_project.pop("issues", None)

    result: ProjectDetailsOutput = {
        "project": cleaned_project,
    }

    return cast(dict[str, Any], remove_none_values_recursive(result))


def clean_project_data(
    api_data: Mapping[str, Any],
    max_description_length: int | None = DEFAULT_DESCRIPTION_MAX_LENGTH,
) -> ProjectOutput:
    """Clean and transform API project data to tool output format.

    Description is truncated to max_description_length (default 500) to reduce token usage.
    Use get_project_description tool for full description with pagination.
    """
    lead_data = api_data.get("lead")
    lead: ProjectLeadOutput | None = None
    if lead_data:
        lead = {
            "id": lead_data.get("id", ""),
            "name": lead_data.get("name") or lead_data.get("displayName", ""),
        }

    teams_conn = api_data.get("teams", {})
    teams_data = teams_conn.get("nodes", []) if teams_conn else []
    teams: list[ProjectTeamOutput] = [
        {
            "id": t.get("id", ""),
            "key": t.get("key", ""),
            "name": t.get("name", ""),
        }
        for t in teams_data
    ]

    issues_data = api_data.get("issues", {})
    issues_nodes = issues_data.get("nodes", []) if issues_data else []
    issues = _extract_issues(issues_nodes)
    issue_count = len(issues)

    document_content: dict[str, Any] = api_data.get("documentContent") or {}
    description = (
        document_content.get("content")
        or api_data.get("content")
        or api_data.get("description")
        or ""
    )
    if max_description_length and len(description) > max_description_length:
        description = description[:max_description_length] + "..."

    return cast(
        ProjectOutput,
        {
            "id": api_data.get("id", ""),
            "name": api_data.get("name", ""),
            "slug_id": api_data.get("slugId", ""),
            "description": description if description else None,
            "url": api_data.get("url", ""),
            "state": api_data.get("state", ""),
            "progress": api_data.get("progress", 0.0),
            "start_date": api_data.get("startDate"),
            "target_date": api_data.get("targetDate"),
            "created_at": str(api_data.get("createdAt", "")),
            "updated_at": str(api_data.get("updatedAt", "")),
            "lead": lead,
            "teams": teams,
            "issue_count": issue_count,
            "issues": issues,
        },
    )


def _extract_issues(issues_nodes: list[Mapping[str, Any]]) -> list[ProjectIssueOutput]:
    """Extract issues from API data (already limited to 10 by query)."""
    return [_map_project_issue(i) for i in issues_nodes]


def _map_project_issue(issue_data: Mapping[str, Any]) -> ProjectIssueOutput:
    """Map a single issue to ProjectIssueOutput."""
    priority_value = issue_data.get("priority")
    priority_str = None
    if isinstance(priority_value, int):
        priority_str = IssuePriority.from_numeric(priority_value).value

    state = issue_data.get("state") or {}
    return {
        "id": issue_data.get("id", ""),
        "identifier": issue_data.get("identifier", ""),
        "title": issue_data.get("title", ""),
        "url": issue_data.get("url", ""),
        "state_name": state.get("name", "") if state else "",
        "state_type": state.get("type", "") if state else "",
        "priority": priority_str,
        "updated_at": issue_data.get("updatedAt", ""),
    }


def clean_project_summary(api_data: Mapping[str, Any]) -> ProjectSummaryOutput:
    """Clean and transform API project data to summary output format."""
    lead_data = api_data.get("lead")
    lead_name = lead_data.get("name") if lead_data else None

    teams_conn = api_data.get("teams", {})
    teams_data = teams_conn.get("nodes", []) if teams_conn else []
    teams: list[ProjectTeamOutput] = [
        {
            "id": t.get("id", ""),
            "key": t.get("key", ""),
            "name": t.get("name", ""),
        }
        for t in teams_data
    ]

    return cast(
        ProjectSummaryOutput,
        {
            "id": api_data.get("id", ""),
            "name": api_data.get("name", ""),
            "slug_id": api_data.get("slugId", ""),
            "url": api_data.get("url", ""),
            "state": api_data.get("state", ""),
            "progress": api_data.get("progress", 0.0),
            "start_date": api_data.get("startDate"),
            "target_date": api_data.get("targetDate"),
            "created_at": str(api_data.get("createdAt", "")),
            "lead_name": lead_name,
            "teams": teams,
        },
    )


def build_project_filter(
    name: str | None = None,
    state: str | None = None,
    created_after: str | None = None,
) -> dict[str, Any]:
    """Build a Linear ProjectFilter object from structured parameters."""
    project_filter: dict[str, Any] = {}

    if name:
        project_filter["name"] = {"containsIgnoreCase": name}

    if state:
        project_filter["state"] = {"eq": state}

    if created_after:
        project_filter["createdAt"] = {"gte": f"{created_after}T00:00:00Z"}

    return project_filter


def filter_projects_by_team(
    projects: Sequence[Mapping[str, Any]], team_name: str
) -> list[Mapping[str, Any]]:
    """Filter projects by team name (case-insensitive partial match)."""
    team_lower = team_name.lower()
    filtered: list[Mapping[str, Any]] = []
    for project in projects:
        teams_conn = project.get("teams", {})
        teams = teams_conn.get("nodes", []) if teams_conn else []
        for team in teams:
            if team_lower in team.get("name", "").lower():
                filtered.append(project)
                break
    return filtered


def add_basic_update_fields(
    input_data: dict[str, Any],
    fields_updated: list[str],
    name: str | None,
    description: str | None,
    state: ProjectState | None,
    start_date: str | None,
    target_date: str | None,
) -> None:
    """Add basic fields to the update input."""
    if name:
        input_data["name"] = name
        fields_updated.append("name")
    if description is not None:
        input_data["description"] = description
        fields_updated.append("description")
    if state:
        input_data["state"] = state.value
        fields_updated.append("state")
    if start_date:
        input_data["startDate"] = start_date
        fields_updated.append("start_date")
    if target_date:
        input_data["targetDate"] = target_date
        fields_updated.append("target_date")


async def update_project_teams(
    client: "LinearClient",
    current_project: Mapping[str, Any] | None,
    teams_to_add: list[str] | None,
    teams_to_remove: list[str] | None,
    auto_accept_matches: bool,
) -> tuple[list[str], list[str]]:
    """Update project teams and return (team_ids, fields_updated)."""
    teams_response = await client.get_teams(first=MAX_PAGE_SIZE)
    all_teams = teams_response.get("nodes", [])

    current_team_ids: set[str] = set()
    if current_project:
        teams_conn = current_project.get("teams", {})
        team_nodes = teams_conn.get("nodes", []) if teams_conn else []
        current_team_ids = {t.get("id") for t in team_nodes if t.get("id")}

    fields: list[str] = []
    if teams_to_add:
        for team_input in teams_to_add:
            team_id = resolve_team(list(all_teams), team_input, auto_accept_matches)
            current_team_ids.add(team_id)
        fields.append("teams_added")

    if teams_to_remove:
        for team_input in teams_to_remove:
            team_id = resolve_team(list(all_teams), team_input, auto_accept_matches)
            current_team_ids.discard(team_id)
        fields.append("teams_removed")

    return list(current_team_ids), fields


def resolve_team(
    teams: Sequence[Mapping[str, Any]], team_input: str, auto_accept_matches: bool
) -> str:
    """Resolve team by ID, key, or name."""
    team_input_lower = team_input.lower()

    for t in teams:
        if t.get("id") == team_input:
            return str(t["id"])
        key = t.get("key")
        if key and key.lower() == team_input_lower:
            return str(t["id"])
        name = t.get("name")
        if name and name.lower() == team_input_lower:
            return str(t["id"])

    result = fuzzy_match_entity(team_input, list(teams), "name", "id")

    if result.exact_match and result.best_match:
        return result.best_match.id

    if (
        auto_accept_matches
        and result.best_match
        and result.best_match.confidence >= FUZZY_AUTO_ACCEPT_CONFIDENCE
    ):
        return result.best_match.id

    suggestions = [
        f"{s.name} ({round(s.confidence * 100)}%)"
        for s in result.suggestions[:MAX_FUZZY_SUGGESTIONS]
    ]
    available = [f"{t.get('name')} ({t.get('key')})" for t in teams[:10]]
    raise RetryableToolError(
        message=f"Team '{team_input}' not found",
        additional_prompt_content=(
            f"Suggestions: {', '.join(suggestions) if suggestions else 'none'}. "
            f"Available teams: {', '.join(available)}"
        ),
    )


async def resolve_lead(client: "LinearClient", lead_input: str, auto_accept_matches: bool) -> str:
    """Resolve lead by name or email."""
    viewer_data = await client.get_viewer()
    org = viewer_data.get("organization", {})
    org_id = org.get("id") if org else None
    if not org_id:
        raise ToolExecutionError(message="Could not get organization info to resolve lead.")

    teams_response = await client.get_teams(first=MAX_PAGE_SIZE)
    teams = teams_response.get("nodes", [])

    all_members: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for t in teams:
        members_conn = t.get("members", {})
        members = members_conn.get("nodes", []) if members_conn else []
        for member in members:
            member_id = member.get("id")
            if member_id and member_id not in seen_ids:
                all_members.append(dict(member))
                seen_ids.add(member_id)

    lead_lower = lead_input.lower()
    for member_data in all_members:
        email = member_data.get("email")
        if email and email.lower() == lead_lower:
            return str(member_data["id"])
        name = member_data.get("name")
        if name and name.lower() == lead_lower:
            return str(member_data["id"])

    result = fuzzy_match_entity(lead_input, all_members, "name", "id")

    if result.exact_match and result.best_match:
        return result.best_match.id

    if (
        auto_accept_matches
        and result.best_match
        and result.best_match.confidence >= FUZZY_AUTO_ACCEPT_CONFIDENCE
    ):
        return result.best_match.id

    suggestions = [
        f"{s.name} ({round(s.confidence * 100)}%)"
        for s in result.suggestions[:MAX_FUZZY_SUGGESTIONS]
    ]
    available = [m.get("name") or m.get("email") for m in all_members[:10]]
    raise RetryableToolError(
        message=f"User '{lead_input}' not found",
        additional_prompt_content=(
            f"Suggestions: {', '.join(suggestions) if suggestions else 'none'}. "
            f"Available members: {', '.join([a for a in available if a])}"
        ),
    )


def build_create_project_response(project_data: Mapping[str, Any]) -> CreateProjectOutput:
    """Build response for create_project."""
    lead_data = project_data.get("lead")
    teams_conn = project_data.get("teams", {})
    teams_data = teams_conn.get("nodes", []) if teams_conn else []

    teams: list[ProjectTeamOutput] = [
        {"id": t.get("id", ""), "key": t.get("key", ""), "name": t.get("name", "")}
        for t in teams_data
    ]

    project: CreatedProjectOutput = {
        "id": project_data.get("id", ""),
        "name": project_data.get("name", ""),
        "slug_id": project_data.get("slugId", ""),
        "url": project_data.get("url", ""),
        "state": project_data.get("state", ""),
        "start_date": project_data.get("startDate"),
        "target_date": project_data.get("targetDate"),
        "created_at": project_data.get("createdAt", ""),
        "lead_name": lead_data.get("name") if lead_data else None,
        "teams": teams,
    }

    result: CreateProjectOutput = {"project": project}
    return cast(CreateProjectOutput, remove_none_values_recursive(result))


def build_update_project_response(
    project_data: Mapping[str, Any], fields_updated: list[str]
) -> UpdateProjectOutput:
    """Build response for update_project."""
    lead_data = project_data.get("lead")
    teams_conn = project_data.get("teams", {})
    teams_data = teams_conn.get("nodes", []) if teams_conn else []

    teams: list[ProjectTeamOutput] = [
        {"id": t.get("id", ""), "key": t.get("key", ""), "name": t.get("name", "")}
        for t in teams_data
    ]

    project: CreatedProjectOutput = {
        "id": project_data.get("id", ""),
        "name": project_data.get("name", ""),
        "slug_id": project_data.get("slugId", ""),
        "url": project_data.get("url", ""),
        "state": project_data.get("state", ""),
        "start_date": project_data.get("startDate"),
        "target_date": project_data.get("targetDate"),
        "created_at": project_data.get("createdAt", ""),
        "lead_name": lead_data.get("name") if lead_data else None,
        "teams": teams,
    }

    result: UpdateProjectOutput = {
        "project": project,
        "fields_updated": fields_updated,
    }
    return cast(UpdateProjectOutput, remove_none_values_recursive(result))
