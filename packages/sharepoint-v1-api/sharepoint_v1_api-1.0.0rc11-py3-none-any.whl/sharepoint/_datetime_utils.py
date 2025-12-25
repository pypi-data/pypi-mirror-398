"""
Utility functions for parsing SharePoint datetime strings.
"""

from __future__ import annotations

from datetime import datetime
from pytz import timezone
from typing import Optional


def parse_sharepoint_datetime(dt_str: str | None, tz: timezone | None = None) -> Optional[datetime]:
    """
    Parse a SharePoint datetime string into a timezone-aware ``datetime``.

    * Accepts ISO-8601 strings (e.g. ``2023-04-01T12:34:56+00:00``) via
      ``datetime.fromisoformat``.
    * Falls back to the classic SharePoint format ``%Y-%m-%dT%H:%M:%SZ``.
    * If parsing succeeds and the resulting ``datetime`` is naive,
      the provided ``tz`` (normally ``self.sp.timezone``) is attached.
    * Returns ``None`` for missing/empty strings or unparsable values.
    """
    if not dt_str:
        return None

    # Try modern ISO-8601 parsing first
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        # Fallback to the legacy SharePoint format
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return None

    # Ensure timezone awareness
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt
