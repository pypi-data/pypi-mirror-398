"""Constants for Linear toolkit configuration."""

import os

# Linear API configuration
LINEAR_API_URL = "https://api.linear.app/graphql"

# Concurrency and timeout settings
try:
    LINEAR_MAX_CONCURRENT_REQUESTS = int(os.getenv("LINEAR_MAX_CONCURRENT_REQUESTS", 3))
except ValueError:
    LINEAR_MAX_CONCURRENT_REQUESTS = 3

try:
    LINEAR_MAX_TIMEOUT_SECONDS = int(os.getenv("LINEAR_MAX_TIMEOUT_SECONDS", 30))
except ValueError:
    LINEAR_MAX_TIMEOUT_SECONDS = 30

# Fuzzy matching thresholds
FUZZY_MATCH_THRESHOLD = 0.70
FUZZY_AUTO_ACCEPT_CONFIDENCE = 0.90
DISABLE_AUTO_ACCEPT_THRESHOLD = 1.01

# Fuzzy matching limits
MAX_FUZZY_SUGGESTIONS = 20
MAX_DISPLAY_SUGGESTIONS = 5

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Validation query limits (for issue create/update entity resolution)
VALIDATION_TEAM_LIMIT = 20
VALIDATION_MEMBER_LIMIT = 50
VALIDATION_STATE_LIMIT = 25
VALIDATION_CYCLE_LIMIT = 10
VALIDATION_LABEL_LIMIT = 50
VALIDATION_PROJECT_LIMIT = 50

# Description truncation defaults
DEFAULT_DESCRIPTION_MAX_LENGTH = 500
DESCRIPTION_CHUNK_SIZE = 2000


