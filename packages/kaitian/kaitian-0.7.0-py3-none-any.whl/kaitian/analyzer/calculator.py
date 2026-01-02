"""指标计算器

calc_*
    feature : 特征值
    target : 目标值
    group : 分组列
    debug : 是否输出结果信息
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from ..utils.plextras import sort_frame

logger = logging.getLogger(__package__)


def calc_woe(feature: pl.Series, target: pl.Series, woe_adjust: float = 0, debug: bool = False) -> dict[str, float]:
    """Calculate Information Value

                (N_bad + adjust) / All_bad
    WOE_i = LN(-----------------------------)
                (N_good + adjust) / All_good

    Reference
    ---------
    [1]. https://documentation.sas.com/doc/en/vdmmlcdc/8.1/casstat/viyastat_binning_details02.htm
    """

    data = pl.DataFrame({"feature": feature, "target": target})

    data_binned = (
        data.group_by("feature")
        .agg(
            n_good=(1 - pl.col("target")).sum(),
            n_bad=pl.col("target").sum(),
        )
        .with_columns(
            n_good_adj=pl.col("n_good") + woe_adjust,
            n_bad_adj=pl.col("n_bad") + woe_adjust,
        )
        .with_columns(
            p_good=pl.col("n_good_adj") / pl.col("n_good").sum(),
            p_bad=pl.col("n_bad_adj") / pl.col("n_bad").sum(),
        )
        .with_columns(woe=np.log(pl.col("p_bad") / pl.col("p_good")))
        .with_columns(lift=pl.col("n_bad") / (pl.col("n_bad") + pl.col("n_good")) / data["target"].mean())
    ).sort("feature")

    data_binned = sort_frame(data_binned, "feature")

    if debug:
        logger.info(
            f"{feature.name} WOE Calculated: {data_binned.select(['feature', 'n_good', 'n_bad', 'p_good', 'p_bad', 'woe', 'lift'])}"
        )

    return dict(zip(data_binned["feature"], data_binned["woe"]))


def calc_iv(feature: pl.Series, target: pl.Series, woe_adjust: float = 0.5, debug: bool = False):
    """Calculate Information Value

               (N_good + adjust) / All_good
    WOE_i = LN(-----------------------------)
                (N_bad + adjust) / All_bad

             N_good      N_bad
    IV_i = (-------- - ---------) * WOE_i
            All_good    All_bad
    Reference
    ---------
    [1]. https://documentation.sas.com/doc/en/vdmmlcdc/8.1/casstat/viyastat_binning_details02.htm
    """

    data = pl.DataFrame({"feature": feature, "target": target})

    data_binned = (
        (
            data.group_by("feature")
            .agg(
                n_good=(1 - pl.col("target")).sum(),
                n_bad=pl.col("target").sum(),
            )
            .with_columns(
                n_good_adj=pl.col("n_good") + woe_adjust,
                n_bad_adj=pl.col("n_bad") + woe_adjust,
            )
            .with_columns(
                p_good=pl.col("n_good_adj") / pl.col("n_good").sum(),
                p_bad=pl.col("n_bad_adj") / pl.col("n_bad").sum(),
            )
            .with_columns(woe=np.log(pl.col("p_bad") / pl.col("p_good")))
            .with_columns(lift=pl.col("n_bad") / (pl.col("n_bad") + pl.col("n_good")) / data["target"].mean())
        )
        .with_columns(iv=(pl.col("p_bad") - pl.col("p_good")) * pl.col("woe"))
        .sort("feature")
    )

    data_binned = sort_frame(data_binned, "feature")

    iv = data_binned["iv"].sum()

    if debug:
        if iv < 0.02:
            iv_flag = "TOO WEEK"
        elif iv < 0.1:
            iv_flag = "WEEK"
        elif iv < 0.3:
            iv_flag = "MEDIUM"
        elif iv < 0.5:
            iv_flag = "STRONG"
        else:
            iv_flag = "TOO STRONG"
        logger.info(
            f"{feature.name} IV Calculated: {iv:.5f} *{iv_flag}*\n"
            f"{data_binned.select(['feature', 'n_good', 'n_bad', 'p_good', 'p_bad', 'woe', 'iv', 'lift'])}"
        )

    return iv


def calc_psi(feature: pl.Series, group: pl.Series, base: str | None = None, debug: bool = False) -> dict[str, float]:
    """Population Stability Index Calculation.

    Parameters
    ----------
    feature : pl.Series
        The feature to be calculated.
    group : pl.Series
        The group to be compared.
    base : str, optional
        The base group, will calculate bi-month psi if not provided.
    debug : bool, optional
        Whether to print debug information, by default False.

    Returns
    -------
    result : Dict[str, float]
        The psi result, key is group-base, value is the psi.
    """

    if base is not None:
        assert base in group.unique(), f"base group [{base}] not found: {group.unique()}"
        group_list = [base] + [g for g in group.unique().sort().to_list() if g != base]
    else:
        group_list = group.unique().sort().to_list()

    result: dict[str, float] = {}

    data_all = pl.DataFrame({"feature": feature, "group": group})

    for i, g in enumerate(group_list):
        if i == 0:
            continue

        _base = group_list[i - 1] if base is None else group_list[0]

        data_group = (
            data_all.filter(pl.col("group").is_in([_base, g]))
            .pivot(on="group", index="feature", values="group", aggregate_function="len")
            .with_columns(*[pl.col(seg).fill_null(0.9) / pl.col(seg).sum() for seg in [_base, g]])
            .with_columns(psi=(pl.col(g) - pl.col(_base)) * np.log(pl.col(g) / pl.col(_base)))
        ).sort("feature")

        data_group = sort_frame(data_group, "feature")

        psi = data_group["psi"].sum()
        result[f"{g}~{_base}"] = psi
        if debug:
            if psi < 0.1:
                psi_flag = "STABLE"
            elif psi < 0.25:
                psi_flag = "MEDIUM"
            else:
                psi_flag = "UNSTABLE"

            logger.info(
                f"{feature.name} PSI [{g}~{_base}] Calculated: {psi:.5f} *{psi_flag}*\n"
                f"{data_group.select(['feature', _base, g, 'psi'])}"
            )
    return result


def calc_timevol(feature: pl.Series, target: pl.Series, time: pl.Series, debug: bool = False) -> float:
    """计算特征在时间维度上的波动率

    如果 time 是时间特征, 默认按月分组计算, 否则按值计算, 此时需要提前分好组.

    Reference
    ---------
    [1]. 智能风控实践指南, Page 44 - 蒋宏
    """

    if isinstance(time.dtype, (pl.Datetime, pl.Date)):
        time = time.dt.strftime("%Y-%m")

    data = pl.DataFrame({"feature": feature, "target": target, "time": time}).pivot(
        on="time",
        index="feature",
        values="target",
        aggregate_function="mean",
        sort_columns=True,
    )

    data = (
        data.with_columns(*[pl.col(t).rank() for t in data.columns if t not in ["feature"]])
        .with_columns(timevol=pl.concat_list([t for t in data.columns if t not in ["feature"]]).list.std())
        .sort("feature")
    )

    data = sort_frame(data, "feature")

    timevol = data.select(pl.col("timevol").mean()).get_column("timevol").item(0)

    if debug:
        logger.info(f"{feature.name} Time Volatility Calculated: {timevol:.3f}\n{data}")

    return timevol
