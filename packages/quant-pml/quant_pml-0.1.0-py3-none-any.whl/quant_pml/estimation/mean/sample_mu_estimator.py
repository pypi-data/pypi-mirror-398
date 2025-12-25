from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

from quant_pml.estimation.mean.base_mu_estimator import BaseMuEstimator


class SampleMuEstimator(BaseMuEstimator):
    def __init__(self) -> None:
        super().__init__()

        self._fitted_mu = None

    def _fit(self, training_data: TrainingData) -> None:
        self._fitted_mu = training_data.simple_excess_returns.mean()

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:  # noqa: ARG002
        return self._fitted_mu
