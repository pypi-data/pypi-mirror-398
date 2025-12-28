from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.sql.split_sql_scripts import split_sql_batches
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @dwh_scripts meta.dwh_scripts_table
--deployment

exec meta.add_all_dwh_scripts @instance_id=1,@type=N'Default',@component_id=${component_id},@dwh_scripts=@dwh_scripts,@instance_execution_id=${instance_execution_id}
"""


def generate_dwh_deployment_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    result = TEMPLATE

    for script in component.dwh_deployment_scripts:
        for batch in split_sql_batches(script.sql):
            string = (
                f"insert into @dwh_scripts values("
                f"N'{script.name}'"
                f",N'{script.sqlpath}'"
                f",{script.index}"
                f",N'{batch.sql}'"
                f",{batch.index})\n"
            )
            result = var_insert_line(
                text=result, new_line=string, needle="--deployment"
            )

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)

    return result


def execute_dwh_deployment_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_dwh_deployment_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
