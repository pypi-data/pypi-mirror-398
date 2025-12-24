"""TypedDict definitions for project-related tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo


class MilestoneOutput(TypedDict, total=False):
    """Project milestone data in tool outputs."""

    id: str
    """Milestone's unique identifier."""

    name: str
    """Milestone name."""

    description: str | None
    """Milestone description."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""


class ProjectLeadOutput(TypedDict, total=False):
    """Project lead data in tool outputs."""

    id: str
    """User's unique identifier."""

    name: str
    """User's full name."""


class ProjectMemberOutput(TypedDict, total=False):
    """Project member data in tool outputs."""

    id: str
    """User's unique identifier."""

    name: str
    """User's full name."""


class ProjectTeamOutput(TypedDict, total=False):
    """Team associated with a project."""

    id: str
    """Team's unique identifier."""

    key: str
    """Team's short key (e.g., FE, BE)."""

    name: str
    """Team's full name."""


class ProjectIssueOutput(TypedDict, total=False):
    """Issue summary in project outputs."""

    id: str
    """Issue's unique identifier."""

    identifier: str
    """Issue's human-readable identifier (e.g., 'FE-123')."""

    title: str
    """Issue title."""

    url: str
    """URL to the issue in Linear."""

    state_name: str
    """Name of the issue's workflow state."""

    state_type: str
    """Type of the workflow state (e.g., 'started', 'completed')."""

    priority: str | None
    """Issue priority."""

    updated_at: str
    """ISO 8601 timestamp in UTC when issue was last updated."""


class ProjectOutput(TypedDict, total=False):
    """Full project data in tool outputs."""

    id: str
    """Project's unique identifier."""

    name: str
    """Project name."""

    slug_id: str
    """Project's URL-friendly slug identifier."""

    description: str | None
    """Project description."""

    url: str
    """URL to the project in Linear."""

    state: str
    """Project state."""

    progress: float
    """Project progress (0.0 to 1.0)."""

    start_date: str | None
    """Project start date in YYYY-MM-DD format."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when project was created."""

    updated_at: str
    """ISO 8601 timestamp in UTC when project was last updated."""

    lead: ProjectLeadOutput | None
    """Project lead user."""

    teams: list[ProjectTeamOutput]
    """Teams associated with the project."""

    issue_count: int
    """Total number of issues in the project."""

    issues: list[ProjectIssueOutput]
    """Latest updated issues in the project (max 10)."""


class ProjectSummaryOutput(TypedDict, total=False):
    """Summary project data for search results."""

    id: str
    """Project's unique identifier."""

    name: str
    """Project name."""

    slug_id: str
    """Project's URL-friendly slug identifier."""

    url: str
    """URL to the project in Linear."""

    state: str
    """Project state."""

    progress: float
    """Project progress (0.0 to 1.0)."""

    start_date: str | None
    """Project start date in YYYY-MM-DD format."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when project was created."""

    lead_name: str | None
    """Name of the project lead."""

    teams: list[ProjectTeamOutput]
    """Teams associated with the project."""


class ProjectDetailsOutput(TypedDict, total=False):
    """Output for get_project tool."""

    project: ProjectOutput
    """Full project details."""


class ProjectSearchOutput(TypedDict, total=False):
    """Output for search_projects tool."""

    projects: list[ProjectSummaryOutput]
    """List of projects."""

    items_returned: int
    """Number of projects returned in this response."""

    pagination: PaginationInfo | None
    """Pagination information for fetching more results."""

    filters: dict | None
    """Applied filters."""

    filtering_note: str | None
    """Note when local filtering reduced results below requested limit."""


class ProjectDescriptionOutput(TypedDict, total=False):
    """Output for get_project_description tool."""

    project_id: str
    """Project's unique identifier."""

    project_name: str
    """Project name for reference."""

    description: str
    """Full or partial description content."""

    total_length: int
    """Total length of the full description in characters."""

    has_more: bool
    """True if there is more content after this chunk."""


class ProjectUpdateOutput(TypedDict, total=False):
    """Project status update data."""

    id: str
    """Update's unique identifier."""

    body: str
    """Update content in Markdown."""

    health: str | None
    """Project health status at time of update."""

    created_at: str
    """ISO 8601 timestamp in UTC when update was created."""

    user_name: str
    """Name of user who created the update."""

    project_id: str
    """Project's unique identifier."""

    project_name: str
    """Project name for reference."""

    project_url: str
    """URL to the project in Linear."""


class CreateProjectUpdateOutput(TypedDict, total=False):
    """Output for create_project_update tool."""

    project_update: ProjectUpdateOutput
    """The created project update."""


class CreatedProjectOutput(TypedDict, total=False):
    """Simplified project output for create/update responses."""

    id: str
    """Project's unique identifier."""

    name: str
    """Project name."""

    slug_id: str
    """Project's URL-friendly slug identifier."""

    url: str
    """URL to the project in Linear."""

    state: str
    """Project state."""

    start_date: str | None
    """Project start date in YYYY-MM-DD format."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when project was created."""

    lead_name: str | None
    """Name of the project lead."""

    teams: list[ProjectTeamOutput]
    """Teams associated with the project."""


class CreateProjectOutput(TypedDict, total=False):
    """Output for create_project tool."""

    project: CreatedProjectOutput
    """The created project details."""


class UpdateProjectOutput(TypedDict, total=False):
    """Output for update_project tool."""

    project: CreatedProjectOutput
    """The updated project details."""

    fields_updated: list[str]
    """List of field names that were updated."""
