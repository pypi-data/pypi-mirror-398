# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/7/23 10:16
# Description:

def guess_plotly_rangebreaks(dt_index):
    """
    This function `guesses` the rangebreaks required to remove gaps in datetime index.
    It basically calculates the difference between a `continuous` datetime index and index given.

    For more details on `rangebreaks` params in plotly, see
    https://plotly.com/python/reference/layout/xaxis/#layout-xaxis-rangebreaks

    Parameters
    ----------
    dt_index: pandas.DatetimeIndex
    The datetimes of the data.

    Returns
    -------
    the `rangebreaks` to be passed into plotly axis.

    Notes
    -----
    Copyright (c) Microsoft Corporation.
    Licensed under the MIT License.
    """
    dt_idx = dt_index.sort_values()
    gaps = dt_idx[1:] - dt_idx[:-1]
    min_gap = gaps.min()
    gaps_to_break = {}
    for gap, d in zip(gaps, dt_idx[:-1]):
        if gap > min_gap:
            gaps_to_break.setdefault(gap - min_gap, []).append(d + min_gap)
    return [dict(values=v, dvalue=int(k.total_seconds() * 1000)) for k, v in gaps_to_break.items()]