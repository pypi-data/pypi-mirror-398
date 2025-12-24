"""Common TypedDict definitions shared across Linear tool outputs."""

from typing_extensions import TypedDict


class PaginationInfo(TypedDict, total=False):
    """Pagination information for paginated tool outputs."""

    has_next_page: bool
    """Whether more results are available."""

    end_cursor: str | None
    """Cursor for fetching next page of results."""


class UserData(TypedDict, total=False):
    """User information in tool outputs."""

    id: str
    """User's unique identifier."""

    name: str
    """User's full name or display name."""

    email: str | None
    """User's email address."""


class TeamSummary(TypedDict, total=False):
    """Team summary information in tool outputs."""

    id: str
    """Team's unique identifier."""

    key: str
    """Team's short key (e.g., FE, BE)."""

    name: str
    """Team's full name."""


class StateData(TypedDict, total=False):
    """Workflow state information in tool outputs."""

    id: str
    """State's unique identifier."""

    name: str
    """State name (e.g., 'In Progress', 'Done')."""

    type: str
    """State type."""


class LabelData(TypedDict, total=False):
    """Label information in tool outputs."""

    id: str
    """Label's unique identifier."""

    name: str
    """Label name."""

    color: str
    """Label color (hex code)."""


class FuzzyMatchInfo(TypedDict, total=False):
    """Information about a fuzzy match result."""

    matched_id: str
    """ID of the matched entity."""

    matched_name: str
    """Name of the matched entity."""

    confidence: float
    """Match confidence score (0.0 to 1.0)."""


class FuzzyMatchSuggestion(TypedDict, total=False):
    """Suggestion for fuzzy match when auto-accept is disabled."""

    id: str
    """Entity ID."""

    name: str
    """Entity name."""

    confidence: float
    """Match confidence score."""
