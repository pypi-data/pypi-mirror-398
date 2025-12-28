from typing import Literal

from birds_bi.db.models import DbConfig
from birds_bi.engine.deploy_dwh.deployment_scripts import (
    execute_add_dwh_component_script,
    execute_deploy_script,
    execute_dwh_deployment_script,
    execute_fact_dimension_joins_script,
    execute_manual_mode_script,
    execute_post_deployment_script,
    execute_pre_deployment_script,
    execute_query_and_aliases_script,
    execute_query_columns_script,
    execute_start_logging_script,
    execute_stop_logging_script,
    execute_table_indexes_script,
    execute_validate_columns_script,
    execute_validate_query_script,
)
from birds_bi.repo.component import Component


def deploy_component(component: Component, db_config: DbConfig) -> None:

    load_type = component.load_type
    error = None
    status: Literal["S", "F"] = "S"

    if component.manual_mode is False:
        execute_validate_query_script(
            component=component,
            db_config=db_config,
        )
    if component.category == "dim" and component.manual_mode is False:
        load_type = execute_validate_columns_script(
            component=component,
            db_config=db_config,
        )

    logging = execute_start_logging_script(
        component=component,
        db_config=db_config,
    )
    try:
        component_id = execute_add_dwh_component_script(
            component=component,
            load_type=load_type,
            instance_execution_id=logging.instance_execution_id,
            db_config=db_config,
        )

        if component.table_indexes:
            execute_table_indexes_script(
                component=component,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if component.manual_mode:
            execute_manual_mode_script(
                component=component,
                instance_execution_id=logging.instance_execution_id,
                component_id=component_id,
                db_config=db_config,
            )

        if not component.manual_mode:
            execute_query_and_aliases_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if not component.manual_mode:
            execute_query_columns_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if component.category == "fact" and not component.manual_mode:
            execute_fact_dimension_joins_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if component.manual_mode:
            execute_dwh_deployment_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if component.pre_deployment_scripts:
            execute_pre_deployment_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        if component.post_deployment_scripts:
            execute_post_deployment_script(
                component=component,
                component_id=component_id,
                instance_execution_id=logging.instance_execution_id,
                db_config=db_config,
            )

        execute_deploy_script(
            component_execution_id=logging.component_execution_id,
            component_id=component_id,
            instance_execution_id=logging.instance_execution_id,
            deploy_action="components",
            db_config=db_config,
        )

    except Exception as e:
        status = "F"
        error = e

    execute_stop_logging_script(
        component=component,
        instance_execution_id=logging.instance_execution_id,
        component_execution_id=logging.component_execution_id,
        status=status,
        db_config=db_config,
    )

    if error:
        raise Exception(error)
