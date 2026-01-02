from __future__ import annotations

import logging
import pickle
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar, overload

import polars as pl
from typing_extensions import Self

T = TypeVar("T")


class Preprocessor(Generic[T], metaclass=ABCMeta):
    """预处理器

    _core : dict[str, T]
        预处理器核心, 存储训练结果
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._core: dict[str, T] | None = None

    @property
    def fitted(self) -> bool:
        return self._core is not None

    def fit(
        self,
        data: pl.DataFrame | pl.LazyFrame,
        f_process: list[str] | str | None = None,
        f_ignores: list[str] | None = None,
        target: str | None = None,
        batch_size: int | None = None,
        show_progress: bool = True,
    ) -> Self:
        """Processor Fit

        Parameters
        ----------
        data : pl.DataFrame | pl.LazyFrame
            用来训练的数据集
        f_process : list[str] | str | None
            用来训练的字段, 如果为 None 表示选择全部字段
        target : str | None
            作为标签的字段, 如果为 None 一般为无监督
        f_ignores : list[str] | None
            跳过的字段, 可与 f_process 组合使用, 会强制跳过
        batch_size : int | None
            批处理数, 如果为 None 表示一次全部处理, 数据量过大可能会 OOM
        """

        if f_process is None:
            f_process = data.collect_schema().names()
            f_missed = []
        else:
            f_missed = [f for f in f_process if f not in data.collect_schema().names()]
        if len(f_missed) > 0:
            self._logger.warning(f"缺失指定字段: {f_missed}")

        features_all = [f for f in f_process if f not in [target, *f_missed, *(f_ignores or [])]]
        self._logger.info(f"待处理字段数: {len(features_all)}")

        if batch_size is not None and batch_size > 0:
            features_batch = [
                features_all[i * int(batch_size) : (i + 1) * int(batch_size)]
                for i in range(int(len(features_all) // int(batch_size)) + 1)
            ]
            self._logger.debug(f"分批处理, 一共 {len(features_batch)} 批")
        else:
            features_batch = [features_all]

        if isinstance(data, pl.DataFrame):
            stream = data.lazy()
        else:
            stream = data

        self._core = self._core or {}  # 初始化
        for idx, fbatch in enumerate(features_batch):
            fbatch_with_target = fbatch if target is None else [*fbatch, target]
            _data = stream.select(fbatch_with_target).collect()
            _pg_bar = f"Binning [{idx + 1}/{len(features_batch)}]: " if show_progress else None
            _cores = self._fit(data=_data, features=fbatch, target=target, progress_bar=_pg_bar)
            self._core.update(_cores)
            if _pg_bar is None:
                self._logger.info(f"已完成 [{idx + 1}/{len(features_batch)}] 批次样本.")
        return self

    @abstractmethod
    def _fit(
        self,
        data: pl.DataFrame,
        features: list[str],
        target: str | None = None,
        progress_bar: str | None = None,
    ) -> dict[str, T]: ...

    @overload
    def transform(self, data: pl.DataFrame) -> pl.DataFrame: ...
    @overload
    def transform(self, data: pl.LazyFrame) -> pl.LazyFrame: ...
    @overload
    def transform(self, data: pl.Series) -> pl.Series: ...
    def transform(self, data: pl.DataFrame | pl.LazyFrame | pl.Series) -> pl.DataFrame | pl.LazyFrame | pl.Series:
        if self._core is None:
            raise ValueError("未训练的处理器")

        if isinstance(data, pl.Series):
            return (
                data.to_frame()
                .with_columns(self._transform(data.name, self._core[data.name]).alias(data.name))
                .get_column(data.name)
            )

        for f in data.collect_schema().names():
            if f not in self._core:
                self._logger.debug(f"未处理特征: {f}")
                continue
            data = data.with_columns(self._transform(f, self._core[f]).alias(f))
        return data

    @abstractmethod
    def _transform(self, feature: str, core: T) -> pl.Expr: ...

    def dump(self, file: str | Path) -> Path:
        with open(Path(file), "wb") as f:
            pickle.dump(self._core, f)
        return Path(file)

    def load(self, core: str | Path | dict[str, T]) -> Self:
        if isinstance(core, (str, Path)):
            with open(Path(core), "rb") as f:
                self._core = pickle.load(f)
        else:
            assert isinstance(core, dict)
            self._core = core
        return self
