# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2024/11/24 下午4:50
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""
from itertools import chain

import pandas as pd
import polars as pl

from . import perf
from . import utils

DECIMAL_TO_BPS = 10000


def get_summary_report(
        factor_data: pl.DataFrame,
        long_short=True,
        group_neutral=True,
        by_time=True,
) -> pl.DataFrame:
    """
    创建一个完整的报告，用于分析和评估单一收益预测（alpha）因子。

    Parameters
    ----------
    factor_data : pl.DataFrame
        包含单一 alpha 因子的值、每个期限的前向收益、因子分位数/区间以及（可选的）资产所属的组。

    long_short : bool, 可选
        是否在多空头寸组合上进行计算, 默认 True
        - True: 收益去均值

    group_neutral : bool, 可选
        是否在行业中性组合上进行计算

    by_time : bool, 可选
        如果为 True，则分组统计时考虑时间维度

    Returns
    -------
    pl.DataFrame
        包含 alpha 因子的统计报告
    """
    alpha_beta = perf.factor_alpha_beta(factor_data,
                                        demeaned=long_short,
                                        by_time=by_time,
                                        group_adjust=group_neutral,
                                        )
    mean_ret_quantile, std_err_ret, mean_ret_quantile_t_stat = perf.mean_return_by_quantile(factor_data,
                                                                                            by_time=by_time,
                                                                                            by_group=False,
                                                                                            demeaned=long_short,
                                                                                            group_adjust=group_neutral)
    mean_ret_spread_quantile, std_err_spread, mean_ret_spread_quantile_t_stat = perf.compute_mean_returns_spread(
        mean_ret_quantile,
        mean_ret_quantile[
            "factor_quantile"].max(),
        mean_ret_quantile[
            "factor_quantile"].min(),
        std_err=std_err_ret)
    periods = utils.get_forward_returns_columns(alpha_beta.columns)
    # 转换为透视表
    select_fields = ["time", "metric"] if by_time else ["metric"]
    select_fields.extend(periods)
    top_mean_ret = (
        mean_ret_quantile
        .filter(
            pl.col("factor_quantile") == pl.col("factor_quantile").max())
        .with_columns(
            pl.lit("top alpha (bps)").alias("metric"),
            *[pl.col(col) * DECIMAL_TO_BPS for col in periods])
    ).select(*select_fields)

    bottom_mean_ret = (
        mean_ret_quantile
        .filter(
            pl.col("factor_quantile") == pl.col("factor_quantile").min())
        .with_columns(
            pl.lit("bottom alpha (bps)").alias("metric"),
            *[pl.col(col) * DECIMAL_TO_BPS for col in periods])
    ).select(*select_fields)

    top_tstat = (
        mean_ret_quantile_t_stat
        .filter(
            pl.col("factor_quantile") == pl.col("factor_quantile").max())
        .with_columns(
            pl.lit("top alpha t-stat").alias("metric"))
    ).select(*select_fields)

    bottom_tstat = (
        mean_ret_quantile_t_stat
        .filter(
            pl.col("factor_quantile") == pl.col("factor_quantile").min())
        .with_columns(
            pl.lit("bottom alpha t-stat").alias("metric"))
    ).select(*select_fields)

    ret_spread = (
        mean_ret_spread_quantile
        .with_columns(
            pl.lit("spread alpha (bps)").alias("metric"),
            *[pl.col(col) * DECIMAL_TO_BPS for col in periods])
    ).select(*select_fields)

    spread_tstat = (
        mean_ret_spread_quantile_t_stat
        .with_columns(
            pl.lit("spread alpha t-stat").alias("metric"), )
        .select(*select_fields)
    )

    join_tb = pl.concat([
        alpha_beta,
        top_mean_ret,
        top_tstat,
        bottom_mean_ret,
        bottom_tstat,
        ret_spread,
        spread_tstat], how="vertical")

    cols_exclude_metric = pd.Index(join_tb.columns).difference(["time", "metric"] if by_time else ["metric"]).tolist()
    join_tb = join_tb.select(
        *["time", "metric"] if by_time else ["metric"],
        *[pl.col(col).round(3) for col in cols_exclude_metric]
    )

    join_tb = (
        join_tb
        .unpivot(on=periods, index=["time", "metric"] if by_time else "metric", variable_name="period", )
        .pivot(on="metric", values="value", index=["period", "time"] if by_time else "period")
        .select(
            *["period", "time"] if by_time else ["period"],
            pl.col("top alpha (bps)").alias("top_bps"),
            pl.col("top alpha t-stat").alias("top_tstat"),
            pl.col("bottom alpha (bps)").alias("bottom_bps"),
            pl.col("bottom alpha t-stat").alias("bottom_tstat"),
            pl.col("spread alpha (bps)").alias("spread_bps"),
            pl.col("spread alpha t-stat").alias("spread_tstat"),
            pl.col("ann.alpha").alias("ann_alpha"),
            pl.col("alpha t-stat").alias("alpha_tstat"),
            pl.col("beta")
        )
    )
    ic_tb = get_ic_report(factor_data, group_neutral=group_neutral, by_time=by_time, by_group=False)
    join_index = ["period", "time"] if by_time else ["period"]
    return ic_tb.join(join_tb, on=join_index, how="left").sort(by=join_index)


