from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.covariance import ShrunkCovariance
from sklearn.model_selection import BaseCrossValidator

from quant_pml.estimation.covariance.shrinkage.base_cross_val_cov_estimator import (
    BaseCrossValCovEstimator,
)

warnings.filterwarnings("ignore")


class IdentityBasedCovEstimator(BaseCrossValCovEstimator):
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
        while True:
            try:
                shrunk = ShrunkCovariance(shrinkage=alpha)
                shrunk.fit(ret)
                self._fitted_cov = shrunk.covariance_
                break
            except FloatingPointError:
                alpha += 0.01
