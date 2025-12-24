"""Mapper functions to transform Linear API responses to tool outputs."""

from collections.abc import Mapping
from typing import Any, cast

from arcade_linear.models.api_responses import (
    AttachmentResponse,
    ChildIssueResponse,
    CommentResponse,
    CycleSummaryResponse,
    InitiativeProjectResponse,
    InitiativeResponse,
    IssueRelationResponse,
    IssueResponse,
    LabelResponse,
    NotificationResponse,
    PageInfoResponse,
    ParentIssueSummaryResponse,
    ProjectSummaryResponse,
    TeamSummaryResponse,
    UserResponse,
    ViewerResponse,
    WorkflowStateResponse,
)
from arcade_linear.models.tool_outputs.common import (
    LabelData,
    PaginationInfo,
    StateData,
    TeamSummary,
    UserData,
)
from arcade_linear.models.tool_outputs.initiatives import (
    InitiativeOutput,
    InitiativeProjectOutput,
    InitiativeSummaryOutput,
)
from arcade_linear.models.tool_outputs.issues import (
    AttachmentOutput,
    ChildIssueData,
    CommentOutput,
    CycleSummary,
    IssueDetailsOutput,
    IssueOutput,
    IssueRelationData,
    ParentIssueSummary,
    ProjectSummary,
)
from arcade_linear.models.tool_outputs.user_context import (
    NotificationData,
    WhoAmIOutput,
)


def map_user(api_data: UserResponse | None) -> UserData:
    """Map API user response to UserData output."""
    if not api_data:
        return cast(UserData, {})
    return cast(
        UserData,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name") or api_data.get("displayName") or "Unknown",
            "email": api_data.get("email"),
        },
    )


def map_team_summary(api_data: TeamSummaryResponse | Mapping[str, Any] | None) -> TeamSummary:
    """Map API team response to TeamSummary output."""
    if not api_data:
        return cast(TeamSummary, {})
    return cast(
        TeamSummary,
        {
            "id": api_data.get("id"),
            "key": api_data.get("key"),
            "name": api_data.get("name"),
        },
    )


def map_state(api_data: WorkflowStateResponse | None) -> StateData:
    """Map API workflow state response to StateData output."""
    if not api_data:
        return cast(StateData, {})
    return cast(
        StateData,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "type": api_data.get("type"),
        },
    )


def map_label(api_data: LabelResponse | None) -> LabelData:
    """Map API label response to LabelData output."""
    if not api_data:
        return cast(LabelData, {})
    return cast(
        LabelData,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "color": api_data.get("color"),
        },
    )


def map_project_summary(api_data: ProjectSummaryResponse | None) -> ProjectSummary:
    """Map API project response to ProjectSummary output."""
    if not api_data:
        return cast(ProjectSummary, {})
    return cast(
        ProjectSummary,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "state": api_data.get("state"),
            "progress": api_data.get("progress"),
            "url": api_data.get("url"),
        },
    )


def map_cycle_summary(api_data: CycleSummaryResponse | None) -> CycleSummary:
    """Map API cycle response to CycleSummary output."""
    if not api_data:
        return cast(CycleSummary, {})
    return cast(
        CycleSummary,
        {
            "id": api_data.get("id"),
            "number": api_data.get("number"),
            "name": api_data.get("name"),
            "progress": api_data.get("progress"),
        },
    )


def map_comment(
    api_data: CommentResponse | Mapping[str, Any] | None,
    max_body_length: int | None = None,
) -> CommentOutput:
    """Map API comment response to CommentOutput."""
    if not api_data:
        return cast(CommentOutput, {})

    body = api_data.get("body") or ""
    if max_body_length and len(body) > max_body_length:
        body = body[:max_body_length] + "..."

    return cast(
        CommentOutput,
        {
            "id": api_data.get("id") or "",
            "body": body,
            "created_at": api_data.get("createdAt") or "",
            "user": map_user(api_data.get("user")),
        },
    )


def map_attachment(api_data: AttachmentResponse | None) -> AttachmentOutput:
    """Map API attachment response to AttachmentOutput."""
    if not api_data:
        return cast(AttachmentOutput, {})
    return cast(
        AttachmentOutput,
        {
            "id": api_data.get("id"),
            "title": api_data.get("title"),
            "url": api_data.get("url"),
            "created_at": api_data.get("createdAt"),
        },
    )


def map_relation(api_data: IssueRelationResponse | None) -> IssueRelationData:
    """Map API issue relation response to IssueRelationData output."""
    if not api_data:
        return cast(IssueRelationData, {})
    related_issue = api_data.get("relatedIssue", {})
    return cast(
        IssueRelationData,
        {
            "id": api_data.get("id"),
            "type": api_data.get("type"),
            "related_issue_id": related_issue.get("id") if related_issue else None,
            "related_issue_identifier": related_issue.get("identifier") if related_issue else None,
            "related_issue_title": related_issue.get("title") if related_issue else None,
            "related_issue_url": related_issue.get("url") if related_issue else None,
        },
    )


