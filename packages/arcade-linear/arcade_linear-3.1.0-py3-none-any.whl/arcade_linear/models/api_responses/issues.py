"""TypedDict definitions for Linear issue-related API responses."""

from typing import Any

from typing_extensions import TypedDict

from arcade_linear.models.api_responses.common import (
    LabelResponse,
    PageInfoResponse,
    UserResponse,
)


class WorkflowStateResponse(TypedDict, total=False):
    """Workflow state data from Linear API."""

    id: str
    name: str
    type: str
    color: str
    position: float
    description: str | None


class LabelsConnectionResponse(TypedDict, total=False):
    """Labels connection from Linear API."""

    nodes: list[LabelResponse]


class TeamSummaryResponse(TypedDict, total=False):
    """Team summary data from Linear API (nested in issue)."""

    id: str
    key: str
    name: str


class ProjectSummaryResponse(TypedDict, total=False):
    """Project summary data from Linear API (nested in issue)."""

    id: str
    name: str
    state: str
    progress: float
    startDate: str | None
    targetDate: str | None


class CycleSummaryResponse(TypedDict, total=False):
    """Cycle summary data from Linear API (nested in issue)."""

    id: str
    number: int
    name: str | None
    startsAt: str
    endsAt: str
    progress: float


class ParentIssueSummaryResponse(TypedDict, total=False):
    """Parent issue summary from Linear API."""

    id: str
    identifier: str
    title: str


class CommentResponse(TypedDict, total=False):
    """Comment data from Linear API."""

    id: str
    body: str
    createdAt: str
    updatedAt: str
    user: UserResponse


class AttachmentResponse(TypedDict, total=False):
    """Attachment data from Linear API."""

    id: str
    title: str
    subtitle: str | None
    url: str
    metadata: dict[str, Any] | None
    createdAt: str
    sourceType: str | None


class RelatedIssueResponse(TypedDict, total=False):
    """Related issue data from Linear API."""

    id: str
    identifier: str
    title: str


class IssueRelationResponse(TypedDict, total=False):
    """Issue relation data from Linear API."""

    id: str
    type: str
    relatedIssue: RelatedIssueResponse


class ChildIssueResponse(TypedDict, total=False):
    """Child issue data from Linear API."""

    id: str
    identifier: str
    title: str
    state: WorkflowStateResponse


class CommentsConnectionResponse(TypedDict, total=False):
    """Comments connection from Linear API."""

    nodes: list[CommentResponse]


class AttachmentsConnectionResponse(TypedDict, total=False):
    """Attachments connection from Linear API."""

    nodes: list[AttachmentResponse]


class RelationsConnectionResponse(TypedDict, total=False):
    """Relations connection from Linear API."""

    nodes: list[IssueRelationResponse]


class ChildrenConnectionResponse(TypedDict, total=False):
    """Children connection from Linear API."""

    nodes: list[ChildIssueResponse]


class IssueResponse(TypedDict, total=False):
    """Complete issue data from Linear API."""

    id: str
    identifier: str
    title: str
    description: str | None
    priority: int
    priorityLabel: str
    estimate: float | None
    sortOrder: float
    createdAt: str
    updatedAt: str
    completedAt: str | None
    canceledAt: str | None
    dueDate: str | None
    url: str
    branchName: str | None
    creator: UserResponse
    assignee: UserResponse | None
    state: WorkflowStateResponse
    team: TeamSummaryResponse
    project: ProjectSummaryResponse | None
    cycle: CycleSummaryResponse | None
    parent: ParentIssueSummaryResponse | None
    labels: LabelsConnectionResponse
    comments: CommentsConnectionResponse
    attachments: AttachmentsConnectionResponse
    relations: RelationsConnectionResponse
    children: ChildrenConnectionResponse


class IssueSearchConnectionResponse(TypedDict, total=False):
    """Issue search results from Linear API."""

    nodes: list[IssueResponse]
    pageInfo: PageInfoResponse
    totalCount: int


class NotificationResponse(TypedDict, total=False):
    """Notification data from Linear API."""

    id: str
    type: str
    createdAt: str
    readAt: str | None
    archivedAt: str | None
    issue: IssueResponse | None
    actor: UserResponse | None


class NotificationsConnectionResponse(TypedDict, total=False):
    """Notifications connection from Linear API."""

    nodes: list[NotificationResponse]
    pageInfo: PageInfoResponse
