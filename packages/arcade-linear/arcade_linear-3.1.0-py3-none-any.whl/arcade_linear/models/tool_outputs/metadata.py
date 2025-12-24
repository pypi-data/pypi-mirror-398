"""TypedDict definitions for metadata-related tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo, TeamSummary


class LabelOutput(TypedDict, total=False):
    """Label data in tool outputs."""

    id: str
    """Label's unique identifier."""

    name: str
    """Label name."""

    color: str
    """Label color (hex code)."""

    description: str | None
    """Label description."""


class ListLabelsOutput(TypedDict, total=False):
    """Output for list_labels tool."""

    labels: list[LabelOutput]
    """List of labels."""

    items_returned: int
    """Number of labels returned in this response."""

    pagination: PaginationInfo | None
    """Pagination information for fetching more results."""


class WorkflowStateOutput(TypedDict, total=False):
    """Workflow state data in tool outputs."""

    id: str
    """State's unique identifier."""

    name: str
    """State name (e.g., 'In Progress', 'Done')."""

    type: str
    """State type."""

    team: TeamSummary | None
    """Team this state belongs to."""


class ListWorkflowStatesOutput(TypedDict, total=False):
    """Output for list_workflow_states tool."""

    states: list[WorkflowStateOutput]
    """List of workflow states."""

    items_returned: int
    """Number of states returned in this response."""

    pagination: PaginationInfo | None
    """Pagination information for fetching more results."""

    filters: dict | None
    """Applied filters."""

    filtering_note: str | None
    """Note when local filtering reduced results below requested limit."""
