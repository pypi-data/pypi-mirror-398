from datetime import date

import polars as pl


def q(
    store_sales: pl.LazyFrame,
    store_returns: pl.LazyFrame,
    date_dim: pl.LazyFrame,
    store: pl.LazyFrame,
    catalog_sales: pl.LazyFrame,
    catalog_returns: pl.LazyFrame,
    catalog_page: pl.LazyFrame,
    web_sales: pl.LazyFrame,
    web_returns: pl.LazyFrame,
    web_site: pl.LazyFrame,
):
    DATE_MIN = date(2000, 8, 23)
    DATE_MAX = date(2000, 9, 6)

    s1 = store_sales.select(
        [
            pl.col("ss_store_sk").alias("store_sk"),
            pl.col("ss_sold_date_sk").alias("date_sk"),
            pl.col("ss_ext_sales_price").alias("sales_price"),
            pl.col("ss_net_profit").alias("profit"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("return_amt"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("net_loss"),
        ],
    )

    s2 = store_returns.select(
        [
            pl.col("sr_store_sk").alias("store_sk"),
            pl.col("sr_returned_date_sk").alias("date_sk"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("sales_price"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("profit"),
            pl.col("sr_return_amt").alias("return_amt"),
            pl.col("sr_net_loss").alias("net_loss"),
        ],
    )

    store_channel = (
        pl.concat([s1, s2])
        .join(
            date_dim.select([pl.col("d_date_sk"), pl.col("d_date")]),
            left_on="date_sk",
            right_on="d_date_sk",
        )
        .filter(pl.col("d_date") >= DATE_MIN, pl.col("d_date") <= DATE_MAX)
        .join(
            store.select([pl.col("s_store_sk"), pl.col("s_store_id")]),
            left_on="store_sk",
            right_on="s_store_sk",
        )
        .group_by(pl.col("s_store_id"))
        .agg(
            pl.col("sales_price").sum().alias("sales"),
            pl.col("profit").sum().alias("profit"),
            pl.col("return_amt").sum().alias("returns_"),
            pl.col("net_loss").sum().alias("profit_loss"),
        )
    ).select(
        [
            pl.lit("store_channel").alias("channel"),
            (pl.lit("store") + pl.col("s_store_id")).alias("id"),
            pl.col("sales"),
            pl.col("returns_"),
            (pl.col("profit") - pl.col("profit_loss")).alias("profit"),
        ],
    )

    c1 = catalog_sales.select(
        [
            pl.col("cs_catalog_page_sk").alias("page_sk"),
            pl.col("cs_sold_date_sk").alias("date_sk"),
            pl.col("cs_ext_sales_price").alias("sales_price"),
            pl.col("cs_net_profit").alias("profit"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("return_amt"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("net_loss"),
        ],
    )

    c2 = catalog_returns.select(
        [
            pl.col("cr_catalog_page_sk").alias("page_sk"),
            pl.col("cr_returned_date_sk").alias("date_sk"),
            # For the returns records, set sales_price and profit to 0
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("sales_price"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("profit"),
            pl.col("cr_return_amount").alias("return_amt"),
            pl.col("cr_net_loss").alias("net_loss"),
        ],
    )

    catalog_channel = (
        pl.concat([c1, c2])
        .join(
            date_dim.select([pl.col("d_date_sk"), pl.col("d_date")]),
            left_on="date_sk",
            right_on="d_date_sk",
        )
        .filter(pl.col("d_date") >= DATE_MIN, pl.col("d_date") <= DATE_MAX)
        .join(
            catalog_page.select(
                [pl.col("cp_catalog_page_sk"), pl.col("cp_catalog_page_id")],
            ),
            left_on="page_sk",
            right_on="cp_catalog_page_sk",
        )
        .group_by(pl.col("cp_catalog_page_id"))
        .agg(
            [
                pl.col("sales_price").sum().alias("sales"),
                pl.col("profit").sum().alias("profit"),
                pl.col("return_amt").sum().alias("returns_"),
                pl.col("net_loss").sum().alias("profit_loss"),
            ],
        )
        .select(
            [
                pl.lit("catalog channel").alias("channel"),
                (pl.lit("catalog_page") + pl.col("cp_catalog_page_id")).alias("id"),
                pl.col("sales"),
                pl.col("returns_"),
                (pl.col("profit") - pl.col("profit_loss")).alias("profit"),
            ],
        )
    )

    w1 = web_sales.select(
        [
            pl.col("ws_web_site_sk").alias("web_site_sk"),
            pl.col("ws_sold_date_sk").alias("date_sk"),
            pl.col("ws_ext_sales_price").alias("sales_price"),
            pl.col("ws_net_profit").alias("profit"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("return_amt"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("net_loss"),
        ],
    )

    w2 = web_returns.join(
        web_sales.select(
            [
                pl.col("ws_item_sk"),
                pl.col("ws_order_number"),
                pl.col("ws_web_site_sk"),
            ],
        ),
        left_on=["wr_item_sk", "wr_order_number"],
        right_on=["ws_item_sk", "ws_order_number"],
        how="left",
    ).select(
        [
            pl.col("ws_web_site_sk").alias("web_site_sk"),
            pl.col("wr_returned_date_sk").alias("date_sk"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("sales_price"),
            pl.lit(0).cast(pl.Decimal(None, 2)).alias("profit"),
            pl.col("wr_return_amt").alias("return_amt"),
            pl.col("wr_net_loss").alias("net_loss"),
        ],
    )

    web_channel = (
        pl.concat([w1, w2])
        .join(
            date_dim.select([pl.col("d_date_sk"), pl.col("d_date")]),
            left_on="date_sk",
            right_on="d_date_sk",
        )
        .filter(pl.col("d_date") >= DATE_MIN, pl.col("d_date") <= DATE_MAX)
        .join(
            web_site.select([pl.col("web_site_sk"), pl.col("web_site_id")]),
            on="web_site_sk",
        )
        .group_by(pl.col("web_site_id"))
        .agg(
            pl.col("sales_price").sum().alias("sales"),
            pl.col("profit").sum().alias("profit"),
            pl.col("return_amt").sum().alias("returns_"),
            pl.col("net_loss").sum().alias("profit_loss"),
        )
        .select(
            [
                pl.lit("web channel").alias("channel"),
                (pl.lit("web_site") + pl.col("web_site_id")).alias("id"),
                pl.col("sales"),
                pl.col("returns_"),
                (pl.col("profit") - pl.col("profit_loss")).alias("profit"),
            ],
        )
    )

    channels = pl.concat([store_channel, catalog_channel, web_channel])

    detail = channels.group_by(["channel", "id"]).agg(
        [
            pl.col("sales").cast(pl.Float64).sum().alias("sales"),
            pl.col("returns_").cast(pl.Float64).sum().alias("returns_"),
            pl.col("profit").cast(pl.Float64).sum().alias("profit"),
        ],
    )

    by_channel = (
        channels.group_by(["channel"])
        .agg(
            [
                pl.col("sales").cast(pl.Float64).sum().alias("sales"),
                pl.col("returns_").cast(pl.Float64).sum().alias("returns_"),
                pl.col("profit").cast(pl.Float64).sum().alias("profit"),
            ],
        )
        .select(
            [
                pl.col("channel"),
                pl.lit(None).alias("id"),
                pl.col("sales"),
                pl.col("returns_"),
                pl.col("profit"),
            ],
        )
    )

    total = channels.select(
        [
            pl.col("sales").cast(pl.Float64).sum().alias("sales"),
            pl.col("returns_").cast(pl.Float64).sum().alias("returns_"),
            pl.col("profit").cast(pl.Float64).sum().alias("profit"),
        ],
    ).select(
        [
            pl.lit(None).alias("channel"),
            pl.lit(None).alias("id"),
            pl.col("sales"),
            pl.col("returns_"),
            pl.col("profit"),
        ],
    )

    return (
        pl.concat([detail, by_channel, total])
        .sort(by=[pl.col("channel"), pl.col("id")], descending=[False, False])
        .limit(100)
    )
