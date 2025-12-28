from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @query_columns meta.dwh_query_columns_table
--query_columns

exec meta.add_all_dwh_query_columns @component_id=${component_id},@query_columns=@query_columns,@instance_execution_id=${instance_execution_id}
"""


def generate_query_columns_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    result = TEMPLATE

    for column in component.columns:
        string = (
            f"insert into @query_columns values({column.index}"
            f",N'{column.column_name}'"
            f",N'{column.data_type_full}'"
            f",N'{column.type}'"
            f",N'N')\n"
        )

        result = var_insert_line(text=result, new_line=string, needle="--query_columns")

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)
    return result


def execute_query_columns_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_query_columns_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
