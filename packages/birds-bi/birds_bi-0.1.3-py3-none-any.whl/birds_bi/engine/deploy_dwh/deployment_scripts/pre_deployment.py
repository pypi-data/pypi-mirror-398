from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @Pre_deployment meta.dwh_scripts_table
--Pre_deployment

exec meta.add_all_dwh_scripts @instance_id=1,@type=N'pre_deploy',@component_id=${component_id},@dwh_scripts=@Pre_deployment,@instance_execution_id=${instance_execution_id}
"""


def generate_pre_deployment_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    """Generate SQL for pre‑deployment scripts of a component."""

    result = TEMPLATE

    for pre_script in component.pre_deployment_scripts:
        string = (
            f"insert into @pre_deployment values("
            f"N'{pre_script.name}'"
            f",N'{component.category}\\{component.component}\\pre_deploy\\{pre_script.name}'"
            f",{pre_script.index}"
            f",N'{pre_script.sql.replace("'", "''")}'"
            f",1)\n"
        )
        result = var_insert_line(
            text=result, new_line=string, needle="--pre_deployment"
        )

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)

    return result


def execute_pre_deployment_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    """Execute SQL for pre‑deployment scripts of a component."""

    sql = generate_pre_deployment_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
