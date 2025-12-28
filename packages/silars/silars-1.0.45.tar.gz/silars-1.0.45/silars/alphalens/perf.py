from itertools import chain

import numpy as np
import pandas as pd
import polars as pl

from . import utils

def factor_information_coefficient(factor_data: pl.DataFrame,
                                   group_adjust=False,
                                   by_time=False,
                                   by_group=False,
                                   method="spearman"):
    """
    计算因子值与 N 个周期的 forward returns 的 Spearman Rank 信息系数 (IC)。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars DataFrame，包含以下列：
        - 日期 (date)、时间 (time)、资产 (asset)、因子值 (factor)
        - N 个周期的 forward returns 列（如 return_1D, return_5D 等）
        - 可选列：因子所属的分组 (group)、因子 quantile/bin 列等。

        如果需要清洗数据，请参考 utils.get_clean_factor_and_forward_returns。
    group_adjust : bool
        是否在计算 IC 前，对分组内的 forward returns 去均值化。默认值为 False
    by_group : bool
        是否对每个分组分别计算 IC, 默认值为 False
    by_time : bool
        是否对每个时间节点分别计算IC, 默认 False
    method: str

    Returns
    -------
    ic : pl.DataFrame
        每个分组的 Spearman Rank 相关系数 (IC)，以及 `index` 中的分组键。
        返回的列：
        - `index`：用于分组的列（如 date, time, group 等）
        - forward returns 的 IC 值，每列对应一个周期的 forward returns。
    """

    index = pd.Index(["date"]).intersection(factor_data.columns).tolist()
    grouper = index.copy()
    return_cols = utils.get_forward_returns_columns(factor_data.columns)
    if group_adjust:
        factor_data = utils.demean_forward_returns(factor_data, grouper + ["time", "group"])
    if by_time:
        grouper.append("time")
    if by_group:
        grouper.append('group')

    factor_data = factor_data.drop_nulls(subset=grouper)
    # 在每个分组内计算因子和 forward returns 的相关性
    result = factor_data.group_by(grouper).agg([
        pl.corr("factor", col, method=method).alias(col) for col in return_cols
    ])
    return result.sort(by=grouper).fill_nan(None)


