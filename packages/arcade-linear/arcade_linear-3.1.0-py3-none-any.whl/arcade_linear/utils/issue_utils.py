"""Utility functions for issue tools - validation and entity resolution."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError

if TYPE_CHECKING:
    from arcade_linear.client import LinearClient

from arcade_linear.constants import (
    FUZZY_AUTO_ACCEPT_CONFIDENCE,
    MAX_DISPLAY_SUGGESTIONS,
    MAX_FUZZY_SUGGESTIONS,
    MAX_PAGE_SIZE,
)
from arcade_linear.utils.fuzzy_utils import fuzzy_match_entity


def validate_and_resolve_team(
    teams: list[Mapping[str, Any]],
    team_input: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve team by name/key to team ID."""
    team_input_lower = team_input.lower()

    for team in teams:
        if team.get("id") == team_input:
            return str(team["id"])
        key = team.get("key")
        if key and str(key).lower() == team_input_lower:
            return str(team["id"])
        name = team.get("name")
        if name and str(name).lower() == team_input_lower:
            return str(team["id"])

    suggestions = _fuzzy_match_entities(team_input, list(teams), "name", auto_accept_matches)

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [f"{t.get('name')} ({t.get('key')})" for t in list(teams)[:MAX_FUZZY_SUGGESTIONS]]
    raise RetryableToolError(
        message=f"Team '{team_input}' not found",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Available teams: {', '.join(available)}"
        ),
    )


def validate_and_resolve_assignee(
    users: list[Mapping[str, Any]],
    assignee_input: str,
    team_name: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve assignee by name/email to user ID."""
    assignee_lower = assignee_input.lower()

    for user in users:
        if user.get("id") == assignee_input:
            return str(user["id"])
        email = user.get("email")
        if email and str(email).lower() == assignee_lower:
            return str(user["id"])
        name = user.get("name")
        if name and str(name).lower() == assignee_lower:
            return str(user["id"])
        display_name = user.get("displayName")
        if display_name and str(display_name).lower() == assignee_lower:
            return str(user["id"])

    suggestions = _fuzzy_match_entities(assignee_input, list(users), "name", auto_accept_matches)

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [
        str(u.get("name") or u.get("email") or "") for u in list(users)[:MAX_FUZZY_SUGGESTIONS]
    ]
    raise RetryableToolError(
        message=f"User '{assignee_input}' not found in team '{team_name}'",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Team members: {', '.join(available)}"
        ),
    )


def validate_and_resolve_state(
    states: list[Mapping[str, Any]],
    state_input: str,
    team_name: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve workflow state by name to state ID."""
    state_lower = state_input.lower()

    for state in states:
        if state.get("id") == state_input:
            return str(state["id"])
        name = state.get("name")
        if name and str(name).lower() == state_lower:
            return str(state["id"])

    suggestions = _fuzzy_match_entities(state_input, list(states), "name", auto_accept_matches)

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [f"{s.get('name')} ({s.get('type')})" for s in states]
    raise RetryableToolError(
        message=f"State '{state_input}' not found for team '{team_name}'",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Available states: {', '.join(available)}"
        ),
    )


