from typing import Literal

from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component

TEMPLATE = """
exec audit.log_component_stop @component_execution_id=${component_execution_id},@status=N'${status}',@inserted=NULL,@updated=NULL,@deleted=NULL

exec audit.log_instance_stop @instance_execution_id=${instance_execution_id},@status=N'${status}'

exec audit.log_instance_stop @instance_execution_id=${instance_execution_id},@status=N'${status}'
"""


def generate_stop_logging_script(
    component: Component,
    instance_execution_id: str,
    component_execution_id: str,
    status: Literal["S", "F"],
) -> str:
    result = TEMPLATE
    result = result.replace("${category}", component.category)
    result = result.replace("${component}", component.component)
    result = result.replace("${status}", status)
    result = result.replace("${instance_execution_id}", instance_execution_id)
    result = result.replace("${component_execution_id}", component_execution_id)
    return result


def execute_stop_logging_script(
    component: Component,
    instance_execution_id: str,
    component_execution_id: str,
    status: Literal["S", "F"],
    db_config: DbConfig,
) -> None:

    sql = generate_stop_logging_script(
        component=component,
        instance_execution_id=instance_execution_id,
        component_execution_id=component_execution_id,
        status=status,
    )

    execute_sql_string(db_config=db_config, sql=sql)
