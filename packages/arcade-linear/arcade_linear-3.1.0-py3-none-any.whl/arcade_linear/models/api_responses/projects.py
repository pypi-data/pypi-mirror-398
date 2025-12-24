"""TypedDict definitions for Linear project and initiative API responses."""

from typing_extensions import TypedDict

from arcade_linear.models.api_responses.common import PageInfoResponse


class ProjectTeamResponse(TypedDict, total=False):
    """Team data nested in project response."""

    id: str
    name: str
    key: str


class ProjectTeamsConnectionResponse(TypedDict, total=False):
    """Teams connection in project response."""

    nodes: list[ProjectTeamResponse]


class ProjectIssuesCountResponse(TypedDict, total=False):
    """Issue count data in project response."""

    totalCount: int


class ProjectMilestoneResponse(TypedDict, total=False):
    """Milestone data from Linear API."""

    id: str
    name: str
    description: str | None
    targetDate: str | None
    sortOrder: float


class ProjectMilestonesConnectionResponse(TypedDict, total=False):
    """Milestones connection in project response."""

    nodes: list[ProjectMilestoneResponse]


class ProjectResponse(TypedDict, total=False):
    """Project data from Linear API."""

    id: str
    slugId: str
    name: str
    description: str | None
    state: str
    progress: float
    health: str | None
    startDate: str | None
    targetDate: str | None
    completedAt: str | None
    canceledAt: str | None
    createdAt: str
    updatedAt: str
    url: str
    icon: str | None
    color: str | None
    teams: ProjectTeamsConnectionResponse
    issues: ProjectIssuesCountResponse
    milestones: ProjectMilestonesConnectionResponse


class ProjectConnectionResponse(TypedDict, total=False):
    """Projects connection from Linear API."""

    nodes: list[ProjectResponse]
    pageInfo: PageInfoResponse


class InitiativeProjectResponse(TypedDict, total=False):
    """Project summary nested in initiative response."""

    id: str
    name: str
    state: str
    progress: float
    url: str


class InitiativeProjectsConnectionResponse(TypedDict, total=False):
    """Projects connection in initiative response."""

    nodes: list[InitiativeProjectResponse]


class InitiativeResponse(TypedDict, total=False):
    """Initiative data from Linear API."""

    id: str
    name: str
    description: str | None
    status: str
    progress: float | None
    targetDate: str | None
    createdAt: str
    updatedAt: str
    url: str
    projects: InitiativeProjectsConnectionResponse


class InitiativeConnectionResponse(TypedDict, total=False):
    """Initiatives connection from Linear API."""

    nodes: list[InitiativeResponse]
    pageInfo: PageInfoResponse
