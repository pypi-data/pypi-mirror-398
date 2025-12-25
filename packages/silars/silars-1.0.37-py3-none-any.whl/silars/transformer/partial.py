# Copyright (c) ZhangYundi.
# Licensed under the MIT License.
# Created on 2025/7/17 10:53
# Description:

import polars as pl
from sklearn.base import BaseEstimator, TransformerMixin


class StandardScaler(BaseEstimator, TransformerMixin):
    """
    Parameters
    ----------
    ddof: int
        自由度(0为总体标准差，1为样本标准差)
    """

    def __init__(self, subset: list[str], ddof=1):
        self.subset = subset
        self._count = {col: 0 for col in subset}
        self._mean = {col: 0 for col in subset}
        self._M2 = {col: 0 for col in subset}
        self.count = None
        self.mean = None
        self.M2 = None
        self.ddof = ddof
        self.reset()

    def reset(self):
        """重置"""
        self._count = {col: 0 for col in self.subset}
        self._mean = {col: 0 for col in self.subset}
        self._M2 = {col: 0 for col in self.subset}
        self.count = pl.DataFrame(self._count)
        self.mean = pl.DataFrame(self._mean)
        self.M2 = pl.DataFrame(self._M2)

    def fit(self, X: pl.DataFrame, y=None):
        self.reset()
        self.partial_fit(X, y)
        return self

    def partial_fit(self, X: pl.DataFrame, y=None):
        data = X.select(self.subset)
        mu_new = data.mean()
        n_new = data.count() - data.null_count()
        m2_new = data.select(((pl.col(c) - mu_new[c]) ** 2).sum() for c in self.subset)
        # 新旧均值差异
        delta = mu_new - self.mean
        # 全局均值
        new_count = self.count + n_new
        new_mean = (self.mean * self.count + mu_new * n_new) / new_count
        # 全局M2
        # 误差项
        correction_term = delta.select(pl.col(c) ** 2 * (self.count[c] * n_new[c]) / new_count[c] for c in self.subset)

        new_M2 = self.M2 + m2_new + correction_term
        # 更新状态
        self.count = new_count
        self.mean = new_mean
        self.M2 = new_M2
        return self

    def get_std(self, col: str):
        return (self.M2[col] / (self.count[col] - self.ddof)) ** 0.5

    def transform(self, X: pl.DataFrame):
        if not self.subset:
            return X
        return (X
                .with_columns((pl.col(c) - self.mean[c]) / self.get_std(c) for c in self.subset)
                .with_columns(pl.col(c).cast(pl.Float32).replace([float("inf"), float("-inf")], None) for c in self.subset))

    def partial_fit_transform(self, X: pl.DataFrame, y=None):
        if not self.subset:
            return X
        return self.partial_fit(X).transform(X)
