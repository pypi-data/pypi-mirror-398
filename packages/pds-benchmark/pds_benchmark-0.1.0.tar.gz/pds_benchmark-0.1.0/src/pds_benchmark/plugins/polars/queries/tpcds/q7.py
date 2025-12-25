import polars as pl


def q(
    store_sales: pl.LazyFrame,
    item: pl.LazyFrame,
    customer_demographics: pl.LazyFrame,
    promotion: pl.LazyFrame,
    date_dim: pl.LazyFrame,
):
    return (
        store_sales.join(date_dim, left_on="ss_sold_date_sk", right_on="d_date_sk")
        .join(item, left_on="ss_item_sk", right_on="i_item_sk")
        .join(customer_demographics, left_on="ss_cdemo_sk", right_on="cd_demo_sk")
        .join(promotion, left_on="ss_promo_sk", right_on="p_promo_sk")
        .filter(
            pl.col("cd_gender") == "M",
            pl.col("cd_marital_status") == "S",
            pl.col("cd_education_status") == "College",
            pl.col("d_year") == 2000,
            (pl.col("p_channel_email") == "N") | (pl.col("p_channel_event") == "N"),
        )
        .group_by(pl.col("i_item_id"))
        .agg(
            [
                pl.col("ss_quantity").cast(pl.Float64).mean().alias("agg1"),
                pl.col("ss_list_price").cast(pl.Float64).mean().alias("agg2"),
                pl.col("ss_coupon_amt").cast(pl.Float64).mean().alias("agg3"),
                pl.col("ss_sales_price").cast(pl.Float64).mean().alias("agg4"),
            ],
        )
        .sort(by="i_item_id")
        .limit(100)
    )
