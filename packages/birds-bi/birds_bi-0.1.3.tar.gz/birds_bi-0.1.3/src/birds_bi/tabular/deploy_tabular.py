from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TabularDeploymentError(RuntimeError):
    """Raised when Tabular Editor deployment fails."""


class Auth(Enum):
    WINDOWS = "windows"
    INTERACTIVE = "interactive"
    SERVICE_PRINCIPAL_SECRET = "service_principal_secret"
    USERNAME_PASSWORD = "username_password"


@dataclass(frozen=True, slots=True)
class Connection:
    endpoint: str
    auth: Auth = Auth.INTERACTIVE

    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None

    username: str | None = None
    password: str | None = None

    provider: str = "MSOLAP.8"

    def data_source(self) -> str:
        endpoint = self.endpoint.strip()

        match self.auth:
            case Auth.WINDOWS | Auth.INTERACTIVE:
                return endpoint

            case Auth.SERVICE_PRINCIPAL_SECRET:
                _require(self.tenant_id, "tenant_id")
                _require(self.client_id, "client_id")
                _require(self.client_secret, "client_secret")
                return (
                    f"Provider={self.provider};"
                    f"Data Source={endpoint};"
                    f"User ID=app:{self.client_id}@{self.tenant_id};"
                    f"Password={self.client_secret};"
                )

            case Auth.USERNAME_PASSWORD:
                _require(self.username, "username")
                _require(self.password, "password")
                return (
                    f"Provider={self.provider};"
                    f"Data Source={endpoint};"
                    f"User ID={self.username};"
                    f"Password={self.password};"
                )

        raise ValueError(f"Unsupported auth method: {self.auth}")


def _require(value: str | None, name: str) -> None:
    if not value:
        raise ValueError(f"{name} is required for the selected auth method")


def _ensure_te_folder_model(model_folder: Path) -> None:
    if not (model_folder / "database.json").exists():
        raise FileNotFoundError(
            f"Model folder must contain database.json (Tabular Editor 'Save to Folder' format): {model_folder}"
        )


def _redact(text: str) -> str:
    if not text:
        return text
    lower = text.lower()
    i = lower.find("password=")
    if i < 0:
        return text
    j = text.find(";", i)
    if j < 0:
        return text[:i] + "Password=***REDACTED***"
    return text[:i] + "Password=***REDACTED***" + text[j:]


def _te_version(te_exe: Path) -> tuple[int, int, int]:
    """
    Extract TE version from `TabularEditor.exe /?` output.
    """
    r = subprocess.run([str(te_exe), "/?"], text=True, capture_output=True)
    txt = (r.stdout or "") + "\n" + (r.stderr or "")
    m = re.search(r"Tabular Editor\s+(\d+)\.(\d+)\.(\d+)", txt)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def deploy_tabular_model(
    *,
    tabular_editor_exe: str | Path,
    model_folder: str | Path,
    connection: Connection | str,
    database: str,
    overwrite: bool = True,
    # Selective deploy controls:
    deploy_connections: bool = False,  # -C
    deploy_partitions: bool = True,  # -P
    deploy_shared_expressions: bool = False,  # -S (deploy flag, TE >= 2.27.0)
    deploy_roles: bool = False,  # -R
    deploy_role_members: bool = False,  # -M (only meaningful with -R)
    # Other flags:
    skip_incremental_policy_partitions: bool = False,  # -P -Y
    warn_unprocessed: bool = False,  # -W
    fail_on_dax_errors: bool = False,  # -E
    extra_flags: Sequence[str] | None = None,
) -> None:
    """
    Deploy a Tabular Editor folder model using TE2 CLI, with selective deployment categories.

    Defaults are aligned with your requirements:
      - Do NOT deploy connections/data sources (-C)
      - Do NOT deploy roles (-R)
      - Do NOT deploy role members (-M)
    """

    te = Path(tabular_editor_exe)
    if not te.exists():
        raise FileNotFoundError(f"TabularEditor.exe not found: {te}")

    folder = Path(model_folder)
    _ensure_te_folder_model(folder)

    te_ver = _te_version(te)

    data_source = (
        connection.data_source()
        if isinstance(connection, Connection)
        else str(connection).strip()
    )

    cmd: list[str] = [str(te), str(folder), "-D", data_source, database]

    if overwrite:
        cmd.append("-O")

    # Deploy connections/data sources (optional)
    if deploy_connections:
        cmd.append("-C")

    # Deploy partitions (optional)
    if deploy_partitions:
        cmd.append("-P")
        if skip_incremental_policy_partitions:
            cmd.append("-Y")

    # Deploy shared expressions (TE >= 2.27.0 deploy flag)
    if deploy_shared_expressions:
        if te_ver >= (2, 27, 0):
            cmd.append("-S")
        else:
            # TE < 2.27.0 does not have deploy -S; ignoring is safer than breaking the CLI.
            pass

    # Deploy roles / members (optional)
    if deploy_roles:
        cmd.append("-R")
        if deploy_role_members:
            cmd.append("-M")
    # If deploy_roles is False, we intentionally do nothing even if deploy_role_members is True.

    if warn_unprocessed:
        cmd.append("-W")
    if fail_on_dax_errors:
        cmd.append("-E")
    if extra_flags:
        cmd.extend(extra_flags)

    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.returncode != 0:
        safe_cmd = " ".join(_redact(p) for p in cmd)
        raise TabularDeploymentError(
            "Tabular deployment failed\n"
            f"Return code: {result.returncode}\n"
            f"Command: {safe_cmd}\n"
            f"STDOUT:\n{_redact(result.stdout)}\n"
            f"STDERR:\n{_redact(result.stderr)}"
        )


# Convenience constructors (optional)
def ssas_windows(endpoint: str) -> Connection:
    return Connection(endpoint=endpoint, auth=Auth.WINDOWS)


def aas_service_principal(
    endpoint: str, *, tenant_id: str, client_id: str, client_secret: str
) -> Connection:
    return Connection(
        endpoint=endpoint,
        auth=Auth.SERVICE_PRINCIPAL_SECRET,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )


def pbi_service_principal(
    endpoint: str, *, tenant_id: str, client_id: str, client_secret: str
) -> Connection:
    return Connection(
        endpoint=endpoint,
        auth=Auth.SERVICE_PRINCIPAL_SECRET,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
