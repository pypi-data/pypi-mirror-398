from typing import Any

import duckdb


def q(lineitem: str, **kwargs: Any):
    query_str = f"""
    SELECT
        sum(l_extendedprice * l_discount) AS revenue
    FROM
        {lineitem}
    WHERE
        l_shipdate >= CAST('1994-01-01' AS date)
        AND l_shipdate < CAST('1995-01-01' AS date)
        AND l_discount BETWEEN 0.05
        AND 0.07
        AND l_quantity < 24;
    """

    return duckdb.sql(query_str)
