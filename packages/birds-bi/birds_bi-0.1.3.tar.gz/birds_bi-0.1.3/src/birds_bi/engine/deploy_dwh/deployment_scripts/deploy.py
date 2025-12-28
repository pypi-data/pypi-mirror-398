from typing import Literal

from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string

TEMPLATE = """
DECLARE @rc INT;
exec audit.log_message @message_type=N'I',@source=N'Unknown',@message=N'${message}',@instance_execution_id=${instance_execution_id},@component_execution_id=${component_execution_id}

exec @rc = dwh.deploy @deploy_action=N'${deploy_action}',@component_id=${component_id},@instance_execution_id=${instance_execution_id}
select @rc as return_code
"""


def generate_deploy_script(
    deploy_action: Literal["components", "staging"],
    component_id: str,
    instance_execution_id: str,
    component_execution_id: str,
) -> str:
    result = TEMPLATE

    if deploy_action == "components":
        message = "Deploying DWH Components..."
        result = result.replace("${message}", message)
        result = result.replace("${deploy_action}", deploy_action)
    elif deploy_action == "staging":
        message = "Deploying stage tables for DWH."
        result = result.replace("${message}", message)
        result = result.replace("${deploy_action}", deploy_action)

    result = result.replace("${component_id}", component_id)
    result = result.replace("${instance_execution_id}", instance_execution_id)
    result = result.replace("${component_execution_id}", component_execution_id)

    return result


def execute_deploy_script(
    deploy_action: Literal["components", "staging"],
    component_id: str,
    instance_execution_id: str,
    component_execution_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_deploy_script(
        deploy_action=deploy_action,
        component_id=component_id,
        instance_execution_id=instance_execution_id,
        component_execution_id=component_execution_id,
    )

    result = execute_sql_string(db_config=db_config, sql=sql)

    df = result.result_sets[0].dataframe

    if df["return_code"][0] != 0:
        raise Exception("deployment failed of component.")
