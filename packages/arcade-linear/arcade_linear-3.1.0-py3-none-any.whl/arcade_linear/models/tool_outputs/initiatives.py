"""TypedDict definitions for initiative-related tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo


class InitiativeProjectOutput(TypedDict, total=False):
    """Project data nested in initiative outputs."""

    id: str
    """Project's unique identifier."""

    name: str
    """Project name."""

    state: str
    """Project state."""

    progress: float
    """Project progress (0.0 to 1.0)."""

    url: str | None
    """URL to the project in Linear."""


class InitiativeOutput(TypedDict, total=False):
    """Full initiative data in tool outputs."""

    id: str
    """Initiative's unique identifier."""

    name: str
    """Initiative name."""

    description: str | None
    """Initiative description."""

    status: str
    """Initiative status."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when initiative was created."""

    updated_at: str
    """ISO 8601 timestamp in UTC when initiative was last updated."""

    url: str
    """URL to the initiative in Linear."""

    project_count: int
    """Total number of projects linked to this initiative."""

    projects: list[InitiativeProjectOutput]
    """Projects linked to this initiative (max 10)."""


class InitiativeSummaryOutput(TypedDict, total=False):
    """Summary initiative data for list results."""

    id: str
    """Initiative's unique identifier."""

    name: str
    """Initiative name."""

    status: str
    """Initiative status."""

    progress: float | None
    """Initiative progress (0.0 to 1.0)."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when initiative was created."""

    url: str
    """URL to the initiative in Linear."""

    project_count: int
    """Total number of projects linked to this initiative."""


class InitiativeDetailsOutput(TypedDict, total=False):
    """Output for get_initiative tool."""

    initiative: InitiativeOutput
    """Full initiative details."""


class ListInitiativesOutput(TypedDict, total=False):
    """Output for list_initiatives tool."""

    initiatives: list[InitiativeSummaryOutput]
    """List of initiatives."""

    items_returned: int
    """Number of initiatives returned in this response."""

    pagination: PaginationInfo | None
    """Pagination information for fetching more results."""

    filters: dict | None
    """Applied filters."""

    filtering_note: str | None
    """Note when local filtering reduced results below requested limit."""


class InitiativeDescriptionOutput(TypedDict, total=False):
    """Output for get_initiative_description tool."""

    initiative_id: str
    """Initiative's unique identifier."""

    initiative_name: str
    """Initiative name for reference."""

    description: str
    """Full or partial description content."""

    total_length: int
    """Total length of the full description in characters."""

    has_more: bool
    """True if there is more content after this chunk."""


class CreatedInitiativeOutput(TypedDict, total=False):
    """Simplified initiative output for create/update responses."""

    id: str
    """Initiative's unique identifier."""

    name: str
    """Initiative name."""

    description: str | None
    """Initiative description."""

    status: str
    """Initiative status."""

    target_date: str | None
    """Target completion date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when initiative was created."""

    updated_at: str
    """ISO 8601 timestamp in UTC when initiative was last updated."""

    url: str
    """URL to the initiative in Linear."""


class CreateInitiativeOutput(TypedDict, total=False):
    """Output for create_initiative tool."""

    initiative: CreatedInitiativeOutput
    """The created initiative details."""


class UpdateInitiativeOutput(TypedDict, total=False):
    """Output for update_initiative tool."""

    initiative: CreatedInitiativeOutput
    """The updated initiative details."""

    fields_updated: list[str]
    """List of field names that were updated."""


class AddProjectToInitiativeOutput(TypedDict, total=False):
    """Output for add_project_to_initiative tool."""

    initiative_id: str
    """ID of the initiative."""

    initiative_name: str
    """Name of the initiative."""

    project_id: str
    """ID of the linked project."""

    project_name: str
    """Name of the linked project."""

    project_url: str
    """URL of the linked project."""
