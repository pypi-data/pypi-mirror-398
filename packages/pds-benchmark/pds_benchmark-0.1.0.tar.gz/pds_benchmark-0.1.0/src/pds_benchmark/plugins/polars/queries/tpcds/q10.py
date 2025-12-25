import polars as pl


def q(
    date_dim: pl.LazyFrame,
    store_sales: pl.LazyFrame,
    web_sales: pl.LazyFrame,
    catalog_sales: pl.LazyFrame,
    customer: pl.LazyFrame,
    customer_address: pl.LazyFrame,
    customer_demographics: pl.LazyFrame,
):
    date_filter = date_dim.filter(
        (pl.col("d_year") == 2002),
        (pl.col("d_moy").is_between(1, 1 + 3)),
    )

    return (
        customer.join(
            customer_address,
            left_on="c_current_addr_sk",
            right_on="ca_address_sk",
        )
        .filter(
            pl.col("ca_county").is_in(
                [
                    "Rush County",
                    "Toole County",
                    "Jefferson County",
                    "Dona Ana County",
                    "La Porte County",
                ],
            ),
        )
        .join(
            customer_demographics,
            left_on="c_current_cdemo_sk",
            right_on="cd_demo_sk",
        )
        .join(
            store_sales.join(
                date_filter,
                left_on="ss_sold_date_sk",
                right_on="d_date_sk",
            ).select(pl.col("ss_customer_sk")),
            left_on="c_customer_sk",
            right_on="ss_customer_sk",
            how="semi",
        )
        .join(
            pl.concat(
                [
                    web_sales.join(
                        date_filter,
                        left_on="ws_sold_date_sk",
                        right_on="d_date_sk",
                    )
                    .select("ws_bill_customer_sk")
                    .rename({"ws_bill_customer_sk": "online_customer_sk"}),
                    catalog_sales.join(
                        date_filter,
                        left_on="cs_sold_date_sk",
                        right_on="d_date_sk",
                    )
                    .select("cs_ship_customer_sk")
                    .rename({"cs_ship_customer_sk": "online_customer_sk"}),
                ],
            ),
            left_on="c_customer_sk",
            right_on="online_customer_sk",
            how="semi",
        )
        .group_by(
            [
                pl.col("cd_gender"),
                pl.col("cd_marital_status"),
                pl.col("cd_education_status"),
                pl.col("cd_purchase_estimate"),
                pl.col("cd_credit_rating"),
                pl.col("cd_dep_count"),
                pl.col("cd_dep_employed_count"),
                pl.col("cd_dep_college_count"),
            ],
        )
        .agg([pl.len().alias("count")])
        .select(
            [
                "cd_gender",
                "cd_marital_status",
                "cd_education_status",
                pl.col("count").alias("cnt1"),
                "cd_purchase_estimate",
                pl.col("count").alias("cnt2"),
                "cd_credit_rating",
                pl.col("count").alias("cnt3"),
                "cd_dep_count",
                pl.col("count").alias("cnt4"),
                "cd_dep_employed_count",
                pl.col("count").alias("cnt5"),
                "cd_dep_college_count",
                pl.col("count").alias("cnt6"),
            ],
        )
        .sort(
            [
                "cd_gender",
                "cd_marital_status",
                "cd_education_status",
                "cd_purchase_estimate",
                "cd_credit_rating",
                "cd_dep_count",
                "cd_dep_employed_count",
                "cd_dep_college_count",
            ],
        )
        .limit(100)
    )
