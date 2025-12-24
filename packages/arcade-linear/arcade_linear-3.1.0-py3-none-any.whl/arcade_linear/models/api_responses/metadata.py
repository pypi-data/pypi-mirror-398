"""TypedDict definitions for Linear metadata API responses (teams, labels, states)."""

from typing_extensions import TypedDict

from arcade_linear.models.api_responses.common import (
    LabelResponse,
    OrganizationResponse,
    PageInfoResponse,
    UserResponse,
)
from arcade_linear.models.api_responses.issues import WorkflowStateResponse


class TeamMembersConnectionResponse(TypedDict, total=False):
    """Team members connection from Linear API."""

    nodes: list[UserResponse]


class TeamResponse(TypedDict, total=False):
    """Team data from Linear API."""

    id: str
    key: str
    name: str
    description: str | None
    private: bool
    archivedAt: str | None
    createdAt: str
    updatedAt: str
    icon: str | None
    color: str | None
    cyclesEnabled: bool
    issueEstimationType: str
    organization: OrganizationResponse
    members: TeamMembersConnectionResponse


class TeamsConnectionResponse(TypedDict, total=False):
    """Teams connection from Linear API."""

    nodes: list[TeamResponse]
    pageInfo: PageInfoResponse


class LabelsConnectionResponse(TypedDict, total=False):
    """Labels connection from Linear API."""

    nodes: list[LabelResponse]
    pageInfo: PageInfoResponse


class WorkflowStatesConnectionResponse(TypedDict, total=False):
    """Workflow states connection from Linear API."""

    nodes: list[WorkflowStateResponse]
    pageInfo: PageInfoResponse
