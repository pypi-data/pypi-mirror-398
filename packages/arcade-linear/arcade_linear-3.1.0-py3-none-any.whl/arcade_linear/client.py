"""Linear GraphQL API client using gql library."""

import asyncio
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, cast

from arcade_mcp_server.exceptions import ToolExecutionError
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import DocumentNode

from arcade_linear.constants import (
    DEFAULT_PAGE_SIZE,
    LINEAR_API_URL,
    LINEAR_MAX_CONCURRENT_REQUESTS,
    LINEAR_MAX_TIMEOUT_SECONDS,
    Mutations,
    Queries,
)
from arcade_linear.models.api_responses import (
    AttachmentResponse,
    CommentResponse,
    CycleResponse,
    CyclesConnectionResponse,
    InitiativeConnectionResponse,
    InitiativeResponse,
    IssueRelationResponse,
    IssueResponse,
    IssueSearchConnectionResponse,
    LabelsConnectionResponse,
    NotificationsConnectionResponse,
    ProjectConnectionResponse,
    ProjectResponse,
    TeamResponse,
    TeamsConnectionResponse,
    ViewerResponse,
    WorkflowStatesConnectionResponse,
)
from arcade_linear.models.api_responses.issues import TeamSummaryResponse


@dataclass
class LinearClient:
    """Client for interacting with Linear's GraphQL API using gql library.

    Supports connection pooling for better performance when making multiple requests.
    Use as a context manager for proper connection cleanup:

        async with LinearClient(token) as client:
            result = await client.get_viewer()
    """

    auth_token: str
    api_url: str = LINEAR_API_URL
    max_concurrent_requests: int = LINEAR_MAX_CONCURRENT_REQUESTS
    timeout_seconds: int = LINEAR_MAX_TIMEOUT_SECONDS
    _semaphore: asyncio.Semaphore | None = field(default=None, repr=False)
    _gql_client: Client | None = field(default=None, repr=False)
    _gql_session: Any | None = field(default=None, repr=False)
    _transport: AIOHTTPTransport | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._semaphore = self._semaphore or asyncio.Semaphore(self.max_concurrent_requests)

    def _create_transport(self) -> AIOHTTPTransport:
        """Create aiohttp transport with auth headers."""
        return AIOHTTPTransport(
            url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout_seconds,
        )

    async def __aenter__(self) -> "LinearClient":
        """Enter async context - create gql client with connection pooling."""
        if self._gql_client is None:
            self._transport = self._create_transport()
            self._gql_client = Client(
                transport=self._transport,
                fetch_schema_from_transport=False,
            )
            self._gql_session = await self._gql_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context - cleanup gql client."""
        if self._gql_client:
            await self._gql_client.__aexit__(exc_type, exc_val, exc_tb)
            self._gql_client = None
            self._gql_session = None
            self._transport = None

    def _parse_query(self, query_str: str) -> DocumentNode:
        """Parse a GraphQL query string into a DocumentNode."""
        return gql(query_str.strip())

    async def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against Linear API."""
        parsed_query = self._parse_query(query)

        async with self._semaphore:  # type: ignore[union-attr]
            if self._gql_session is not None:
                result = await self._gql_session.execute(
                    parsed_query,
                    variable_values=variables,
                    operation_name=operation_name,
                )
                return {"data": result}

            transport = self._create_transport()
            async with Client(
                transport=transport,
                fetch_schema_from_transport=False,
            ) as session:
                result = await session.execute(
                    parsed_query,
                    variable_values=variables,
                    operation_name=operation_name,
                )
                return {"data": result}

    async def get_viewer(self) -> ViewerResponse:
        """Get authenticated user information."""
        result = await self.execute_query(Queries.viewer)
        return cast(ViewerResponse, result.get("data", {}).get("viewer", {}))

    async def get_viewer_teams(self, first: int = DEFAULT_PAGE_SIZE) -> list[TeamSummaryResponse]:
        """Get teams the authenticated user belongs to."""
        result = await self.execute_query(Queries.viewer_teams, {"first": first})
        teams_data = result.get("data", {}).get("viewer", {}).get("teams", {})
        return cast(list[TeamSummaryResponse], teams_data.get("nodes", []))

    async def get_notifications(
        self,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> NotificationsConnectionResponse:
        """Get user notifications with pagination."""
        variables: dict[str, Any] = {"first": first}
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.notifications, variables)
        return cast(
            NotificationsConnectionResponse, result.get("data", {}).get("notifications", {})
        )

    async def get_user_created_issues(
        self,
        user_id: str,
        created_after: str | None = None,
        first: int = DEFAULT_PAGE_SIZE,
    ) -> IssueSearchConnectionResponse:
        """Get issues created by a specific user."""
        issue_filter: dict[str, Any] = {"creator": {"id": {"eq": user_id}}}
        if created_after:
            issue_filter["createdAt"] = {"gte": created_after}

        result = await self.execute_query(
            Queries.user_issues, {"filter": issue_filter, "first": first}
        )
        return cast(IssueSearchConnectionResponse, result.get("data", {}).get("issues", {}))

    async def get_user_assigned_issues(
        self,
        user_id: str,
        first: int = DEFAULT_PAGE_SIZE,
    ) -> IssueSearchConnectionResponse:
        """Get issues assigned to a specific user."""
        issue_filter = {"assignee": {"id": {"eq": user_id}}}
        result = await self.execute_query(
            Queries.user_issues, {"filter": issue_filter, "first": first}
        )
        return cast(IssueSearchConnectionResponse, result.get("data", {}).get("issues", {}))

    async def search_issues(
        self,
        issue_filter: dict[str, Any] | None = None,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> IssueSearchConnectionResponse:
        """Search issues using Linear's filter syntax."""
        variables: dict[str, Any] = {
            "filter": issue_filter or {},
            "first": first,
        }
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.issue_search, variables)
        return cast(IssueSearchConnectionResponse, result.get("data", {}).get("issues", {}))

    async def get_issue_by_id(self, issue_id: str) -> IssueResponse:
        """Get a single issue by ID or identifier."""
        result = await self.execute_query(Queries.issue_detail, {"id": issue_id})
        return cast(IssueResponse, result.get("data", {}).get("issue", {}))

    async def get_team_by_id(self, team_id: str) -> TeamResponse:
        """Get a single team by ID."""
        result = await self.execute_query(Queries.team_detail, {"id": team_id})
        return cast(TeamResponse, result.get("data", {}).get("team", {}))

    async def get_teams(
        self,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
        include_archived: bool = False,
        name_filter: str | None = None,
    ) -> TeamsConnectionResponse:
        """Get teams with optional filtering."""
        team_filter: dict[str, Any] = {}
        if name_filter:
            team_filter["name"] = {"containsIgnoreCase": name_filter}

        variables: dict[str, Any] = {
            "first": first,
            "after": after,
            "filter": team_filter if team_filter else None,
        }

        result = await self.execute_query(Queries.teams, variables)
        teams_data = result.get("data", {}).get("teams", {})

        if not include_archived:
            nodes = teams_data.get("nodes", [])
            teams_data["nodes"] = [t for t in nodes if not t.get("archivedAt")]

        return cast(TeamsConnectionResponse, teams_data)

    async def get_projects(
        self,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
        filter_params: dict[str, Any] | None = None,
    ) -> ProjectConnectionResponse:
        """Get projects with optional filtering."""
        variables: dict[str, Any] = {"first": first}
        if after:
            variables["after"] = after
        if filter_params:
            variables["filter"] = filter_params

        result = await self.execute_query(Queries.projects, variables)
        return cast(ProjectConnectionResponse, result.get("data", {}).get("projects", {}))

    async def get_initiatives(
        self,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> InitiativeConnectionResponse:
        """Get initiatives with pagination."""
        variables: dict[str, Any] = {"first": first}
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.initiatives, variables)
        return cast(InitiativeConnectionResponse, result.get("data", {}).get("initiatives", {}))

    async def get_initiative_by_id(self, initiative_id: str) -> InitiativeResponse:
        """Get a single initiative by ID."""
        result = await self.execute_query(Queries.initiative_detail, {"id": initiative_id})
        return cast(InitiativeResponse, result.get("data", {}).get("initiative") or {})

    async def get_labels(self, first: int = 100) -> LabelsConnectionResponse:
        """Get issue labels."""
        result = await self.execute_query(Queries.labels, {"first": first})
        return cast(LabelsConnectionResponse, result.get("data", {}).get("issueLabels", {}))

    async def get_workflow_states(self, first: int = 100) -> WorkflowStatesConnectionResponse:
        """Get workflow states."""
        result = await self.execute_query(Queries.workflow_states, {"first": first})
        return cast(
            WorkflowStatesConnectionResponse, result.get("data", {}).get("workflowStates", {})
        )

    async def get_issue_validation_data(self) -> dict[str, Any]:
        """Get all data needed for issue creation/update validation in one call."""
        result = await self.execute_query(Queries.issue_validation_data, {})
        data = result.get("data", {})
        return cast(
            dict[str, Any],
            {
                "teams": data.get("teams", {}).get("nodes", []),
                "labels": data.get("issueLabels", {}).get("nodes", []),
                "projects": data.get("projects", {}).get("nodes", []),
            },
        )

    async def get_team_issues(self, team_id: str, first: int = 50) -> list[IssueResponse]:
        """Get recent issues from a team for parent issue resolution."""
        result = await self.execute_query(Queries.team_issues, {"teamId": team_id, "first": first})
        team_data = result.get("data", {}).get("team", {})
        return cast(list[IssueResponse], team_data.get("issues", {}).get("nodes", []))

    async def create_issue(self, input_data: dict[str, Any]) -> IssueResponse:
        """Create a new issue."""
        result = await self.execute_query(Mutations.issue_create, {"input": input_data})
        mutation_result = result.get("data", {}).get("issueCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create issue",
                developer_message=f"issueCreate returned success=false: {mutation_result}",
            )

        return cast(IssueResponse, mutation_result.get("issue", {}))

    async def update_issue(self, issue_id: str, input_data: dict[str, Any]) -> IssueResponse:
        """Update an existing issue."""
        result = await self.execute_query(
            Mutations.issue_update,
            {"id": issue_id, "input": input_data},
        )
        mutation_result = result.get("data", {}).get("issueUpdate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to update issue",
                developer_message=f"issueUpdate returned success=false: {mutation_result}",
            )

        return cast(IssueResponse, mutation_result.get("issue", {}))

    async def create_comment(self, issue_id: str, body: str) -> CommentResponse:
        """Create a comment on an issue."""
        result = await self.execute_query(
            Mutations.comment_create,
            {"input": {"issueId": issue_id, "body": body}},
        )
        mutation_result = result.get("data", {}).get("commentCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create comment",
                developer_message=f"commentCreate returned success=false: {mutation_result}",
            )

        return cast(CommentResponse, mutation_result.get("comment", {}))

    async def get_issue_comments(
        self,
        issue_id: str,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> IssueResponse:
        """Get comments for an issue with pagination."""
        variables: dict[str, Any] = {"issueId": issue_id, "first": first}
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.issue_comments, variables)
        issue_data = result.get("data", {}).get("issue", {})
        return cast(IssueResponse, issue_data)

    async def update_comment(self, comment_id: str, body: str) -> CommentResponse:
        """Update an existing comment."""
        result = await self.execute_query(
            Mutations.comment_update,
            {"id": comment_id, "input": {"body": body}},
        )
        mutation_result = result.get("data", {}).get("commentUpdate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to update comment",
                developer_message=f"commentUpdate returned success=false: {mutation_result}",
            )

        return cast(CommentResponse, mutation_result.get("comment", {}))

    async def create_comment_reply(
        self, issue_id: str, parent_id: str, body: str
    ) -> CommentResponse:
        """Create a reply to an existing comment."""
        result = await self.execute_query(
            Mutations.comment_create,
            {"input": {"issueId": issue_id, "body": body, "parentId": parent_id}},
        )
        mutation_result = result.get("data", {}).get("commentCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create comment reply",
                developer_message=f"commentCreate returned success=false: {mutation_result}",
            )

        return cast(CommentResponse, mutation_result.get("comment", {}))

    async def subscribe_to_issue(self, issue_id: str) -> bool:
        """Subscribe to an issue."""
        result = await self.execute_query(Mutations.issue_subscribe, {"id": issue_id})
        return bool(result.get("data", {}).get("issueSubscribe", {}).get("success"))

    async def unsubscribe_from_issue(self, issue_id: str) -> bool:
        """Unsubscribe from an issue."""
        result = await self.execute_query(Mutations.issue_unsubscribe, {"id": issue_id})
        return bool(result.get("data", {}).get("issueUnsubscribe", {}).get("success"))

    async def link_url_to_issue(
        self,
        issue_id: str,
        url: str,
        title: str | None = None,
    ) -> AttachmentResponse:
        """Link a URL to an issue as an attachment."""
        variables: dict[str, Any] = {"issueId": issue_id, "url": url}
        if title:
            variables["title"] = title

        result = await self.execute_query(Mutations.attachment_link_url, variables)
        mutation_result = result.get("data", {}).get("attachmentLinkURL", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to link URL to issue",
                developer_message=f"attachmentLinkURL returned success=false: {mutation_result}",
            )

        return cast(AttachmentResponse, mutation_result.get("attachment", {}))

    async def create_project_update(
        self,
        project_id: str,
        body: str,
        health: str | None = None,
    ) -> dict[str, Any]:
        """Create a project status update."""
        input_data: dict[str, Any] = {"projectId": project_id, "body": body}
        if health:
            input_data["health"] = health

        result = await self.execute_query(Mutations.project_update_create, {"input": input_data})
        mutation_result = result.get("data", {}).get("projectUpdateCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create project update",
                developer_message=f"projectUpdateCreate returned success=false: {mutation_result}",
            )

        return cast(dict[str, Any], mutation_result.get("projectUpdate", {}))

    async def get_project_by_id(self, project_id: str) -> ProjectResponse:
        """Get a single project by ID or slugId."""
        result = await self.execute_query(Queries.project_detail, {"id": project_id})
        return cast(ProjectResponse, result.get("data", {}).get("project") or {})

    async def search_projects(
        self,
        project_filter: dict[str, Any] | None = None,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> ProjectConnectionResponse:
        """Search projects using Linear's filter syntax."""
        variables: dict[str, Any] = {
            "filter": project_filter or {},
            "first": first,
        }
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.project_search, variables)
        return cast(ProjectConnectionResponse, result.get("data", {}).get("projects", {}))

    async def get_cycle_by_id(self, cycle_id: str) -> CycleResponse:
        """Get a single cycle by ID."""
        result = await self.execute_query(Queries.cycle_detail, {"id": cycle_id})
        return cast(CycleResponse, result.get("data", {}).get("cycle") or {})

    async def get_cycles(
        self,
        team_id: str | None = None,
        first: int = DEFAULT_PAGE_SIZE,
        after: str | None = None,
    ) -> CyclesConnectionResponse:
        """Get cycles, optionally filtered by team."""
        variables: dict[str, Any] = {"first": first}
        if team_id:
            variables["filter"] = {"team": {"id": {"eq": team_id}}}
        if after:
            variables["after"] = after

        result = await self.execute_query(Queries.cycles, variables)
        return cast(CyclesConnectionResponse, result.get("data", {}).get("cycles", {}))

    async def create_project(self, input_data: dict[str, Any]) -> ProjectResponse:
        """Create a new project."""
        result = await self.execute_query(Mutations.project_create, {"input": input_data})
        mutation_result = result.get("data", {}).get("projectCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create project",
                developer_message=f"projectCreate returned success=false: {mutation_result}",
            )

        return cast(ProjectResponse, mutation_result.get("project", {}))

    async def update_project(self, project_id: str, input_data: dict[str, Any]) -> ProjectResponse:
        """Update an existing project."""
        result = await self.execute_query(
            Mutations.project_update,
            {"id": project_id, "input": input_data},
        )
        mutation_result = result.get("data", {}).get("projectUpdate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to update project",
                developer_message=f"projectUpdate returned success=false: {mutation_result}",
            )

        return cast(ProjectResponse, mutation_result.get("project", {}))

    async def create_initiative(self, input_data: dict[str, Any]) -> InitiativeResponse:
        """Create a new initiative."""
        result = await self.execute_query(Mutations.initiative_create, {"input": input_data})
        mutation_result = result.get("data", {}).get("initiativeCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create initiative",
                developer_message=f"initiativeCreate returned success=false: {mutation_result}",
            )

        return cast(InitiativeResponse, mutation_result.get("initiative", {}))

    async def update_initiative(
        self, initiative_id: str, input_data: dict[str, Any]
    ) -> InitiativeResponse:
        """Update an existing initiative."""
        result = await self.execute_query(
            Mutations.initiative_update,
            {"id": initiative_id, "input": input_data},
        )
        mutation_result = result.get("data", {}).get("initiativeUpdate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to update initiative",
                developer_message=f"initiativeUpdate returned success=false: {mutation_result}",
            )

        return cast(InitiativeResponse, mutation_result.get("initiative", {}))

    async def add_project_to_initiative(
        self, initiative_id: str, project_id: str
    ) -> dict[str, Any]:
        """Link a project to an initiative."""
        result = await self.execute_query(
            Mutations.initiative_to_project_create,
            {"input": {"initiativeId": initiative_id, "projectId": project_id}},
        )
        mutation_result = result.get("data", {}).get("initiativeToProjectCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to link project to initiative",
                developer_message=(
                    f"initiativeToProjectCreate returned success=false: {mutation_result}"
                ),
            )

        return cast(dict[str, Any], mutation_result.get("initiativeToProject", {}))

    async def archive_issue(self, issue_id: str) -> bool:
        """Archive an issue."""
        result = await self.execute_query(Mutations.issue_archive, {"id": issue_id})
        return bool(result.get("data", {}).get("issueArchive", {}).get("success"))

    async def archive_project(self, project_id: str) -> bool:
        """Archive a project."""
        result = await self.execute_query(Mutations.project_archive, {"id": project_id})
        return bool(result.get("data", {}).get("projectArchive", {}).get("success"))

    async def archive_initiative(self, initiative_id: str) -> bool:
        """Archive an initiative."""
        result = await self.execute_query(Mutations.initiative_archive, {"id": initiative_id})
        return bool(result.get("data", {}).get("initiativeArchive", {}).get("success"))

    async def create_issue_relation(
        self, issue_id: str, related_issue_id: str, relation_type: str
    ) -> IssueRelationResponse:
        """Create a relation between two issues."""
        result = await self.execute_query(
            Mutations.issue_relation_create,
            {
                "input": {
                    "issueId": issue_id,
                    "relatedIssueId": related_issue_id,
                    "type": relation_type,
                }
            },
        )
        mutation_result = result.get("data", {}).get("issueRelationCreate", {})

        if not mutation_result.get("success"):
            raise ToolExecutionError(
                "Failed to create issue relation",
                developer_message=(
                    f"issueRelationCreate returned success=false: {mutation_result}"
                ),
            )

        return cast(IssueRelationResponse, mutation_result.get("issueRelation", {}))
