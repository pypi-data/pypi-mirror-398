"""TypedDict definitions for Linear issue tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import (
    FuzzyMatchInfo,
    LabelData,
    PaginationInfo,
    StateData,
    TeamSummary,
    UserData,
)


class ProjectSummary(TypedDict, total=False):
    """Project summary in issue output."""

    id: str
    """Project's unique identifier."""

    name: str
    """Project name."""

    state: str
    """Project state."""

    progress: float
    """Project progress (0.0 to 1.0)."""

    url: str
    """Project URL in Linear."""


class CycleSummary(TypedDict, total=False):
    """Cycle summary in issue output."""

    id: str
    """Cycle's unique identifier."""

    number: int
    """Cycle number."""

    name: str | None
    """Cycle name if set."""

    progress: float
    """Cycle progress (0.0 to 1.0)."""


class CommentOutput(TypedDict, total=False):
    """Comment data in tool outputs."""

    id: str
    """Comment unique identifier."""

    body: str
    """Comment content (Markdown)."""

    created_at: str
    """ISO 8601 timestamp in UTC when comment was created."""

    user: UserData
    """User who created the comment."""


class AttachmentOutput(TypedDict, total=False):
    """Attachment data in tool outputs."""

    id: str
    """Attachment unique identifier."""

    title: str
    """Attachment title."""

    url: str
    """Attachment URL for user reference."""

    created_at: str
    """ISO 8601 timestamp in UTC when attachment was created."""


class IssueRelationData(TypedDict, total=False):
    """Issue relation data in tool outputs."""

    id: str
    """Relation's unique identifier."""

    type: str
    """Relation type (blocks, blocked_by, duplicate, related)."""

    related_issue_id: str
    """Related issue's unique identifier."""

    related_issue_identifier: str
    """Related issue identifier (e.g., FE-456)."""

    related_issue_title: str
    """Related issue title."""

    related_issue_url: str
    """Related issue URL in Linear."""


class ChildIssueData(TypedDict, total=False):
    """Child issue (sub-issue) data in tool outputs."""

    id: str
    """Child issue's unique identifier."""

    identifier: str
    """Child issue identifier (e.g., FE-123-1)."""

    title: str
    """Child issue title."""

    state: StateData
    """Child issue current state."""

    url: str
    """Child issue URL in Linear."""


class ParentIssueSummary(TypedDict, total=False):
    """Parent issue summary in issue output."""

    id: str
    """Parent issue's unique identifier."""

    identifier: str
    """Parent issue identifier (e.g., FE-100)."""

    title: str
    """Parent issue title."""

    url: str
    """Parent issue URL in Linear."""


class IssueOutput(TypedDict, total=False):
    """Issue data for tool outputs (summary view)."""

    id: str
    """Issue's unique identifier."""

    identifier: str
    """Human-readable issue identifier (e.g., FE-123)."""

    title: str
    """Issue title."""

    description: str | None
    """Issue description (Markdown)."""

    url: str
    """URL to the issue in Linear for user reference."""

    priority: str | None
    """Priority level (None, Urgent, High, Medium, Low)."""

    state: StateData
    """Current workflow state."""

    team: TeamSummary
    """Team the issue belongs to."""

    assignee: UserData | None
    """User assigned to the issue."""

    labels: list[LabelData]
    """Labels attached to the issue."""

    project: ProjectSummary | None
    """Project the issue belongs to."""

    due_date: str | None
    """Due date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when issue was created."""

    updated_at: str
    """ISO 8601 timestamp in UTC when issue was last updated."""