def map_child_issue(api_data: ChildIssueResponse | None) -> ChildIssueData:
    """Map API child issue response to ChildIssueData output."""
    if not api_data:
        return cast(ChildIssueData, {})
    return cast(
        ChildIssueData,
        {
            "id": api_data.get("id"),
            "identifier": api_data.get("identifier"),
            "title": api_data.get("title"),
            "state": map_state(api_data.get("state")),
            "url": api_data.get("url"),
        },
    )


def map_parent_issue(api_data: ParentIssueSummaryResponse | None) -> ParentIssueSummary:
    """Map API parent issue response to ParentIssueSummary output."""
    if not api_data:
        return cast(ParentIssueSummary, {})
    return cast(
        ParentIssueSummary,
        {
            "id": api_data.get("id"),
            "identifier": api_data.get("identifier"),
            "title": api_data.get("title"),
            "url": api_data.get("url"),
        },
    )


def map_issue(api_data: IssueResponse | None) -> IssueOutput:
    """Map API issue response to IssueOutput."""
    if not api_data:
        return cast(IssueOutput, {})

    labels_conn = api_data.get("labels", {})
    labels_data: list[Any] = labels_conn.get("nodes", []) if labels_conn else []

    document_content: dict[str, Any] = api_data.get("documentContent") or {}  # type: ignore[assignment]
    description = document_content.get("content") or api_data.get("description")

    return cast(
        IssueOutput,
        {
            "id": api_data.get("id"),
            "identifier": api_data.get("identifier"),
            "title": api_data.get("title"),
            "description": description,
            "url": api_data.get("url"),
            "priority": api_data.get("priorityLabel"),
            "state": map_state(api_data.get("state")),
            "team": map_team_summary(api_data.get("team")),
            "assignee": map_user(api_data.get("assignee")) if api_data.get("assignee") else None,
            "labels": [map_label(label) for label in labels_data if label],
            "project": map_project_summary(api_data.get("project"))
            if api_data.get("project")
            else None,
            "due_date": api_data.get("dueDate"),
            "created_at": api_data.get("createdAt"),
            "updated_at": api_data.get("updatedAt"),
        },
    )


def map_issue_details(api_data: IssueResponse | None) -> IssueDetailsOutput:
    """Map API issue response to IssueDetailsOutput with full details."""
    if not api_data:
        return cast(IssueDetailsOutput, {})

    labels_conn = api_data.get("labels", {})
    labels_data: list[Any] = labels_conn.get("nodes", []) if labels_conn else []

    comments_conn = api_data.get("comments", {})
    comments_data: list[Any] = comments_conn.get("nodes", []) if comments_conn else []

    attachments_conn = api_data.get("attachments", {})
    attachments_data: list[Any] = attachments_conn.get("nodes", []) if attachments_conn else []

    relations_conn = api_data.get("relations", {})
    relations_data: list[Any] = relations_conn.get("nodes", []) if relations_conn else []

    children_conn = api_data.get("children", {})
    children_data: list[Any] = children_conn.get("nodes", []) if children_conn else []

    document_content: dict[str, Any] = api_data.get("documentContent") or {}  # type: ignore[assignment]
    description = document_content.get("content") or api_data.get("description")

    return cast(
        IssueDetailsOutput,
        {
            "id": api_data.get("id"),
            "identifier": api_data.get("identifier"),
            "title": api_data.get("title"),
            "description": description,
            "url": api_data.get("url"),
            "priority": api_data.get("priorityLabel"),
            "estimate": api_data.get("estimate"),
            "state": map_state(api_data.get("state")),
            "team": map_team_summary(api_data.get("team")),
            "assignee": map_user(api_data.get("assignee")) if api_data.get("assignee") else None,
            "creator": map_user(api_data.get("creator")) if api_data.get("creator") else None,
            "labels": [map_label(label) for label in labels_data if label],
            "project": map_project_summary(api_data.get("project"))
            if api_data.get("project")
            else None,
            "cycle": map_cycle_summary(api_data.get("cycle")) if api_data.get("cycle") else None,
            "parent": map_parent_issue(api_data.get("parent")) if api_data.get("parent") else None,
            "due_date": api_data.get("dueDate"),
            "created_at": api_data.get("createdAt"),
            "updated_at": api_data.get("updatedAt"),
            "completed_at": api_data.get("completedAt"),
            "branch_name": api_data.get("branchName"),
            "comments": [map_comment(c) for c in comments_data if c],
            "attachments": [map_attachment(a) for a in attachments_data if a],
            "relations": [map_relation(r) for r in relations_data if r],
            "children": [map_child_issue(child) for child in children_data if child],
        },
    )


