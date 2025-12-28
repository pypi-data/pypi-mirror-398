from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

__all__ = [
    "DbConfig",
    "ResultSet",
    "SqlExecutionResult",
]

AuthMethod = Literal["windows", "sql"]


@dataclass(slots=True)
class DbConfig:
    """Configuration required to open a SQL Server connection.

    The fields map directly to common pyodbc / ODBC connection string options.
    """

    server: str
    database: str
    auth_method: AuthMethod = "windows"
    driver: str = "ODBC Driver 18 for SQL Server"
    user: str | None = None
    password: str | None = None
    encrypt: bool = False
    trust_server_certificate: bool = True
    timeout_seconds: int = 30


@dataclass(slots=True)
class ResultSet:
    """Single tabular result produced by a SQL statement."""

    statement_index: int
    dataframe: pd.DataFrame


@dataclass(slots=True)
class SqlExecutionResult:
    """High‑level structured result produced by ``execute_sql_string``."""

    statements_executed: int
    rows_affected: int
    result_sets: list[ResultSet]
    messages: list[str]
    errors: list[str]
