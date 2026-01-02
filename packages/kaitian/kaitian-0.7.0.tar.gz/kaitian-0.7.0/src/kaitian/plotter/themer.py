"""Themer 样式管理器"""

from __future__ import annotations

import importlib.resources as import_resources
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from matplotlib import font_manager


@dataclass
class HatchingStyle:
    """填充样式"""


@dataclass
class LineStyle:
    """线条样式"""


@dataclass
class Theme:
    font_title: font_manager.FontProperties  # 标题字体
    font_content: font_manager.FontProperties  # 内容字体, 备注, 图例, 坐标轴
    font_marker: font_manager.FontProperties  # 标记字体, 数据标签
    color_palette: list[str]  # 调色盘: 用于普通颜色组
    color_highlight: list[str]  # 高亮色: 用于需要强调的内容

    # hatching & line 通过与 palette 组合实现多对象绘制

    hatching_style: HatchingStyle  # 填充样式
    hatching_style_highlight: HatchingStyle  # 强调填充样式

    line_style: LineStyle  # 线条样式
    line_style_highlight: LineStyle  # 强调线条样式


class Themer:
    def __init__(self, theme: Literal["science", "sharp", "nature", "purple"] | Theme = "science") -> None:
        self._logger = logging.getLogger(__name__)

        if isinstance(theme, str):
            self._theme = self._build_default_theme(theme)
        else:
            self._theme = theme

        self._color_idx = 0
        self._color_highlight_idx = 0

    def _build_default_theme(self, default_theme: Literal["science", "sharp", "nature", "purple"]) -> Theme:
        with import_resources.path(f"{__package__}.static", f"theme_{default_theme}.json") as default_theme_file:
            default_theme_json = json.load(open(default_theme_file))

        with import_resources.path(f"{__package__}.static", "LXGWNeoXiHeiPlus.ttf") as default_font_file:
            theme = Theme(
                font_title=font_manager.FontProperties(
                    fname=Path(default_font_file),  # type: ignore
                    size="large",
                    weight="bold",
                ),
                font_content=font_manager.FontProperties(
                    fname=Path(default_font_file),  # type: ignore
                    size="medium",
                    weight="normal",
                ),
                font_marker=font_manager.FontProperties(
                    fname=Path(default_font_file),  # type: ignore
                    size="small",
                    weight="normal",
                ),
                color_palette=default_theme_json["color_palette"],
                color_highlight=default_theme_json["color_highlight"],
                hatching_style=HatchingStyle(),
                hatching_style_highlight=HatchingStyle(),
                line_style=LineStyle(),
                line_style_highlight=LineStyle(),
            )
        return theme

    def get_color(self, idx: int | None = None, highlight: bool = False) -> str:
        if highlight:
            color_idx = idx if idx is not None else self._color_highlight_idx
            color = self._theme.color_highlight[color_idx % len(self._theme.color_highlight)]
            if idx is None:
                self._color_highlight_idx += 1
        else:
            color_idx = idx if idx is not None else self._color_idx
            color = self._theme.color_palette[color_idx % len(self._theme.color_palette)]
            if idx is None:
                self._color_idx += 1

        return color

    def get_font(self, ftype: Literal['title', 'content', 'marker']) -> font_manager.FontProperties:
        if ftype == 'title':
            return self._theme.font_title
        elif ftype == 'content':
            return self._theme.font_content
        elif ftype == 'marker':
            return self._theme.font_marker
        else:
            raise ValueError(f"font type {ftype} is not supported")