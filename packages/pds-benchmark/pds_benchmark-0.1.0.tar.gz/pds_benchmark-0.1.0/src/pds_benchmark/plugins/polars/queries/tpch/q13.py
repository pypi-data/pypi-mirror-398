from typing import Any

import polars as pl


def q(
    customer: pl.LazyFrame,
    orders: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = "special"
    var2 = "requests"

    orders = orders.filter(pl.col("o_comment").str.contains(f"{var1}.*{var2}").not_())
    return (
        customer.join(orders, left_on="c_custkey", right_on="o_custkey", how="left")
        .group_by("c_custkey")
        .agg(pl.col("o_orderkey").count().alias("c_count"))
        .group_by("c_count")
        .len()
        .select(pl.col("c_count"), pl.col("len").alias("custdist"))
        .sort(by=["custdist", "c_count"], descending=[True, True])
    )
