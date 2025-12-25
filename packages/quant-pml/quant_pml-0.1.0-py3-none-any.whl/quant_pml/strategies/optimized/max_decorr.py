from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.config.trading_config import TradingConfig
    from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import pandas as pd

from quant_pml.optimization.constraints import Constraints
from quant_pml.optimization.optimization import CorrelationMinimizer
from quant_pml.strategies.optimized.base_estimated_strategy import BaseEstimatedStrategy
from quant_pml.utils.linalg import corr_matrix_from_cov


class MaxDecorr(BaseEstimatedStrategy):
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
        covmat = self.cov_estimator.predict(prediction_data)
        corr = corr_matrix_from_cov(covmat.to_numpy())
        corr = pd.DataFrame(corr, index=covmat.index, columns=covmat.columns)

        # TODO(@V): Constraints to metaclass
        constraints = Constraints(ids=self.available_assets)

        if self.trading_config.min_exposure is None and self.trading_config.max_exposure is None:
            constr_type = "Unbounded"
        elif self.trading_config.min_exposure >= 0:
            constr_type = "LongOnly"
        else:
            constr_type = "LongShort"

        constraints.add_box(
            box_type=constr_type,
            lower=self.trading_config.min_exposure,
            upper=self.trading_config.max_exposure,
        )
        constraints.add_budget(rhs=self.trading_config.total_exposure, sense="=")

        self.corr_min = CorrelationMinimizer(constraints=constraints)

        self.corr_min.set_objective(corr_mat=corr)
        self.corr_min.solve()

        return pd.Series(self.corr_min.results["weights"])
