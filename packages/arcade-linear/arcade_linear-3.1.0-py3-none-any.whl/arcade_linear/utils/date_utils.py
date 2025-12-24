"""Date parsing utilities for Linear toolkit."""

from datetime import datetime, timezone
from typing import cast

import dateparser
from arcade_mcp_server.exceptions import ToolExecutionError

INVALID_DATE_FORMAT_ERROR = "Invalid date format for {field}: '{value}'"


def parse_date_string(date_str: str) -> datetime | None:
    """Parse a date string into a timezone-aware datetime object.

    Uses dateparser for flexible parsing of ISO dates and common formats.
    """
    if not date_str:
        return None

    try:
        parsed_date = dateparser.parse(date_str)
        if parsed_date is None:
            return None

        parsed_datetime = cast(datetime, parsed_date)

        if parsed_datetime.tzinfo is None:
            return parsed_datetime.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    else:
        return parsed_datetime


def validate_date_format(field_name: str, date_str: str | None) -> None:
    """Validate date format and raise ToolExecutionError if invalid."""
    if not date_str:
        return

    parsed_date = parse_date_string(date_str)
    if parsed_date is None:
        raise ToolExecutionError(INVALID_DATE_FORMAT_ERROR.format(field=field_name, value=date_str))


def format_iso_date(dt: datetime | None) -> str | None:
    """Format datetime as ISO 8601 string in UTC with Z suffix."""
    if dt is None:
        return None
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