def validate_and_resolve_labels(
    all_labels: list[Mapping[str, Any]],
    label_inputs: list[str],
    auto_accept_matches: bool,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Validate and resolve label names to label IDs."""
    resolved_ids: list[str] = []
    unresolved: list[dict[str, Any]] = []

    for label_input in label_inputs:
        label_lower = label_input.lower()
        found = False

        for label in all_labels:
            if label.get("id") == label_input:
                resolved_ids.append(str(label["id"]))
                found = True
                break
            name = label.get("name")
            if name and str(name).lower() == label_lower:
                resolved_ids.append(str(label["id"]))
                found = True
                break

        if not found:
            suggestions = _fuzzy_match_entities(
                label_input, list(all_labels), "name", auto_accept_matches
            )
            if suggestions.get("auto_accepted_id"):
                resolved_ids.append(str(suggestions["auto_accepted_id"]))
            else:
                unresolved.append({
                    "input": label_input,
                    "suggestions": suggestions.get("matches", []),
                })

    if unresolved:
        available = [str(lb.get("name") or "") for lb in list(all_labels)[:MAX_FUZZY_SUGGESTIONS]]
        error_parts = [
            f"'{u['input']}' ({_format_suggestions(u['suggestions'])})" for u in unresolved
        ]
        raise RetryableToolError(
            message=f"Labels not found: {', '.join([u['input'] for u in unresolved])}",
            additional_prompt_content=(
                f"Suggestions for each: {'; '.join(error_parts)}. "
                f"Available labels: {', '.join(available)}"
            ),
        )

    return resolved_ids, []


def validate_and_resolve_project(
    projects: list[Mapping[str, Any]],
    project_input: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve project by name/slug to project ID."""
    project_lower = project_input.lower()

    for project in projects:
        if project.get("id") == project_input:
            return str(project["id"])
        if project.get("slugId") == project_input:
            return str(project["id"])
        name = project.get("name")
        if name and str(name).lower() == project_lower:
            return str(project["id"])

    suggestions = _fuzzy_match_entities(project_input, list(projects), "name", auto_accept_matches)

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [str(p.get("name") or "") for p in list(projects)[:MAX_FUZZY_SUGGESTIONS]]
    raise RetryableToolError(
        message=f"Project '{project_input}' not found",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Available projects: {', '.join(available)}"
        ),
    )


