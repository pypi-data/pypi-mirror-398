from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @p2 meta.dwh_query_columns_table
--query_columns

declare @p3 int
set @p3=0
declare @id int
select @id = component_id from meta.dwh_components where name = 'dim${component}'
exec meta.validate_deploy_component_changes @component_id=@id,@query_columns=@p2,@requires_redeploy=@p3 output
select @p3 as load_type
"""


def generate_validate_columns_script(component: Component) -> str:
    """Generate SQL that validates whether a component requires redeploy."""

    result = TEMPLATE.replace("${component}", component.component)

    for column in component.columns:
        line = (
            "insert into @p2 values("
            f"{column.index},"
            f"N'{column.column_name}',"
            f"N'{column.data_type_full}',"
            f"N'{column.data_type_full}',"
            "N'N')\n"
        )
        result = var_insert_line(text=result, new_line=line, needle="--query_columns")

    return result


def execute_validate_columns_script(
    component: Component,
    db_config: DbConfig,
) -> str:

    sql = generate_validate_columns_script(component=component)

    result = execute_sql_string(db_config=db_config, sql=sql)

    df = result.result_sets[1].dataframe

    return str(df["load_type"][0])
