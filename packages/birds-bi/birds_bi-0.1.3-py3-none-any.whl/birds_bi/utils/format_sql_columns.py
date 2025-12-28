from __future__ import annotations

from collections.abc import Iterable


def format_sql_columns(columns: Iterable[str] | None) -> str:
    """Format a list of column names for safe embedding in SQL.

    The function is intentionally conservative and only trims whitespace and
    surrounding quotes; it does not attempt to quote or escape identifiers.
    """

    if not columns:
        return ""

    cleaned = [col.strip().strip("'\"") for col in columns]
    return ", ".join(cleaned)
