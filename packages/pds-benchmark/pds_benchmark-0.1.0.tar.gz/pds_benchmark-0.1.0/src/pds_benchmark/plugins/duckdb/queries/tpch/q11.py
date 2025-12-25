from typing import Any

import duckdb


def q(nation: str, partsupp: str, supplier: str, **kwargs: Any):
    query_str = f"""
    SELECT
        ps_partkey,
        sum(ps_supplycost * ps_availqty) AS value
    FROM
        {partsupp},
        {supplier},
        {nation}
    WHERE
        ps_suppkey = s_suppkey
        AND s_nationkey = n_nationkey
        AND n_name = 'GERMANY'
    GROUP BY
        ps_partkey
    HAVING
        sum(ps_supplycost * ps_availqty) > (
            SELECT
                sum(ps_supplycost * ps_availqty) * 0.0001000000
            FROM
                {partsupp},
                {supplier},
                {nation}
            WHERE
                ps_suppkey = s_suppkey
                AND s_nationkey = n_nationkey
                AND n_name = 'GERMANY')
    ORDER BY
        value DESC;
    """
    return duckdb.sql(query_str)
