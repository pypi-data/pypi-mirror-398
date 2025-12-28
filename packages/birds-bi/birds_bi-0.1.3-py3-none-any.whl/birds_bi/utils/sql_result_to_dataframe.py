from __future__ import annotations

from typing import Any

import pandas as pd


def sql_result_to_dataframe(
    sql_result: dict[str, Any],
) -> pd.DataFrame | list[pd.DataFrame]:
    """Convert the raw ``dict`` structure from :func:`execute_sql` into DataFrames.

    - No result sets  -> empty DataFrame
    - One result set  -> single DataFrame
    - Many result sets -> list of DataFrames
    """

    result_sets = sql_result.get("result_sets", [])

    dataframes: list[pd.DataFrame] = []
    for rs in result_sets:
        df = pd.DataFrame(
            data=rs.get("rows", []),
            columns=rs.get("columns", []),
        )
        dataframes.append(df)

    if not dataframes:
        return pd.DataFrame()  # empty result
    if len(dataframes) == 1:
        return dataframes[0]

    return dataframes