class IssueDetailsOutput(TypedDict, total=False):
    """Extended issue data including comments and relations (detail view)."""

    id: str
    """Issue's unique identifier."""

    identifier: str
    """Human-readable issue identifier (e.g., FE-123)."""

    title: str
    """Issue title."""

    description: str | None
    """Issue description (Markdown)."""

    url: str
    """Issue URL in Linear."""

    priority: str | None
    """Priority level (None, Urgent, High, Medium, Low)."""

    estimate: float | None
    """Effort estimate in points."""

    state: StateData
    """Current workflow state."""

    team: TeamSummary
    """Team the issue belongs to."""

    assignee: UserData | None
    """User assigned to the issue."""

    creator: UserData | None
    """User who created the issue."""

    labels: list[LabelData]
    """Labels attached to the issue."""

    project: ProjectSummary | None
    """Project the issue belongs to."""

    cycle: CycleSummary | None
    """Cycle the issue is part of."""

    parent: ParentIssueSummary | None
    """Parent issue if this is a sub-issue."""

    due_date: str | None
    """Due date in YYYY-MM-DD format."""

    created_at: str
    """ISO 8601 timestamp in UTC when issue was created."""

    updated_at: str
    """ISO 8601 timestamp in UTC when issue was last updated."""

    completed_at: str | None
    """ISO 8601 timestamp in UTC when issue was completed."""

    branch_name: str | None
    """Suggested Git branch name for development."""

    comments: list[CommentOutput]
    """Issue comments."""

    attachments: list[AttachmentOutput]
    """Issue attachments."""

    relations: list[IssueRelationData]
    """Issue relations (blocks, blocked_by, etc.)."""

    children: list[ChildIssueData]
    """Sub-issues."""


class IssueSearchOutput(TypedDict, total=False):
    """Output for the list_issues tool."""

    issues: list[IssueOutput]
    """List of matching issues."""

    items_returned: int
    """Number of issues returned in this response."""

    pagination: PaginationInfo
    """Pagination information."""

    filters: dict | None
    """Filters applied to the search."""

    fuzzy_matches: dict[str, FuzzyMatchInfo] | None
    """Details of fuzzy matches applied for entity resolution."""


class IssueTransitionOutput(TypedDict, total=False):
    """Output for the transition_issue_state tool."""

    issue_id: str
    """Issue's unique identifier."""

    issue_identifier: str
    """Human-readable issue identifier (e.g., FE-123)."""

    previous_state: str
    """Name of the previous workflow state."""

    new_state: str
    """Name of the new workflow state."""

    transitioned: bool
    """Whether the transition was successful."""


class SubscriptionOutput(TypedDict, total=False):
    """Output for the manage_issue_subscription tool."""

    issue_id: str
    """Issue that subscription was modified for."""

    issue_identifier: str
    """Issue identifier (e.g., FE-123)."""

    action: str
    """Action performed (subscribe or unsubscribe)."""

    success: bool
    """Whether the action succeeded."""


class AddCommentOutput(TypedDict, total=False):
    """Output for the add_comment tool."""

    id: str
    """Comment unique identifier."""

    issue_id: str
    """Issue the comment was added to."""

    issue_identifier: str
    """Issue identifier (e.g., FE-123)."""

    body: str
    """Comment body content."""

    created_at: str
    """ISO 8601 timestamp when the comment was created."""


class IssueRelationOutput(TypedDict, total=False):
    """Output for the create_issue_relation tool."""

    id: str
    """Relation unique identifier."""

    type: str
    """Relation type (blocks, blocked_by, duplicate, related)."""

    issue_id: str
    """Source issue ID."""

    issue_identifier: str
    """Source issue identifier (e.g., FE-123)."""

    related_issue_id: str
    """Related issue ID."""

    related_issue_identifier: str
    """Related issue identifier (e.g., FE-456)."""


class ArchiveOutput(TypedDict, total=False):
    """Output for archive operations."""

    id: str
    """Archived entity ID."""

    identifier: str | None
    """Entity identifier if applicable (e.g., FE-123 for issues)."""

    name: str | None
    """Entity name if applicable."""

    entity_type: str
    """Type of entity archived (issue, project, initiative)."""

    success: bool
    """Whether the archive operation succeeded."""
