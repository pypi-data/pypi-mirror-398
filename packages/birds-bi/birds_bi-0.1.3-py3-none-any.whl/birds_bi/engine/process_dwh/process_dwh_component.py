from typing import Literal

from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component


def process_component(
    component: Component,
    db_config: DbConfig,
    process_action: Literal["default", "staging", "components"] = "default",
    load_type: int = -1,
) -> None:
    sql: str = (
        "exec dwh.process "
        f"@component_object = '{component}'"
        f",@process_action = '{process_action}'"
        f",@staging_load_type = {load_type}"
        f",@components_load_type = {load_type}"
    )

    execute_sql_string(db_config=db_config, sql=sql)


def process_component_list(
    component_list: list[Component],
    db_config: DbConfig,
    process_action: Literal["default", "staging", "components"] = "default",
    load_type: int = -1,
) -> None:

    component_list_string = "["
    for component in component_list:
        component_list_string += f'"{component}",'
    component_list_string = component_list_string.rstrip(",") + "]"

    sql: str = (
        "exec dwh.process "
        f"@component_object_list = '{component_list_string}'"
        f",@process_action = '{process_action}'"
        f",@staging_load_type = {load_type}"
        f",@components_load_type = {load_type}"
    )

    execute_sql_string(db_config=db_config, sql=sql)
