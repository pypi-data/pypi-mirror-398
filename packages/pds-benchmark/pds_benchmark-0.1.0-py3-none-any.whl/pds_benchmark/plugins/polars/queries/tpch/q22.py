from typing import Any

import polars as pl


def q(
    customer: pl.LazyFrame,
    orders: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    q1 = (
        customer.with_columns(pl.col("c_phone").str.slice(0, 2).alias("cntrycode"))
        .filter(pl.col("cntrycode").str.contains("13|31|23|29|30|18|17"))
        .select("c_acctbal", "c_custkey", "cntrycode")
    )

    q2 = q1.filter(pl.col("c_acctbal") > 0.0).select(
        pl.col("c_acctbal").mean().alias("avg_acctbal"),
    )

    q3 = orders.select(pl.col("o_custkey").unique()).with_columns(
        pl.col("o_custkey").alias("c_custkey"),
    )

    return (
        q1.join(q3, on="c_custkey", how="left")
        .filter(pl.col("o_custkey").is_null())
        .join(q2, how="cross")
        .filter(pl.col("c_acctbal") > pl.col("avg_acctbal"))
        .group_by("cntrycode")
        .agg(
            pl.col("c_acctbal").count().alias("numcust"),
            pl.col("c_acctbal").sum().round(2).alias("totacctbal"),
        )
        .sort("cntrycode")
    )
