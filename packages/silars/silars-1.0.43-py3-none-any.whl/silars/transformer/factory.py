# Copyright (c) ZhangYundi.
# Licensed under the MIT License.
# Created on 2025/7/17 10:53
# Description:

import inspect
import math
from collections.abc import Sequence, Iterable
from typing import Literal

import numpy as np
import polars as pl
import ygo
from sklearn.base import BaseEstimator, TransformerMixin

SPECIAL_VALUES = {
    "null": None,
    "none": None,
    "nan": None,
    "inf": np.inf,
    "-inf": -np.inf,
    "int": int,
}




class Function(BaseEstimator, TransformerMixin):
    """
    将任意函数封装为支持 set_params 的 BaseEstimator

    Parameters
    ----------
    fn: callable
        方法对象
    kwargs: dict
        fn的参数

    Examples
    --------
    >>> import polars as pl
    >>> func = Function(lambda date, ds_path: pl.scan_parquet("/path/to/your/data.parquet"))
    >>> func.set_params(ds_path="mc/stock_kline_day")
    """

    def __init__(self, fn: callable, **kwargs):
        self.fn = ygo.delay(fn)(**kwargs)
        self.params = {k: inspect.Parameter.empty for k in ygo.fn_signature_params(self.fn)}
        self.params.update(self.fn.stored_kwargs)

    def set_params(self, **params):
        self.fn = ygo.delay(self.fn)(**params)
        self.params.update(self.fn.stored_kwargs)
        return self

    def get_params(self, deep=True):
        return self.params

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if self.fn is None:
            raise ValueError("Function not provided.")
        params = {k: v for k, v in self.fn.stored_kwargs.items() if v is not inspect.Parameter.empty}
        return self.fn(X, **params)


class DropNull(BaseEstimator, TransformerMixin):
    """
    Drop all rows that contain one or more null values

    Parameters
    ----------
    subset: Sequence[str] | str | None
        剔除空值的字段, 支持sql
    Notes
    -----
    使用sql字段时，尤其注意收益字段

    """

    def __init__(self, subset: Sequence[str] | str | None = None):
        self.subset = subset

    def fit(self, X=None, y=None):
        return self

    def transform(self, X: pl.LazyFrame):
        if self.subset:
            return X.drop_nulls(pl.sql_expr(self.subset))
        return X


class Cast(BaseEstimator, TransformerMixin):
    """
    类型转换

    Parameters
    ----------
    old: str | polars.DataType | polars.Expr
        原本类型或者需要转换的列
    new: polars.DataType
        转换的目标类型

    Examples
    --------
    >>> Cast("asset", pl.UInt16)

    """

    def __init__(self, old: pl.Expr | str | pl.DataType = None, new=None):
        self.old = old
        self.new = new
        self.old_expr: pl.Expr = None

    def fit(self, X, y=None):
        if isinstance(self.old, str):
            if self.old in SPECIAL_VALUES:
                self.old = SPECIAL_VALUES[self.old]
        self.old_expr = self.old if isinstance(self.old, pl.Expr) else pl.col(self.old)
        return self

    def transform(self, X):
        return X.with_columns(self.old_expr.cast(self.new))


class Imputer(BaseEstimator, TransformerMixin):
    """
    插值器

    Parameters
    ----------
    strategy
        插值策略
    over_spec
        用于滚动插值
    columns
        需要处理的列
    """

    def __init__(self,
                 strategy: Literal[
                               "forward", "backward", "mean", "zero", "max", "min", "one"] | None = "forward",
                 over_spec: dict | None = None,
                 columns: Sequence[str] | None = None):
        self.strategy = strategy
        self.over_spec = over_spec
        self.columns = [columns, ] if isinstance(columns, str) else columns
        self._exprs: list[pl.Expr] = list()

    def fit(self, X=None, y=None):
        return self

    def transform(self, X: pl.LazyFrame):
        cols = X.collect_schema().names() if not self.columns else self.columns
        if not self.over_spec:
            self._exprs = [pl.col(col).fill_null(strategy=self.strategy) for col in cols]
        else:
            self._exprs = [pl.col(col).fill_null(strategy=self.strategy).over(**self.over_spec) for col in self.columns]
        return X.with_columns(self._exprs)


class Replace(BaseEstimator, TransformerMixin):
    """
    替换器

    Parameters
    ----------
    columns: list
        需要替换的目标列
    old
        旧值, 可以是list, 如[np.inf, -np.inf]
    new
        新值
    """

    def __init__(self, columns: list | None = None, old=None, new=None):

        self.columns = columns
        self.old = old
        self.new = new

    def fit(self, X, y=None):
        if isinstance(self.old, str):
            if self.old in SPECIAL_VALUES:
                self.old = SPECIAL_VALUES[self.old]
        elif isinstance(self.old, Iterable):
            self.old = [SPECIAL_VALUES[old] if old in SPECIAL_VALUES else old for old in self.old]
        if self.columns is None:
            self.columns = list()
        return self

    def transform(self, X):
        return X.with_columns(pl.col(c).replace(self.old, self.new) for c in self.columns)


