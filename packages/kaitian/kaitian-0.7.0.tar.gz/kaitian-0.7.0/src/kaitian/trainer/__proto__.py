from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Callable, Generic, Protocol, TypeVar

import numpy as np
import optuna
import polars as pl
from optuna import Trial
from sklearn.model_selection import train_test_split
from typing_extensions import Self

D = TypeVar("D")  # 数据集 DataSet
E = TypeVar("E")  # 评估函数 Eval Metrics
L = TypeVar("L")  # 目标损失 Loss
M = TypeVar("M")  # 模型对象
P = TypeVar("P")  # 参数对象


class LossFunction(metaclass=ABCMeta):
    @abstractmethod
    def loss(self, data: Dataset, y_pred: np.ndarray) -> tuple[np.ndarray, ...]: ...


class EvalMetric(Protocol):
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray, sample_weight: np.ndarray | None = None) -> float: ...


class TuningMetric(Protocol):
    def __call__(self, train_score: float, valid_score: float) -> float: ...


@dataclass
class ParamSet:
    """参数集

    description : 参数描述
    type : 参数类型 enum, int, float, manual
    range : 参数取值范围
    """

    def build(self, trial: Trial) -> dict:
        params = {}
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            metadata = field_obj.metadata

            if metadata["type"] == "enum":
                params[field_obj.name] = trial.suggest_categorical(field_obj.name, metadata["range"])
            elif metadata["type"] == "int":
                params[field_obj.name] = trial.suggest_int(field_obj.name, *metadata["range"])
            elif metadata["type"] == "float":
                params[field_obj.name] = trial.suggest_float(field_obj.name, *metadata["range"])
            elif metadata["type"] == "manual":
                params[field_obj.name] = value

        return params


class Dataset(Generic[D], metaclass=ABCMeta):
    """数据集"""

    def __init__(
        self,
        f_continue: list[str],
        f_category: list[str] | None = None,
        target: str | None = None,
        weight: str | None = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.f_continue = f_continue
        self.f_category = f_category or []
        self.target = target
        self.weight = weight

        self.raw: pl.DataFrame

    def build(self, data: pl.DataFrame) -> Self:
        """构造原始数据集"""
        self.raw = data

        if self.target is not None and self.target not in self.raw.columns:
            self._logger.warning(f"目标变量 {self.target} 不在数据集中")
        if self.weight is not None and self.weight not in self.raw.columns:
            self._logger.warning(f"权重变量 {self.weight} 不在数据集中")

        for f in self.f_continue + self.f_category:
            assert f in self.raw.columns, f"特征 {f} 不在数据集中"
        return self

    def get_trainset(
        self,
        split_size: int | float | None = None,
        shuffle: bool = True,
        stratify: str | np.ndarray | pl.Series | None = None,
        seed: int = 42,
    ) -> tuple[D, D]:
        # TODO: 增加 Fold 支持

        if isinstance(stratify, str):
            stratify = self.raw.get_column(stratify)

        if split_size is None or split_size <= 0:
            dtrain = self.raw
            dtest = self.raw
        else:
            dtrain, dtest = train_test_split(
                self.raw,
                test_size=split_size,
                random_state=seed,
                shuffle=shuffle,
                stratify=stratify,
            )

        return (self._buid_dataset(dtrain), self._buid_dataset(dtest))

    @abstractmethod
    def _buid_dataset(self, data: pl.DataFrame) -> D: ...


class Trainer(Generic[M, P, L, E], metaclass=ABCMeta):
    """训练器"""

    def __init__(
        self,
        name: str | None = None,
        workdir: Path | None = None,
        loss_function: str | LossFunction | None = None,
    ) -> None:
        self.name = name
        self.workdir = workdir or Path.cwd()
        self.loss_function = loss_function
        self._logger = logging.getLogger(__name__)

    def setup(self) -> Self:
        self.workdir.mkdir(parents=True, exist_ok=True)
        return self

    @abstractmethod
    def build_loss_function(self) -> L | str: ...

    @abstractmethod
    def build_eval_metric(self, eval_metric: EvalMetric) -> E: ...

    @abstractmethod
    def fit(
        self,
        data: Dataset,
        eval_metrics: EvalMetric | list[EvalMetric] | str | None,
        nrounds: int,
        learning_rate: float,
        nthreads: int,
        seed: int,
        split_size: float,
        shuffle: bool,
        stratify: str | np.ndarray | pl.Series | None,
        verbose: int | None,
        early_stopping_rounds: int | None,
        early_stopping_log: bool,
        callbacks: list[Callable] | None,
        **kwargs,
    ) -> M: ...

    @abstractmethod
    def predict(self, data: pl.DataFrame | Dataset) -> np.ndarray: ...

    @abstractmethod
    def tune(
        self,
        data: Dataset,
        eval_metrics: EvalMetric | list[EvalMetric] | str | None = None,
        ntrials: int = 100,
        verbose: int = 1,
        param_set: ParamSet | None = None,
        study: optuna.Study | None = None,
        tuning_metric: TuningMetric | None = None,
        nrounds: int = 1000,
        early_stopping_rounds: int | None = None,
        learning_rate: float | None = None,
        seed: int = 42,
        split_size: float = 0.3,
        stratify: str | np.ndarray | pl.Series | None = None,
    ) -> tuple[optuna.Study, dict]: ...
