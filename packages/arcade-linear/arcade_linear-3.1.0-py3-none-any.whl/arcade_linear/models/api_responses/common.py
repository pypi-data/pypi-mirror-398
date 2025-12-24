"""Common TypedDict definitions shared across Linear API responses."""

from typing_extensions import TypedDict


class PageInfoResponse(TypedDict, total=False):
    """GraphQL pagination info from Linear API."""

    hasNextPage: bool
    hasPreviousPage: bool
    startCursor: str | None
    endCursor: str | None


class UserResponse(TypedDict, total=False):
    """User data from Linear API."""

    id: str
    name: str | None
    email: str | None
    displayName: str | None
    avatarUrl: str | None
    active: bool
    admin: bool
    createdAt: str
    updatedAt: str


class OrganizationResponse(TypedDict, total=False):
    """Organization data from Linear API."""

    id: str
    name: str
    urlKey: str
    logoUrl: str | None
    createdAt: str


class ViewerResponse(TypedDict, total=False):
    """Authenticated user data from Linear API viewer query."""

    id: str
    name: str | None
    email: str | None
    displayName: str | None
    avatarUrl: str | None
    active: bool
    admin: bool
    createdAt: str
    organization: OrganizationResponse


class LabelResponse(TypedDict, total=False):
    """Label data from Linear API."""

    id: str
    name: str
    description: str | None
    color: str