def map_pagination(
    page_info: PageInfoResponse | Mapping[str, Any] | None,
) -> PaginationInfo:
    """Map API pageInfo response to PaginationInfo output."""
    if not page_info:
        return cast(PaginationInfo, {})
    return cast(
        PaginationInfo,
        {
            "has_next_page": page_info.get("hasNextPage", False),
            "end_cursor": page_info.get("endCursor"),
        },
    )


def map_viewer(
    api_data: ViewerResponse | None, teams_data: list[TeamSummaryResponse] | None = None
) -> WhoAmIOutput:
    """Map API viewer response to WhoAmIOutput."""
    if not api_data:
        return cast(WhoAmIOutput, {})

    org = api_data.get("organization", {})
    teams = teams_data or []

    return cast(
        WhoAmIOutput,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "email": api_data.get("email"),
            "display_name": api_data.get("displayName"),
            "avatar_url": api_data.get("avatarUrl"),
            "active": api_data.get("active", True),
            "admin": api_data.get("admin", False),
            "organization_name": org.get("name") if org else None,
            "teams": [map_team_summary(team) for team in teams if team],
        },
    )


def map_notification(api_data: NotificationResponse | None) -> NotificationData:
    """Map API notification response to NotificationData output."""
    if not api_data:
        return cast(NotificationData, {})

    issue = api_data.get("issue", {})

    return cast(
        NotificationData,
        {
            "id": api_data.get("id"),
            "type": api_data.get("type"),
            "created_at": api_data.get("createdAt"),
            "read_at": api_data.get("readAt"),
            "issue_id": issue.get("id") if issue else None,
            "issue_identifier": issue.get("identifier") if issue else None,
            "issue_title": issue.get("title") if issue else None,
            "actor": map_user(api_data.get("actor")) if api_data.get("actor") else None,
        },
    )


def map_initiative_project(api_data: InitiativeProjectResponse | None) -> InitiativeProjectOutput:
    """Map API project response nested in initiative to InitiativeProjectOutput."""
    if not api_data:
        return cast(InitiativeProjectOutput, {})
    return cast(
        InitiativeProjectOutput,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "state": api_data.get("state"),
            "progress": api_data.get("progress"),
            "url": api_data.get("url"),
        },
    )


MAX_INITIATIVE_PROJECTS = 10


def map_initiative(
    api_data: InitiativeResponse | Mapping[str, Any] | None,
    max_description_length: int | None = None,
    max_projects: int = MAX_INITIATIVE_PROJECTS,
) -> InitiativeOutput:
    """Map API initiative response to InitiativeOutput.

    Projects are limited to max_projects (default 10) to reduce response size.
    """
    if not api_data:
        return cast(InitiativeOutput, {})

    document_content: dict[str, Any] = api_data.get("documentContent") or {}  # type: ignore[assignment]
    description = document_content.get("content") or api_data.get("description") or ""
    if max_description_length and len(description) > max_description_length:
        description = description[:max_description_length] + "..."

    projects_conn = api_data.get("projects", {})
    projects_data: list[Any] = projects_conn.get("nodes", []) if projects_conn else []
    total_project_count = len(projects_data)
    limited_projects = projects_data[:max_projects]
    projects = [map_initiative_project(p) for p in limited_projects if p]

    return cast(
        InitiativeOutput,
        {
            "id": api_data.get("id") or "",
            "name": api_data.get("name") or "",
            "description": description if description else None,
            "status": api_data.get("status") or "",
            "target_date": api_data.get("targetDate"),
            "created_at": api_data.get("createdAt") or "",
            "updated_at": api_data.get("updatedAt") or "",
            "url": api_data.get("url") or "",
            "project_count": total_project_count,
            "projects": projects,
        },
    )


def map_initiative_summary(
    api_data: InitiativeResponse | Mapping[str, Any] | None,
) -> InitiativeSummaryOutput:
    """Map API initiative response to InitiativeSummaryOutput."""
    if not api_data:
        return cast(InitiativeSummaryOutput, {})

    projects_conn = api_data.get("projects", {})
    projects_data: list[Any] = projects_conn.get("nodes", []) if projects_conn else []

    return cast(
        InitiativeSummaryOutput,
        {
            "id": api_data.get("id"),
            "name": api_data.get("name"),
            "status": api_data.get("status"),
            "progress": api_data.get("progress"),
            "target_date": api_data.get("targetDate"),
            "created_at": api_data.get("createdAt"),
            "url": api_data.get("url"),
            "project_count": len(projects_data),
        },
    )
