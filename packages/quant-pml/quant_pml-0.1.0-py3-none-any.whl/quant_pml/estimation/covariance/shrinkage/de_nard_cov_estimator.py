from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import BaseCrossValidator

from quant_pml.estimation.covariance.shrinkage.base_cross_val_cov_estimator import (
    BaseCrossValCovEstimator,
)

warnings.filterwarnings("ignore")


class DeNardCovEstimator(BaseCrossValCovEstimator):
    def __init__(
        self,
        alphas: list[float] | np.ndarray[float] | None = None,
        cv: BaseCrossValidator | None = None,
    ) -> None:
        super().__init__(
            alphas=alphas,
            cv=cv,
        )

    def _fit_shrunk_cov(self, ret: pd.DataFrame, alpha: float) -> pd.DataFrame:
        sample_cov = ret.cov()
        target_cov = self._calc_target_cov(ret)

        return (1 - alpha) * sample_cov + alpha * target_cov

    @staticmethod
    def _calc_target_cov(ret: pd.DataFrame) -> pd.DataFrame:
        sample_cov = ret.cov()
        avg_var = np.mean(np.diag(sample_cov))

        # Get off-diagonal elements
        n = sample_cov.shape[0]
        mask = ~np.eye(n, dtype=bool)
        avg_cov = np.mean(sample_cov.to_numpy()[mask])

        # Create target covariance matrix
        target_cov = np.full((n, n), avg_cov)
        np.fill_diagonal(target_cov, avg_var)

        # Convert back to DataFrame with same index and columns
        return pd.DataFrame(target_cov, index=sample_cov.index, columns=sample_cov.columns)
