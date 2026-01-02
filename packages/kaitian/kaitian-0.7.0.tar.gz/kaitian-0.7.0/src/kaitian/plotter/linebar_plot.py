"""线柱图

如果数据集中包含线性维度, 例如时间, 为了表示多种维度的动态变化, 常常把线柱图绘制在同一个
画布上, 共享线性轴, 线图表示变化趋势, 柱图表示切片的分布.
"""

from __future__ import annotations

import logging
from typing import Literal

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import polars as pl
from matplotlib.lines import Line2D

from .themer import Theme, Themer


def _plot_bar(
    bars: pl.DataFrame,
    highlights: list[str] | None,
    bar_style: Literal["stack", "overlap", "parallel"],
    ax: plt.Axes,
    themer: Themer,
) -> tuple[plt.Axes, list[mpatches.Patch]]:
    bar_width = 0.8 / bars.width if bar_style == "parallel" else 0.8  # 非堆叠柱宽
    highlights = highlights or []

    bars_xoffset = [0] * bars.width
    if bar_style == "overlap":
        bars_sorted = bars.select(sorted(bars.columns, key=lambda c: float(bars[c].mean())))  # type: ignore
    elif bar_style == "stack":
        bars_sorted = bars.select(sorted(bars.columns, key=lambda c: -float(bars[c].mean())))  # type: ignore
    else:
        bars_sorted = bars
        bars_xoffset = [idx * bar_width for idx in range(bars_sorted.width)]

    bars_yoffset = [0.0] * bars_sorted.height

    legend_handles = []
    for idx, bar_series in enumerate(bars_sorted.iter_columns()):
        if bar_series.name in highlights:
            color = themer.get_color(highlight=True)
        else:
            color = themer.get_color(highlight=False)

        ax.bar(
            [x + bars_xoffset[idx] for x in range(bars_sorted.height)],
            bar_series.to_list(),
            width=bar_width,
            label=bar_series.name,
            bottom=bars_yoffset,
            alpha=0.8,
            color=color,
        )
        legend_handles.append(
            mpatches.Patch(
                color=color,
                label=bar_series.name,
                alpha=0.8,
                fontproperties=themer.get_font("marker"),
            )
        )
        if bar_style == "stack":
            bars_yoffset = [b + y for b, y in zip(bars_yoffset, bar_series.to_list())]

    return ax, legend_handles


def _plot_line(
    lines: pl.DataFrame,
    highlights: list[str] | None,
    line_style: Literal["share", "exclusive"],
    ax: plt.Axes,
    themer: Themer,
) -> tuple[plt.Axes, list[mpatches.Patch]]:
    legend_handles = []
    highlights = highlights or []

    exclusive_ax: plt.Axes | None = None
    ax_offset = 0

    for idx, line_series in enumerate(lines.iter_columns()):
        if line_series.name in highlights:
            color = themer.get_color(highlight=True)
        else:
            color = themer.get_color(highlight=False)

        if line_style == "exclusive" or exclusive_ax is None:
            exclusive_ax = ax.twinx()

        exclusive_ax.plot(
            range(lines.height), line_series.to_list(), marker="o", label=line_series.name, linewidth=2, color=color
        )

        exclusive_ax.spines["right"].set_position(("outward", ax_offset))
        if line_style == "exclusive":
            ax_offset += 50
            exclusive_ax.set_ylabel(line_series.name, fontproperties=themer.get_font("marker"))

        legend_handles.append(
            Line2D(
                [],
                [],
                color=color,
                marker="o",
                label=line_series.name,
                linewidth=1.5,
                markersize=4,
                fontproperties=themer.get_font("marker"),
            )
        )

    return ax, legend_handles


