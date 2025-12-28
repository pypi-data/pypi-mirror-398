from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pandas as pd
import pyodbc

from .models import DbConfig, ResultSet, SqlExecutionResult


def _build_connection_string(cfg: DbConfig) -> str:
    """Build a SQL Server connection string from a ``DbConfig`` instance."""

    parts: list[str] = [
        f"DRIVER={{{cfg.driver}}}",
        f"SERVER={cfg.server}",
        f"DATABASE={cfg.database}",
        f"Connection Timeout={cfg.timeout_seconds}",
        f"Encrypt={'yes' if cfg.encrypt else 'no'}",
        f"TrustServerCertificate={'yes' if cfg.trust_server_certificate else 'no'}",
    ]

    if cfg.auth_method == "windows":
        parts.append("Trusted_Connection=yes")
    else:
        if not cfg.user or not cfg.password:
            msg = "SQL authentication requires both user and password."
            raise ValueError(msg)
        parts.append(f"UID={cfg.user}")
        parts.append(f"PWD={cfg.password}")

    return ";".join(parts) + ";"


def connect(cfg: DbConfig) -> pyodbc.Connection:
    """Create and return a live ``pyodbc.Connection``.

    The function propagates ``pyodbc`` exceptions so callers can handle them.
    """

    conn_str = _build_connection_string(cfg)
    return pyodbc.connect(conn_str, timeout=cfg.timeout_seconds)


@contextmanager
def db_connection(cfg: DbConfig) -> Iterator[pyodbc.Connection]:
    """Context manager that ensures proper close and rollback on exceptions."""

    conn: pyodbc.Connection | None = None
    try:
        conn = connect(cfg)
        yield conn
    except Exception:  # noqa: BLE001
        if conn is not None:
            try:
                conn.rollback()
            except Exception:  # noqa: BLE001
                pass
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass


def _split_sql_statements(sql_content: str, *, split_on_go: bool = False) -> list[str]:
    """Split SQL text into statements.

    - Default: execute as a single batch (best for scripts relying on variables/temp
      tables).
    - If ``split_on_go=True``: split on lines containing only ``GO`` (common for
      SQLCMD/SSMS scripts).
    """

    sql = sql_content.strip()
    if not sql:
        return []

    if not split_on_go:
        return [sql]

    statements: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        if line.strip().upper() == "GO":
            stmt = "\n".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(line)

    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)

    return statements


def execute_sql(
    sql_content: str,
    connection: pyodbc.Connection,
    *,
    split_on_go: bool = False,
    continue_on_error: bool = True,
) -> dict[str, Any]:
    """Execute SQL content and return a low‑level structured result.

    The structure is a plain ``dict`` that is later converted to
    :class:`~birds_bi.db.models.SqlExecutionResult` by :func:`execute_sql_string`.
    """

    if connection is None:
        raise RuntimeError("No database connection provided.")

    results: dict[str, Any] = {
        "statements_executed": 0,
        "rows_affected": 0,
        "result_sets": [],  # list of {statement_index, columns, rows}
        "messages": [],
        "errors": [],
    }

    statements = _split_sql_statements(sql_content, split_on_go=split_on_go)
    if not statements:
        results["messages"].append("No SQL to execute.")
        return results

    cursor = connection.cursor()

    for i, statement in enumerate(statements, start=1):
        if not statement.strip():
            continue

        try:
            cursor.execute(statement)

            # Consume all result sets for this statement
            while True:
                if cursor.description:  # result set available
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    results["result_sets"].append(
                        {
                            "statement_index": i,
                            "columns": columns,
                            "rows": [list(r) for r in rows],
                        },
                    )
                else:
                    # Not a SELECT; rowcount may be -1 for some operations/drivers.
                    rowcount = getattr(cursor, "rowcount", -1)
                    if rowcount is not None and rowcount >= 0:
                        results["rows_affected"] += rowcount

                if not cursor.nextset():
                    break

            results["statements_executed"] += 1
            results["messages"].append(f"Statement {i} executed successfully.")

        except Exception as exc:  # noqa: BLE001
            msg = f"Error in statement {i}: {exc}"
            results["errors"].append(msg)

            if not continue_on_error:
                connection.rollback()
                raise

    # Commit once at the end if all went as far as we allow.
    connection.commit()
    return results


def execute_sql_string(
    sql: str,
    db_config: DbConfig,
    *,
    split_on_go: bool = False,
    continue_on_error: bool = False,
) -> SqlExecutionResult:
    """Convenience wrapper.

    Opens a connection, executes the SQL, and returns a :class:`SqlExecutionResult`.
    """

    with db_connection(db_config) as conn:
        data = execute_sql(
            sql,
            conn,
            split_on_go=split_on_go,
            continue_on_error=continue_on_error,
        )

    result_sets: list[ResultSet] = []

    for rs in data.get("result_sets", []):
        df = pd.DataFrame(
            data=rs.get("rows", []),
            columns=rs.get("columns", []),
        )

        result_sets.append(
            ResultSet(
                statement_index=rs.get("statement_index"),
                dataframe=df,
            ),
        )

    return SqlExecutionResult(
        statements_executed=data.get("statements_executed", 0),
        rows_affected=data.get("rows_affected", 0),
        result_sets=result_sets,
        messages=data.get("messages", []),
        errors=data.get("errors", []),
    )
