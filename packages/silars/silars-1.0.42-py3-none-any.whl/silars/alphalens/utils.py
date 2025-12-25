# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/8 14:58
# Description:

import pandas as pd
import polars as pl

def get_forward_returns_columns(columns: list[str]) -> list[str]:
    """
    从列名列表中筛选出代表时间差的列名。

    参数:
    - columns: 列名列表。

    返回:
    - 代表时间差的列名列表。
    """
    timedelta_columns = []
    for col in columns:
        try:
            # 尝试将列名解析为 Timedelta
            pd.Timedelta(col)
            timedelta_columns.append(col)
        except ValueError:
            # 如果解析失败，说明不是时间差
            pass
    return timedelta_columns

def demean_forward_returns(factor_data: pl.DataFrame, grouper=None):
    if grouper is None:
        grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
    # 提取需要计算的列
    cols = get_forward_returns_columns(factor_data.columns)

    # 按 grouper 分组，对 cols 列进行中心化 (x - x.mean())
    result = factor_data.with_columns([
        (pl.col(col) - pl.col(col).mean().over(grouper)).alias(col)
        for col in cols
    ])

    return result

def freq_adjust(period, trading_hours=4, target_period="252d"):
    """调整周期: 按照1天交易时间4h"""
    scaler = (pd.Timedelta(target_period).days * trading_hours * 60 * 60 + pd.Timedelta(target_period).seconds) / (pd.Timedelta(period).days * trading_hours * 60 * 60 + pd.Timedelta(period).seconds)
    return scaler