def get_ic_report(factor_data, group_neutral: bool = True, by_time: bool = True, by_group: bool = False):
    ic = perf.factor_information_coefficient(factor_data, group_adjust=group_neutral, by_group=by_group,
                                             by_time=by_time).fill_nan(None)
    cols = utils.get_forward_returns_columns(factor_data.columns)

    grouper = []
    if by_time:
        grouper.append("time")
    if by_group:
        grouper.append("group")
    if len(grouper) > 0:
        ic = ic.drop_nulls(subset=grouper)
        ic_stat = ic.group_by(grouper).agg(
            *chain.from_iterable(
                [
                    [
                        pl.col(col).mean().alias(f"{col}_mu"),
                        pl.col(col).std().alias(f"{col}_sd"),
                        pl.col(col).count().alias(f"{col}_n"),
                    ]
                    for col in cols
                ]
            )
        )
    else:
        ic_stat = ic.select(
            *chain.from_iterable(
                [
                    [
                        pl.col(col).mean().alias(f"{col}_mu"),
                        pl.col(col).std().alias(f"{col}_sd"),
                        pl.col(col).count().alias(f"{col}_n"),
                    ]
                    for col in cols
                ]
            )
        )
    tstat = ic_stat.select(
        *grouper,
        *[(pl.col(f"{col}_mu") / (pl.col(f"{col}_sd") / pl.col(f"{col}_n").sqrt())).alias(col) for col in cols],
    ).with_columns(pl.lit("ic_tstat").alias("metric"))
    icmean = ic_stat.select(
        *grouper,
        *[pl.col(f"{col}_mu").alias(col) for col in cols]
    ).with_columns(
        pl.lit("ic").alias("metric")
    )
    icir = ic_stat.select(
        *grouper,
        *[(pl.col(f"{col}_mu") / pl.col(f"{col}_sd")).alias(col) for col in cols]
    ).with_columns(
        pl.lit("icir").alias("metric")
    )
    result = pl.concat([icmean, icir, tstat], how="vertical").select(*grouper, "metric", *cols)
    result = (
        result
        .unpivot(on=cols, index=["time", "metric"] if by_time else "metric", variable_name="period")
        .pivot(on="metric", index=["period", "time"] if by_time else "period")
    )

    if len(grouper) > 0:
        result = result.sort(by=grouper)

    cols_exclude_metric = pd.Index(result.columns).difference(
        ["period", "time", "metric"] if by_time else ["period", "metirc"]).tolist()

    return result.select(
        "period", *grouper,
        *[pl.col(col).round(4) for col in cols_exclude_metric],
    )
