# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/23 15:41
# Description:

import polars as pl

def qcut(score_df: pl.DataFrame, N: int = 10, by_group: bool = False) -> pl.DataFrame:
    grouper = ["date", "time"]
    if by_group:
        grouper.append("group")
    labels = [str(i) for i in range(1, N + 1)]
    cat = pl.Enum(labels)
    return (
        score_df
        .drop_nulls()
        .with_columns(
            pl.col("score")
            .qcut(N,
                  labels=labels,
                  allow_duplicates=True)
            .over(grouper)
            .cast(cat)
            .alias("quantile"))
        .cast({pl.Categorical: pl.Utf8})
        .filter(quantile=str(N))
        .drop("quantile")
        .with_columns(target_weight=(1/pl.col("asset").n_unique()).over("date", "time"))
    )
