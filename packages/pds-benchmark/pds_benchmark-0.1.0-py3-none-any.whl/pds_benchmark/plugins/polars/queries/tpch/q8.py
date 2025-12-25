from datetime import date
from typing import Any

import polars as pl


def q(
    customer: pl.LazyFrame,
    lineitem: pl.LazyFrame,
    nation: pl.LazyFrame,
    orders: pl.LazyFrame,
    supplier: pl.LazyFrame,
    region: pl.LazyFrame,
    part: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = "BRAZIL"
    var2 = "AMERICA"
    var3 = "ECONOMY ANODIZED STEEL"
    var4 = date(1995, 1, 1)
    var5 = date(1996, 12, 31)

    n1 = nation.select("n_nationkey", "n_regionkey")
    n2 = nation.select("n_nationkey", "n_name")

    return (
        part.join(lineitem, left_on="p_partkey", right_on="l_partkey")
        .join(supplier, left_on="l_suppkey", right_on="s_suppkey")
        .join(orders, left_on="l_orderkey", right_on="o_orderkey")
        .join(customer, left_on="o_custkey", right_on="c_custkey")
        .join(n1, left_on="c_nationkey", right_on="n_nationkey")
        .join(region, left_on="n_regionkey", right_on="r_regionkey")
        .filter(pl.col("r_name") == var2)
        .join(n2, left_on="s_nationkey", right_on="n_nationkey")
        .filter(pl.col("o_orderdate").is_between(var4, var5))
        .filter(pl.col("p_type") == var3)
        .select(
            pl.col("o_orderdate").dt.year().alias("o_year"),
            (pl.col("l_extendedprice") * (1 - pl.col("l_discount"))).alias("volume"),
            pl.col("n_name").alias("nation"),
        )
        .with_columns(
            pl.when(pl.col("nation") == var1)
            .then(pl.col("volume"))
            .otherwise(0)
            .alias("_tmp"),
        )
        .group_by("o_year")
        .agg((pl.sum("_tmp") / pl.sum("volume")).round(2).alias("mkt_share"))
        .sort("o_year")
    )
