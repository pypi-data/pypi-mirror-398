from dataclasses import dataclass
from pathlib import Path
from typing import Literal

__all__ = [
    "Column",
    "QueryInformation",
    "QueryAlias",
    "QueryLoadProcedures",
    "Dimension",
    "DimensionJoin",
    "TableDefinitionColumn",
    "TableDefinition",
    "TableIndex",
    "PreDeploymentScript",
    "PostDeploymentScript",
    "DwhDeploymentScript",
]


@dataclass
class QueryLoadProcedures:
    sequence: int
    identifier: str


@dataclass
class QueryAlias:
    name: str
    type: Literal["primary", "non_primary"]
    index: int


@dataclass
class QueryInformation:
    name: str
    select_file_path: str
    sequence: int
    aliases: list[QueryAlias]
    query: str | None


@dataclass
class Column:
    index: int
    column_name: str
    data_type_full: str
    type: str
    nullable: bool


@dataclass
class DimensionJoin:
    delta_column: str
    dimension_column: str


@dataclass
class Dimension:
    dimension: str
    role_playing: str
    dimension_joins: list[DimensionJoin]


@dataclass
class TableDefinitionColumn:
    column_name: str
    data_type: str
    character_maximum_length: int
    numeric_precision: int
    numeric_scale: int
    nullable: bool
    business_key: bool


@dataclass
class TableDefinition:
    schema: str
    table_identifier: str
    columns: list[TableDefinitionColumn]


@dataclass
class TableIndex:
    name: str
    type: str
    columns: list[str]
    included_columns: list[str]
    fill_factor: int
    is_unique: bool


@dataclass
class PostDeploymentScript:
    name: str
    file_path: Path
    sql: str
    index: int


@dataclass
class PreDeploymentScript:
    name: str
    file_path: Path
    sql: str
    index: int


@dataclass
class DwhDeploymentScript:
    name: str
    file_path: Path
    sql: str
    index: int
    sqlpath: str
