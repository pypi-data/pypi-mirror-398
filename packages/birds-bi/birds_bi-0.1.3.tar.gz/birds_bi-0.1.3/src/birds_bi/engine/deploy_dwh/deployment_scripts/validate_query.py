from birds_bi.db.models import DbConfig
from birds_bi.db.sql_execution import execute_sql_string
from birds_bi.repo.component import Component
from birds_bi.utils.insert_line import var_insert_line

TEMPLATE = """
declare @p1 meta.dwh_queries_table
--queries

declare @p2 meta.dwh_aliases_table

exec meta.validate_all_queries @queries=@p1,@aliases=@p2
"""


def generate_validate_query_script(component: Component) -> str:
    """Generate SQL that validates all queries for a component."""

    if component.manual_mode:
        return "--Component is manual mode so no validating query."

    result = TEMPLATE
    for query_information in component.query_information:
        string = (
            "insert into @p1 values("
            f"{query_information.sequence},"
            f"N'{query_information.name}',"
            f"N'{(query_information.query or "").replace("'", "''")}')\n"
        )
        result = var_insert_line(
            text=result,
            new_line=string,
            needle="--queries",
        )
    return result


def execute_validate_query_script(
    component: Component,
    db_config: DbConfig,
) -> None:
    """Execute SQL that validates all queries for a component."""

    sql = generate_validate_query_script(component=component)

    result = execute_sql_string(db_config=db_config, sql=sql)

    df = result.result_sets[0].dataframe

    if df.empty is False:
        raise Exception(df["error_message"][0])
