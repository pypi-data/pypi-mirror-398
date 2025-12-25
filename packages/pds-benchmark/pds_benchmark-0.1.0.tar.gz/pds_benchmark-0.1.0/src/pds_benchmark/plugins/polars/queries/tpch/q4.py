from datetime import date
from typing import Any

import polars as pl


def q(
    lineitem: pl.LazyFrame,
    orders: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = date(1993, 7, 1)
    var2 = date(1993, 10, 1)

    return (
        # SQL EXISTS translates to semi join in Polars API
        orders.join(
            lineitem.filter(pl.col("l_commitdate") < pl.col("l_receiptdate")),
            left_on="o_orderkey",
            right_on="l_orderkey",
            how="semi",
        )
        .filter(pl.col("o_orderdate").is_between(var1, var2, closed="left"))
        .group_by("o_orderpriority")
        .agg(pl.len().alias("order_count"))
        .sort("o_orderpriority")
    )
