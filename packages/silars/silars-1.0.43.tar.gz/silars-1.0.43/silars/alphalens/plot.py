# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/8 15:15
# Description:

from typing import Sequence, Literal

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import polars as pl
import statsmodels.api as sm
from scipy import stats

from .graph import ScatterGraph, SubplotsGraph, BarGraph, HeatmapGraph
from .tears import get_summary_report
from .utils import get_forward_returns_columns
from ..plot import table as Table
from ..plot.utils import guess_plotly_rangebreaks

layout = dict(template='gridon',
              hovermode='x unified',
              hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
              legend=dict(
                  orientation="h",  # 垂直排列
                  yanchor="bottom",  # 图例的锚点在上
                  y=1.02,  # 图例的 y 位置
                  # xanchor="center",  #
                  xanchor="right", # 靠右
                  x=1,
                  bordercolor='lightgrey',  # 边框颜色
                  borderwidth=1,  # 边框宽度
                  bgcolor='rgba(255, 255, 255, 0.8)',  # 背景颜色
              ),
              # margin=dict(r=0,),
              xaxis=dict(linecolor="black",
                         linewidth=1,
                         mirror=True,
                         gridcolor='lightgrey',
                         gridwidth=1,
                         griddash='dot',
                         showspikes=True,  # 启用 x 轴的十字光标
                         spikemode='across',  # 十字光标模式
                         spikecolor='black',  # 十字光标颜色
                         spikethickness=1.5,  # 十字光标粗细
                         spikedash='dot',), # 十字光标样式),
              yaxis=dict(linecolor="black",
                         linewidth=1,
                         mirror=True,
                         gridcolor='lightgrey',
                         gridwidth=1.5,
                         griddash='dot',
                         showspikes=True,  # 启用 x 轴的十字光标
                         spikemode='across',  # 十字光标模式
                         spikecolor='black',  # 十字光标颜色
                         spikethickness=1,  # 十字光标粗细
                         spikedash='dot',),  # 十字光标样式),
              height=500,
              )


def _group_return(pred_label: pl.DataFrame = None, N: int = 5, **kwargs) -> tuple:
    """
    绘制 分组收益 图: 平均收益(直方图)/累计收益(曲线图)
    Parameters
    ----------
    pred_label
    N
    by_group
    kwargs

    Returns
    -------

    """

    # Group1 ~ Group5 only consider the dropna values
    pred_label_drop = pred_label.drop_nulls(subset=["score"])

    # Group
    grouper = ["date", "time"]

    # demean
    pred_label_demeaned = pred_label.with_columns(
        (pl.col("label") - pl.col("label").mean().over(grouper)).alias("label"))

    long_demeaned = pred_label_demeaned.filter(pl.col("quantile") == str(N))

    # t_df = pred_label_drop.select("date", "time", "quantile", "label").drop("time").group_by("date", "quantile").sum().sort(
    #     by=["date", "quantile"])
    t_df = (pred_label_drop
            .select("date", "time", "quantile", "label")
            .group_by("date", "time", "quantile")
            .mean()
            .drop("time")
            .group_by("date", "quantile")
            .sum()
            .sort(by=["date", "quantile"]))
    # 分组平均收益
    group_mean = t_df.group_by("quantile").mean().drop("date")
    group_mean = group_mean.with_columns((pl.col("label") * 1e4).round(2))
    # group_mean_figure = finplot.bar_plot(group_mean.to_pandas().set_index("quantile", drop=True), title="Group Mean Returns")
    group_mean = group_mean.to_pandas().set_index("quantile", drop=True)
    group_bar_figure = BarGraph(
        group_mean,
        layout=dict(
            title="Group Mean Return",
            # xaxis=dict(rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(group_mean.index))),
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
        ),
    ).figure
    group_bar_figure.update_layout(**layout,)

    long_demeaned = (long_demeaned
                     .select("date", "time", pl.col("label").alias("long-average"))
                     .group_by("date", "time")
                     .mean()
                     .drop("time")
                     .group_by("date")
                     .sum()
                     .sort(by="date"))
    t_df = t_df.pivot(on="quantile", index="date", values="label").join(long_demeaned, on="date", how="left")
    t_df = t_df.with_columns(
        (pl.col(str(N)) - pl.col("1")).alias("long-short"),
    ).to_pandas().set_index("date", drop=True)
    t_df.rename(columns={str(i): f"Group{i}" for i in range(1, N + 1)}, inplace=True)
    t_df.index = pd.to_datetime(t_df.index)

    t_df = t_df.dropna(how="all")  # for days which does not contain label
    # Cumulative Return By Group
    group_scatter_figure = ScatterGraph(
        (t_df.fillna(0.0)+1).cumprod()-1,
        layout=dict(
            title="Cumulative Return",
            xaxis=dict(tickangle=45, rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(t_df.index))),
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
        ),
    ).figure
    group_scatter_figure.update_xaxes(tickformat="%Y-%m-%d",)
    group_scatter_figure.update_layout(**layout,)

    t_df = t_df.loc[:, ["long-short", "long-average"]]
    _bin_size = float(((t_df.max() - t_df.min()) / 20).min())
    group_hist_figure = SubplotsGraph(
        t_df,
        kind_map=dict(kind="DistplotGraph", kwargs=dict(bin_size=_bin_size)),
        subplots_kwargs=dict(
            rows=1,
            cols=2,
            print_grid=False,
            subplot_titles=["long-short", "long-average"],
        ),
    ).figure

    return group_bar_figure, group_scatter_figure, group_hist_figure


