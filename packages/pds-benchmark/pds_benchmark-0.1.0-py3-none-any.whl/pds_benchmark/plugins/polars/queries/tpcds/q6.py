import polars as pl


def q(
    customer_address: pl.LazyFrame,
    store_sales: pl.LazyFrame,
    customer: pl.LazyFrame,
    date_dim: pl.LazyFrame,
    item: pl.LazyFrame,
):
    return (
        customer_address.join(
            customer,
            left_on="ca_address_sk",
            right_on="c_current_addr_sk",
        )
        .join(store_sales, left_on="c_customer_sk", right_on="ss_customer_sk")
        .join(date_dim, left_on="ss_sold_date_sk", right_on="d_date_sk")
        .join(item, left_on="ss_item_sk", right_on="i_item_sk")
        .join(
            date_dim.filter(pl.col("d_year") == 2001, pl.col("d_moy") == 1),
            on="d_month_seq",
            how="semi",
        )
        .join(
            item.join(
                item.group_by(pl.col("i_category")).agg(
                    pl.col("i_current_price")
                    .cast(pl.Float64)
                    .mean()
                    .alias("avg_price_cat"),
                ),
                on="i_category",
                how="left",
            ).filter(pl.col("i_current_price") > 1.2 * pl.col("avg_price_cat")),
            left_on="ss_item_sk",
            right_on="i_item_sk",
        )
        .group_by(pl.col("ca_state"))
        .agg(pl.len().alias("cnt"))
        .filter(pl.col("cnt") >= 10)
        .sort(by=["cnt", "ca_state"], descending=False, nulls_last=False)
        .limit(100)
    )
