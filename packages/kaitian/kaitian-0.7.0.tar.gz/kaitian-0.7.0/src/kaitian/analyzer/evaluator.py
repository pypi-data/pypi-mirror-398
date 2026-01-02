"""预测评估器

eval_*
    y_true : 真实标签
    y_pred : 预测标签
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.metrics import auc, roc_curve


def eval_ks(
    y_true: pl.Series | np.ndarray, y_pred: pl.Series | np.ndarray, sample_weight: pl.Series | np.ndarray | None = None
) -> float:
    """计算KS值"""
    fpr, tpr, _ = roc_curve(y_true, y_pred, sample_weight=sample_weight)
    ks = np.max(np.abs(tpr - fpr))
    return ks


def eval_auc(
    y_true: pl.Series | np.ndarray, y_pred: pl.Series | np.ndarray, sample_weight: pl.Series | np.ndarray | None = None
) -> float:
    """计算KS值"""
    fpr, tpr, _ = roc_curve(y_true, y_pred, sample_weight=sample_weight)
    return float(auc(fpr, tpr))
