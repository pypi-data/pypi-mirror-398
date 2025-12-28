from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component

TEMPLATE = """
declare @component_id int
exec meta.add_dwh_component @instance_id=1
,@category=${Category}
,@name=${ComponentName}
,@db_object=${DbObject}
,@load_type=${LoadType}
,@manual_mode=${ManualMode}
,@instance_execution_id=${InstanceExecutionId}
,@component_id=@component_id 
output
select @component_id as component_id
"""


def generate_add_dwh_component_script(
    component: Component, instance_execution_id: str, load_type: str
) -> str:
    result = TEMPLATE
    result = result.replace("${Category}", f"N'{component.category}'")
    result = result.replace("${ComponentName}", f"N'{component.component}'")
    result = result.replace("${DbObject}", f"N'{component}'")
    result = result.replace("${Type}", f"N'{component.process_type}'")
    result = result.replace("${LoadType}", str(load_type))
    result = result.replace("${ProcessType}", f"N'{component.process_type}'")
    result = result.replace("${ManualMode}", "1" if component.manual_mode else "0")
    result = result.replace("${InstanceExecutionId}", instance_execution_id)
    return result


def execute_add_dwh_component_script(
    component: Component,
    instance_execution_id: str,
    load_type: str,
    db_config: DbConfig,
) -> str:
    sql = generate_add_dwh_component_script(
        component=component,
        instance_execution_id=instance_execution_id,
        load_type=load_type,
    )

    result = execute_sql_string(db_config=db_config, sql=sql)

    df = result.result_sets[0].dataframe

    return str(df["component_id"][0])
