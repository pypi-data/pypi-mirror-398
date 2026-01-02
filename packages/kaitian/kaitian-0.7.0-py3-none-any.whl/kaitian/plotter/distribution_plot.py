"""Dist plot."""

from __future__ import annotations

import logging
from typing import Literal

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.stats import gaussian_kde

from ..utils.logger import silent_on_error
from .themer import Theme

_logger = logging.getLogger(__name__)


@silent_on_error
def plot_dist(
    series: list[pl.Series],
    ax: plt.Axes,
    theme: Literal["science", "sharp", "nature", "purple"] = "science",
    fontsize: int | None = None,
    title: str | None = None,
) -> plt.Axes:
    """绘制分布图

    绘制多个序列的密度分布图, 请确保传入的变量都是同一尺度. 密度图的源数据
    不需要来自同一张表, 例如需要绘制训练集和测试集某个指标的分布图, 此时该
    指标在不同数据集上必然尺度相同, 但是长度不一定相同, 所以需要以 `polars.Series`
    的格式传入.
    """
    themer = Theme(theme=theme, fontsize=fontsize)

    series_to_plot: list[tuple[str, np.ndarray, np.ndarray]] = []
    for s in series:
        if s.drop_nans().drop_nulls().len() == 0:
            _logger.warning(f"{s.name} 全为空, 无法绘制")
            continue
        try:
            _s = s.drop_nans().drop_nulls().to_numpy()
            _kde = gaussian_kde(_s)
            _x = np.linspace(_s.min(), _s.max(), 1000)
            _y = _kde(_x)
            series_to_plot.append((s.name, _x, _y))
        except Exception as e:
            _logger.error(f"{s.name} 绘制失败: {e}")
            continue

    if len(series_to_plot) == 0:
        raise ValueError("序列数据为空, 无法绘制")

    if len(series_to_plot) > 5:
        _logger.warning(f"需要绘制的序列数过多({len(series_to_plot)})")

    legend_handles = []
    for sname, sx, sy in series_to_plot:
        _color = themer.get_color()
        ax.plot(sx, sy, color=_color, alpha=0.5, linewidth=1, label=sname)
        legend_handles.append(mpatches.Patch(color=_color, label=sname, alpha=0.5))
        ax.fill_between(sx.tolist(), sy.tolist(), color=_color, alpha=0.5 * 0.5)

    if title is None:
        if len(series) == 1:
            title = f"{series[0].name} 分布图"
        else:
            title = "数据分布图"

    ax.set_title(title, fontproperties=themer.font)
    ax.set_xlabel("区间", fontproperties=themer.font)
    ax.set_ylabel("密度", fontproperties=themer.font)
    ax.legend(handles=legend_handles)
    return ax
