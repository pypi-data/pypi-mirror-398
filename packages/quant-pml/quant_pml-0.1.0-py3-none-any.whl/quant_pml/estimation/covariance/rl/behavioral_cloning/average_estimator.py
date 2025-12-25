from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from quant_pml.estimation.covariance.rl.base_rl_estimator import BaseRLCovEstimator


class AverageCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size)

        self.last_pred = None
        self.encountered_nan = False

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        self.average = shrinkage_target.mean().item()

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        return self.average
