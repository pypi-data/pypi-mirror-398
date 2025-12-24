"""Date utilities for Pylon toolkit."""

from datetime import datetime, timedelta, timezone

from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_pylon.constants import MAX_DATE_RANGE_DAYS


def get_default_date_range() -> tuple[str, str]:
    """Get default date range (7 days ago to now).

    Returns:
        Tuple of (start_time, end_time) in RFC3339 format.
    """
    return get_date_range_for_days(7)


def get_date_range_for_days(days: int) -> tuple[str, str]:
    """Get date range for specified number of days ago to now.

    Args:
        days: Number of days to look back.

    Returns:
        Tuple of (start_time, end_time) in RFC3339 format.
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return (
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def parse_rfc3339(timestamp: str) -> datetime:
    """Parse RFC3339 timestamp string to datetime.

    Args:
        timestamp: RFC3339 formatted timestamp string.

    Returns:
        datetime object in UTC.

    Raises:
        ToolExecutionError: If timestamp format is invalid.
    """
    try:
        # Handle both 'Z' suffix and '+00:00'
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp)
    except ValueError as e:
        raise ToolExecutionError(
            f"Invalid timestamp format: {timestamp}. Use RFC3339 format (YYYY-MM-DDTHH:MM:SSZ).",
            developer_message=str(e),
        ) from e


def validate_date_range(start_time: str, end_time: str) -> None:
    """Validate that date range is within allowed limits.

    Args:
        start_time: Start of date range in RFC3339 format.
        end_time: End of date range in RFC3339 format.

    Raises:
        ToolExecutionError: If date range is invalid or exceeds 30 days.
    """
    start = parse_rfc3339(start_time)
    end = parse_rfc3339(end_time)

    if end < start:
        raise ToolExecutionError(
            "end_time must be after start_time.",
            developer_message=f"start_time={start_time}, end_time={end_time}",
        )

    duration = end - start
    if duration.days > MAX_DATE_RANGE_DAYS:
        raise ToolExecutionError(
            f"Date range exceeds maximum of {MAX_DATE_RANGE_DAYS} days. "
            f"Requested range: {duration.days} days.",
            developer_message=f"start={start_time}, end={end_time}, days={duration.days}",
        )
