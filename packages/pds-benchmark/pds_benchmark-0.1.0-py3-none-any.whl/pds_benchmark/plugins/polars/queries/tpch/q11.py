from typing import Any

import polars as pl


def q(
    nation: pl.LazyFrame,
    partsupp: pl.LazyFrame,
    supplier: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = "GERMANY"
    var2 = 0.0001

    q1 = (
        partsupp.join(supplier, left_on="ps_suppkey", right_on="s_suppkey")
        .join(nation, left_on="s_nationkey", right_on="n_nationkey")
        .filter(pl.col("n_name") == var1)
    )
    q2 = q1.select(
        ((pl.col("ps_supplycost") * pl.col("ps_availqty")).sum() * var2)
        .round(2)
        .cast(pl.Float64)
        .alias("tmp"),
    )

    return (
        q1.group_by("ps_partkey")
        .agg(
            (pl.col("ps_supplycost") * pl.col("ps_availqty"))
            .sum()
            .round(2)
            .cast(pl.Float64)
            .alias("value"),
        )
        .join(q2, how="cross")
        .filter(pl.col("value") > pl.col("tmp"))
        .select("ps_partkey", "value")
        .sort("value", descending=True)
    )
