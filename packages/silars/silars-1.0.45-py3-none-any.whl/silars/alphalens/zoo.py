# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/17 10:28
# Description:
from typing import Literal

import lidb
import ygo
from lidb import DataLoader, Dataset, from_polars
from lidb.qdf import QDF, Expr
import polars as pl
import pandas as pd
from polars import selectors as cs
import logair

from .utils import demean_forward_returns
from .plot import model_performance_graph
from tqdm.auto import tqdm
from .backtest import backtest

logger = logair.get_logger(__name__)

class Zoo:
    """用于研究alpha因子的数据管理部分"""

    def __init__(self):
        self._factor_dls = DataLoader("factor", )
        self._add_dls = DataLoader("adding", )
        self._label_dls = DataLoader("label", )
        self._mount_dls = DataLoader("mount", )
        self._filter_dls = DataLoader("filter", )
        self._loader_params = dict()
        self._factors: pl.DataFrame = None
        self._qdf: QDF = None
        self.logger = logair.get_logger(f"{__name__}.{self.__class__.__name__}")

    def load(self,
             beg_date: str,
             end_date: str,
             times: list[str],
             ds_list: list[Dataset],
             n_jobs: int = 11,
             backend: Literal["threading", "multiprocessing", "loky"] = "threading",
             **constraints):
        self._loader_params = dict(beg_date=beg_date,
                                   end_date=end_date,
                                   times=times,
                                   n_jobs=n_jobs,
                                   backend=backend,
                                   eager=True,
                                   **constraints)
        self._factor_dls.get(ds_list=ds_list, **self._loader_params)
        return self.filter()

    def add_dataset(self, ds_list: list[Dataset]):
        """添加新的数据集"""
        if ds_list:
            self._add_dls.get(ds_list=ds_list, **self._loader_params)
            self._factor_dls.add_data(self._add_dls.data)
        return self

    def to_qdf(self, data: pl.DataFrame | pl.LazyFrame):
        self._qdf = from_polars(data, align=True)
        return self

    def label(self, ds_list: list[Dataset]):
        if ds_list:
            self._label_dls.get(ds_list=ds_list, **self._loader_params)
            self._factor_dls.add_data(self._label_dls.data)
        return self

    def mount(self, ds_list: list[Dataset] = None):
        """挂载数据: 比如alphalens需要的行业(group)/收益数据..."""
        if ds_list:
            self._mount_dls.get(ds_list=ds_list, **self._loader_params)
            # 更新 factor_data
            self._factor_dls.add_data(self._mount_dls.data)
        return self

    def filter(self, ds_list: list[Dataset] = None):
        """过滤数据集：每个过滤数据集列名必须命名为 `cond` """
        if ds_list:
            index = ("date", "time", "asset")
            self._filter_dls.get(ds_list=ds_list, **self._loader_params)
            filter_df = self._filter_dls.data.select(*index,
                                                     cond=pl.sum_horizontal(cs.exclude(index)).fill_null(1).fill_nan(1))
            target_index = filter_df.filter(pl.col("cond") < 1).select(*index)
            if self._factor_dls.data is not None:
                self._factors = target_index.join(self._factor_dls.data, on=index, how="left")
        else:
            self._filter_dls = DataLoader("filter", )
            self._factors = self._factor_dls.data  # 恢复成过滤前的状态
            self._qdf = None
        return self

    def sql(self, *exprs: str) -> pl.DataFrame:
        if self._qdf is None:
            self.to_qdf(self._factors)
        return self._qdf.sql(*exprs, show_progress=True)

    def _to_alphalens(self,
                      alpha_name: str,
                      demeaned: bool = False,
                      group_adjust: bool = False,
                      beg_date: str = None,
                      end_date: str = None,
                      times: list[str] = None,
                      bins: int = 10,
                      by_group: bool = False,
                      reverse: bool = False,):
        """转成 alphalens 所需要的因子分析格式"""
        grouper = ["date", "time"]
        index = ("date", "time", "asset")
        # 处理收益列
        if not beg_date:
            beg_date = self.factors["date"].min()
        if not end_date:
            end_date = self.factors["date"].max()
        if not times:
            times = self.factors["time"].unique().to_list()
        factor_data = self.factors.filter(
            (pl.col("date") >= beg_date),
            (pl.col("date") <= end_date),
            (pl.col("time").is_in(times)))
        factor_data = factor_data.sort(by=["date", "time", "asset"])
        if group_adjust:
            grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
            factor_data = demean_forward_returns(factor_data, grouper + ["group"]).sort(by=["date", "time", "asset"])
        elif demeaned:
            factor_data = demean_forward_returns(factor_data)
        factor_data = factor_data.with_columns(
            (factor_data[period]).alias(period)
            for period in self.periods
        )

        cols = [*index, *self.periods, ]
        if reverse:
            cols.append((-pl.col(alpha_name)).alias("factor"))
        else:
            cols.append(pl.col(alpha_name).alias("factor"))
        if by_group:
            grouper.append("group")
            cols.append("group")
        labels = [str(i) for i in range(1, bins + 1)]
        cat = pl.Enum(labels)
        return (
            factor_data
            .select(cols)
            .drop_nulls()
            .with_columns(
                pl.col("factor")
                .qcut(bins,
                      labels=labels,
                      allow_duplicates=True)
                .over(grouper)
                .cast(cat)
                .alias("factor_quantile"))
            .cast({pl.Categorical: pl.Utf8})
            .select(*index, "factor", "factor_quantile", *self.periods)
        )

    def factor_report(self,
                      exprs: list[str],
                      by_group: bool = False,
                      reverse: bool = False,
                      lag: int = 1,
                      N: int = 10,
                      demeaned: bool = False,
                      group_adjust: bool = False,
                      beg_date: str = None,
                      end_date: str = None,
                      times: list[str] = None,
                      show_notebook: bool = True, ):
        """
        qlib 版本的因子报告

        Parameters
        ----------
        exprs: list[str]
            因子表达式
        by_group : bool
            分组是否在行业内进行分组, 默认False-全市场分组
        reverse : bool
        lag: int
            计算因子自回归以及换手时的滞后期数, 默认上一期:1
        N: int
            分组数量, 默认10
        demeaned : bool
            是否进行去均值处理。如果为 True，则在计算收益时会去掉因子的均值影响。
        group_adjust : bool
            是否进行组中性处理。如果为 True，则收益会减去行业均值
            **注意**: 该参数优先级大于 demeaned，该参数为True时，demeaned参数失去作用
        beg_date: str
        end_date: str
        times: list[str]
        show_notebook: bool

        Notes
        -----
        group_neutral 和 demeaned 控制是否对收益做调整, group_neutral优先级更高
            - group_neutral 为 True: 收益-行业均值
            - group_neutral 为 False: 如果demeaned 为 True，则收益 - 全市场均值
        """
        index = ("date", "time", "asset")
        logger.info("Calculating alpha expr.")
        expr_data = self.sql(*exprs)
        alpha_names = expr_data.select(cs.exclude(index)).columns

        beg_date = self.factors["date"].min() if beg_date is None else beg_date
        end_date = self.factors["date"].max() if end_date is None else end_date
        _times = self.factors["time"].unique().to_list()
        _times.sort()
        times = _times if times is None else times
        logger.info(f"{beg_date} -> {end_date}: {times}")

        task_num = len(alpha_names)
        figs_collect = dict()
        with tqdm(total=task_num, desc="Generating report", leave=False) as bar:
            for alpha_name in alpha_names:
                bar.set_postfix_str(alpha_name)
                logger.info(f"REPORT NAME: {alpha_name}")
                _factor_data = self._to_alphalens(alpha_name,
                                                  demeaned=demeaned,
                                                  group_adjust=group_adjust,
                                                  beg_date=beg_date,
                                                  end_date=end_date,
                                                  times=times,
                                                  bins=N,
                                                  by_group=by_group,
                                                  reverse=reverse, )
                figs_collect[alpha_name] = model_performance_graph(_factor_data, lag=lag, N=N, show_notebook=show_notebook)
                bar.update()
            bar.close()
        return figs_collect

    def backtest(self,
                 expr: str,
                 weight_fn,
                 period: str = "",
                 limit: bool = True,
                 reverse: bool = False,
                 by_group: bool = False,
                 beg_date: str = None,
                 end_date: str = None,
                 times: list[str] = None,):

        """
        多因子回测
        Parameters
        ----------
        expr: str
        weight_fn: Callable
        period: str
        limit: bool
            是否限制涨跌停买卖
        reverse: bool
        by_group: bool
        beg_date: str
        end_date: str
        times: list[str]

        Returns
        -------
        polars.DataFrame

        """

        if limit:
            assert "limit" in self.factors.columns, "`limit` not in factors.columns"

        index = ("date", "time", "asset")
        logger.info("Calculating alpha expr.")
        self.sql(expr)
        if not period:
            period = self.periods[0]
        alias = Expr(expr).alias
        cols = [*index, pl.col(alias).alias("score")]
        if by_group:
            cols.append("group")
        df = self.factors.select(*cols)
        if reverse:
            df = df.with_columns((-pl.col("score")).alias("score"))

        beg_date = df["date"].min() if beg_date is None else beg_date
        end_date = df["date"].max() if end_date is None else end_date
        _times = df["time"].unique().to_list()
        _times.sort()
        times = _times if times is None else times
        logger.info(f"{beg_date} -> {end_date}: {times}")

        df = df.filter(
            (pl.col("date") >= beg_date),
            (pl.col("date") <= end_date),
            (pl.col("time").is_in(times)))

        weight_fn = ygo.delay(weight_fn)(by_group=by_group)
        weight_df = weight_fn(df)
        weight_df = lidb.from_polars(weight_df, index=index, align=True).data
        weight_df = (weight_df
                     .join(self.labels.select(*index, period), on=index, how="left")
                     .with_columns(target_weight=pl.col("target_weight").fill_null(0.0)))
        if limit:
            weight_df = weight_df.join(self.factors.select("date", "time", "asset", "limit"),
                                       on=["date", "time", "asset"],
                                       how="left")

        return backtest(weight_df, period, limit=limit)

    @property
    def periods(self) -> list[str]:
        res = list()
        if self._label_dls.data is None:
            return res
        index = ("date", "time", "asset")
        cols = self._label_dls.data.select(cs.exclude(index)).columns
        for col in cols:
            try:
                pd.Timedelta(col)
                res.append(col)
            except ValueError:
                # 解析失败，说明不是时间差
                pass
        return res

    @property
    def factors(self) -> pl.DataFrame | None:
        """过滤后的因子数据"""
        if self._qdf is not None:
            return self._qdf.data
        return self._factors

    @property
    def mounted(self) -> pl.DataFrame | None:
        return self._mount_dls.data

    @property
    def filters(self) -> pl.DataFrame | None:
        return self._filter_dls.data

    @property
    def labels(self) -> pl.DataFrame | None:
        return self._label_dls.data


zoo = Zoo()