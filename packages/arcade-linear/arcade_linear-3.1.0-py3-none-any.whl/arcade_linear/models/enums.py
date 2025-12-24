"""Enum definitions for Linear API values."""

from enum import Enum


class IssuePriority(str, Enum):
    """Priority levels for Linear issues.

    Linear uses numeric priority values (0-4) internally,
    but we expose human-readable string values.
    """

    NONE = "none"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_numeric(cls, value: int) -> "IssuePriority":
        """Convert Linear's numeric priority to enum."""
        mapping = {
            0: cls.NONE,
            1: cls.URGENT,
            2: cls.HIGH,
            3: cls.MEDIUM,
            4: cls.LOW,
        }
        return mapping.get(value, cls.NONE)

    def to_numeric(self) -> int:
        """Convert enum to Linear's numeric priority."""
        mapping = {
            IssuePriority.NONE: 0,
            IssuePriority.URGENT: 1,
            IssuePriority.HIGH: 2,
            IssuePriority.MEDIUM: 3,
            IssuePriority.LOW: 4,
        }
        return mapping[self]


class IssueStateType(str, Enum):
    """Workflow state types in Linear."""

    TRIAGE = "triage"
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"


class SubscriptionAction(str, Enum):
    """Actions for managing issue subscriptions."""

    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class IssueRelationType(str, Enum):
    """Types of relations between Linear issues."""

    BLOCKS = "blocks"
    BLOCKED_BY = "blockedBy"
    DUPLICATE = "duplicate"
    RELATED = "related"


class ArtifactType(str, Enum):
    """Types of GitHub artifacts that can be linked to issues."""

    PR = "pr"
    COMMIT = "commit"
    DEPLOYMENT = "deployment"


class ProjectState(str, Enum):
    """State values for Linear projects."""

    BACKLOG = "backlog"
    PLANNED = "planned"
    STARTED = "started"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class InitiativeState(str, Enum):
    """Status values for Linear initiatives."""

    BACKLOG = "Backlog"
    PLANNED = "Planned"
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class NotificationType(str, Enum):
    """Types of notifications in Linear."""

    ISSUE_COMMENT = "issueComment"
    ISSUE_MENTION = "issueMention"
    ISSUE_ASSIGNMENT = "issueAssignment"
    ISSUE_STATE_CHANGE = "issueStatusChanged"
    ISSUE_PRIORITY_CHANGE = "issuePriorityChanged"
    ISSUE_DUE_DATE = "issueDueDateChanged"
    PROJECT_UPDATE = "projectUpdate"


class ActivityType(str, Enum):
    """Types of user activity for filtering."""

    CREATED = "created"
    ASSIGNED = "assigned"
    COMMENTED = "commented"


class TeamLookupBy(str, Enum):
    """Lookup type for get_team tool."""

    ID = "id"
    KEY = "key"
    NAME = "name"


class ProjectLookupBy(str, Enum):
    """Lookup type for get_project tool."""

    ID = "id"
    SLUG_ID = "slug_id"
    NAME = "name"


class InitiativeLookupBy(str, Enum):
    """Lookup type for get_initiative tool."""

    ID = "id"
    NAME = "name"


class ProjectHealth(str, Enum):
    """Health status values for Linear project updates."""

    ON_TRACK = "onTrack"
    AT_RISK = "atRisk"
    OFF_TRACK = "offTrack"
