from datetime import date
from typing import Any

import polars as pl


def q(
    lineitem: pl.LazyFrame,
    orders: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = "MAIL"
    var2 = "SHIP"
    var3 = date(1994, 1, 1)
    var4 = date(1995, 1, 1)

    return (
        orders.join(lineitem, left_on="o_orderkey", right_on="l_orderkey")
        .filter(pl.col("l_shipmode").is_in([var1, var2]))
        .filter(pl.col("l_commitdate") < pl.col("l_receiptdate"))
        .filter(pl.col("l_shipdate") < pl.col("l_commitdate"))
        .filter(pl.col("l_receiptdate").is_between(var3, var4, closed="left"))
        .with_columns(
            pl.when(pl.col("o_orderpriority").is_in(["1-URGENT", "2-HIGH"]))
            .then(1)
            .otherwise(0)
            .alias("high_line_count"),
            pl.when(pl.col("o_orderpriority").is_in(["1-URGENT", "2-HIGH"]).not_())
            .then(1)
            .otherwise(0)
            .alias("low_line_count"),
        )
        .group_by("l_shipmode")
        .agg(pl.col("high_line_count").sum(), pl.col("low_line_count").sum())
        .sort("l_shipmode")
    )
