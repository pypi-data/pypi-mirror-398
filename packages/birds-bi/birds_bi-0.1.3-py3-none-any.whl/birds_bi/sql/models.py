from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SqlBatch:
    """Single batch of SQL statements (split from a larger script)."""

    index: int
    sql: str
