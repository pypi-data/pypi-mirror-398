from datetime import date
from typing import Any

import polars as pl


def q(
    lineitem: pl.LazyFrame,
    part: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = date(1995, 9, 1)
    var2 = date(1995, 10, 1)

    return (
        lineitem.join(part, left_on="l_partkey", right_on="p_partkey")
        .filter(pl.col("l_shipdate").is_between(var1, var2, closed="left"))
        .select(
            (
                100.00
                * pl.when(pl.col("p_type").str.contains("PROMO*"))
                .then(pl.col("l_extendedprice") * (1 - pl.col("l_discount")))
                .otherwise(0)
                .sum()
                / (pl.col("l_extendedprice") * (1 - pl.col("l_discount"))).sum()
            )
            .round(2)
            .alias("promo_revenue"),
        )
    )
