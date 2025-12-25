from typing import Any

import polars as pl

Q_NUM = 16


def q(
    partsupp: pl.LazyFrame,
    supplier: pl.LazyFrame,
    part: pl.LazyFrame,
    **kwargs: Any,
) -> pl.LazyFrame:
    var1 = "Brand#45"

    supplier = supplier.filter(
        pl.col("s_comment").str.contains(".*Customer.*Complaints.*"),
    ).select(pl.col("s_suppkey"), pl.col("s_suppkey").alias("ps_suppkey"))

    return (
        part.join(partsupp, left_on="p_partkey", right_on="ps_partkey")
        .filter(pl.col("p_brand") != var1)
        .filter(pl.col("p_type").str.contains("MEDIUM POLISHED*").not_())
        .filter(pl.col("p_size").is_in([49, 14, 23, 45, 19, 3, 36, 9]))
        .join(supplier, left_on="ps_suppkey", right_on="s_suppkey", how="left")
        .filter(pl.col("ps_suppkey_right").is_null())
        .group_by("p_brand", "p_type", "p_size")
        .agg(pl.col("ps_suppkey").n_unique().alias("supplier_cnt"))
        .sort(
            by=["supplier_cnt", "p_brand", "p_type", "p_size"],
            descending=[True, False, False, False],
        )
    )
