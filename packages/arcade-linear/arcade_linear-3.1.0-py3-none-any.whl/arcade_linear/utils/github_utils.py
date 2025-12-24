"""Utility functions for GitHub integration tools."""

import re


def parse_github_url(url: str) -> dict[str, str | None]:
    """Parse a GitHub URL to extract owner, repo, and artifact info."""
    patterns = [
        (r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", "pr"),
        (r"github\.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)", "commit"),
        (r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", "issue"),
    ]

    for pattern, artifact_type in patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "owner": match.group(1),
                "repo": match.group(2),
                "number": match.group(3),
                "type": artifact_type,
            }

    return {"owner": None, "repo": None, "number": None, "type": None}


def generate_github_title(url_info: dict[str, str | None], url: str) -> str:
    """Generate a descriptive title for the GitHub artifact."""
    if not url_info.get("type"):
        return url

    owner = url_info.get("owner") or ""
    repo = url_info.get("repo") or ""
    number = url_info.get("number") or ""
    artifact_type = url_info.get("type") or ""

    type_labels = {"pr": "PR", "commit": "Commit", "issue": "Issue"}
    label = type_labels.get(artifact_type, artifact_type.upper() if artifact_type else "")

    if artifact_type == "commit":
        short_sha = number[:7] if number else ""
        return f"GitHub {label}: {owner}/{repo}@{short_sha}"

    return f"GitHub {label}: {owner}/{repo}#{number}"