def _plot_qq(data: pd.Series = None, dist=stats.norm) -> go.Figure:
    """

    :param data:
    :param dist:
    :return:
    """
    # NOTE: plotly.tools.mpl_to_plotly not actively maintained, resulting in errors in the new version of matplotlib,
    # ref: https://github.com/plotly/plotly.py/issues/2913#issuecomment-730071567
    # removing plotly.tools.mpl_to_plotly for greater compatibility with matplotlib versions
    _plt_fig = sm.qqplot(data.dropna(), dist=dist, fit=True, line="45")
    plt.close(_plt_fig)
    qqplot_data = _plt_fig.gca().lines
    fig = go.Figure()

    fig.add_trace(
        {
            "type": "scatter",
            "x": qqplot_data[0].get_xdata(),
            "y": qqplot_data[0].get_ydata(),
            "mode": "markers",
            "marker": {"color": "#19d3f3"},
        }
    )

    fig.add_trace(
        {
            "type": "scatter",
            "x": qqplot_data[1].get_xdata(),
            "y": qqplot_data[1].get_ydata(),
            "mode": "lines",
            "line": {"color": "#636efa"},
        }
    )
    del qqplot_data
    fig.update_layout(**dict(hovermode='x unified', hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'), ))
    return fig


def _pred_ic(
        pred_label: pl.DataFrame = None, methods: Sequence[Literal["IC", "Rank IC"]] = ("IC", "Rank IC"), **kwargs
) -> tuple:
    """

    :param pred_label: pd.DataFrame
    must contain one column of realized return with name `label` and one column of predicted score names `score`.
    :param methods: Sequence[Literal["IC", "Rank IC"]]
    IC series to plot.
    IC is sectional pearson correlation between label and score
    Rank IC is the spearman correlation between label and score
    For the Monthly IC, IC histogram, IC Q-Q plot.  Only the first type of IC will be plotted.
    :return:
    """
    _methods_mapping = {"IC": "pearson", "Rank IC": "spearman"}
    grouper = ["date", "time"]

    ic_df = (pred_label
             .drop_nulls(subset=grouper)
             .group_by(grouper)
             .agg(pl.corr("score", "label", method=_methods_mapping[m]).alias(m) for m in methods)
             .drop("time")
             .group_by("date")
             .mean().sort(by="date"))
    ic_df = ic_df.to_pandas().set_index("date", drop=True)
    ic_df.index = pd.to_datetime(ic_df.index)

    _ic = ic_df.iloc(axis=1)[0]

    _index = _ic.index.get_level_values(0).astype("str").str.replace("-", "").str.slice(0, 6)
    _monthly_ic = _ic.groupby(_index).mean()
    _monthly_ic.index = pd.MultiIndex.from_arrays(
        [_monthly_ic.index.str.slice(0, 4), _monthly_ic.index.str.slice(4, 6)],
        names=["year", "month"],
    )

    # fill month
    _month_list = pd.date_range(
        start=pd.Timestamp(f"{_index.min()[:4]}0101"),
        end=pd.Timestamp(f"{_index.max()[:4]}1231"),
        freq="1ME",
    )
    _years = []
    _month = []
    for _date in _month_list:
        _date = _date.strftime("%Y%m%d")
        _years.append(_date[:4])
        _month.append(_date[4:6])

    fill_index = pd.MultiIndex.from_arrays([_years, _month], names=["year", "month"])

    _monthly_ic = _monthly_ic.reindex(fill_index)

    ic_bar_figure = ic_figure(ic_df, kwargs.get("show_nature_day", False))

    ic_heatmap_figure = HeatmapGraph(
        _monthly_ic.unstack(),
        layout=dict(title="Monthly IC",
                    xaxis=dict(dtick=1),
                    yaxis=dict(tickformat="04d", dtick=1),
                    hovermode='x unified',
                    hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'), ),
        graph_kwargs=dict(xtype="array", ytype="array"),
    ).figure
    ic_heatmap_figure.update_layout(**layout,)

    dist = stats.norm
    _qqplot_fig = _plot_qq(_ic, dist)

    if isinstance(dist, stats.norm.__class__):
        dist_name = "Normal"
    else:
        dist_name = "Unknown"

    _ic_df = _ic.to_frame("IC")
    _bin_size = ((_ic_df.max() - _ic_df.min()) / 20).min()
    _sub_graph_data = [
        (
            "IC",
            dict(
                row=1,
                col=1,
                name="",
                kind="DistplotGraph",
                graph_kwargs=dict(bin_size=_bin_size),
            ),
        ),
        (_qqplot_fig, dict(row=1, col=2)),
    ]
    ic_hist_figure = SubplotsGraph(
        _ic_df.dropna(),
        kind_map=dict(kind="HistogramGraph", kwargs=dict()),
        subplots_kwargs=dict(
            rows=1,
            cols=2,
            print_grid=False,
            subplot_titles=["IC", "IC %s Dist. Q-Q" % dist_name],
        ),
        sub_graph_data=_sub_graph_data,
        layout=dict(
            yaxis2=dict(title="Observed Quantile"),
            xaxis2=dict(title=f"{dist_name} Distribution Quantile"),
        ),
    ).figure

    return ic_bar_figure, ic_heatmap_figure, ic_hist_figure


def ic_figure(ic_df: pd.DataFrame, show_nature_day=True, **kwargs) -> go.Figure:
    r"""IC figure

    :param ic_df: ic DataFrame
    :param show_nature_day: whether to display the abscissa of non-trading day
    :param \*\*kwargs: contains some parameters to control plot style in plotly. Currently, supports
       - `rangebreaks`: https://plotly.com/python/time-series/#Hiding-Weekends-and-Holidays
    :return: plotly.graph_objs.Figure
    """
    if show_nature_day:
        date_index = pd.date_range(ic_df.index.min(), ic_df.index.max())
        ic_df = ic_df.reindex(date_index)
    ic_bar_figure = BarGraph(
        ic_df,
        layout=dict(
            title="Information Coefficient (IC)",
            xaxis=dict(tickangle=45, rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(ic_df.index))),
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
        ),
    ).figure
    ic_bar_figure.update_xaxes(tickformat="%Y-%m-%d",)
    ic_bar_figure.update_layout(**layout,)
    return ic_bar_figure


def _pred_autocorr(pred_label: pl.DataFrame, lag=1, **kwargs) -> tuple:
    df = pred_label.with_columns(score_lag=pl.col("score").shift(lag).over("asset", order_by=["date", "time"]))
    _df = df.drop_nulls(["score", "score_lag"]).group_by("date").agg(
        autocorr=pl.corr("score", "score_lag", method="spearman")).sort("date")
    _df = _df.to_pandas().set_index("date", drop=True)
    _df.index = pd.to_datetime(_df.index)
    ac_figure = ScatterGraph(
        _df,
        layout=dict(
            title="Auto Correlation",
            xaxis=dict(tickangle=45, rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(_df.index))),
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
        ),
    ).figure
    ac_figure.update_xaxes(tickformat="%Y-%m-%d",)
    ac_figure.update_layout(**layout,)
    return (ac_figure,)


def _pred_turnover(pred_label: pl.DataFrame, N=5, lag=1, **kwargs) -> tuple:
    pred_label = pred_label.drop_nulls(subset="quantile").filter(
        ((pl.col("quantile") == "1") | (pl.col("quantile") == str(N))))
    grouper = ["quantile", "date", "time"]
    cur_asset_set = pred_label.group_by(grouper).agg(
        pl.col("asset").unique()
    ).sort(by=grouper)
    shift_grouper = ["quantile", "time"]
    prev_asset_set = cur_asset_set.select(
        *grouper,
        pl.col("asset").shift(lag).over(shift_grouper)
    )
    r_df = cur_asset_set.join(
        prev_asset_set, on=grouper, how="left", suffix="_prev"
    ).with_columns(
        pl.col("asset").list.set_difference("asset_prev").alias("asset_diff").list.len().alias("diff_count"),
        pl.col("asset").list.len().alias("cur_count"),
    ).select(
        # "factor_quantile",
        "quantile", "date", "time",
        (pl.col("diff_count") / pl.col("cur_count")).alias("turnover")
    )
    r_df = r_df.group_by("quantile", "date").mean().drop("time").sort(by="date")
    r_df = r_df.pivot(on="quantile", index="date", values="turnover").to_pandas().set_index("date", drop=True)
    r_df.rename(columns={"1": "Group1", str(N): f"Group{N}"}, inplace=True)
    r_df.index = pd.to_datetime(r_df.index)

    turnover_figure = ScatterGraph(
        r_df,
        layout=dict(
            title="Top-Bottom Turnover",
            xaxis=dict(tickangle=45, rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(r_df.index))),
            hovermode='x unified',
            hoverlabel=dict(bgcolor='rgba(255, 255, 255, 0.5)'),
        ),
    ).figure
    turnover_figure.update_xaxes(tickformat="%Y-%m-%d",)
    turnover_figure.update_layout(**layout,)
    return (turnover_figure,)


