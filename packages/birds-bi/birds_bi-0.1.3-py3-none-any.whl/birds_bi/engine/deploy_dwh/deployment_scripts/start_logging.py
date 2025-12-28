from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.engine.deploy_dwh.models import StartLogging
from birds_bi.repo.component import Component

TEMPLATE = """
declare @p3 int
declare @p5 int
declare @instanceexecutionid int
declare @componentexecutionid int

exec audit.log_instance_start @instance_id=1,@user_name=N'deployagent',@instance_execution_id= @p3 output

select @instanceexecutionid = @p3

exec audit.log_component_start @instance_execution_id=@instanceexecutionid,@action=N'D',@component_database=N'${category}',@component_name=N'${category}.${component}',@component_execution_id=@p5 output

select @componentexecutionid = @p5

exec audit.log_message @message_type=N'I',@source=N'Unknown',@message=N'Configuring metadata...',@instance_execution_id=@instanceexecutionid ,@component_execution_id=@componentexecutionid 

SELECT @instanceexecutionid AS instanceexecutionid
, @componentexecutionid AS componentexecutionid
"""


def generate_start_logging_script(component: Component) -> str:
    result = TEMPLATE
    result = result.replace("${category}", component.category)
    result = result.replace("${component}", component.component)
    return result


def execute_start_logging_script(
    component: Component,
    db_config: DbConfig,
) -> StartLogging:
    sql = generate_start_logging_script(component=component)

    result = execute_sql_string(db_config=db_config, sql=sql)

    df = result.result_sets[0].dataframe

    return StartLogging(
        component_execution_id=df["componentexecutionid"][0],
        instance_execution_id=df["instanceexecutionid"][0],
    )
