"""
tabular_process.py

A small, importable helper module to:
1) Deploy a Tabular Editor "Save to Folder" model via Tabular Editor CLI (TabularEditor.exe)
2) Run a FULL processing (TMSL Refresh type=full) against the target database/model

Targets
-------
- SSAS Tabular (on-prem)
- Azure Analysis Services (AAS)
- Power BI Premium / Fabric semantic models via XMLA endpoints

Authentication
--------------
This module does NOT implement OAuth flows. It relies on MSOLAP/ADOMD.NET behavior.
Supported connection patterns:

- SSAS (on-prem): Windows Integrated (SSPI)
- AAS / Power BI XMLA:
  - Interactive AAD (local dev): MSOLAP prompts for login where supported
  - Service Principal (CI/CD): app:<client_id>@<tenant_id> + client secret
- Explicit MSOLAP connection string (advanced/custom scenarios)

Requirements
------------
- Windows recommended (MSOLAP/ADOMD.NET dependency)
- pythonnet (pip install pythonnet)
- ADOMD.NET available on the host (commonly installed with SSMS / MSOLAP client libs)

Notes
-----
- Deployment is done by your existing deploy module (tabular_deploy.py), which wraps TabularEditor.exe.
- Processing is executed via ADOMD.NET by sending a TMSL Refresh command over XMLA.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

AuthKind = Literal["windows", "interactive", "service_principal", "connection_string"]


@dataclass(frozen=True)
class Connection:
    """
    A thin authentication descriptor.

    - kind="windows": SSAS on-prem Windows Integrated (SSPI)
    - kind="interactive": AAD interactive via MSOLAP prompt (local dev)
    - kind="service_principal": AAD service principal via app id + secret (CI/CD)
    - kind="connection_string": provide the full MSOLAP connection string yourself
    """

    kind: AuthKind
    endpoint: str

    # For service principal
    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None

    # For connection_string
    ms_string: str | None = None


class TabularProcessError(RuntimeError):
    """Raised when processing (TMSL execution) fails."""


def ssas_windows(endpoint: str) -> Connection:
    return Connection(kind="windows", endpoint=endpoint)


def aas_interactive(endpoint: str) -> Connection:
    return Connection(kind="interactive", endpoint=endpoint)


def pbi_interactive(endpoint: str) -> Connection:
    return Connection(kind="interactive", endpoint=endpoint)


def aas_service_principal(
    *, endpoint: str, tenant_id: str, client_id: str, client_secret: str
) -> Connection:
    return Connection(
        kind="service_principal",
        endpoint=endpoint,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )


def pbi_service_principal(
    *, endpoint: str, tenant_id: str, client_id: str, client_secret: str
) -> Connection:
    return Connection(
        kind="service_principal",
        endpoint=endpoint,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )


def ms_connection_string(connection_string: str) -> Connection:
    """
    Use this when you already have a fully-formed MSOLAP connection string.
    """
    return Connection(
        kind="connection_string",
        endpoint="(explicit connection string)",
        ms_string=connection_string,
    )


def _build_msolap_connection_string(conn: Connection | str) -> str:
    """
    Build a MSOLAP connection string for ADOMD.NET.

    If a raw string is provided, it is treated as an endpoint (NOT a full connection string).
    Prefer passing a Connection, or use ms_connection_string(...).
    """
    if isinstance(conn, str):
        return f"Provider=MSOLAP;Data Source={conn};"

    match conn.kind:
        case "connection_string":
            if not conn.ms_string:
                msg = "Connection.kind='connection_string' requires ms_string."
                raise ValueError(msg)
            return conn.ms_string
        case "windows":
            return (
                "Provider=MSOLAP;"
                f"Data Source={conn.endpoint};"
                "Integrated Security=SSPI;"
            )
        case "interactive":
            # Suitable for local dev; MSOLAP may prompt for sign-in where supported.
            return "Provider=MSOLAP;" f"Data Source={conn.endpoint};"
        case "service_principal":
            if not (conn.tenant_id and conn.client_id and conn.client_secret):
                raise ValueError(
                    "Service principal auth requires tenant_id, client_id, client_secret."
                )
            return (
                "Provider=MSOLAP;"
                f"Data Source={conn.endpoint};"
                f"User ID=app:{conn.client_id}@{conn.tenant_id};"
                f"Password={conn.client_secret};"
                "Persist Security Info=True;"
            )
        case _:
            raise ValueError(f"Unsupported connection kind: {conn.kind!r}")


def _tmsl_refresh_full(database: str) -> str:
    payload = {
        "refresh": {"type": "full", "objects": [{"database": database}]}
    }  # Process Full
    return json.dumps(payload, separators=(",", ":"))


def _redact_secrets(text: str, secrets: Sequence[str]) -> str:
    redacted = text
    for s in secrets:
        if not s:
            continue
        redacted = redacted.replace(s, "***REDACTED***")
        redacted = re.sub(r"(?i)(Password\s*=\s*)[^;]+", r"\1***REDACTED***", redacted)
    return redacted


def _execute_tmsl(
    conn_str: str, tmsl_json: str, *, secrets_to_redact: Sequence[str] = ()
) -> None:
    """
    Execute a JSON command over XMLA using ADOMD.NET via pythonnet.
    """
    try:
        import clr

        clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
        from Microsoft.AnalysisServices.AdomdClient import (
            AdomdCommand,
            AdomdConnection,
        )
    except Exception as e:  # noqa: BLE001
        raise TabularProcessError(
            "Could not load ADOMD.NET (Microsoft.AnalysisServices.AdomdClient). "
            "Install SSMS or the Microsoft Analysis Services client libraries on this machine."
        ) from e

    try:
        connection = AdomdConnection(conn_str)
        connection.Open()
        try:
            cmd = AdomdCommand(tmsl_json, connection)
            cmd.CommandTimeout = 0  # infinite; manage timeouts at pipeline level
            cmd.ExecuteNonQuery()
        finally:
            connection.Close()
    except Exception as e:  # noqa: BLE001
        msg = _redact_secrets(str(e), secrets_to_redact)
        raise TabularProcessError(f"TMSL execution failed: {msg}") from e


def process_tabular(
    *,
    connection: Connection | str,
    database: str,
) -> None:
    conn_str = _build_msolap_connection_string(connection)
    tmsl = _tmsl_refresh_full(database)

    secrets = []
    if isinstance(connection, Connection) and connection.client_secret:
        secrets.append(connection.client_secret)

    _execute_tmsl(conn_str, tmsl, secrets_to_redact=secrets)
