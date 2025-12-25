import polars as pl


def q(store_sales: pl.LazyFrame):
    return pl.concat(
        [
            store_sales.filter(pl.col("ss_quantity").is_between(1, 20)).select(
                pl.when(pl.len() > 74129)
                .then(pl.mean("ss_ext_discount_amt"))
                .otherwise(pl.mean("ss_net_paid"))
                .alias("bucket1"),
            ),
            store_sales.filter(pl.col("ss_quantity").is_between(21, 40)).select(
                pl.when(pl.len() > 122840)
                .then(pl.mean("ss_ext_discount_amt"))
                .otherwise(pl.mean("ss_net_paid"))
                .alias("bucket2"),
            ),
            store_sales.filter(pl.col("ss_quantity").is_between(41, 60)).select(
                pl.when(pl.len() > 56580)
                .then(pl.mean("ss_ext_discount_amt"))
                .otherwise(pl.mean("ss_net_paid"))
                .alias("bucket3"),
            ),
            store_sales.filter(pl.col("ss_quantity").is_between(61, 80)).select(
                pl.when(pl.len() > 10097)
                .then(pl.mean("ss_ext_discount_amt"))
                .otherwise(pl.mean("ss_net_paid"))
                .alias("bucket4"),
            ),
            store_sales.filter(pl.col("ss_quantity").is_between(81, 100)).select(
                pl.when(pl.len() > 165306)
                .then(pl.mean("ss_ext_discount_amt"))
                .otherwise(pl.mean("ss_net_paid"))
                .alias("bucket5"),
            ),
        ],
        how="horizontal",
    )
