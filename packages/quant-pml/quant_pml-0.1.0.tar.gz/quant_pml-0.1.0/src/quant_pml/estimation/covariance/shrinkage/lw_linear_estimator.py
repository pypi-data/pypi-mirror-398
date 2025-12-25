from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import pandas as pd
from sklearn.covariance import LedoitWolf

from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator

warnings.filterwarnings("ignore")


class LedoitWolfCovEstimator(BaseCovEstimator):
    def __init__(
        self,
    ) -> None:
        super().__init__()

    def _fit(self, training_data: TrainingData) -> None:
        ret = training_data.simple_excess_returns

        lw = LedoitWolf(store_precision=False)
        lw.fit(ret)
        self._fitted_cov = lw.covariance_

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:  # noqa: ARG002
        cov = self._fitted_cov

        if not isinstance(cov, pd.DataFrame):
            cov = pd.DataFrame(cov, index=self.available_assets, columns=self.available_assets)

        return cov
