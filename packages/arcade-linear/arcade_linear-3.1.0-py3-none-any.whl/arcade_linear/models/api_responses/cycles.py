"""TypedDict definitions for Linear cycle API responses."""

from typing_extensions import TypedDict

from arcade_linear.models.api_responses.common import PageInfoResponse
from arcade_linear.models.api_responses.issues import TeamSummaryResponse


class CycleResponse(TypedDict, total=False):
    """Cycle data from Linear API."""

    id: str
    number: int
    name: str | None
    description: str | None
    startsAt: str
    endsAt: str
    completedAt: str | None
    progress: float
    scopeHistory: list[float]
    completedScopeHistory: list[float]
    team: TeamSummaryResponse


class CyclesConnectionResponse(TypedDict, total=False):
    """Cycles connection from Linear API."""

    nodes: list[CycleResponse]
    pageInfo: PageInfoResponse
