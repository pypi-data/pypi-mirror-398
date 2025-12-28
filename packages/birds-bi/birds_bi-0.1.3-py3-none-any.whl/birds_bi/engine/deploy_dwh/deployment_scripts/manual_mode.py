from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component


def generate_manual_mode_script(
    component: Component, instance_execution_id: str, component_id: str
) -> str:
    result = (
        "declare @procedure_id INT;"
        "exec meta.remove_all_dwh_component_load_procedures "
        "@instance_id=1"
        ",@component_id=${component_id}"
        ",@instance_execution_id=${instance_execution_id}\n"
    )

    for procedure in component.load_procedures:
        string = (
            f"exec meta.add_dwh_load_procedure "
            f"@component_id=${{component_id}}"
            f",@instance_execution_id=${{instance_execution_id}}"
            f",@db_object=N'{procedure.identifier}'"
            f",@process_sequence={procedure.sequence}"
            f", @procedure_id=@procedure_id\n"
        )
        result += string

    result = result.replace("${instance_execution_id}", instance_execution_id)
    result = result.replace("${component_id}", component_id)

    return result


def execute_manual_mode_script(
    component: Component,
    instance_execution_id: str,
    component_id: str,
    db_config: DbConfig,
) -> None:
    sql = generate_manual_mode_script(
        component=component,
        instance_execution_id=instance_execution_id,
        component_id=component_id,
    )

    execute_sql_string(db_config=db_config, sql=sql)