class Target(BaseEstimator, TransformerMixin):
    """
    添加目标收益列

    Parameters
    ----------
    price_tag
        价格列，支持sql语法，如 `if(ask_p1 > 0, bid_p1 > 0, (ask_p1+bid_p1)/2, null) as price`
    frequency
        数据集频率, 默认`3s`
    target
        目标收益，默认`5min`。大于日级别的：出场价使用最后一条数据
    partition_by
        分区
    order_by
        排序
    """

    def __init__(self,
                 price_tag: str = "price",
                 frequency: str = "3s",
                 target: str = "5min",
                 gap: str = "3s",
                 partition_by: Sequence[str] | str = "asset",
                 order_by: Sequence[str] | str | None = "time",
                 alias: str = None):
        self.price_tag = price_tag
        self.frequency = frequency
        self.target = target
        self.gap = gap
        self.partition_by = partition_by
        self.order_by = order_by
        self.alias = alias
        self._exprs = list()

    def fit(self, X=None, y=None):
        from pandas import Timedelta
        self.alias = self.alias if self.alias else self.target
        over_spec = {"partition_by": self.partition_by}
        if self.order_by:
            over_spec["order_by"] = self.order_by
        freq_secs = int(Timedelta(self.frequency).seconds)
        target_timedelta = Timedelta(self.target)
        if target_timedelta.days > 0:
            expr_target = (
                (
                        pl.sql_expr(self.price_tag)
                        .last()
                        .over(**over_spec) / pl.sql_expr(self.price_tag) - 1
                ).alias(self.alias)
            )
        else:
            expr_target = (
                (
                        pl.sql_expr(self.price_tag)
                        .shift(-math.ceil(target_timedelta.seconds / freq_secs))
                        .over(**over_spec) / pl.sql_expr(self.price_tag) - 1
                ).alias(self.alias)
            )
        expr_inf = pl.col(self.alias).cast(pl.Float32).replace([float("inf"), float("-inf")], None)

        self._exprs = [expr_target, expr_inf]
        gap_secs = int(Timedelta(self.gap).seconds)
        if gap_secs > 0:
            expr_gap = (
                pl.col(self.alias)
                .shift(-math.ceil(gap_secs / freq_secs))
                .over(**over_spec)
            )
            self._exprs.insert(1, expr_gap)
        return self

    def transform(self, X: pl.LazyFrame):
        for expr in self._exprs:
            X = X.with_columns(expr)
        return X


class TargetFromDifferentTag(BaseEstimator, TransformerMixin):
    """
    添加目标收益列: 使用不同的价格列

    Parameters
    ----------
    enter_price_tag: str
        进场价格列，支持sql语法，如 `if(ask_p1 > 0, bid_p1 > 0, (ask_p1+bid_p1)/2, null) as price`
    exit_price_tag: str
        出场价格列
    frequency
        数据集频率, 默认`3s`
    target
        目标收益，默认`5min`
    partition_by
        分区
    order_by
        排序
    alias: str
        重新命名
    """

    def __init__(self,
                 enter_price_tag: str,
                 exit_price_tag: str,
                 frequency: str = "3s",
                 target: str = "5min",
                 gap: str = "3s",
                 partition_by: Sequence[str] | str = "asset",
                 order_by: Sequence[str] | str | None = "time",
                 alias: str = None):
        self.enter_price_tag = enter_price_tag
        self.exit_price_tag = exit_price_tag
        self.frequency = frequency
        self.target = target
        self.gap = gap
        self.partition_by = partition_by
        self.order_by = order_by
        self.alias = alias
        self._exprs = list()

    def fit(self, X=None, y=None):
        from pandas import Timedelta
        self.alias = self.alias if self.alias else self.target
        over_spec = {"partition_by": self.partition_by}
        if self.order_by:
            over_spec["order_by"] = self.order_by
        freq_secs = int(Timedelta(self.frequency).seconds)
        expr_target = (
            (
                    pl.sql_expr(self.exit_price_tag)
                    .shift(-math.ceil(Timedelta(self.target).seconds / freq_secs))
                    .over(**over_spec) / pl.sql_expr(self.enter_price_tag) - 1
            ).alias(self.alias)
        )
        expr_inf = pl.col(self.alias).cast(pl.Float32).replace([float("inf"), float("-inf")], None)

        self._exprs = [expr_target, expr_inf]
        gap_secs = int(Timedelta(self.gap).seconds)
        if gap_secs > 0:
            expr_gap = (
                pl.col(self.alias)
                .shift(-math.ceil(gap_secs / freq_secs))
                .over(**over_spec)
            )
            self._exprs.insert(1, expr_gap)
        return self

    def transform(self, X: pl.LazyFrame):
        for expr in self._exprs:
            X = X.with_columns(expr)
        return X

class Reindex(BaseEstimator, TransformerMixin):

    def __init__(self, new_index: pl.LazyFrame | pl.DataFrame):
        self.new_index = new_index

    def fit(self, X, y=None):
        self.new_index = self.new_index.lazy()
        return self

    def transform(self, X: pl.LazyFrame):
        return self.new_index.join(X, on=self.new_index.collect_schema().names(), how="left")