"""TypedDict definitions for GitHub integration tool outputs."""

from typing_extensions import TypedDict


class LinkGitHubToIssueOutput(TypedDict, total=False):
    """Output for the link_github_to_issue tool."""

    issue_id: str
    """Linear issue ID the artifact was linked to."""

    issue_identifier: str
    """Linear issue identifier (e.g., FE-123)."""

    attachment_id: str
    """Created attachment ID."""

    url: str
    """GitHub URL that was linked."""

    title: str
    """Title generated for the link."""
