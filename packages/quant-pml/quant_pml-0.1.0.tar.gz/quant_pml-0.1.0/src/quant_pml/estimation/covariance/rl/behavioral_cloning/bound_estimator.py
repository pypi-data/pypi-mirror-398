from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from quant_pml.estimation.covariance.rl.base_rl_estimator import BaseRLCovEstimator


class BoundCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None, refit: bool = True) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size, refit=refit)

        self._last_target = None

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        self._last_target = shrinkage_target.iloc[-1]

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        return self._last_target