def mean_information_coefficient(factor_data: pl.DataFrame,
                                 group_adjust: bool = False,
                                 by_group: bool = False,
                                 by_time: bool = False,
                                 every: str = None) -> pl.DataFrame:
    """
    计算指定条件下的平均信息系数（IC，Information Coefficient）。

    信息系数（IC）用于衡量因子值与未来收益之间的相关性，通常以 **Spearman 等级相关系数** 表示。
    本函数支持按时间窗口、资产分组或两者结合来分别计算平均 IC。

    功能示例：
    - 计算每个月的平均 IC。
    - 计算整个时间范围内，每个分组的平均 IC。
    - 计算每周、每个分组的平均 IC。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars DataFrame，包含以下列：
        - 日期列 (`date`)：用于时间索引；
        - 因子值列：包含单因子的值；
        - 前瞻收益列（forward returns columns）：用于计算因子与未来收益的相关性；
        - （可选）分组列（`group`）：按资产类别或自定义分组标识资产所属类别。
        数据格式需参考 `utils.get_clean_factor_and_forward_returns` 处理后的输出。

    group_adjust : bool, 默认值为 False
        如果为 True，则在计算 IC 之前，按分组对前瞻收益去均值。

    by_group : bool, 默认值为 False
        如果为 True，则按分组分别计算平均 IC。

    by_time : bool, 默认值为 False
        如果为 True，则按时间窗口分别计算平均 IC。

    every : str, 可选，默认值为 None
        按指定时间频率动态分组，例如 "1d"（按日）、"1w"（按周）、"1mo"（按月）、"1q"（按季度）、"1y" (按年)。
        若指定此参数，则使用 Polars 的 `group_by_dynamic` 按时间窗口分组。

    Returns
    -------
    pl.DataFrame
        一个 Polars DataFrame，包含平均 IC 值，具体结构取决于参数组合：
        - 如果仅指定 `by_group=True`：返回按分组计算的平均 IC；
        - 如果仅指定 `by_time=True`：返回按时间窗口计算的平均 IC；
        - 如果同时指定 `by_group=True` 和 `by_time=True`：返回按分组和时间窗口的平均 IC；
        - 如果未指定分组参数：返回整个数据集的平均 IC。

    Notes
    -----
    - 信息系数（IC）的计算基于因子值与前瞻收益的 **Spearman 等级相关系数**。
    - 可以通过参数组合自定义分组方式，例如按时间窗口和分组同时分组。

    Examples
    --------
    按时间窗口分组计算 IC：

    >>> mean_information_coefficient(factor_data=df, every="1m")

    按分组计算 IC：

    >>> mean_information_coefficient(factor_data=df, by_group=True)

    按时间窗口和分组同时计算 IC：

    >>> mean_information_coefficient(factor_data=df, every="1w", by_time=True, by_group=True)

    计算全局平均 IC：

    >>> mean_information_coefficient(factor_data=df)
    """

    ic = factor_information_coefficient(factor_data, group_adjust=group_adjust, by_group=by_group,
                                        by_time=by_time).fill_nan(None)
    cols = utils.get_forward_returns_columns(factor_data.columns)

    grouper = []
    if by_time:
        grouper.append("time")
    if by_group:
        grouper.append("group")
    ic = ic.drop_nulls(subset=grouper)
    if every is not None:
        # 使用 groupby_dynamic 按时间频率分组
        ic = ic.group_by_dynamic("date", every=every).agg(
            pl.col(*cols, *grouper)).explode(*cols, *grouper)
    if len(grouper) == 0:
        return ic.select(pl.col(*cols)).mean()
    ic_result = ic.group_by(grouper).agg(
        pl.col(*cols).mean()
    )

    return ic_result


def factor_weights(factor_data: pl.DataFrame,
                   demeaned=True,
                   group_adjust=False,
                   equal_weight=False) -> pl.DataFrame:
    """
    使用 Polars 实现资产权重计算，基于因子值按分组进行归一化处理。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars DataFrame，包含以下列：
        - `date`：日期；
        - `time`：时间；
        - `asset`：资产标识；
        - `factor`：因子值；
        - `group`：资产所属分组（可选）。
    demeaned : bool, 默认值为 True
        是否对因子值进行去均值处理以构建多空组合。
    group_adjust : bool, 默认值为 False
        是否按分组进行中性化处理，使每组权重的绝对值总和相等。
    equal_weight : bool, 默认值为 False
        是否对资产进行等权分配。

    Returns
    -------
    pl.DataFrame
        包含计算出的资产权重的 DataFrame，列包括：
        - `date`：日期；
        - `time`：时间；
        - `asset`：资产标识；
        - `weight`：计算出的权重。
    """

    index = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
    grouper = index.copy()
    if group_adjust:
        grouper.append("group")
    factor_data = factor_data.fill_nan(None).drop_nulls(subset=grouper)
    if demeaned:
        factor_data = factor_data.with_columns(pl.col("factor") - pl.col("factor").median().over(grouper))
    if equal_weight:
        negative_mask = pl.col("factor") < 0
        positive_mask = pl.col("factor") > 0
        factor_data = factor_data.with_columns(
            pl.when(negative_mask).then(-1.0).when(positive_mask).then(1.0).otherwise(0.0).alias("factor"))
    factor_data = factor_data.select(*index, "asset",
                                     pl.col("factor") / pl.col("factor").abs().sum().over(grouper)).fill_nan(None)
    if group_adjust:
        # 归一化
        factor_data = factor_data.select(*index, "asset",
                                         pl.col("factor") / pl.col("factor").abs().sum().over(index))
    return factor_data.sort(by=[*index, "asset"])


