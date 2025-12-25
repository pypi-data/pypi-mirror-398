import polars as pl


def q(
    customer: pl.LazyFrame,
    store_sales: pl.LazyFrame,
    date_dim: pl.LazyFrame,
    catalog_sales: pl.LazyFrame,
    web_sales: pl.LazyFrame,
):
    return (
        pl.concat(
            [
                store_sales.join(
                    customer,
                    left_on="ss_customer_sk",
                    right_on="c_customer_sk",
                )
                .join(date_dim, left_on="ss_sold_date_sk", right_on="d_date_sk")
                .filter(pl.col("d_year").is_in([2001, 2002]))
                .select(
                    [
                        pl.col("c_customer_id"),
                        pl.col("c_first_name"),
                        pl.col("c_last_name"),
                        pl.col("c_preferred_cust_flag"),
                        pl.col("d_year"),
                        (
                            (
                                pl.col("ss_ext_list_price")
                                - pl.col("ss_ext_wholesale_cost")
                                - pl.col("ss_ext_discount_amt")
                                + pl.col("ss_ext_sales_price")
                            )
                            / 2
                        ).alias("profit"),
                        pl.lit("s").alias("channel"),
                    ],
                ),
                catalog_sales.join(
                    customer,
                    left_on="cs_bill_customer_sk",
                    right_on="c_customer_sk",
                )
                .join(date_dim, left_on="cs_sold_date_sk", right_on="d_date_sk")
                .filter(pl.col("d_year").is_in([2001, 2002]))
                .select(
                    [
                        pl.col("c_customer_id"),
                        pl.col("c_first_name"),
                        pl.col("c_last_name"),
                        pl.col("c_preferred_cust_flag"),
                        pl.col("d_year"),
                        (
                            (
                                pl.col("cs_ext_list_price")
                                - pl.col("cs_ext_wholesale_cost")
                                - pl.col("cs_ext_discount_amt")
                                + pl.col("cs_ext_sales_price")
                            )
                            / 2
                        ).alias("profit"),
                        pl.lit("c").alias("channel"),
                    ],
                ),
                web_sales.join(
                    customer,
                    left_on="ws_bill_customer_sk",
                    right_on="c_customer_sk",
                )
                .join(date_dim, left_on="ws_sold_date_sk", right_on="d_date_sk")
                .filter(pl.col("d_year").is_in([2001, 2002]))
                .select(
                    [
                        pl.col("c_customer_id"),
                        pl.col("c_first_name"),
                        pl.col("c_last_name"),
                        pl.col("c_preferred_cust_flag"),
                        pl.col("d_year"),
                        (
                            (
                                pl.col("ws_ext_list_price")
                                - pl.col("ws_ext_wholesale_cost")
                                - pl.col("ws_ext_discount_amt")
                                + pl.col("ws_ext_sales_price")
                            )
                            / 2
                        ).alias("profit"),
                        pl.lit("w").alias("channel"),
                    ],
                ),
            ],
        )
        .group_by(
            [
                "c_customer_id",
                "c_first_name",
                "c_last_name",
                "c_preferred_cust_flag",
                "channel",
                "d_year",
            ],
        )
        .agg([pl.col("profit").sum().alias("year_total")])
        .sort(["c_customer_id", "channel", "d_year"])
        .with_columns(
            [
                pl.col("year_total")
                .shift(1)
                .over(["c_customer_id", "channel"])
                .alias("prev_total"),
            ],
        )
        .filter(
            (pl.col("d_year") == 2002)
            & (pl.col("prev_total") > 0)
            & (pl.col("year_total") > 0),
        )
        .with_columns(
            [(pl.col("year_total") / pl.col("prev_total")).alias("growth_ratio")],
        )
        .group_by(
            ["c_customer_id", "c_first_name", "c_last_name", "c_preferred_cust_flag"],
        )
        .agg(
            [
                pl.col("growth_ratio")
                .filter(pl.col("channel") == "s")
                .first()
                .alias("store_growth"),
                pl.col("growth_ratio")
                .filter(pl.col("channel") == "c")
                .first()
                .alias("catalog_growth"),
                pl.col("growth_ratio")
                .filter(pl.col("channel") == "w")
                .first()
                .alias("web_growth"),
            ],
        )
        .filter(
            pl.col("store_growth").is_not_null(),
            pl.col("catalog_growth").is_not_null(),
            pl.col("web_growth").is_not_null(),
            (pl.col("catalog_growth") > pl.col("store_growth")),
            (pl.col("catalog_growth") > pl.col("web_growth")),
        )
        .select(
            [
                pl.col("c_customer_id").alias("customer_id"),
                pl.col("c_first_name").alias("customer_first_name"),
                pl.col("c_last_name").alias("customer_last_name"),
                pl.col("c_preferred_cust_flag").alias("customer_preferred_cust_flag"),
            ],
        )
        .sort(
            [
                "customer_id",
                "customer_first_name",
                "customer_last_name",
                "customer_preferred_cust_flag",
            ],
        )
        .limit(100)
    )
