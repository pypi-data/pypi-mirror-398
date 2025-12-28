from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @queries meta.dwh_queries_table
--queries

declare @dwh_aliases meta.dwh_aliases_table
--dwh_aliases

exec meta.add_all_dwh_queries @component_id=${component_id},@queries=@queries,@aliases=@dwh_aliases,@instance_execution_id=${instance_execution_id}
"""


def generate_query_and_aliases_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    """Generate SQL for queries and alias definitions of a component."""

    result = TEMPLATE

    for query_information in component.query_information:
        query_string = (
            "insert into @queries values("
            f"{query_information.sequence},"
            f"N'{query_information.name}',"
            f"N'{(query_information.query or "").replace("'", "''")}')\n"
        )
        result = var_insert_line(text=result, new_line=query_string, needle="--queries")

        for alias in query_information.aliases:
            alias_string = (
                "insert into @dwh_aliases values("
                f"N'{query_information.name}',"
                f"N'{alias.name}',"
                f"N'{alias.type}',"
                f"{alias.index})\n"
            )
            result = var_insert_line(
                text=result,
                new_line=alias_string,
                needle="--dwh_aliases",
            )

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)
    return result


def execute_query_and_aliases_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    """Execute SQL for queries and alias definitions of a component."""

    sql = generate_query_and_aliases_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