def factor_returns(factor_data: pl.DataFrame,
                   demeaned=True,
                   group_adjust=False,
                   equal_weight=False,
                   by_asset=False) -> pl.DataFrame:
    """
    计算按因子值加权的投资组合在每个周期的收益。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars DataFrame，包含以下列：
        - `date`：日期；
        - `time`：时间（可选，若存在则使用）；
        - `asset`：资产标识；
        - `factor`：因子值；
        - 若存在未来收益列（例如 `1D`, `5D` 等），则用于计算收益；
        - 可选的 `group` 列用于分组。
        因子数据被预处理以确保数据完整和符合要求。
    demeaned : bool, 默认值为 True
        是否去均值以构建多空组合。
        - 如果为 True，权重将按去均值后的因子值计算。
    group_adjust : bool, 默认值为 False
        是否按分组进行中性化处理。
        - 如果为 True，每组权重的绝对值总和将相等。
    equal_weight : bool, 默认值为 False
        是否对资产进行等权分配。
        - 如果为 True，所有资产的权重将相等。
    by_asset : bool, 默认值为 False
        是否按资产单独返回收益。
        - 如果为 True，将按资产分别报告收益；
        - 如果为 False，将返回整体组合的收益。

    Returns
    -------
    returns : pl.DataFrame
        每个周期的因子收益。
        - 如果 `by_asset=True`，返回按资产分组的收益；
        - 如果 `by_asset=False`，返回整体因子组合的周期收益。
        返回的 DataFrame 列包括：
        - 时间索引列（如 `date` 和 `time`）；
        - 每个周期的收益列（例如 `1D`, `5D` 等）。
    """

    index = pd.Index(["date", "time", "asset"]).intersection(factor_data.columns).tolist()

    weights = factor_weights(factor_data, demeaned, group_adjust, equal_weight)

    factor_data = factor_data.join(weights.rename({"factor": "w"}), on=index, how="left")
    cols = utils.get_forward_returns_columns(factor_data.columns)
    weighted_returns = factor_data.select(*index, pl.col(cols) * pl.col("w"))

    if by_asset:
        returns = weighted_returns
    else:
        index = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
        returns = weighted_returns.fill_nan(None).group_by(index).agg(pl.col(cols).sum())

    return returns.sort(by=index)