def validate_and_resolve_cycle(
    cycles: list[Mapping[str, Any]],
    cycle_input: str,
    team_name: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve cycle by name/number to cycle ID."""
    cycle_lower = cycle_input.lower()

    for cycle in cycles:
        if cycle.get("id") == cycle_input:
            return str(cycle["id"])
        if str(cycle.get("number")) == cycle_input:
            return str(cycle["id"])
        name = cycle.get("name")
        if name and str(name).lower() == cycle_lower:
            return str(cycle["id"])

    suggestions = _fuzzy_match_entities(cycle_input, list(cycles), "name", auto_accept_matches)

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [
        f"#{c.get('number')}" + (f" ({c.get('name')})" if c.get("name") else "")
        for c in list(cycles)[:MAX_FUZZY_SUGGESTIONS]
    ]
    raise RetryableToolError(
        message=f"Cycle '{cycle_input}' not found for team '{team_name}'",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Available cycles: {', '.join(available)}"
        ),
    )


def validate_and_resolve_parent_issue(
    issues: list[Mapping[str, Any]],
    parent_input: str,
    auto_accept_matches: bool,
) -> str:
    """Validate and resolve parent issue by identifier to issue ID."""
    parent_upper = parent_input.upper()

    for issue in issues:
        if issue.get("id") == parent_input:
            return str(issue["id"])
        identifier = issue.get("identifier")
        if identifier and str(identifier).upper() == parent_upper:
            return str(issue["id"])

    suggestions = _fuzzy_match_entities(
        parent_input, list(issues), "identifier", auto_accept_matches
    )

    if suggestions.get("auto_accepted_id"):
        return str(suggestions["auto_accepted_id"])

    available = [str(i.get("identifier") or "") for i in list(issues)[:MAX_FUZZY_SUGGESTIONS]]
    raise RetryableToolError(
        message=f"Parent issue '{parent_input}' not found",
        additional_prompt_content=(
            f"Suggestions: {_format_suggestions(suggestions.get('matches', []))}. "
            f"Recent issues: {', '.join(available)}"
        ),
    )


def _fuzzy_match_entities(
    query: str,
    entities: list[Mapping[str, Any]],
    name_key: str,
    auto_accept_matches: bool,
) -> dict[str, Any]:
    """Perform fuzzy matching on entities using shared fuzzy_match_entity."""
    result = fuzzy_match_entity(query, list(entities), name_key=name_key)

    if result.exact_match and result.best_match:
        return {"auto_accepted_id": result.best_match.id}

    if (
        auto_accept_matches
        and result.best_match
        and result.best_match.confidence >= FUZZY_AUTO_ACCEPT_CONFIDENCE
    ):
        return {"auto_accepted_id": result.best_match.id}

    return {
        "matches": [
            {"name": s.name, "confidence": round(s.confidence * 100), "id": s.id}
            for s in result.suggestions[:MAX_FUZZY_SUGGESTIONS]
        ]
    }


def _format_suggestions(suggestions: list[dict[str, Any]]) -> str:
    """Format suggestions list for error message."""
    if not suggestions:
        return "none"
    return ", ".join(
        f"{s['name']} ({s['confidence']}%)" for s in suggestions[:MAX_DISPLAY_SUGGESTIONS]
    )


def _add_optional_fields(
    input_data: dict[str, Any],
    fields: list[tuple[str, Any]],
    check_truthy: bool = False,
) -> None:
    """Add optional fields to input dict if they have values."""
    for key, value in fields:
        if check_truthy:
            if value:
                input_data[key] = value
        elif value is not None:
            input_data[key] = value


def build_create_issue_input(
    team_id: str,
    title: str,
    description: str | None,
    assignee_id: str | None,
    label_ids: list[str] | None,
    priority_value: int | None,
    state_id: str | None,
    project_id: str | None,
    cycle_id: str | None,
    parent_id: str | None,
    estimate: int | None,
    due_date: str | None,
) -> dict[str, Any]:
    """Build the input dict for issue creation."""
    input_data: dict[str, Any] = {"teamId": team_id, "title": title}
    _add_optional_fields(
        input_data,
        [
            ("description", description),
            ("assigneeId", assignee_id),
            ("labelIds", label_ids),
            ("stateId", state_id),
            ("projectId", project_id),
            ("cycleId", cycle_id),
            ("parentId", parent_id),
            ("dueDate", due_date),
        ],
        check_truthy=True,
    )
    _add_optional_fields(input_data, [("priority", priority_value), ("estimate", estimate)])
    return input_data


def build_update_issue_input(
    title: str | None,
    description: str | None,
    assignee_id: str | None,
    label_ids: list[str] | None,
    priority_value: int | None,
    state_id: str | None,
    project_id: str | None,
    cycle_id: str | None,
    estimate: int | None,
    due_date: str | None,
) -> dict[str, Any]:
    """Build the input dict for issue update."""
    input_data: dict[str, Any] = {}
    _add_optional_fields(
        input_data,
        [
            ("title", title),
            ("description", description),
            ("assigneeId", assignee_id),
            ("labelIds", label_ids),
            ("priority", priority_value),
            ("stateId", state_id),
            ("projectId", project_id),
            ("cycleId", cycle_id),
            ("estimate", estimate),
            ("dueDate", due_date),
        ],
    )

    return input_data


def resolve_labels_for_update(
    current_label_ids: list[str],
    all_labels: list[Mapping[str, Any]],
    labels_to_add: list[str] | None,
    labels_to_remove: list[str] | None,
    auto_accept_matches: bool,
) -> list[str] | None:
    """Resolve labels for an update operation."""
    if not labels_to_add and not labels_to_remove:
        return None

    new_label_ids = set(current_label_ids)

    if labels_to_add:
        add_ids, _ = validate_and_resolve_labels(
            list(all_labels), labels_to_add, auto_accept_matches
        )
        new_label_ids.update(add_ids)

    if labels_to_remove:
        remove_ids, _ = validate_and_resolve_labels(
            list(all_labels), labels_to_remove, auto_accept_matches
        )
        new_label_ids -= set(remove_ids)

    return list(new_label_ids)


async def resolve_create_issue_entities(
    client: Any,
    validation_data: dict[str, Any],
    team_input: str,
    assignee: str | None,
    labels_to_add: list[str] | None,
    state: str | None,
    project: str | None,
    cycle: str | None,
    parent_issue: str | None,
    auto_accept_matches: bool,
) -> dict[str, Any]:
    """Resolve all entity references for issue creation."""
    teams = validation_data["teams"]
    all_labels = validation_data["labels"]
    all_projects = validation_data["projects"]

    team_id = validate_and_resolve_team(teams, team_input, auto_accept_matches)
    team_data: dict[str, Any] = next((t for t in teams if t["id"] == team_id), {})
    team_name = str(team_data.get("name") or team_input)
    members_conn = team_data.get("members", {})
    team_members = members_conn.get("nodes", []) if members_conn else []
    states_conn = team_data.get("states", {})
    team_states = states_conn.get("nodes", []) if states_conn else []
    cycles_conn = team_data.get("cycles", {})
    team_cycles = cycles_conn.get("nodes", []) if cycles_conn else []

    resolved: dict[str, Any] = {"team_id": team_id}

    if assignee:
        if assignee == "@me":
            viewer = await client.get_viewer()
            viewer_id = viewer.get("id")
            if viewer_id:
                resolved["assignee_id"] = str(viewer_id)
        else:
            resolved["assignee_id"] = validate_and_resolve_assignee(
                team_members, assignee, team_name, auto_accept_matches
            )

    if labels_to_add:
        resolved["label_ids"], _ = validate_and_resolve_labels(
            all_labels, labels_to_add, auto_accept_matches
        )

    if state:
        resolved["state_id"] = validate_and_resolve_state(
            team_states, state, team_name, auto_accept_matches
        )

    if project:
        resolved["project_id"] = validate_and_resolve_project(
            all_projects, project, auto_accept_matches
        )

    if cycle:
        resolved["cycle_id"] = validate_and_resolve_cycle(
            team_cycles, cycle, team_name, auto_accept_matches
        )

    if parent_issue:
        team_issues = await client.get_team_issues(team_id, first=MAX_PAGE_SIZE)
        resolved["parent_id"] = validate_and_resolve_parent_issue(
            team_issues, parent_issue, auto_accept_matches
        )

    return resolved


def resolve_update_issue_entities(
    validation_data: dict[str, Any],
    team_id: str,
    team_name: str,
    assignee: str | None,
    state: str | None,
    project: str | None,
    cycle: str | None,
    auto_accept_matches: bool,
) -> dict[str, Any]:
    """Resolve entity references for issue update."""
    teams = validation_data["teams"]
    all_labels = validation_data["labels"]
    all_projects = validation_data["projects"]

    current_team: dict[str, Any] = next((t for t in teams if t["id"] == team_id), {})
    members_conn = current_team.get("members", {})
    team_members = members_conn.get("nodes", []) if members_conn else []
    states_conn = current_team.get("states", {})
    team_states = states_conn.get("nodes", []) if states_conn else []
    cycles_conn = current_team.get("cycles", {})
    team_cycles = cycles_conn.get("nodes", []) if cycles_conn else []

    resolved: dict[str, Any] = {"all_labels": all_labels}

    if assignee is not None:
        resolved["assignee_id"] = validate_and_resolve_assignee(
            team_members, assignee, team_name, auto_accept_matches
        )

    if state is not None:
        resolved["state_id"] = validate_and_resolve_state(
            team_states, state, team_name, auto_accept_matches
        )

    if project is not None:
        resolved["project_id"] = validate_and_resolve_project(
            all_projects, project, auto_accept_matches
        )

    if cycle is not None:
        resolved["cycle_id"] = validate_and_resolve_cycle(
            team_cycles, cycle, team_name, auto_accept_matches
        )

    return resolved


async def resolve_issue(client: "LinearClient", issue_input: str) -> "IssueResponse":  # type: ignore[name-defined]  # noqa: F821
    """Resolve issue by ID or identifier and return issue data.

    Raises ToolExecutionError if issue is not found.
    """
    issue = await client.get_issue_by_id(issue_input)
    if not issue:
        raise ToolExecutionError(
            message=f"Issue '{issue_input}' not found",
            developer_message=f"No issue found with ID or identifier: {issue_input}",
        )
    return issue
