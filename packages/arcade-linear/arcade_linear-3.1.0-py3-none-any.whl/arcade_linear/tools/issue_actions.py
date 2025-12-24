"""Tools for additional issue actions: relations, subscriptions, archive."""

import asyncio
from typing import Annotated, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Linear

from arcade_linear.client import LinearClient
from arcade_linear.models.enums import IssueRelationType
from arcade_linear.models.tool_outputs.issues import (
    ArchiveOutput,
    IssueRelationOutput,
    SubscriptionOutput,
)
from arcade_linear.utils.issue_utils import resolve_issue
from arcade_linear.utils.response_utils import remove_none_values_recursive


# =============================================================================
# create_issue_relation
# API Calls: 3 (get source + related issue in parallel, create relation)
# APIs Used: issue query, issueRelationCreate mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Create Issue Relation"
#   readOnlyHint: false     - Creates relation between issues
#   destructiveHint: false  - Additive operation, creates link
#   idempotentHint: true    - Creating same relation again = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def create_issue_relation(
    context: Context,
    issue: Annotated[str, "Source issue ID or identifier."],
    related_issue: Annotated[str, "Related issue ID or identifier."],
    relation_type: Annotated[IssueRelationType, "Type of relation to create."],
) -> Annotated[IssueRelationOutput, "Created relation details"]:
    """Create a relation between two issues.

    Relation types define the relationship from the source issue's perspective:
    - blocks: Source issue blocks the related issue
    - blockedBy: Source issue is blocked by the related issue
    - duplicate: Source issue is a duplicate of the related issue
    - related: Issues are related (bidirectional)
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        source_issue, target_issue = await asyncio.gather(
            resolve_issue(client, issue),
            resolve_issue(client, related_issue),
        )

        source_id = str(source_issue.get("id", ""))
        target_id = str(target_issue.get("id", ""))

        relation_data = await client.create_issue_relation(
            source_id, target_id, relation_type.value
        )

    result: IssueRelationOutput = {
        "id": relation_data.get("id", ""),
        "type": relation_type.value,
        "issue_id": source_id,
        "issue_identifier": source_issue.get("identifier", ""),
        "related_issue_id": target_id,
        "related_issue_identifier": target_issue.get("identifier", ""),
    }
    return cast(IssueRelationOutput, remove_none_values_recursive(result))


# =============================================================================
# manage_issue_subscription
# API Calls: 2 (get issue, subscribe/unsubscribe)
# APIs Used: issue query, issueSubscribe/issueUnsubscribe mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Manage Issue Subscription"
#   readOnlyHint: false     - Modifies user's subscription state
#   destructiveHint: false  - Toggles subscription, reversible
#   idempotentHint: true    - Subscribing when subscribed = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["issues:create"]))
async def manage_issue_subscription(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier."],
    subscribe: Annotated[bool, "True to subscribe, False to unsubscribe."],
) -> Annotated[SubscriptionOutput, "Subscription action result"]:
    """Subscribe to or unsubscribe from an issue's notifications."""
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        if subscribe:
            success = await client.subscribe_to_issue(issue_id)
            action = "subscribe"
        else:
            success = await client.unsubscribe_from_issue(issue_id)
            action = "unsubscribe"

    result: SubscriptionOutput = {
        "issue_id": issue_id,
        "issue_identifier": issue_data.get("identifier", ""),
        "action": action,
        "success": success,
    }
    return cast(SubscriptionOutput, remove_none_values_recursive(result))


# =============================================================================
# archive_issue
# API Calls: 2 (get issue, archive)
# APIs Used: issue query, issueArchive mutation (GraphQL)
# Response Complexity: LOW
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Archive Issue"
#   readOnlyHint: false     - Archives (soft-deletes) issue
#   destructiveHint: true   - Hides issue from default views
#   idempotentHint: true    - Archiving already-archived = no change
#   openWorldHint: true     - Interacts with Linear's external API
# =============================================================================
@tool(requires_auth=Linear(scopes=["write"]))
async def archive_issue(
    context: Context,
    issue: Annotated[str, "Issue ID or identifier to archive."],
) -> Annotated[ArchiveOutput, "Archive operation result"]:
    """Archive an issue.

    Archived issues are hidden from default views but can be restored.
    """
    async with LinearClient(context.get_auth_token_or_empty()) as client:
        issue_data = await resolve_issue(client, issue)
        issue_id = str(issue_data.get("id", ""))

        success = await client.archive_issue(issue_id)

    result: ArchiveOutput = {
        "id": issue_id,
        "identifier": issue_data.get("identifier"),
        "name": issue_data.get("title"),
        "entity_type": "issue",
        "success": success,
    }
    return cast(ArchiveOutput, remove_none_values_recursive(result))
