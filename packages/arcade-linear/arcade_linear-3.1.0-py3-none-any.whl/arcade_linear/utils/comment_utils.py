"""Utility functions for comment tools."""

from collections.abc import Mapping
from typing import Any, cast

from arcade_linear.models.tool_outputs.comments import CommentData
from arcade_linear.utils.response_utils import remove_none_values_recursive


def map_comment(comment_data: Mapping[str, Any]) -> CommentData:
    """Map API comment data to output format."""
    user_data = comment_data.get("user", {}) or {}
    parent_data = comment_data.get("parent")
    children_conn = comment_data.get("children", {}) or {}
    children_data = children_conn.get("nodes", []) if children_conn else []

    return cast(
        CommentData,
        remove_none_values_recursive({
            "id": comment_data.get("id", ""),
            "body": comment_data.get("body", ""),
            "created_at": str(comment_data.get("createdAt", "")),
            "user_id": user_data.get("id") if user_data else None,
            "user_name": (user_data.get("name") or user_data.get("displayName"))
            if user_data
            else None,
            "parent_id": parent_data.get("id") if parent_data else None,
            "reply_count": len(children_data),
        }),
    )