def factor_alpha_beta(factor_data: pl.DataFrame,
                      returns: pl.DataFrame = None,
                      demeaned: bool = True,
                      by_time: bool = False,
                      group_adjust: bool = False,
                      equal_weight: bool = False) -> pl.DataFrame:
    """
    使用 Polars 计算因子的 alpha（超额收益）、alpha t-stat（alpha 显著性）和 beta（市场敞口）。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars DataFrame，包含以下列：
        - `date`：日期；
        - `time`：时间；
        - `asset`：资产标识；
        - `factor`：因子值；
        - `group`：资产所属分组（可选）。
    returns : pl.DataFrame
        因子收益的 Polars DataFrame。如果未提供，将根据 `factor_returns()` 计算。
    demeaned : bool
        是否去均值，用于控制因子收益的计算, 默认 True
    by_time : bool
        是否计算每个时间节点的 Alpha/Beta, 默认 False
    group_adjust : bool
        是否进行分组中性化，用于控制因子收益的计算, 默认 False
    equal_weight : bool
        是否等权重分配，用于控制因子收益的计算, 默认 False

    Returns
    -------
    pl.DataFrame
        包含 alpha、beta 和 alpha t-stat 的 DataFrame，按周期返回。
    """
    # 如果未提供 returns，则计算
    if returns is None:
        returns = factor_returns(factor_data, demeaned, group_adjust, equal_weight)

    grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()

    # 收益列
    cols = utils.get_forward_returns_columns(factor_data.columns)

    # 计算市场组合收益（universe returns）：按日期分组取平均值
    universe_ret = (factor_data
                    .group_by(grouper)
                    .agg(pl.col(cols).mean())
                    .rename({col: f"{col}_universe" for col in cols})
                    .fill_nan(None)
                    .sort(by=grouper))
    data = returns.join(universe_ret, on=grouper, how="left")
    data = data.drop_nulls()

    if by_time:
        stats = data.with_columns(
            pl.count().over("time").alias("n"),
            *chain.from_iterable(
                [
                    [
                        pl.cov(col, f"{col}_universe").over("time").alias(f"cov_{col}"),
                        pl.var(f"{col}_universe").over("time").alias(f"var_x_{col}"),
                        pl.mean(col).over("time").alias(f"mean_y_{col}"),
                        pl.mean(f"{col}_universe").over("time").alias(f"mean_x_{col}")
                    ]
                    for col in cols
                ]
            )
        )
    else:
        stats = data.with_columns(
            pl.count().alias("n"),
            *chain.from_iterable(
                [
                    [
                        pl.cov(col, f"{col}_universe").alias(f"cov_{col}"),
                        pl.var(f"{col}_universe").alias(f"var_x_{col}"),
                        pl.mean(col).alias(f"mean_y_{col}"),
                        pl.mean(f"{col}_universe").alias(f"mean_x_{col}")
                    ]
                    for col in cols
                ]
            )
        )
    stats = stats.with_columns(
        (pl.col(f"cov_{col}") / pl.col(f"var_x_{col}")).alias(f"beta_{col}") for col in cols
    ).with_columns(
        (pl.col(f"mean_y_{col}") - pl.col(f"beta_{col}") * pl.col(f"mean_x_{col}")).alias(f"alpha_{col}") for col in
        cols
    ).with_columns(
        *chain.from_iterable(
            [
                [
                    ((1 + pl.col(f"alpha_{col}")) ** utils.freq_adjust(col, target_period="252d") - 1).alias(f"ann_alpha_{col}"),
                    (pl.col(col) - (pl.col(f"beta_{col}") * pl.col(f"{col}_universe") + pl.col(f"alpha_{col}"))).alias(
                        f"resid_{col}"),
                ]
                for col in cols
            ]
        )
    )
    if by_time:
        stats = stats.with_columns(
            *chain.from_iterable(
                [
                    [
                        ((pl.col(f"{col}_universe") - pl.col(f"mean_x_{col}")) ** 2).sum().over("time").alias(
                            f"bss_{col}"),  # x的偏差平方和
                        (pl.col(f"resid_{col}") ** 2).sum().over("time").alias(f"rss_{col}")
                    ]
                    for col in cols
                ]
            )
        )
    else:
        stats = stats.with_columns(
            *chain.from_iterable(
                [
                    [
                        ((pl.col(f"{col}_universe") - pl.col(f"mean_x_{col}")) ** 2).sum().alias(f"bss_{col}"),
                        # x的偏差平方和
                        (pl.col(f"resid_{col}") ** 2).sum().alias(f"rss_{col}")
                    ]
                    for col in cols
                ]
            )
        )

    stats = stats.with_columns(
        (pl.col(f"rss_{col}") / (pl.col("n") - 2)).alias(f"mse_{col}") for col in cols
    ).with_columns(
        (pl.col(f"mse_{col}") * (1 / pl.col("n") + pl.col(f"mean_x_{col}") ** 2 / pl.col(f"bss_{col}"))).sqrt().alias(
            f"se_alpha_{col}") for col in cols  # 标准误
    ).with_columns(
        (pl.col(f"alpha_{col}") / pl.col(f"se_alpha_{col}")).alias(f"alpha_t_stat_{col}") for col in cols
    )

    select_cols = chain.from_iterable([
        [
            f"beta_{col}",
            f"ann_alpha_{col}",
            f"alpha_t_stat_{col}",
        ]
        for col in cols
    ])

    if by_time:
        data = stats.group_by("time").agg(
            pl.col(*select_cols).first()
        )
        data = pl.concat([data.select(pl.lit(col).alias("period"),
                                      "time",
                                      pl.col(f"ann_alpha_{col}").alias("Ann. alpha"),
                                      pl.col(f"beta_{col}").alias("beta"),
                                      pl.col(f"alpha_t_stat_{col}").alias(f"alpha_t_stat")) for col in cols],
                         how="vertical").sort(by=["period", "time"])
    else:
        data = stats.select(pl.col(*select_cols).first())
        data = pl.concat([data.select(pl.lit(col).alias("period"),
                                            pl.col(f"ann_alpha_{col}").alias("Ann. alpha"),
                                            pl.col(f"beta_{col}").alias("beta"),
                                            pl.col(f"alpha_t_stat_{col}").alias(f"alpha_t_stat")) for col in cols],
                               how="vertical").sort(by="period")
    return data.with_columns(
        pl.col("Ann. alpha").alias("ann.alpha"),
        pl.col("alpha_t_stat").alias("alpha t-stat"),
    ).unpivot(
        on=["ann.alpha", "beta", "alpha t-stat"],
        index=["period", "time"] if by_time else "period",
        variable_name="metric").pivot(index=["time", "metric"] if by_time else "metric", columns="period", values="value")


