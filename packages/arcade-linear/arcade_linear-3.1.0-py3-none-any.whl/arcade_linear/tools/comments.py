"""Comment tools for Linear issues."""

from collections.abc import Mapping
from typing import Annotated, Any, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear

from arcade_linear.client import LinearClient
from arcade_linear.models.mappers import map_pagination
from arcade_linear.models.tool_outputs.comments import ListCommentsOutput, UpdateCommentOutput
from arcade_linear.models.tool_outputs.issues import AddCommentOutput
from arcade_linear.utils.comment_utils import map_comment
from arcade_linear.utils.issue_utils import resolve_issue
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_comments
# API Calls: 2 (get issue, get comments)
# APIs Used: issue query (GraphQL)
# Response Complexity: MEDIUM - list of comments with pagination
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Comments"
#   readOnlyHint: true      - Only reads comment data, no modifications
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["read"]))
async def list_comments(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier."],
    limit: Annotated[
        int,
        "Maximum number of comments to return. Min 1, max 50. Default is 20.",
    ] = 20,
    end_cursor: Annotated[
        str | None,
        "Cursor for pagination. Use 'end_cursor' from previous response. Default is None.",
    ] = None,
) -> Annotated[ListCommentsOutput, "Comments on the issue with pagination"]:
    """List comments on an issue.

    Returns comments with user info, timestamps, and reply threading info.
    """
    limit = max(1, min(limit, 50))

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        comments_response = await client.get_issue_comments(
            issue_id=issue_id,
            first=limit,
            after=end_cursor,
        )

    comments_conn = comments_response.get("comments", {}) or {}
    comments_nodes = comments_conn.get("nodes", []) if comments_conn else []
    page_info = cast(
        Mapping[str, Any] | None, comments_conn.get("pageInfo") if comments_conn else None
    )

    comments = [map_comment(c) for c in comments_nodes]

    result: ListCommentsOutput = {
        "issue_id": issue_id,
        "issue_identifier": comments_response.get("identifier", ""),
        "issue_title": comments_response.get("title", ""),
        "comments": comments,
        "items_returned": len(comments),
        "pagination": map_pagination(page_info),
    }

    return cast(ListCommentsOutput, remove_none_values_recursive(result))


# =============================================================================
# add_comment
# API Calls: 2 (get issue, create comment)
# APIs Used: issue query, commentCreate mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Add Comment"
#   readOnlyHint: false     - Creates new comment on issue
#   destructiveHint: false  - Additive operation, creates new comment
#   idempotentHint: false   - Each call creates a new comment
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["comments:create"]))
async def add_comment(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier to comment on."],
    body: Annotated[str, "Comment body in Markdown format."],
) -> Annotated[AddCommentOutput, "Created comment details"]:
    """Add a comment to an issue."""
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        comment_data = await client.create_comment(issue_id, body)

    result: AddCommentOutput = {
        "id": comment_data.get("id", ""),
        "issue_id": issue_id,
        "issue_identifier": issue_data.get("identifier", ""),
        "body": comment_data.get("body", ""),
        "created_at": str(comment_data.get("createdAt", "")),
    }
    return cast(AddCommentOutput, remove_none_values_recursive(result))


# =============================================================================
# update_comment
# API Calls: 1 (update comment)
# APIs Used: commentUpdate mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Update Comment"
#   readOnlyHint: false     - Modifies existing comment
#   destructiveHint: false  - Updates content, doesn't delete
#   idempotentHint: true    - Same update with same args = same result
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def update_comment(
    context: Context,
    comment_id: Annotated[str, "Comment ID to update."],
    body: Annotated[str, "New comment body in Markdown format."],
) -> Annotated[UpdateCommentOutput, "Updated comment details"]:
    """Update an existing comment."""
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        comment_data = await client.update_comment(comment_id, body)

    result: UpdateCommentOutput = {
        "id": comment_data.get("id", ""),
        "body": comment_data.get("body", ""),
        "updated_at": str(comment_data.get("updatedAt", "")),
    }
    return cast(UpdateCommentOutput, remove_none_values_recursive(result))


# =============================================================================
# reply_to_comment
# API Calls: 2 (get issue, create reply)
# APIs Used: issue query, commentCreate mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Reply to Comment"
#   readOnlyHint: false     - Creates reply to existing comment
#   destructiveHint: false  - Additive operation, creates new reply
#   idempotentHint: false   - Each call creates a new reply
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["comments:create"]))
async def reply_to_comment(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier."],
    parent_comment_id: Annotated[str, "ID of the comment to reply to."],
    body: Annotated[str, "Reply body in Markdown format."],
) -> Annotated[AddCommentOutput, "Created reply details"]:
    """Reply to an existing comment on an issue.

    Creates a threaded reply to the specified parent comment.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        comment_data = await client.create_comment_reply(issue_id, parent_comment_id, body)

    result: AddCommentOutput = {
        "id": comment_data.get("id", ""),
        "issue_id": issue_id,
        "issue_identifier": issue_data.get("identifier", ""),
        "body": comment_data.get("body", ""),
        "created_at": str(comment_data.get("createdAt", "")),
    }
    return cast(AddCommentOutput, remove_none_values_recursive(result))
