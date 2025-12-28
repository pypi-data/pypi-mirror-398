from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @fact_dimension_joins meta.dwh_fact_dimension_joins_table
--fact_dimension_joins

exec meta.add_all_dwh_fact_dimensions @component_id=${component_id},@fact_dimension_joins=@fact_dimension_joins,@instance_execution_id=${instance_execution_id}
"""


def generate_fact_dimension_joins_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    result = TEMPLATE

    for d_index, dimension in enumerate(component.dimensions):
        for dj_index, dimension_join in enumerate(dimension.dimension_joins):
            string = (
                f"insert into @fact_dimension_joins values("
                f"N'{dimension.dimension}',"
                f"N'{dimension.role_playing}',"
                f"N'{dimension_join.dimension_column}',"
                f"N'{dimension_join.delta_column}',"
                f"{d_index},"
                f"{dj_index})\n"
            )
            result = var_insert_line(
                text=result, new_line=string, needle="--fact_dimension_joins"
            )

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)

    return result


def execute_fact_dimension_joins_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_fact_dimension_joins_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
