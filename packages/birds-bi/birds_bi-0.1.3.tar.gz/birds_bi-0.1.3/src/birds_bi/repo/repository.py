from pathlib import Path
from typing import Literal, cast, get_args

from .component import Category, Component
from .models import TableDefinition

_CATEGORY_VALUES = set(get_args(Category))


class Repository:
    def __init__(self, path: str | Path) -> None:
        self.path: Path = Path(str(path).strip()).expanduser().resolve(strict=False)
        self.content_path: Path = self.path / "content"
        self.tabular_path: Path = self.path / "tabular"

    def _get_directories(self, path: Path) -> list[Path]:
        if not path.is_dir():
            return []
        return [p for p in path.iterdir() if p.is_dir()]

    @property
    def components(self) -> list[Component]:
        category_order = {
            "help": 0,
            "dim": 1,
            "fact": 2,
        }

        return [
            Component(
                repo=self,
                category=cast(Literal["help", "dim", "fact"], category_dir.name),
                component=component_dir.name,
            )
            for category_dir in sorted(
                self._get_directories(self.content_path),
                key=lambda p: category_order.get(p.name, 99),
            )
            if category_dir.name in _CATEGORY_VALUES
            for component_dir in sorted(
                self._get_directories(category_dir),
                key=lambda p: p.name,
            )
        ]

    def get_components_from_category(
        self, category: Literal[Category]
    ) -> list[Component]:
        category_path = self.content_path / category
        if not category_path.is_dir():
            raise ValueError(f"Category does not exist: {category}")

        return [
            Component(repo=self, category=category, component=component_dir.name)
            for component_dir in self._get_directories(category_path)
        ]

    @property
    def table_definitions(self) -> list[TableDefinition]:
        total_table_definition: list[TableDefinition] = []
        seen_identifiers: set[str] = set()

        for component in self.components:
            for table in component.table_definitions:
                if table.table_identifier not in seen_identifiers:
                    total_table_definition.append(table)
                    seen_identifiers.add(table.table_identifier)
                else:
                    current_table = next(
                        td
                        for td in total_table_definition
                        if td.table_identifier == table.table_identifier
                    )
                    combined_columns = current_table.columns + table.columns
                    unique_columns = {c.column_name: c for c in combined_columns}

                    idx = total_table_definition.index(current_table)
                    total_table_definition[idx] = TableDefinition(
                        schema=table.schema,
                        table_identifier=table.table_identifier,
                        columns=list(unique_columns.values()),
                    )

        return total_table_definition