def mean_return_by_quantile(factor_data: pl.DataFrame,
                            by_date=False,
                            by_time=False,
                            by_group=False,
                            demeaned=True,
                            group_adjust=False):
    """
    计算因子分位数（quantile）对应的平均收益和 t 统计量。

    此函数基于给定的因子数据，按照因子分位数（quantile）计算前瞻收益的平均值和标准误差，
    并进一步计算 t 统计量。

    Parameters
    ----------
    factor_data : pl.DataFrame
        包含因子值、分位数、前瞻收益数据的 DataFrame。通常由 `utils.get_clean_factor_and_forward_returns` 函数生成。
        需要包含以下列：
            - `date`：日期；
            - `time`：时间；
            - `asset`：资产标识；
            - `factor`：因子值；
            - `factor_quantile`：因子值对应的分位数或区间。
            - 前向收益列：每个周期的收益，例如 `1D`、`5D` 等。
            - （可选）`group`：资产所属的分组。
    by_date : bool, 默认为 False
        如果为 True，则按日期分别计算每个分位数的收益。
    by_time : bool, 默认为 False
        如果为 True，则将时间维度包括在分组中。
    by_group : bool, 默认为 False
        如果为 True，则按资产所属分组分别计算分位数收益。
    demeaned : bool, 默认为 True
        如果为 True，则计算去均值的平均收益。
    group_adjust : bool, 默认为 False
        如果为 True，则在分组层级计算减去均值的收益, 此时demeaned参数失去作用

    Returns
    -------
    mean_ret : pl.DataFrame
        每个分位数的平均收益，按指定的分组维度（如日期、时间、分组）计算。
        列出每个前瞻收益周期的分位数平均收益。
    std_err_ret: pl.DataFrame
        每个分位数收益的标准误差，表示精确度。
        列出每个前瞻收益周期的分位数平均收益。
    t_stat_ret : pl.DataFrame
        每个分位数的 t 统计量，表示收益显著性。
        列出每个前瞻收益周期的分位数 t 统计量。

    Examples
    --------
    >>> mean_ret, t_stat_ret = mean_return_by_quantile(
    ...     factor_data=factor_data,
    ...     by_date=True,
    ...     by_time=True,
    ...     by_group=True,
    ...     demeaned=True
    ... )
    >>> print(mean_ret)
    >>> print(t_stat_ret)
    """
    # factor_data = factor_data.drop_nulls(subset=pd.Index(["factor_quantile", "group"]).intersection(factor_data.columns).tolist())
    if group_adjust:
        grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
        factor_data = utils.demean_forward_returns(factor_data, grouper + ["group"])
    elif demeaned:
        factor_data = utils.demean_forward_returns(factor_data)
    grouper = ["factor_quantile", "date"]
    if by_time:
        grouper.append("time")
    grouper = pd.Index(grouper).intersection(factor_data.columns).tolist()

    if by_group:
        grouper.append('group')
    cols = utils.get_forward_returns_columns(factor_data.columns)
    group_stats = factor_data.group_by(grouper).agg(
        *chain.from_iterable(
            [
                [
                    pl.col(col).mean().alias(f"mean_{col}"),
                    pl.col(col).std().alias(f"std_{col}"),
                    pl.col(col).count().alias(f"n_{col}"),
                ]
                for col in cols
            ]
        )
    )
    mean_ret = group_stats.select(
        *grouper,
        *[pl.col(f"mean_{col}").alias(col) for col in cols]
    )
    if not by_date:
        grouper = ["factor_quantile"]
        if by_time:
            grouper.append("time")
        if by_group:
            grouper.append("group")
        group_stats = mean_ret.group_by(grouper).agg(
            *chain.from_iterable(
                [
                    [
                        pl.col(col).mean().alias(f"mean_{col}"),
                        pl.col(col).std().alias(f"std_{col}"),
                        pl.col(col).count().alias(f"n_{col}"),
                    ]
                    for col in cols
                ]
            )
        )
        mean_ret = group_stats.select(
            *grouper,
            *[pl.col(f"mean_{col}").alias(col) for col in cols]
        )

    # 计算标准误
    std_err_ret = group_stats.select(
        *grouper,
        *[(pl.col(f"std_{col}") / pl.col(f"n_{col}").sqrt()).alias(col) for col in cols],
    )

    # 计算t统计量
    t_stat_ret = group_stats.select(
        *grouper,
        *[(pl.col(f"mean_{col}") / (pl.col(f"std_{col}") / pl.col(f"n_{col}").sqrt())).alias(col) for col in cols],
    )

    return (mean_ret
            .drop_nulls(grouper)
            .sort(by=grouper),
            std_err_ret
            .drop_nulls(grouper)
            .sort(by=grouper),
            t_stat_ret
            .drop_nulls(grouper)
            .sort(by=grouper)
            )


