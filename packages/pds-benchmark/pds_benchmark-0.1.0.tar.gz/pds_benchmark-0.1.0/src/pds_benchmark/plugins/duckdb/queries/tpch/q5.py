from typing import Any

import duckdb


def q(
    customer: str,
    lineitem: str,
    nation: str,
    orders: str,
    region: str,
    supplier: str,
    **kwargs: Any,
):
    query_str = f"""
    SELECT
        n_name,
        sum(l_extendedprice * (1 - l_discount)) AS revenue
    FROM
        {customer},
        {orders},
        {lineitem},
        {supplier},
        {nation},
        {region}
    WHERE
        c_custkey = o_custkey
        AND l_orderkey = o_orderkey
        AND l_suppkey = s_suppkey
        AND c_nationkey = s_nationkey
        AND s_nationkey = n_nationkey
        AND n_regionkey = r_regionkey
        AND r_name = 'ASIA'
        AND o_orderdate >= CAST('1994-01-01' AS date)
        AND o_orderdate < CAST('1995-01-01' AS date)
    GROUP BY
        n_name
    ORDER BY
        revenue DESC;
    """

    return duckdb.sql(query_str)