def model_performance_graph(
        factor_data: pl.DataFrame,
        lag: int = 1,
        N: int = 5,
        graph_names: tuple[str] = ("group_return", "pred_ic", "pred_autocorr", "pred_turnover"),
        show_notebook: bool = True,
        show_nature_day: bool = False,
        **kwargs,
) -> [list, tuple]:
    r"""Model performance

    :return: if show_notebook is True, display in notebook; else return `plotly.graph_objs.Figure` list.
    """
    common_figs = list()
    # label已经在 factor_data 层面处理过，所以 long_short/group_neutral 均设置为 False
    summary_tb = get_summary_report(factor_data,
                                    long_short=True, # 减去市场平均
                                    group_neutral=False,
                                    by_time=True)
    table = Table(summary_tb.to_pandas(), highlight_cols=["ic", "top_bps", "bottom_bps", "spread_bps"])
    common_figs.append(table)
    if show_notebook:
        BarGraph.show_graph_in_notebook(common_figs)
    periods = get_forward_returns_columns(factor_data.columns)
    figure_dict = dict()

    for period in periods:
        pred_label = factor_data.select("date", "time", "asset",
                                        pl.col("factor").alias("score"),
                                        pl.col(period).alias("label"),
                                        pl.col("factor_quantile").alias("quantile"))
        figure_list = []
        for graph_name in graph_names:
            fun_res = eval(f"_{graph_name}")(
                pred_label=pred_label, lag=lag, N=N, show_nature_day=show_nature_day, **kwargs
            )
            figure_list += fun_res

        if show_notebook:
            BarGraph.show_graph_in_notebook(figure_list)
        figure_dict[period] = figure_list
    return common_figs, figure_dict
