# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/22 16:36
# Description:

import polars as pl
from tqdm.auto import tqdm


def backtest(weight_df: pl.DataFrame, period: str, limit: bool = True) -> pl.DataFrame | None:
    """
    高频多因子回测

    Parameters
    ----------
    weight_df: polars.DataFrame
        需要包含 target_weight 字段
        如果 limit 为 True，则必须包括 limit 字段
    period: str
    limit: bool
        是否限制某些买卖：比如涨跌停
    Returns
    -------

    """

    assert "target_weight" in weight_df.columns, "`target_weight` not in weight_df.columns"
    if limit:
        assert "limit" in weight_df.columns, "`limit` not in weight_df.columns"

    weight_df = weight_df.with_columns(_sum_weight=pl.col("target_weight").sum().over("date", "time"))
    weight_df = weight_df.with_columns(target_weight=pl.col("target_weight")/pl.col("_sum_weight")).drop("_sum_weight")

    total_num = weight_df.select("date", "time").n_unique()
    pbar = tqdm(total=total_num, desc="Backtesting", leave=False)
    beg_date = weight_df["date"][0]
    beg_time = weight_df["time"][0]
    time_num = weight_df["time"].n_unique()

    scalar = 0.0

    pos_list = list()
    for (date, time), pos in weight_df.group_by("date", "time", maintain_order=True):
        pbar.set_postfix_str(f"{date} {time}")
        if not pos_list:
            # 第一次建仓:
            pos = pos.with_columns(avail_sell=pl.lit(0.0), beg_weight=pl.lit(0.0))
        else:
            prev_pos = pos_list[-1]
            prev_pos = prev_pos.select("asset", "avail_sell", beg_weight=pl.col("end_weight"))
            pos = (pos
                   .join(prev_pos, on="asset", how="full", coalesce=True)
                   .with_columns(date=pl.col("date").fill_null(date),
                                 time=pl.col("time").fill_null(time),
                                 avail_sell=pl.col("avail_sell").fill_null(0.0),
                                 beg_weight=pl.col("beg_weight").fill_null(0.0)))
        if date == beg_date:
            scalar += 1/time_num
        else:
            scalar = 1.0
        target_weight = (pl.when(date=beg_date)
                         .then(pl.col("target_weight")/time_num + pl.col("beg_weight"))
                         .otherwise(pl.col("target_weight")))
        avail_sell = (pl.when(date=beg_date)
                      .then(0.0)
                      .when(time=beg_time)
                      .then(pl.col("beg_weight"))
                      .otherwise(pl.col("avail_sell"))
                      )
        pos = pos.with_columns(target_weight=target_weight, avail_sell=avail_sell)

        chg_weight = (pl.col("target_weight") - pl.col("beg_weight")).clip(lower_bound=-pl.col("avail_sell"))
        pos = pos.with_columns(chg_weight=chg_weight)
        # 涨跌停限制
        if limit:
            chg_weight = pl.when(pl.col("limit") > 0).then(0.0).otherwise(pl.col("chg_weight"))
            pos = pos.with_columns(chg_weight=chg_weight)
        # 更新可卖
        avail_sell = pl.col("avail_sell") + pl.col("chg_weight").clip(upper_bound=0.0)
        # 处理买入： sum(买入) <= sum(卖出)
        total_sell = ((pl.col("chg_weight") < 0) * pl.col("chg_weight")).sum()
        total_buy = ((pl.col("chg_weight") > 0) * pl.col("chg_weight")).sum()
        adj_ratio = 1.0 if date == beg_date else total_sell.abs() / total_buy
        adj_buy = adj_ratio * pl.col("chg_weight")
        change_weight = pl.when(pl.col("chg_weight") > 0).then(adj_buy).otherwise(pl.col("chg_weight"))

        pos = (
            pos
            .with_columns(avail_sell=avail_sell)
            .with_columns(change_weight=change_weight)
            .with_columns(real_weight=pl.col("beg_weight")+pl.col("change_weight"),)
            .with_columns(end_weight=pl.col("real_weight")*(1+pl.col(period)))
            .with_columns(end_weight=pl.col("end_weight")/pl.col("end_weight").sum() * scalar)
        )


        pos_list.append(pos)
        pbar.update()

    if pos_list:
        return pl.concat(pos_list).sort("date", "time", "asset")

    return None