def compute_mean_returns_spread(mean_returns: pl.DataFrame,
                                upper_quant,
                                lower_quant,
                                std_err=None):
    """
    计算两个分位数之间的平均收益差异（Spread），并可选地计算该差异的标准误差和 t 统计量。

    该函数通过 Polars DataFrame 实现，按 `factor_quantile` 分组计算两个指定分位数的平均收益差异。
    如果提供了标准误差数据，还会计算收益差异的联合标准误差和 t 统计量。

    Parameters
    ----------
    mean_returns : pl.DataFrame
        包含按分位数计算的各期平均收益的 Polars DataFrame。
        必须包含 `factor_quantile` 列，以及与日期（如 "date"、"time"）或分组（如 "group"）相关的索引列。
        通常由 `mean_return_by_quantile` 方法生成。
    upper_quant : int
        上层分位数，用于计算收益差异的分子部分。
        比如，取值为 10 表示最高分位数。
    lower_quant : int
        下层分位数，用于计算收益差异的分母部分。
        比如，取值为 1 表示最低分位数。
    std_err : pl.DataFrame, optional
        （可选）包含按分位数计算的每期平均收益标准误差的 Polars DataFrame。
        格式必须与 `mean_returns` 相同，具有相同的列和索引。

    Returns
    -------
    mean_return_difference : pl.DataFrame
        每期分位数收益差异的 DataFrame，按列返回所有收益差异。
        包含索引（如 "date"、"time"、"group"）以及各期收益差异值。
    joint_std_err : pl.DataFrame or None
        每期收益差异的联合标准误差。如果未提供 `std_err` 参数，则返回 None。
        否则，返回包含联合标准误差的 DataFrame。
    t_stat_difference : pl.DataFrame or None
        每期收益差异的 t 统计量（差异值除以联合标准误差）。
        如果 `std_err` 为 None，则返回 None。
        否则，返回包含 t 统计量的 DataFrame。

    Notes
    -----
    1. `mean_returns` 和 `std_err` 必须具有相同的结构，且包含相同的索引列（如 "date"、"time" 等）。
    2. 计算收益差异时，使用 `upper_quant` 和 `lower_quant` 对 `factor_quantile` 进行筛选。
    3. 如果 `std_err` 可用，则联合标准误差按公式计算：
       `sqrt(std_err_upper_quant^2 + std_err_lower_quant^2)`。
    4. t 统计量的计算公式为：
       `t_stat = mean_return_difference / joint_std_err`。
    """

    index = pd.Index(["date", "time", "group"]).intersection(mean_returns.columns)
    cols = utils.get_forward_returns_columns(mean_returns.columns)
    if index.size > 0:
        mean_return_difference = (
            mean_returns
            .filter(pl.col("factor_quantile") == upper_quant)
            .join(
                mean_returns
                .filter(pl.col("factor_quantile") == lower_quant),
                on=index, how="left", suffix="_right")
            .select(
                *index,
                *[pl.col(col) - pl.col(f"{col}_right") for col in cols]
            )
        )
    else:
        top_ret = mean_returns.filter(pl.col("factor_quantile") == upper_quant).select(cols)
        bottom_ret = mean_returns.filter(pl.col("factor_quantile") == lower_quant).select(cols)
        mean_return_difference = top_ret - bottom_ret

    if std_err is None:
        joint_std_err = None
    else:
        if index.size > 0:
            joint_std_err = (
                std_err
                .filter(pl.col("factor_quantile") == upper_quant)
                .join(
                    std_err
                    .filter(pl.col("factor_quantile") == lower_quant),
                    on=index, how="left")
                .select(
                    *index,
                    *[(pl.col(col) ** 2 + pl.col(f"{col}_right") ** 2).sqrt() for col in cols]
                )
            )
        else:
            top_err = std_err.filter(pl.col("factor_quantile") == upper_quant)
            bottom_err = std_err.filter(pl.col("factor_quantile") == lower_quant)
            joint_std_err = top_err.select(
                (pl.col(col)**2+ bottom_err[col]**2).sqrt() for col in cols
            )
    if joint_std_err is None:
        t_stat_difference = None
    else:
        if index.size > 0:
            t_stat_difference = (
                mean_return_difference.join(
                    joint_std_err,
                    on=index, how="left"
                ).select(
                    *index,
                    *[(pl.col(col) / pl.col(f"{col}_right")) for col in cols]
                )
            )
        else:
            t_stat_difference = mean_return_difference/joint_std_err
    return mean_return_difference, joint_std_err, t_stat_difference


