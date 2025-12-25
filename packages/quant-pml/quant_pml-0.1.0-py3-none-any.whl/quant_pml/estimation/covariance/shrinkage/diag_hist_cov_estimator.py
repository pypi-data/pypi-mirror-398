from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from quant_pml.estimation.covariance.heuristic.sample_cov_estimator import (
    SampleCovEstimator,
)

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData


class DiagSampleCovEstimator(SampleCovEstimator):
    def __init__(self) -> None:
        super().__init__()

        self._fitted_cov = None

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:
        cov = super()._predict(prediction_data=prediction_data)
        return pd.DataFrame(np.diag(np.diag(cov)))