class Queries:
    """GraphQL queries for Linear API."""

    viewer = """
        query Viewer {
            viewer {
                id
                name
                email
                displayName
                avatarUrl
                active
                admin
                organization {
                    id
                    name
                    urlKey
                }
            }
        }
    """

    viewer_teams = """
        query ViewerTeams($first: Int!) {
            viewer {
                teams(first: $first) {
                    nodes {
                        id
                        key
                        name
                    }
                }
            }
        }
    """

    notifications = """
        query Notifications($first: Int!, $after: String) {
            notifications(first: $first, after: $after) {
                nodes {
                    id
                    type
                    createdAt
                    readAt
                    archivedAt
                    actor {
                        id
                        name
                        email
                        displayName
                    }
                    ... on IssueNotification {
                        issue {
                            id
                            identifier
                            title
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    user_issues = """
        query GetUserIssues($filter: IssueFilter!, $first: Int!) {
            issues(filter: $filter, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    url
                    createdAt
                    updatedAt
                    team {
                        id
                        name
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    issue_search = """
        query SearchIssues($filter: IssueFilter!, $first: Int!, $after: String) {
            issues(filter: $filter, first: $first, after: $after) {
                nodes {
                    id
                    identifier
                    title
                    description
                    documentContent {
                        content
                    }
                    priority
                    priorityLabel
                    estimate
                    createdAt
                    updatedAt
                    completedAt
                    dueDate
                    url
                    branchName
                    creator {
                        id
                        name
                        email
                        displayName
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    state {
                        id
                        name
                        type
                        color
                    }
                    team {
                        id
                        key
                        name
                    }
                    project {
                        id
                        name
                        state
                        progress
                        url
                    }
                    cycle {
                        id
                        number
                        name
                        progress
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    issue_detail = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                documentContent {
                    content
                }
                priority
                priorityLabel
                estimate
                createdAt
                updatedAt
                completedAt
                dueDate
                url
                branchName
                creator {
                    id
                    name
                    email
                    displayName
                }
                assignee {
                    id
                    name
                    email
                    displayName
                }
                state {
                    id
                    name
                    type
                    color
                }
                team {
                    id
                    key
                    name
                }
                project {
                    id
                    name
                    state
                    progress
                    url
                }
                cycle {
                    id
                    number
                    name
                    progress
                }
                parent {
                    id
                    identifier
                    title
                    url
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                attachments {
                    nodes {
                        id
                        title
                        subtitle
                        url
                        createdAt
                        sourceType
                    }
                }
                comments {
                    nodes {
                        id
                        body
                        createdAt
                        updatedAt
                        user {
                            id
                            name
                            email
                            displayName
                        }
                    }
                }
                children {
                    nodes {
                        id
                        identifier
                        title
                        url
                        state {
                            id
                            name
                            type
                        }
                    }
                }
                relations {
                    nodes {
                        id
                        type
                        relatedIssue {
                            id
                            identifier
                            title
                            url
                        }
                    }
                }
            }
        }
    """

    team_detail = """
        query GetTeam($id: String!) {
            team(id: $id) {
                id
                key
                name
                description
                private
                archivedAt
                createdAt
                updatedAt
                cyclesEnabled
                organization {
                    id
                    name
                }
                members {
                    nodes {
                        id
                        name
                        email
                        displayName
                    }
                }
            }
        }
    """

    teams = """
        query GetTeams($first: Int!, $after: String, $filter: TeamFilter) {
            teams(first: $first, after: $after, filter: $filter) {
                nodes {
                    id
                    key
                    name
                    description
                    private
                    archivedAt
                    createdAt
                    updatedAt
                    cyclesEnabled
                    organization {
                        id
                        name
                    }
                    members {
                        nodes {
                            id
                            name
                            email
                            displayName
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    projects = """
        query Projects($first: Int!, $after: String, $filter: ProjectFilter) {
            projects(first: $first, after: $after, filter: $filter) {
                nodes {
                    id
                    name
                    description
                    documentContent {
                        content
                    }
                    state
                    progress
                    health
                    startDate
                    targetDate
                    createdAt
                    updatedAt
                    url
                    teams {
                        nodes {
                            id
                            key
                            name
                        }
                    }
                    issues {
                        totalCount
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    initiatives = """
        query Initiatives($first: Int!, $after: String) {
            initiatives(first: $first, after: $after) {
                nodes {
                    id
                    name
                    description
                    documentContent {
                        content
                    }
                    status
                    targetDate
                    createdAt
                    updatedAt
                    url
                    projects {
                        nodes {
                            id
                            name
                            state
                            progress
                            url
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    initiative_detail = """
        query GetInitiative($id: String!) {
            initiative(id: $id) {
                id
                name
                description
                documentContent {
                    content
                }
                status
                targetDate
                createdAt
                updatedAt
                url
                projects {
                    nodes {
                        id
                        name
                        state
                        progress
                        url
                    }
                }
            }
        }
    """

    labels = """
        query Labels($first: Int!) {
            issueLabels(first: $first) {
                nodes {
                    id
                    name
                    color
                    description
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    workflow_states = """
        query WorkflowStates($first: Int!) {
            workflowStates(first: $first) {
                nodes {
                    id
                    name
                    type
                    color
                    position
                    team {
                        id
                        name
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    issue_validation_data = """
        query IssueValidationData {
            teams(first: 20) {
                nodes {
                    id
                    key
                    name
                    members(first: 50) {
                        nodes {
                            id
                            name
                            email
                            displayName
                        }
                    }
                    states(first: 25) {
                        nodes {
                            id
                            name
                            type
                        }
                    }
                    cycles(first: 10, orderBy: updatedAt) {
                        nodes {
                            id
                            number
                            name
                            startsAt
                            endsAt
                        }
                    }
                }
            }
            issueLabels(first: 50) {
                nodes {
                    id
                    name
                }
            }
            projects(first: 50, orderBy: updatedAt) {
                nodes {
                    id
                    name
                    slugId
                    state
                }
            }
        }
    """

    team_issues = """
        query TeamIssues($teamId: String!, $first: Int!) {
            team(id: $teamId) {
                issues(first: $first, orderBy: updatedAt) {
                    nodes {
                        id
                        identifier
                        title
                    }
                }
            }
        }
    """

    project_detail = """
        query GetProject($id: String!) {
            project(id: $id) {
                id
                name
                slugId
                description
                content
                documentContent {
                    content
                }
                url
                state
                progress
                startDate
                targetDate
                createdAt
                updatedAt
                lead {
                    id
                    name
                    displayName
                    email
                }
                members {
                    nodes {
                        id
                        name
                        displayName
                        email
                    }
                }
                teams {
                    nodes {
                        id
                        key
                        name
                    }
                }
                projectMilestones(first: 25) {
                    nodes {
                        id
                        name
                        description
                        targetDate
                        sortOrder
                    }
                }
                issues(first: 10, orderBy: updatedAt) {
                    nodes {
                        id
                        identifier
                        title
                        url
                        state {
                            id
                            name
                            type
                        }
                        priority
                        updatedAt
                    }
                }
                initiatives {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
    """

    project_search = """
        query SearchProjects($filter: ProjectFilter, $first: Int!, $after: String) {
            projects(filter: $filter, first: $first, after: $after) {
                nodes {
                    id
                    name
                    slugId
                    url
                    state
                    progress
                    startDate
                    targetDate
                    createdAt
                    lead {
                        id
                        name
                        displayName
                    }
                    teams {
                        nodes {
                            id
                            key
                            name
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    cycle_detail = """
        query GetCycle($id: String!) {
            cycle(id: $id) {
                id
                number
                name
                description
                startsAt
                endsAt
                completedAt
                progress
                team {
                    id
                    key
                    name
                }
            }
        }
    """

    cycles = """
        query Cycles($filter: CycleFilter, $first: Int!, $after: String) {
            cycles(filter: $filter, first: $first, after: $after) {
                nodes {
                    id
                    number
                    name
                    description
                    startsAt
                    endsAt
                    completedAt
                    progress
                    team {
                        id
                        key
                        name
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    issue_comments = """
        query IssueComments($issueId: String!, $first: Int!, $after: String) {
            issue(id: $issueId) {
                id
                identifier
                title
                comments(first: $first, after: $after) {
                    nodes {
                        id
                        body
                        createdAt
                        updatedAt
                        editedAt
                        user {
                            id
                            name
                            email
                            displayName
                        }
                        parent {
                            id
                        }
                        children {
                            nodes {
                                id
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                }
            }
        }
    """


class Mutations:
    """GraphQL mutations for Linear API."""

    issue_create = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    priority
                    priorityLabel
                    createdAt
                    state {
                        id
                        name
                        type
                        color
                    }
                    team {
                        id
                        key
                        name
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    project {
                        id
                        name
                        url
                    }
                }
            }
        }
    """

    issue_update = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    url
                    priority
                    priorityLabel
                    dueDate
                    estimate
                    updatedAt
                    completedAt
                    branchName
                    state {
                        id
                        name
                        type
                        color
                    }
                    team {
                        id
                        key
                        name
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    project {
                        id
                        name
                        state
                        progress
                        url
                    }
                }
            }
        }
    """

    comment_create = """
        mutation CommentCreate($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                    updatedAt
                    user {
                        id
                        name
                        email
                        displayName
                    }
                }
            }
        }
    """

    comment_update = """
        mutation CommentUpdate($id: String!, $input: CommentUpdateInput!) {
            commentUpdate(id: $id, input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                    updatedAt
                    editedAt
                    user {
                        id
                        name
                        email
                        displayName
                    }
                }
            }
        }
    """

    issue_subscribe = """
        mutation IssueSubscribe($id: String!) {
            issueSubscribe(id: $id) {
                success
            }
        }
    """

    issue_unsubscribe = """
        mutation IssueUnsubscribe($id: String!) {
            issueUnsubscribe(id: $id) {
                success
            }
        }
    """

    attachment_link_url = """
        mutation AttachmentLinkURL($url: String!, $issueId: String!, $title: String) {
            attachmentLinkURL(url: $url, issueId: $issueId, title: $title) {
                success
                attachment {
                    id
                    title
                    subtitle
                    url
                    sourceType
                    createdAt
                }
            }
        }
    """

    project_update_create = """
        mutation ProjectUpdateCreate($input: ProjectUpdateCreateInput!) {
            projectUpdateCreate(input: $input) {
                success
                projectUpdate {
                    id
                    body
                    health
                    createdAt
                    updatedAt
                    user {
                        id
                        name
                        displayName
                    }
                    project {
                        id
                        name
                        url
                    }
                }
            }
        }
    """

    project_create = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    slugId
                    description
                    url
                    state
                    progress
                    startDate
                    targetDate
                    createdAt
                    updatedAt
                    lead {
                        id
                        name
                        displayName
                    }
                    teams {
                        nodes {
                            id
                            key
                            name
                        }
                    }
                }
            }
        }
    """

    project_update = """
        mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
            projectUpdate(id: $id, input: $input) {
                success
                project {
                    id
                    name
                    slugId
                    description
                    url
                    state
                    progress
                    startDate
                    targetDate
                    createdAt
                    updatedAt
                    lead {
                        id
                        name
                        displayName
                    }
                    teams {
                        nodes {
                            id
                            key
                            name
                        }
                    }
                }
            }
        }
    """

    initiative_create = """
        mutation InitiativeCreate($input: InitiativeCreateInput!) {
            initiativeCreate(input: $input) {
                success
                initiative {
                    id
                    name
                    description
                    documentContent {
                        content
                    }
                    status
                    targetDate
                    createdAt
                    updatedAt
                    url
                }
            }
        }
    """

    initiative_update = """
        mutation InitiativeUpdate($id: String!, $input: InitiativeUpdateInput!) {
            initiativeUpdate(id: $id, input: $input) {
                success
                initiative {
                    id
                    name
                    description
                    documentContent {
                        content
                    }
                    status
                    targetDate
                    createdAt
                    updatedAt
                    url
                }
            }
        }
    """

    initiative_to_project_create = """
        mutation InitiativeToProjectCreate($input: InitiativeToProjectCreateInput!) {
            initiativeToProjectCreate(input: $input) {
                success
                initiativeToProject {
                    id
                    initiative {
                        id
                        name
                    }
                    project {
                        id
                        name
                        url
                    }
                }
            }
        }
    """

    issue_archive = """
        mutation IssueArchive($id: String!) {
            issueArchive(id: $id) {
                success
            }
        }
    """

    project_archive = """
        mutation ProjectArchive($id: String!) {
            projectArchive(id: $id) {
                success
            }
        }
    """

    initiative_archive = """
        mutation InitiativeArchive($id: String!) {
            initiativeArchive(id: $id) {
                success
            }
        }
    """

    issue_relation_create = """
        mutation IssueRelationCreate($input: IssueRelationCreateInput!) {
            issueRelationCreate(input: $input) {
                success
                issueRelation {
                    id
                    type
                    issue {
                        id
                        identifier
                        title
                    }
                    relatedIssue {
                        id
                        identifier
                        title
                    }
                }
            }
        }
    """
