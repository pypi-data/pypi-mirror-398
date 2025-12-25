from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.model_selection import BaseCrossValidator, TimeSeriesSplit

from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator

warnings.filterwarnings("ignore")


class BaseCrossValCovEstimator(BaseCovEstimator, ABC):
    def __init__(
        self,
        alphas: list[float] | np.ndarray[float] | None = None,
        cv: BaseCrossValidator | None = None,
    ) -> None:
        super().__init__()

        if alphas is None:
            self._alphas = np.linspace(0, 1, 20)
        else:
            self._alphas = alphas
        self.cv = cv if cv is not None else TimeSeriesSplit(n_splits=5)

        self._fitted_cov = None
        self.best_alpha = None

        self.history_alphas = []

    @property
    def alphas(self) -> list[float] | np.ndarray[float] | None:
        return self._alphas

    @alphas.setter
    def alphas(self, alphas: list[float] | np.ndarray[float] | None) -> None:
        self._alphas = alphas

    def _fit(self, training_data: TrainingData) -> None:
        ret = training_data.simple_excess_returns

        if len(self._alphas) > 1:
            self.best_alpha = self._find_cv_shrinkage(ret)
            self.history_alphas.append(self.best_alpha)

            self._fit_shrunk_cov(ret, self.best_alpha)
        else:
            self._fit_shrunk_cov(ret, self._alphas[0])

    @abstractmethod
    def _fit_shrunk_cov(self, ret: pd.DataFrame, alpha: float) -> pd.DataFrame:
        raise NotImplementedError

    def _find_cv_shrinkage(self, ret: pd.DataFrame) -> float:
        alphas = self._alphas
        cv = self.cv
        best_alpha = 0
        best_score = np.inf

        for alpha in alphas:
            scores = []
            for train, test in cv.split(ret):
                fitted_cov = self._fit_shrunk_cov(ret.iloc[train], alpha)
                scores.append(self._evaluate_covariance(fitted_cov, ret.iloc[test]))

            score = np.mean(scores)
            if score < best_score:
                best_alpha = alpha
                best_score = score

        return best_alpha

    @staticmethod
    def _evaluate_covariance(covmat: pd.DataFrame, rets: pd.DataFrame) -> float:
        try:
            # N x N
            covmat_inv = np.linalg.inv(covmat)
            # N x 1
            ones = np.ones((rets.shape[1], 1))

            # N x 1
            w_opt = covmat_inv @ ones
            w_opt = w_opt / np.sum(w_opt)

            opt_var = w_opt.T @ rets.cov() @ w_opt

            return opt_var.to_numpy().item()
        except np.linalg.LinAlgError:
            return np.inf

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:  # noqa: ARG002
        cov = self._fitted_cov

        if not isinstance(cov, pd.DataFrame):
            cov = pd.DataFrame(cov, index=self.available_assets, columns=self.available_assets)

        return cov
