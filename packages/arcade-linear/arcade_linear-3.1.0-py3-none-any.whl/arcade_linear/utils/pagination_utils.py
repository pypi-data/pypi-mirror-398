"""Pagination utilities for Linear toolkit."""

from collections.abc import Mapping
from typing import Any

from arcade_linear.models.tool_outputs.common import PaginationInfo


def build_cursor_pagination(
    page_info: Mapping[str, Any] | None,
) -> PaginationInfo:
    """Build PaginationInfo from Linear GraphQL pageInfo response."""
    if not page_info:
        return PaginationInfo(has_next_page=False)

    result: PaginationInfo = {
        "has_next_page": page_info.get("hasNextPage", False),
    }

    end_cursor = page_info.get("endCursor")
    if end_cursor:
        result["end_cursor"] = end_cursor

    return result


def add_pagination_to_response(
    response: dict[str, Any],
    page_info: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Add pagination info to a response dictionary.

    Adds pagination only if there is a next page.
    """
    pagination = build_cursor_pagination(page_info)

    if pagination.get("has_next_page"):
        response["pagination"] = pagination

    return response
