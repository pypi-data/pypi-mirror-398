from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.format_sql_columns import format_sql_columns
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @table_indexes dbo.table_indexes
--table_indexes

exec meta.add_all_dwh_indexes @instance_id=1
,@component_category=${category}
,@component_name=${component_name}
,@table_indexes=@table_indexes
,@instance_execution_id=${instance_execution_id}
,@additional_indexes=0
"""


def generate_table_indexes_script(
    component: Component, instance_execution_id: str
) -> str:

    result: str = TEMPLATE

    for table_index in component.table_indexes:
        string: str = (
            f"insert into @table_indexes values("
            f"N'{component.category}.{component.component}'"
            f",N'{table_index.name}'"
            f",N'{table_index.type}'"
            f",N'{format_sql_columns(table_index.columns)}'"
            f",N'{format_sql_columns(table_index.included_columns)}'"
            f",{table_index.fill_factor}"
            f",{table_index.is_unique})\n"
        )
        result = var_insert_line(text=result, new_line=string, needle="--table_indexes")

    result = result.replace("${category}", f"N'{component.category}'")
    result = result.replace(
        "${component_name}", f"N'{component.category}{component.component}'"
    )
    result = result.replace("${instance_execution_id}", instance_execution_id)
    return result


def execute_table_indexes_script(
    component: Component,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_table_indexes_script(
        component=component,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
