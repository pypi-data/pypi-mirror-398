# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2024/12/9 下午3:07
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""

from pyecharts import options as opts
from matplotlib.colors import to_rgba
from pyecharts.charts import Bar
from pyecharts.globals import ThemeType

class Options:
    # 颜色配置
    colors = [
        'rgba(255, 99, 132, 1)',  # 红色
        'rgba(54, 162, 235, 1)',  # 蓝色
        'rgba(255, 193, 7, 1)',  # 黄色
        'rgba(140, 86, 75, 1)',  # 棕色
        'rgba(153, 102, 255, 1)',  # 紫色
        'rgba(227, 119, 194, 1)',  # 粉色
        'rgba(75, 192, 192, 1)',  # 绿色
        'rgba(255, 187, 120, 1)',  # 橙色
        *[f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {int(a)})" for r, g, b, a in [to_rgba(color) for color in Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS)).colors]],
        'rgba(169, 169, 169, 1)',  # 深灰色
    ]

    class Table:
        # 表头设置
        header = dict(font=dict(color="black", size=12),  # dict(size=13, family="Arial, sans-serif", color='#ffffff'),
                      fill_color='gold',  # '#3552a2',
                      align='center',
                      line_color='darkslategray',
                      )
        # 单元格配置
        cell = dict(align='center',
                    line_color='darkslategray',
                    )

    # layout plotly
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

    @staticmethod
    def get_colors(alpha):
        """更改透明度"""
        new_colors = list()
        for color in Options.colors:
            # 提取 RGB 部分并替换透明度
            rgb_part = color[:-2]  # 去掉最后的透明度部分
            new_color = f"{rgb_part}{alpha})"  # 添加新的透明度
            new_colors.append(new_color)
        return new_colors

    # echarts 悬停框样式
    echarts_opts = dict(
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            background_color="rgba(255, 255, 255, 0.5)",  # 背景颜色
            # border_color="black",  # 边框颜色
            border_width=1,  # 边框宽度
            axis_pointer_type="cross",
            textstyle_opts=opts.TextStyleOpts(color="black")  # 文字颜色
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
        ),
        datazoom_opts=[
            opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
            opts.DataZoomOpts(type_="slider", range_start=0, range_end=100)
        ],
    )

    # 悬停十字光标样式
    axispointer_opts = dict(
        axispointer_opts=opts.AxisPointerOpts(
            is_show=True,
            linestyle_opts=opts.LineStyleOpts(
                type_="dashed",
                # color="black",  # 设置十字光标颜色
                width=2         # 设置十字光标宽度
            )
        ),
        # axisline_opts=opts.AxisLineOpts(on_zero_axis_index=1, linestyle_opts=opts.LineStyleOpts(width=1, color="black"))
    )

    @staticmethod
    def get_echarts_options(xaxis_name: str=None, yaxis_name: str=None, title: str=None, hidden: list=None):
        default_opts = dict()
        x_axis = {k: v for k, v in Options.axispointer_opts.items()}
        if xaxis_name is not None:
            x_axis["name"] = xaxis_name
        default_opts["xaxis_opts"] = opts.AxisOpts(**x_axis)
        y_axis = {k: v for k, v in Options.axispointer_opts.items()}
        if yaxis_name is not None:
            y_axis["name"] = xaxis_name
        default_opts["yaxis_opts"] = opts.AxisOpts(**y_axis)
        default_opts.update(Options.echarts_opts)
        if title is not None:
            default_opts["title_opts"] = opts.TitleOpts(title=title)
        if hidden is not None:
            default_opts["legend_opts"] = opts.LegendOpts(selected_map={n: False for n in hidden})
        return default_opts
