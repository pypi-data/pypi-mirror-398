"""数据分箱器

连续特征分箱器, 支持默认实现和自定义分箱算法.
"""

from __future__ import annotations

import logging
from typing import Literal, Protocol, overload, runtime_checkable

import numpy as np
import polars as pl
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, _tree

from .__proto__ import Preprocessor

try:
    from rich.progress import Progress
except ImportError:
    Progress = None


class _MockTask:
    pass


class ProgressMock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_task(self, description, **kwargs):
        return _MockTask()

    def update(self, task, **kwargs):
        pass

    @property
    def finished(self):
        return True


BreakPoints = np.ndarray


@runtime_checkable
class BinningMethod(Protocol):
    def __call__(
        self,
        feature: np.ndarray,
        maxbins: int = 8,
        target: np.ndarray | None = None,
        left_closed: bool = True,
        **kwargs,
    ) -> BreakPoints: ...


@overload
def initialize(feature: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]: ...
@overload
def initialize(feature: np.ndarray) -> np.ndarray: ...
def initialize(feature: np.ndarray, target: np.ndarray | None = None) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Array 初始化"""
    feature = feature.flatten()

    if target is not None:
        target = target.flatten()
        return feature, target
    else:
        return feature


def get_boundry(feature: np.ndarray) -> tuple[float, float]:
    qmin, qleft, qright, qmax = np.nanquantile(initialize(feature), ([0.01, 0.25, 0.75, 0.99]))
    qdiff = qright - qleft
    if qdiff == 0:
        qleft = qmin
        qright = qmax
    # o_left = max(qleft - 3 * qdiff, np.nanmin(feature))
    # o_right = min(qright + 3 * qdiff, np.nanmax(feature))
    o_left = qleft - 3 * qdiff
    o_right = qright + 3 * qdiff
    return o_left, o_right


def prettify(feature: np.ndarray, breakpoints: np.ndarray, left_closed: bool) -> np.ndarray:
    """分割点优化

    优化后的分割点是原始数据中的值, 并且不会改变在特征上的分箱结果, 去除空值和重复值, 并重新排序
    """

    feature = initialize(feature)

    f_max = np.nanmax(feature)
    f_min = np.nanmin(feature)
    pretty_brkps = np.sort(np.unique(breakpoints[~np.isnan(breakpoints)]))

    # · brkp / ⌾ feature
    for idx, brkp in enumerate(pretty_brkps):
        if left_closed:
            # [-inf, ⌾), ..., [⌾, ⌾), [⌾, ·), [·, ⌾), [⌾, ⌾), ..., [⌾, +inf)
            if brkp <= f_min or brkp > f_max:
                pretty_brkps[idx] = np.nan
            else:
                # -- ⌾ [·) ⌾ -->
                pretty_brkps[idx] = np.nanmin(feature[feature >= brkp])
        else:
            # (-inf, ⌾], ..., (⌾, ⌾], (⌾, ·], (·, ⌾], (⌾, ⌾], ..., (⌾, +inf]
            if brkp < f_min or brkp >= f_max:
                pretty_brkps[idx] = np.nan
            else:
                # <-- ⌾ (·] ⌾ --
                pretty_brkps[idx] = np.nanmax(feature[feature <= brkp])

    pretty_brkps = pretty_brkps[(pretty_brkps > f_min) & (pretty_brkps < f_max)]
    pretty_brkps = np.sort(np.unique(pretty_brkps[~np.isnan(pretty_brkps)]))
    return pretty_brkps


def get_breakpoints_by_frequency(
    feature: np.ndarray,
    maxbins: int = 8,
    target: np.ndarray | None = None,
    left_closed: bool = True,
) -> BreakPoints:
    """等频分箱"""
    feature = initialize(feature)
    return np.sort(np.unique(np.nanquantile(feature, np.arange(1 / maxbins, 1.0, 1 / maxbins))))


def get_breakpoints_by_distance(
    feature: np.ndarray,
    maxbins: int = 8,
    target: np.ndarray | None = None,
    left_closed: bool = True,
    left: float | None = None,
    right: float | None = None,
) -> BreakPoints:
    """等距分箱"""

    # FIXME: 合并空箱

    feature = initialize(feature)
    o_left, o_right = get_boundry(feature)

    left_ = max(left or o_left, np.nanmin(feature))
    right_ = min(right or o_right, np.nanmax(feature))

    auto_gap: float = (right_ - left_) / maxbins
    if auto_gap <= 0:
        return np.array([])
    brkps = np.arange(left_ + auto_gap, right_, auto_gap)
    return np.sort(np.unique(brkps))


def get_breakpoints_by_rpretty(
    feature: np.ndarray,
    maxbins: int = 8,
    target: np.ndarray | None = None,
    left_closed: bool = True,
    rerange: bool = True,
) -> np.ndarray:
    """R's pretty method.

    类似等宽分箱, 最终的分箱宽度是 2, 5, 10 的倍数, 比较适合用于绘图和解释性处理,
    最终的分箱宽度是由原始值优化而来, 无法严格限制在 maxbins 个, 可能更多, 可能更少.
    """
    feature = initialize(feature)
    if rerange:
        low, high = get_boundry(feature)
    else:
        low = np.nanmin(feature)
        high = np.nanmax(feature)
    width = (high - low) / (maxbins - 1)

    if width <= 0:
        return np.array([])

    width_shrink = width / 10 ** np.floor(np.log10(width))
    if width_shrink < 1.5:
        width_pretty = 1.0
    elif width_shrink < 3.0:
        width_pretty = 2.0
    elif width_shrink < 7.0:
        width_pretty = 5.0
    else:
        width_pretty = 10.0
    width_pretty = width_pretty * 10.0 ** np.floor(np.log10(width))
    low_pretty = np.floor(low / width_pretty) * width_pretty
    high_pretty = np.ceil(high / width_pretty) * width_pretty

    breakpoints = np.arange(low_pretty, high_pretty + width_pretty * 0.5, width_pretty)
    breakpoints = np.sort(np.unique(breakpoints))
    return breakpoints


def get_breakpoints_by_tree(
    feature: np.ndarray,
    maxbins: int = 8,
    target: np.ndarray | None = None,
    left_closed: bool = True,
    seed: int = 42,
) -> BreakPoints:
    if target is None:
        raise ValueError("决策树分箱器必须提供标签值")
    data = pl.DataFrame({"x": feature, "y": target}, nan_to_null=True).drop_nulls()

    if data.height < 2:
        return np.array([])

    X = data.select(["x"]).to_numpy()
    y = data.get_column("y").to_numpy()

    if len(np.unique(y)) < 5:
        is_classification = True
    else:
        is_classification = False

    # 计算合适的树深度，通常分割点数不会超过2^max_depth - 1
    # 这里根据最大分割点数动态调整树深度
    max_depth = 1
    while (2**max_depth - 1) < maxbins and max_depth < 30:
        max_depth += 1

    # 初始化并训练决策树（增加参数控制复杂度）
    if is_classification:
        tree = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=max(2, len(X) // (maxbins + 1)),  # 动态调整分裂阈值
            random_state=seed,
        )
    else:
        tree = DecisionTreeRegressor(
            max_depth=max_depth,
            min_samples_split=max(2, len(X) // (maxbins + 1)),
            random_state=seed,
        )

    tree.fit(X, y)

    split_points = []
    tree_ = tree.tree_

    def traverse(node):
        if tree_.children_left[node] != _tree.TREE_LEAF and len(split_points) < maxbins:  # type: ignore
            split_points.append(tree_.threshold[node])  # type: ignore
            traverse(tree_.children_left[node])  # type: ignore
            traverse(tree_.children_right[node])  # type: ignore

    traverse(0)  # 从根节点开始遍历

    # 去重、排序并确保不超过最大限制
    split_points = sorted(list(set(split_points)))
    if len(split_points) > maxbins - 1:
        # 如果超过限制，均匀采样分割点
        indices = np.linspace(0, len(split_points) - 1, maxbins - 1, dtype=int)
        split_points = [split_points[i] for i in indices]

    brkps = np.sort(np.unique(np.array(split_points)))
    return brkps


def get_breakpoints_by_woeinit(
    feature: np.ndarray, maxbins: int = 8, target: np.ndarray | None = None, left_closed: bool = True
) -> np.ndarray:
    """scorecardpy.woebin 获取初始分割点

    复现 scorecardpy.woebin 获取初始分割点, 后续的决策树分箱和卡方分箱都是从该初始化点
    中逐个抓取得到的, 核心步骤:

    1. 处理 outlier
    2. 获取初始分割点 rpretty
    3. 合并空箱

    忽略 scorecardpy 对于特殊值和空值的处理.
    """
    assert target is not None
    feature, target = initialize(feature, target)

    if len(np.unique(feature)) <= 1:
        return np.empty(0, dtype=np.float64)

    # 1. 处理 outlier
    o_left, o_right = get_boundry(feature)
    feature_remove_outlier = feature[(feature >= o_left) & (feature <= o_right)]
    f_unique = np.unique(feature_remove_outlier)

    if maxbins > len(f_unique):
        maxbins = len(f_unique)
    if len(f_unique) < 10:
        breakpoints_init = np.sort(f_unique).astype(np.float64)
    else:
        breakpoints_init = get_breakpoints_by_rpretty(feature_remove_outlier, maxbins, rerange=False)

    # -inf, x1, x2, x3, ..., xn-1, xn
    #   |    |   |   |        |     |
    #  x1 , x2, x3, x4, ..., xn  , inf
    breakpoints_left = [-np.inf] + [i for i in breakpoints_init]
    breakpoints_right = [i for i in breakpoints_init] + [np.inf]

    if left_closed:
        _bin_all = [
            (len(target[(feature >= _left) & (feature < _right)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]
        _bin_good = [
            (len(target[(feature >= _left) & (feature < _right) & (target == 0)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]
        _bin_bad = [
            (len(target[(feature >= _left) & (feature < _right) & (target == 1)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]
    else:
        _bin_all = [
            (len(target[(feature > _left) & (feature <= _right)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]
        _bin_good = [
            (len(target[(feature > _left) & (feature <= _right) & (target == 0)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]
        _bin_bad = [
            (len(target[(feature > _left) & (feature <= _right) & (target == 1)]))
            for _left, _right in zip(breakpoints_left, breakpoints_right)
        ]

    _bin_empty = [1 if (_good == 0 or _bad == 0) else 0 for _good, _bad in zip(_bin_good, _bin_bad)]

    while _bin_empty.count(1):
        # 定位到 _bin_empty == 1 且 _bin_all 最小的位置
        _bin_all_masked = [_all if _empty else np.inf for _all, _empty in zip(_bin_all, _bin_empty)]
        _index = np.array(_bin_all_masked).argmin()
        _ = _bin_empty.pop(_index)
        _good = _bin_good.pop(_index)
        _bad = _bin_bad.pop(_index)
        _all = _bin_all.pop(_index)

        if len(_bin_all) == 0:
            break

        if _index == 0:
            # 删除第一箱
            # -inf,  ~x1~, x2, x3, ..., xn-1, xn
            #   |   \  |   |   |        |     |
            #  ~x1~,  x2, x3, x4, ..., xn  , inf
            _ = breakpoints_left.pop(1)
            _ = breakpoints_right.pop(0)
            _bin_good[0] += _good
            _bin_bad[0] += _bad
            _bin_all[0] += _all
        elif _index == len(_bin_all_masked) - 1:
            # 删除最后一箱
            # -inf, x1, x2, x3, ..., xn-1, ~xn~
            #   |   |    |   |        |  \  |
            #  x1, x2,  x3, x4, ..., ~xn~, inf
            _ = breakpoints_left.pop(-1)
            _ = breakpoints_right.pop(-2)
            _bin_good[-1] += _good
            _bin_bad[-1] += _bad
            _bin_all[-1] += _all
        else:
            # 确定相邻箱数量
            _all_left = _bin_all[_index - 1]
            _all_right = _bin_all[_index]
            #       _al ⇩ _ar
            # -inf, x1, x2, x3, ..., xn-1, ~xn~
            #   |   |    |   |        |  \  |
            #  x1, x2,  x3, x4, ..., ~xn~, inf

            if (_all_left > _all_right) or _all == 0:  # 相等时合并至右
                # 合并至左箱
                _ = breakpoints_left.pop(_index + 1)
                _ = breakpoints_right.pop(_index)

                _bin_good[_index] += _good
                _bin_bad[_index] += _bad
                _bin_all[_index] += _all

            else:
                # 合并至右箱
                _ = breakpoints_left.pop(_index)
                _ = breakpoints_right.pop(_index - 1)

                _bin_good[_index - 1] += _good
                _bin_bad[_index - 1] += _bad
                _bin_all[_index - 1] += _all

        _bin_empty = [1 if (_good == 0 or _bad == 0) else 0 for _good, _bad in zip(_bin_good, _bin_bad)]

    breakpoints = np.array(breakpoints_left[1:])
    return np.sort(np.unique(breakpoints))


def get_breakpoints_by_woe(
    feature: np.ndarray,
    maxbins: int = 8,
    target: np.ndarray | None = None,
    left_closed: bool = True,
    init_count_distr: float = 0.02,
    count_distr_limit: float = 0.05,
    stop_limit: float = 0.1,
) -> np.ndarray:
    """woebin-tree 分箱器, 参考 scorecardpy 实现

    原始参数:

    - init_count_distr=0.02 生成初始分割点用的参数 1/init_count_distr 初始分割点数量
    - count_distr_limit=0.05 分箱后样本占比, 只考虑 >=count_distr_limit 的分割点
    - stop_limit=0.1 iv-change-ratio 阈值, >=stop_limit 才会增加分割点
    - bin_num_limit=8 最终分箱上限
    """

    assert target is not None
    feature, target = initialize(feature, target)

    breakpoints_pool = get_breakpoints_by_woeinit(
        feature=feature, target=target, maxbins=int(1 / init_count_distr), left_closed=left_closed
    )

    if len(breakpoints_pool) == 0:
        return breakpoints_pool

    iv_lift = np.inf
    n_brkps = 0

    pop_good = len(target[(target == 0) & (~np.isnan(feature))])
    pop_bad = len(target[(target == 1) & (~np.isnan(feature))])
    # left_bound, right_bound, n_good, n_bad
    bin_list = [(-np.inf, np.inf, pop_good, pop_bad)]
    iv_all = 0
    breakpoints = []

    while (iv_lift >= stop_limit) and (n_brkps + 1 <= len(breakpoints_pool)) and (n_brkps + 1 <= maxbins - 1):
        best_iv_gain: float = -np.inf
        best_bin_idx: int = -1
        best_brkp: float | None = None
        best_bin_left: tuple[float, float, int, int] | None = None
        best_bin_right: tuple[float, float, int, int] | None = None
        # region: get_best_brkps
        for bin_idx, (left_bound, right_bound, n_good, n_bad) in enumerate(bin_list):
            n_good = n_good or 0.9
            n_bad = n_bad or 0.9
            for _, brkp in enumerate(breakpoints_pool):
                brkp: float
                if brkp <= left_bound or brkp >= right_bound:
                    continue
                # try add brkp
                if n_good == pop_good:
                    iv_bin = 0
                else:
                    iv_bin = (n_bad / pop_bad - n_good / pop_good) * np.log((n_bad / pop_bad) / (n_good / pop_good))
                if left_closed:
                    # [left, [brkp), right)
                    bin_left = target[(feature >= left_bound) & (feature < brkp)]
                    bin_right = target[(feature >= brkp) & (feature < right_bound)]
                else:
                    # (left, (brkp], right]
                    bin_left = target[(feature > left_bound) & (feature <= brkp)]
                    bin_right = target[(feature > brkp) & (feature <= right_bound)]

                if (len(bin_left) / len(target) < count_distr_limit) or (
                    len(bin_right) / len(target) < count_distr_limit
                ):
                    continue

                left_good = len(bin_left[bin_left == 0])
                left_bad = len(bin_left[bin_left == 1])
                right_good = len(bin_right[bin_right == 0])
                right_bad = len(bin_right[bin_right == 1])

                _l0 = left_good or 0.9
                _l1 = left_bad or 0.9
                _r0 = right_good or 0.9
                _r1 = right_bad or 0.9
                iv_left = (_l1 / pop_bad - _l0 / pop_good) * np.log((_l1 / pop_bad) / (_l0 / pop_good))
                iv_right = (_r1 / pop_bad - _r0 / pop_good) * np.log((_r1 / pop_bad) / (_r0 / pop_good))
                iv_gain = iv_left + iv_right - iv_bin
                if iv_gain > best_iv_gain:
                    best_bin_idx = bin_idx
                    best_iv_gain = iv_gain
                    best_brkp = brkp
                    best_bin_left = (
                        left_bound,
                        best_brkp,
                        len(bin_left[bin_left == 0]),
                        len(bin_left[bin_left == 1]),
                    )
                    best_bin_right = (
                        best_brkp,
                        right_bound,
                        len(bin_right[bin_right == 0]),
                        len(bin_right[bin_right == 1]),
                    )

        if best_bin_idx == -1:
            break
        _ = bin_list.pop(best_bin_idx)
        assert best_bin_left is not None
        assert best_bin_right is not None
        bin_list.append(best_bin_left)
        bin_list.append(best_bin_right)
        # endregion
        if iv_all == 0:
            iv_lift = 1
        else:
            iv_lift = (iv_all + best_iv_gain) / iv_all - 1
        iv_all = iv_all + best_iv_gain
        breakpoints.append(best_brkp)
        n_brkps += 1

    return np.sort(np.unique(breakpoints))


class Binner(Preprocessor[BreakPoints]):
    """分箱器

    Extras
    ------
    dist - 等距分箱
      left : float 左极限
      right : float 右极限
      gap : 固定间隔
    """

    def __init__(
        self,
        method: Literal["dist", "freq", "tree", "rpretty", "woe"] | BinningMethod = "freq",
        maxbins: int = 8,
        left_closed: bool = True,
        pretty: bool = True,
        **extras,
    ) -> None:
        self.maxbins = maxbins
        self.left_closed = left_closed
        self.pretty = pretty
        self.extras = extras

        if isinstance(method, str):
            if method.lower() == "dist":
                self._binner = get_breakpoints_by_distance
            elif method.lower() == "freq":
                self._binner = get_breakpoints_by_frequency
            elif method.lower() == "tree":
                self._binner = get_breakpoints_by_tree
            elif method.lower() == "rpretty":
                self._binner = get_breakpoints_by_rpretty
            elif method.lower() == "woe":
                self._binner = get_breakpoints_by_woe
            else:
                raise NotImplementedError(f"暂不支持 {method} 分箱算法")
        else:
            self._binner = method

        super().__init__()
        self._logger = logging.getLogger(__name__)

    def _fit(
        self,
        data: pl.DataFrame,
        features: list[str],
        target: str | None = None,
        progress_bar: str | None = None,
    ) -> dict[str, BreakPoints]:
        core = {}

        if Progress is not None and progress_bar is not None:
            _pb = Progress(expand=True)
        else:
            self._logger.debug("Install rich for progress bar")
            _pb = ProgressMock()

        with _pb as progress:
            t = progress.add_task(progress_bar or "", total=len(features))
            for f in features:
                if isinstance(t, _MockTask):
                    pass
                else:
                    progress.update(t, advance=1, refresh=True)
                if f not in data.columns:
                    self._logger.warning(f"跳过不存在的列: {f}")
                    continue

                if data[f].drop_nans().is_null().all():
                    self._logger.warning(f"跳过纯空列: {f}")
                    continue

                if not data[f].dtype.is_numeric():
                    self._logger.warning(f"跳过非数值列: {f}")
                    continue

                if target is not None and target in data.columns:
                    target_np = data.get_column(target).to_numpy()
                else:
                    target_np = None

                # f_uniques = data[f].drop_nans().drop_nulls().unique().to_list()
                # if len(f_uniques) <= self.maxbins:
                #     self._logger.debug(f"跳过可枚举列 {f}({len(f_uniques)}): {'|'.join(map(lambda x: str(x), f_uniques))}")
                #     continue

                brkps = self._binner(
                    feature=data[f].to_numpy(),
                    target=target_np,
                    maxbins=self.maxbins,
                    left_closed=self.left_closed,
                    **self.extras,
                )
                if self.pretty:
                    core[f] = prettify(feature=data[f].to_numpy(), breakpoints=brkps, left_closed=self.left_closed)
                else:
                    core[f] = np.sort(np.unique(brkps[~np.isnan(brkps)]))
        return core

    def _transform(self, feature: str, core: BreakPoints) -> pl.Expr:
        return pl.col(feature).cut(list(core), left_closed=self.left_closed).cast(pl.String).fill_null("Missing")
