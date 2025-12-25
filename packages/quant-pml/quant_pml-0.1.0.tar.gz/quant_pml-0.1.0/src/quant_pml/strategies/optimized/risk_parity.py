from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.config.trading_config import TradingConfig
    from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import numpy as np
import pandas as pd

from quant_pml.strategies.optimized.base_estimated_strategy import BaseEstimatedStrategy


class RiskParity(BaseEstimatedStrategy):
    def __init__(
        self,
        cov_estimator: BaseCovEstimator,
        trading_config: TradingConfig,
        window_size: int | None = None,
    ) -> None:
        super().__init__(
            trading_config=trading_config,
            window_size=window_size,
        )

        self.cov_estimator = cov_estimator

    def _fit_estimator(self, training_data: TrainingData) -> None:
        self.cov_estimator.fit(training_data)

    def _optimize(self, prediction_data: PredictionData) -> pd.Series[float]:
        covmat = self.cov_estimator.predict(prediction_data).loc[self.available_assets, self.available_assets]
        variances = np.diag(covmat.to_numpy())

        weights = 1 / variances
        weights = self.trading_config.total_exposure * weights / weights.sum()

        return pd.Series(weights, index=self.available_assets)