def plot_linebar(
    data: pl.DataFrame,
    index: str,
    bars: list[str] | str | None = None,
    lines: list[str] | str | None = None,
    highlights: list[str] | str | None = None,
    title: str | None = None,
    xtick_rotation: float = 45,
    bar_style: Literal["stack", "overlap", "parallel"] = "parallel",
    line_style: Literal["share", "exclusive"] = "share",
    ax: plt.Axes | None = None,
    theme: Literal["science", "sharp", "nature", "purple"] | Theme = "science",
) -> plt.Axes:
    """绘制柱状图

    支持绘制柱状图, 堆叠柱状图, 柱线图, 折线图. 如果 `stack` 则会堆叠柱, 否则就并排.
    所有数据共享横坐标 `index`, 折线图会添加一个单独的纵坐标, 目前不支持折线图再添加
    第二个纵坐标.

    默认纵坐标轴为左一右一, 如果还有新增坐标轴, 例如独享模式的线图, 继续向右添加坐标轴.

    Parameters
    ----------
    data : pl.DataFrame
        预处理好的数据, 如果要绘制柱状图, 需要保证变量离散, 连续变量需要分箱或分组聚合.
    bars : list[str] | str, optional
        柱状图绘制对象, 支持同时绘制多个柱状图, 如果为空表示不绘制柱状图.
    lines : list[str] | str, optional
        折线图绘制对象, 支持同时绘制多个折线图, 如果为空表示不绘制折线图.
    title : str, optional
        图表标题, 默认为 None.
    ax : plt.Axes, optional
        绘制的画布, 如果不提供则创建一个新的画布.
        由于 Jupyter 的特殊机制 Inline 模式, 如果单元格执行完后发现存在未显示的 Figure, 会自动显示,
        所以在 ax = None 的情况下, 在 Jupyter 里调用该函数会自动显示.
        只建议在文学编程和测试时使用 ax = None, 其他情况都建议手动创建 Figure.
    theme : Literal["science", "sharp", "nature", "purple"] | Theme, optional
        主题, 默认为 "science".
    bar_style : stack | overlap | parallel, default parallel
        堆叠模式 stack: 从下往上绘制柱状图, 底层通过对数据进行加合实现, 可以用来表示相互之间的比例关系
        重叠模式 overlap: 从大到小直接绘制柱状图, 一般适用于不同序列大小差异较大的情况, 否则容易覆盖较小的序列
        并排模式 parallel: 并排绘制柱状图, 普通柱状图
        默认使用并排模式
    line_style: share | exclusive, default share
        共享模式 share: 多个线图共享一个纵坐标, 适合多个序列之间相互比较
        独立模式 exclusive: 每个线图都添加一个单独的纵坐标, 适合多个序列之间相互独立关系
    xtick_rotation : float, default 45
        横坐标标签旋转, 横坐标常见标签为时间戳, 过长可能影响读图, 一般会进行旋转.
    """
    logger = logging.getLogger(__name__)
    themer = Themer(theme=theme)

    if ax is None:
        logger.debug("未提供画布, 创建新画布")
        _, ax = plt.subplots()

    x_labels = data.get_column(index).to_list()

    if isinstance(highlights, str):
        highlights = [highlights]

    legends = []

    if bars is not None:
        # 绘制柱状图
        bars = [bars] if isinstance(bars, str) else bars
        ax, bars_legend = _plot_bar(
            bars=data.select(bars), highlights=highlights, bar_style=bar_style, ax=ax, themer=themer
        )
        legends += bars_legend

    if lines is not None:
        # 绘制折线图
        lines = [lines] if isinstance(lines, str) else lines
        ax, lines_legend = _plot_line(
            lines=data.select(lines), highlights=highlights, line_style=line_style, ax=ax, themer=themer
        )
        legends += lines_legend

    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=xtick_rotation, ha="right", fontproperties=themer.get_font("marker"))
    ax.set_xlabel(index, fontproperties=themer.get_font("marker"))

    if title is not None:
        ax.set_title(title, fontproperties=themer.get_font("title"))
    ax.legend(handles=legends, prop=themer.get_font("content"))
    return ax
