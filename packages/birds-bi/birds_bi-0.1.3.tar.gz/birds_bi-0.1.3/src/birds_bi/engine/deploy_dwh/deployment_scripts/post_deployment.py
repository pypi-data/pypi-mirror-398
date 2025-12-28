from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @Post_deployment meta.dwh_scripts_table
--Post_deployment

exec meta.add_all_dwh_scripts @instance_id=1,@type=N'post_deploy',@component_id=${component_id},@dwh_scripts=@Post_deployment,@instance_execution_id=${instance_execution_id}
"""


def generate_post_deployment_script(
    component: Component, component_id: str, instance_execution_id: str
) -> str:
    """Generate SQL for post‑deployment scripts of a component."""

    result = TEMPLATE

    for post_script in component.post_deployment_scripts:
        string = (
            f"insert into @post_deployment values("
            f"N'{post_script.name}'"
            f",N'{component.category}\\{component.component}\\post_deploy\\{post_script.name}'"
            f",{post_script.index}"
            f",N'{post_script.sql.replace("'", "''")}'"
            f",1)\n"
        )
        result = var_insert_line(
            text=result, new_line=string, needle="--post_deployment"
        )

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)

    return result


def execute_post_deployment_script(
    component: Component,
    component_id: str,
    instance_execution_id: str,
    db_config: DbConfig,
) -> None:
    """Execute SQL for post‑deployment scripts of a component."""

    sql = generate_post_deployment_script(
        component=component,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