def quantile_turnover(factor_data: pl.DataFrame, by_time=False, period=1):
    """
    计算因子分位数（quantile）的换手率（Turnover），即当前期分位数资产集合
    与上一期分位数资产集合的差异比例。

    Parameters
    ----------
    factor_data : pl.DataFrame
        包含因子数据的 Polars DataFrame，必须包括以下列：
        - 'factor_quantile': 因子分位数。
        - 'date': 日期。
        - 'time': 时间（如果按时间分组分析，则此列必需）。
        - 'asset': 资产名称或标识。
    by_time : bool, optional
        是否按时间（`time` 列）进一步分组进行换手率计算。
        默认为 False，即仅按 `factor_quantile` 和 `date` 计算。
        - True: 时间对齐后计算换手，比如09:31:00的换手是相对于上一天的09:31:00
    period : int, optional
        时间偏移间隔，用于计算换手率的时间跨度。
        默认为 1，即计算相邻时间段的换手率。

    Returns
    -------
    turnover_data : pl.DataFrame
        包含换手率的 Polars DataFrame，结果包括以下列：
        - 'factor_quantile': 因子分位数。
        - 'date': 日期。
        - 'time': 时间
        - 'turnover': 换手率，表示当前分位数中新增资产的比例。

    Notes
    -----
    - 换手率公式：
       `turnover = len(差集资产集合) / len(当前资产集合)`，
       差集资产集合为当前期资产集合中不属于上一期的资产。
    - 如果 `by_time=True`，则按 `factor_quantile` 和 `time` 进一步分组计算。
    - 如果某期资产集合为空或上一期资产集合缺失，则该期换手率无法计算。
    """
    factor_data = factor_data.drop_nulls(subset="factor_quantile")
    grouper = ["factor_quantile", "date", "time"]
    cur_asset_set = factor_data.group_by(grouper).agg(
        pl.col("asset").unique()
    ).sort(by=grouper)
    shift_grouper = ["factor_quantile", ]
    if by_time:
        shift_grouper.append("time")
    prev_asset_set = cur_asset_set.select(
        *grouper,
        pl.col("asset").shift(period).over(shift_grouper)
    )
    return cur_asset_set.join(
        prev_asset_set, on=grouper, how="left", suffix="_prev"
    ).with_columns(
        pl.col("asset").list.set_difference("asset_prev").alias("asset_diff").list.len().alias("diff_count"),
        pl.col("asset").list.len().alias("cur_count"),
    ).select(
        # "factor_quantile",
        "factor_quantile", "date", "time",
        (pl.col("diff_count") / pl.col("cur_count")).alias("turnover")
    )


