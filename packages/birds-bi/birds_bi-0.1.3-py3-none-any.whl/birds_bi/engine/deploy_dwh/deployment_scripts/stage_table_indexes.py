from birds_bi.repo.component import Component

TEMPLATE = """
declare @stage_table_indexes dbo.table_indexes
--stage_table_indexes

exec meta.add_all_stage_indexes @instance_id=1,@table_indexes=@stage_table_indexes,@debug=0,@instance_execution_id=@instance_execution_id
"""


def generate_indexes_script(component: Component) -> str:  # noqa: ARG001
    """Return the static SQL template for stage table indexes."""

    return TEMPLATE
