"""Lightgbm Trainer

Notes for lightgbm.train -> lightgbm.Booster
--------------------------------------------
keep_training_booster : bool = False
    返回的 Booster 是否是可训练对象, 默认为 False, 会转为 _InnerPredictor
    为 True 时, 可以使用 Booster 的 eval* 接口
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, TypedDict

import lightgbm as lgb
import numpy as np
import optuna
import polars as pl
import psutil
from lightgbm.basic import _LGBM_CustomEvalFunction, _LGBM_CustomObjectiveFunction
from lightgbm.callback import CallbackEnv, early_stopping, log_evaluation
from typing_extensions import Unpack

from .__proto__ import Dataset, EvalMetric, LossFunction, ParamSet, Trainer, TuningMetric


class LGBParams(TypedDict, total=False):
    # gbdt : 梯度提升树
    # rf : 随机森林
    # dart : Dropout + gbdt
    boosting: Literal["gbdt", "rf", "dart"]

    # bagging : Bagging
    # goss : 基于梯度的单侧采样
    data_sample_strategy: Literal["bagging", "goss"]

    # 单树最大叶数, 默认值 31, 1 < num_leaves <= 131072
    num_leaves: int

    # 树模型最大深度
    max_depth: int

    # 单叶中最小样本量
    min_data_in_leaf: int

    # 单叶中最小 Hessian 和
    min_sum_hessian_in_leaf: float

    # 样本抽样比例
    subsample: float

    # 样本抽样频率, 每 N 次进行一次抽样
    bagging_freq: int

    # 特征抽样比例 - 树
    feature_fraction: float

    # 特征抽样比例 - 节点
    feature_fraction_bynode: float

    # L1 正则化
    lambda_l1: float

    # L2 正则化
    lambda_l2: float

    # 线性正则化
    linear_lambda: float

    # 叶节点最大输出 ?
    max_delta_step: float

    # 分裂最小增益 ?
    min_gain_to_split: float


@dataclass
class LGBParamSet(ParamSet):
    boosting: Literal["gbdt", "rf", "dart"] = field(
        default="gbdt",
        metadata={
            "description": "基模型类型",
            "type": "manual",
            "range": ["gbdt", "rf", "dart"],
        },
    )

    data_sample_strategy: Literal["bagging", "goss"] = field(
        default="bagging",
        metadata={
            "description": "数据抽样策略",
            "type": "manual",
            "range": ["bagging", "goss"],
        },
    )

    num_leaves: int = field(
        default=31,
        metadata={
            "description": "单树最大叶数, 不能超过 131072",
            "type": "int",
            "range": [2, 32],
        },
    )

    max_depth: int = field(
        default=0,
        metadata={
            "description": "树模型最大深度, <= 0 时使用自适应树深度",
            "type": "int",
            "range": [1, 5],
        },
    )

    min_data_in_leaf: int = field(
        default=20,
        metadata={
            "description": "单叶中最小样本量",
            "type": "int",
            "range": [50, 500],
        },
    )

    min_sum_hessian_in_leaf: float = field(
        default=1e-3,
        metadata={
            "description": "单叶中最小 Hessian 和",
            "type": "float",
            "range": [1e-3, 250.0],
        },
    )

    subsample: float = field(
        default=1.0,
        metadata={
            "description": "样本抽样比例",
            "type": "float",
            "range": [0.3, 1.0],
        },
    )

    bagging_freq: int = field(
        default=0,
        metadata={
            "description": "样本抽样频率, 每 N 次进行一次抽样",
            "type": "int",
            "range": [0, 5],
        },
    )

    feature_fraction: float = field(
        default=1.0,
        metadata={
            "description": "特征抽样比例 - 树",
            "type": "float",
            "range": [0.3, 1.0],
        },
    )

    feature_fraction_bynode: float = field(
        default=1.0,
        metadata={
            "description": "特征抽样比例 - 节点",
            "type": "float",
            "range": [0.3, 1.0],
        },
    )

    lambda_l1: float = field(
        default=0.0,
        metadata={
            "description": "L1 正则化",
            "type": "float",
            "range": [0, 100],
        },
    )

    lambda_l2: float = field(
        default=0.0,
        metadata={
            "description": "L2 正则化",
            "type": "float",
            "range": [0, 100],
        },
    )

    linear_lambda: float = field(
        default=0.0,
        metadata={
            "description": "线性正则化",
            "type": "float",
            "range": [0, 100],
        },
    )

    max_delta_step: float = field(
        default=0.0,
        metadata={
            "description": "叶节点最大输出",
            "type": "manual",
            "range": [0, np.inf],
        },
    )

    min_gain_to_split: float = field(
        default=0.0,
        metadata={
            "description": "分裂最小增益",
            "type": "float",
            "range": [0, 50],
        },
    )


class LGBDataset(Dataset[lgb.Dataset]):
    def __init__(self, f_continue: list[str], f_category: list[str] | None = None, target: str | None = None) -> None:
        super().__init__(f_continue=f_continue, f_category=f_category, target=target)

    def _buid_dataset(self, data: pl.DataFrame) -> lgb.Dataset:
        if self.target is None or self.target not in data.columns:
            label = None
        else:
            label = data.get_column(self.target).to_numpy()

        if self.weight is None or self.weight not in data.columns:
            weight = None
        else:
            weight = data.get_column(self.weight).to_numpy()

        data_core = data.select(self.f_continue + self.f_category).to_numpy()
        feature_name = self.f_continue + self.f_category
        categorical_feature = self.f_category

        return lgb.Dataset(
            data_core, label=label, weight=weight, feature_name=feature_name, categorical_feature=categorical_feature
        )


class LightGBMPruningCallback:
    def __init__(self, trial: optuna.trial.Trial, metric: str | None = None, dataset: str | None = None) -> None:
        self._trial = trial
        self._metric = metric
        self._dataset = dataset

    def _get_eval_rst(self, env: CallbackEnv) -> tuple[float, bool]:
        evaluation_result_list = env.evaluation_result_list

        assert evaluation_result_list is not None, "中间步验证结果为空, 无法使用剪枝回调函数"

        for evaluation_result in evaluation_result_list:
            dataset, metric, score, is_higher_better = evaluation_result[:4]
            if (dataset == self._dataset or self._dataset is None) and (metric == self._metric or self._metric is None):
                return score, is_higher_better

        raise ValueError(
            f"""未找到验证集 {self._dataset} 和评估指标 {self._metric}\n"""
            f"可选验证集: {list(lambda x: x[0] for x in evaluation_result_list)}\n"
            f"可选评估指标: {list(lambda x: x[1] for x in evaluation_result_list)}"
        )

    def __call__(self, env: CallbackEnv) -> None:
        score, is_higher_better = self._get_eval_rst(env)

        if is_higher_better:
            if self._trial.study.direction != optuna.study.StudyDirection.MAXIMIZE:
                raise ValueError(
                    "The intermediate values are inconsistent with the objective values "
                    "in terms of study directions. Please specify a metric to be minimized "
                    "for LightGBMPruningCallback."
                )
        else:
            if self._trial.study.direction != optuna.study.StudyDirection.MINIMIZE:
                raise ValueError(
                    "The intermediate values are inconsistent with the objective values "
                    "in terms of study directions. Please specify a metric to be "
                    "maximized for LightGBMPruningCallback."
                )

        self._trial.report(score, step=env.iteration)

        if self._trial.should_prune():
            message = "Trial was pruned at iteration {}.".format(env.iteration)
            raise optuna.TrialPruned(message)


class LGBTrainer(Trainer[lgb.Booster, LGBParams, _LGBM_CustomObjectiveFunction, _LGBM_CustomEvalFunction]):
    def __init__(
        self,
        name: str | None = None,
        workdir: Path | None = None,
        loss_function: Literal["regression", "binary"] | LossFunction | None = None,
    ) -> None:
        super().__init__(name=name, workdir=workdir, loss_function=loss_function)

    def _get_params(self, nrounds: int, learning_rate: float, nthreads: int, seed: int, **kwargs) -> dict:
        if nthreads <= 0:
            nthreads = psutil.cpu_count(logical=False) or 0

        params = {
            "objective": self.build_loss_function(),
            "nrounds": nrounds,
            "learning_rate": learning_rate,
            "nthreads": nthreads,
            "seed": seed,
            "deterministic": True,
            "bagging_seed": seed,
            "feature_fraction_seed": seed,
            "first_metric_only": True,
            "verbose": -1,
        }

        for k in LGBParams.__annotations__.keys():
            if kwargs.get(k) is not None:
                params[k] = kwargs[k]

        return params

    def build_loss_function(self) -> _LGBM_CustomObjectiveFunction | str:
        loss_map = {
            "regression": "regression",
            "binary": "binary",
        }

        loss_default = "regression"

        if self.loss_function is None:
            return loss_default
        elif isinstance(self.loss_function, str):
            return loss_map.get(self.loss_function) or loss_default
        else:

            def _custom_loss(preds: np.ndarray, train_data: lgb.Dataset) -> tuple[np.ndarray, np.ndarray]:
                """Lightgbm Custom Loss Function

                returns
                -------
                grad : np.ndarray
                hess : np.ndarray
                """
                ...

            raise NotImplementedError("暂时不支持自定义 LossFunction ")
            return _custom_loss

    def build_eval_metric(self, eval_metric: EvalMetric) -> _LGBM_CustomEvalFunction:
        def _lgb_eval_metric(preds: np.ndarray, eval_data: lgb.Dataset) -> tuple[str, float, bool]:
            y_true = np.array(eval_data.get_label())
            sample_weight = eval_data.get_weight()
            if sample_weight is None:
                sample_weight = np.ones_like(y_true)
            else:
                sample_weight = np.array(sample_weight)
            score = eval_metric(y_true, preds, sample_weight=sample_weight)
            return eval_metric.__qualname__, score, True

        return _lgb_eval_metric

    def fit(
        self,
        data: Dataset,
        eval_metrics: EvalMetric | list[EvalMetric] | str | None = None,
        nrounds: int = 100,
        learning_rate: float = 0.1,
        nthreads: int = -1,
        seed: int = 42,
        split_size: float = 0.3,
        shuffle: bool = True,
        stratify: str | np.ndarray | pl.Series | None = None,
        verbose: int | None = 1,
        early_stopping_rounds: int | None = None,
        early_stopping_log: bool = True,
        callbacks: list[Callable] | None = None,
        **kwargs: Unpack[LGBParams],
    ) -> lgb.Booster:
        params = self._get_params(nrounds=nrounds, learning_rate=learning_rate, nthreads=nthreads, seed=seed, **kwargs)

        if eval_metrics is None:
            params["metric"] = ""  # 默认 Metric, 与 ObjectiveFunction 关联
            feval = None
        elif isinstance(eval_metrics, str):
            params["metric"] = eval_metrics  # 内置 Metrics
            feval = None
        else:
            params["metric"] = "None"  # 自定义 Metrics, 取消内置 Metrics
            feval = (
                [self.build_eval_metric(m) for m in eval_metrics]
                if isinstance(eval_metrics, list)
                else self.build_eval_metric(eval_metrics)
            )

        dtrain, dtest = data.get_trainset(
            split_size=split_size,
            shuffle=shuffle,
            stratify=stratify,
            seed=seed,
        )

        self._logger.debug(f"开始模型训练: {params}")

        cbs = callbacks or []
        if early_stopping_rounds is not None and early_stopping_rounds > 0:
            cbs.append(early_stopping(early_stopping_rounds, first_metric_only=True, verbose=early_stopping_log))

        if verbose is not None and verbose > 0:
            cbs.append(log_evaluation(verbose))

        booster = lgb.train(
            params,
            dtrain,
            num_boost_round=nrounds,
            valid_sets=[dtest],
            feval=feval,
            keep_training_booster=True,
            callbacks=cbs or None,
        )

        return booster

    def predict(self, data: pl.DataFrame | Dataset) -> np.ndarray: ...

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
    ) -> tuple[optuna.Study, dict]:
        if param_set is None:
            param_set = LGBParamSet()

        if study is None:
            study = optuna.create_study(
                study_name="lightgbm-tuning",
                direction="maximize",
                pruner=optuna.pruners.HyperbandPruner(min_resource=1, max_resource="auto", reduction_factor=3),
            )

        if learning_rate is None:
            self._logger.info("未指定 LearningRate, 加入参数调整, 范围 0.01 ~ 1.5")
            _tune_learning_rate = True
        else:
            self._logger.info(f"使用指定 LearningRate: {learning_rate}")
            _tune_learning_rate = False

        if eval_metrics is None:
            self._logger.info("使用默认 Metric")
        elif isinstance(eval_metrics, str):
            self._logger.info(f"使用指定 Metric: {eval_metrics}")
        elif isinstance(eval_metrics, list):
            self._logger.info(f"使用指定 Metric: {', '.join([m.__qualname__ for m in eval_metrics])}")
        else:
            eval_metrics = [eval_metrics]
            self._logger.info(f"使用指定 Metric: {', '.join([m.__qualname__ for m in eval_metrics])}")

        for idx in range(ntrials):
            trial = study.ask()
            params = param_set.build(trial)

            if _tune_learning_rate:
                eta = trial.suggest_float("learning_rate", 0.01, 1.5)
                params["learning_rate"] = eta

            if study.pruner is not None:
                cbks = [LightGBMPruningCallback(trial=trial)]
            else:
                cbks = None

            try:
                booster = self.fit(
                    data,
                    eval_metrics=eval_metrics,
                    verbose=-1,
                    early_stopping_rounds=early_stopping_rounds,
                    nrounds=nrounds,
                    early_stopping_log=False,
                    split_size=split_size,
                    seed=seed,
                    stratify=stratify,
                    callbacks=cbks,
                    **params,
                )
            except optuna.exceptions.TrialPruned:
                study.tell(trial, state=optuna.trial.TrialState.PRUNED)
                if verbose > 0 and (idx + 1) % verbose == 0:
                    self._logger.info(f"[{idx + 1:02d}/{ntrials:02d}] {study.study_name}: PrunedTrial")
                continue

            if isinstance(eval_metrics, list):
                eval_train = booster.eval_train(self.build_eval_metric(eval_metrics[0]))[0][2]
                eval_valid = booster.eval_valid(self.build_eval_metric(eval_metrics[0]))[0][2]
            else:
                eval_train = booster.eval_train()[0][2]
                eval_valid = booster.eval_valid()[0][2]

            if tuning_metric is None:
                score = eval_valid
            else:
                score = tuning_metric(eval_train, eval_valid)

            study.tell(trial, score)

            if verbose > 0 and (idx + 1) % verbose == 0:
                self._logger.info(
                    f"[{idx + 1:02d}/{ntrials:02d}] {study.study_name}: {score:.5f} Train({eval_train:6f}) Valid({eval_valid:.6f})"
                )

        return study, study.best_params