def factor_rank_autocorrelation(factor_data: pl.DataFrame,
                                by_time: bool = False,
                                period=1):
    """
    计算指定时间跨度内因子排名的自相关系数。

    该函数用于计算因子排名在不同时期之间的自相关性。通过比较因子排名而非因子值，
    可以消除因子值在全资产或资产组中的系统性偏移。该指标对衡量因子的稳定性和换手率
    非常有用。如果因子值在不同时期随机变化，则自相关性接近 0。

    Parameters
    ----------
    factor_data : pl.DataFrame
        一个 Polars 数据框，包含因子值相关的数据。数据框必须包含以下列：
        - `date` : 日期信息。
        - `time` : （可选）具体时间（如分钟、小时等），适用于日内数据。
        - `asset`: 资产标识符（如股票代码、资产 ID 等）。
        - `factor`: 与资产相关的因子值。

        数据框应包含多个 `date` 和 `asset` 的组合，因子值将被排序后用于计算自相关性。

    by_time : bool, 可选，默认值为 False
        - 如果为 `False`，不做时间的对齐
        - 如果为 `True`，将同时考虑 `date` 和 `time` 信息，因子排名会在日期和时间维度上对齐。
          适用于需要计算日内数据（如小时、分钟级别数据）的自相关性。

        当 `by_time=True` 时，`period` 参数会乘以唯一时间点的数量，以对齐日期和时间维度的位移。

    period : int, 可选，默认值为 1
        用于计算自相关性的时间跨度（以 `date` 或 `date + time` 为单位）。
        - 正值表示向下偏移排名后计算自相关性。
        - 负值表示向上偏移排名后计算自相关性。

    Returns
    -------
    pl.DataFrame
        一个 Polars 数据框，包含以下列：
        - `date` : 日期信息。
        - `time` : （如果 `by_time=True`）具体时间信息。
        - `rank_autocorr` : 指定时间跨度内因子排名的 Spearman 自相关系数。

    Notes
    -----
    - 该函数使用 **Spearman 排名相关系数** 来计算自相关性，衡量因子排名偏移后的单调性关系。
    - `period` 参数定义了计算自相关性的滞后时间跨度，滞后时间越大，比较时间点之间的距离越远。
    - 如果数据框中没有 `time` 列且 `by_time=True`，函数可能会抛出错误。
    """
    dateList = factor_data["date"].unique(maintain_order=True)
    timeList = factor_data["time"].unique(maintain_order=True)
    asset_length = factor_data["asset"].unique().len()
    reshape = (-1, asset_length)
    arr = factor_data["factor"].to_numpy().reshape(reshape)
    shifted = np.full_like(arr, np.nan)
    if by_time:
        time_length = timeList.len()
        period = period * time_length
    if period > 0:
        shifted[period:, :] = arr[:-period, :]  # 向下移动
    else:
        shifted[:period, :] = arr[-period:, :]  # 向上移动
    corr = pd.DataFrame(arr).corrwith(pd.DataFrame(shifted), method="spearman", axis=1)
    index = dateList.to_frame().join(timeList.to_frame(), how="cross")
    return index.with_columns(
        pl.Series(name="rank_autocorr", values=corr.values, )
    )
