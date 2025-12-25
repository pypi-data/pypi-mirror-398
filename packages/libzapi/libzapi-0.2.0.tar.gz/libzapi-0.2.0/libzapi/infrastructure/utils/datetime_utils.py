from datetime import datetime, timezone
from typing import Optional


def parse_dt(value: Optional[str]) -> datetime:
    """
    Parse Zendesk-style ISO 8601 timestamps into timezone-aware UTC datetimes.

    Zendesk commonly returns strings like:
        "2025-11-05T12:34:56Z"
        "2025-11-05T12:34:56+00:00"

    If value is None, returns Unix epoch (UTC).
    """
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)

    # Zendesk uses 'Z' to mean UTC
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        # Fallback for any malformed input
        return datetime.fromtimestamp(0, tz=timezone.utc)
