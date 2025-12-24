"""GitHub integration tools for Linear issues."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_linear.client import LinearClient
from arcade_linear.models.tool_outputs.github import LinkGitHubToIssueOutput
from arcade_linear.utils.github_utils import generate_github_title, parse_github_url
from arcade_linear.utils.issue_utils import resolve_issue
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# link_github_to_issue
# API Calls: 2 (get issue, link URL)
# APIs Used: issue query, attachmentLinkURL mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Link GitHub to Issue"
#   readOnlyHint: false     - Attaches GitHub link to issue
#   destructiveHint: false  - Additive operation, creates attachment
#   idempotentHint: true    - Linking same URL again = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def link_github_to_issue(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier to link to."],
    github_url: Annotated[
        str,
        "GitHub URL to link (PR, commit, or issue).",
    ],
    title: Annotated[
        str | None,
        "Custom title for the link. If not provided, auto-generated from URL.",
    ] = None,
) -> Annotated[LinkGitHubToIssueOutput, "Link result with attachment details"]:
    """Link a GitHub PR, commit, or issue to a Linear issue.

    Automatically detects the artifact type from the URL and generates
    an appropriate title if not provided.
    """
    url_info = parse_github_url(github_url)

    if not url_info.get("type"):
        raise ToolExecutionError(
            message="Unrecognized GitHub URL format",
            developer_message=f"Could not detect PR, commit, or issue from URL: {github_url}",
        )

    link_title = title or generate_github_title(url_info, github_url)

    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        attachment = await client.link_url_to_issue(issue_id, github_url, link_title)

    result: LinkGitHubToIssueOutput = {
        "issue_id": issue_id,
        "issue_identifier": issue_data.get("identifier", ""),
        "attachment_id": attachment.get("id", ""),
        "url": github_url,
        "title": link_title,
    }

    return cast(LinkGitHubToIssueOutput, remove_none_values_recursive(result))
