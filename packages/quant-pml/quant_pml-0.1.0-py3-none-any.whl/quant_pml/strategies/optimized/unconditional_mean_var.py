from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sklearn.base import BaseEstimator

    from quant_pml.config.trading_config import TradingConfig
    from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import TimeSeriesSplit

from quant_pml.strategies.optimized.base_estimated_strategy import BaseEstimatedStrategy


class UnconditionalMeanVariance(BaseEstimatedStrategy):
    def __init__(
        self,
        cov_estimator: BaseCovEstimator,
        trading_config: TradingConfig,
        model: BaseEstimator | None = None,
        window_size: int | None = None,
    ) -> None:
        super().__init__(
            trading_config=trading_config,
            window_size=window_size,
        )

        self.cov_estimator = cov_estimator

        if model is None:
            model = RidgeCV(alphas=np.logspace(-3, 3, 100), cv=TimeSeriesSplit(n_splits=5))
        self.model = model

    def _fit_estimator(self, training_data: TrainingData) -> None:
        ranks = training_data.cross_sectional_features
        targets = training_data.targets

        self.model.fit(ranks, targets)

        self.cov_estimator.fit(training_data)

    def _optimize(self, prediction_data: PredictionData) -> pd.Series[float]:
        mu_hat = self.model.predict(prediction_data.cross_sectional_features)
        # mu_hat = np.ones(len(self.available_assets)) corresponds to GMV portfolio
        covmat = self.cov_estimator.predict(prediction_data)

        covmat_inv = np.linalg.inv(covmat)
        weights = (covmat_inv @ mu_hat) / (mu_hat.T @ covmat_inv @ mu_hat)
        weights /= weights.sum()

        return pd.Series(weights, index=self.available_assets)
