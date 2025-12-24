"""TypedDict definitions for Linear comment tool outputs."""

from typing_extensions import TypedDict

from arcade_linear.models.tool_outputs.common import PaginationInfo


class CommentData(TypedDict, total=False):
    """Comment data in tool outputs."""

    id: str
    """Comment unique identifier."""

    body: str
    """Comment content in Markdown."""

    created_at: str
    """ISO 8601 timestamp in UTC when comment was created."""

    user_id: str
    """ID of the user who created the comment."""

    user_name: str
    """Name of the user who created the comment."""

    parent_id: str | None
    """ID of the parent comment if this is a reply."""

    reply_count: int
    """Number of replies to this comment."""


class ListCommentsOutput(TypedDict, total=False):
    """Output for the list_comments tool."""

    issue_id: str
    """Issue ID the comments belong to."""

    issue_identifier: str
    """Issue identifier (e.g., FE-123)."""

    issue_title: str
    """Issue title."""

    comments: list[CommentData]
    """List of comments on the issue."""

    items_returned: int
    """Number of comments returned in this response."""

    pagination: PaginationInfo
    """Pagination information for fetching more comments."""


class UpdateCommentOutput(TypedDict, total=False):
    """Output for the update_comment tool."""

    id: str
    """Comment unique identifier."""

    body: str
    """Updated comment content."""

    updated_at: str
    """ISO 8601 timestamp when comment was updated."""
