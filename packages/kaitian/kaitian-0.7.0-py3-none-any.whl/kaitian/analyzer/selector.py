"""特征筛选器"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from .calculator import calc_iv, calc_psi

logger = logging.getLogger(__package__)


def feature_selection_by_dtype(data: pl.DataFrame, features: list[str], dtype: list | None = None) -> list[str]:
    if dtype is None:
        features = [f for f in features if data[f].dtype.is_numeric()]
    else:
        features = [f for f in features if data[f].dtype in dtype]

    return features


def feature_selection_by_psi(
    data: pl.DataFrame, features: list[str], group: str | pl.Series, base: str | None = None, threshold: float = 0.1
) -> list[str]:
    features_removed = []

    g_series = data[group] if isinstance(group, str) else group

    for f in features:
        psi_f: dict[str, float] = calc_psi(feature=data[f], group=g_series, base=base)
        if max(psi_f.values()) > threshold:
            features_removed.append(f)
            logger.debug(f"{f} removed due to PSI > {threshold}")
        else:
            logger.debug(f"{f} left: {psi_f}")

    features_left = [f for f in features if f not in features_removed]
    return features_left


def feature_selection_by_iv(
    data: pl.DataFrame,
    features: list[str],
    target: str,
    group: str,
    base: str,
    threshold: float = 0.01,
    stability: float = 0.5,
) -> list[str]:
    """Feature selection by IV.

    筛选后的变量:

    1). iv >= threshold
    2). |train_iv - test_iv| <= stability * min(train_iv, test_iv)
    """

    features_removed = []
    for f in features:
        _data_base = data.filter(pl.col(group) == base)
        iv_base = calc_iv(_data_base[f], _data_base[target])
        if iv_base < threshold:
            features_removed.append(f)
            logger.debug(f"{f} removed due to IV ({iv_base:.4f}) < {threshold}")
            continue
        for _group in data["group"].unique():
            _data_group = data.filter(pl.col(group) == _group)
            _iv_group = calc_iv(_data_group[f], _data_group[target])
            if abs(iv_base - _iv_group) > stability * min(iv_base, _iv_group):
                features_removed.append(f)
                logger.debug(f"{f} removed due to IV {_iv_group:.4f}~{iv_base:.4f} is not stable")
    features_left = [f for f in features if f not in features_removed]
    return features_left


# TODO: feature_sleection_by_trend (d-value)


def feature_selection_by_corr(
    data: pl.DataFrame, features: list[str], threshold: float = 0.9, reference: dict | None = None
) -> list[str]:
    """按照相关性筛选变量.

    线性相关系数 >= threshold 的变量

    - 如果 reference 不提供, 则默认保留非空值更大的特征
    - 如果 reference 提供, 则保留reference值更大的特征
    """

    features = features.copy()

    if reference is None:
        ref_dict: dict[str, int] = (data.select(features).null_count() * -1).to_dicts()[0]
    else:
        ref_dict = reference.copy()

    corr = data.select(features).to_pandas().corr().abs()
    _ = np.fill_diagonal(corr.values, 0)

    while corr.max().max() >= threshold:
        x1, x2 = corr.stack().idxmax()  # type: ignore
        assert isinstance(x1, str)
        assert isinstance(x2, str)
        logger.debug(f"高相关性: {x1} ~ {x2}")
        if ref_dict[x1] < ref_dict[x2]:
            logger.debug(f"remove {x1}")
            features.remove(x1)
            corr.loc[x1, :] = 0
            corr.loc[:, x1] = 0
        else:
            logger.debug(f"remove {x2}")
            features.remove(x2)
            corr.loc[x2, :] = 0
            corr.loc[:, x2] = 0

    logger.debug(f"Left {len(features)} features, max correlation {corr.max().max():.5f}")
    return features
