"""TypedDict models for cycle tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo, TeamSummary


class CycleOutput(TypedDict, total=False):
    """Full cycle data in tool outputs."""

    id: str
    """Cycle's unique identifier."""

    number: int
    """Cycle number within the team."""

    name: str | None
    """Cycle name if set."""

    description: str | None
    """Cycle description."""

    starts_at: str
    """Start date in ISO 8601 format."""

    ends_at: str
    """End date in ISO 8601 format."""

    completed_at: str | None
    """Completion timestamp in ISO 8601 format, if completed."""

    progress: float
    """Cycle progress (0.0 to 1.0)."""

    is_active: bool
    """True if cycle is currently active (between start and end dates)."""

    team: TeamSummary | None
    """Team this cycle belongs to."""


class CycleDetailsOutput(TypedDict, total=False):
    """Output for get_cycle tool."""

    cycle: CycleOutput
    """Cycle details."""


class ListCyclesOutput(TypedDict, total=False):
    """Output for list_cycles tool."""

    cycles: list[CycleOutput]
    """List of cycles matching filters."""

    items_returned: int
    """Number of cycles returned in this response."""

    pagination: PaginationInfo | None
    """Pagination info for fetching more results."""

    filters: dict | None
    """Filters that were applied."""

    filtering_note: str | None
    """Note when local filtering reduced results below requested limit."""
