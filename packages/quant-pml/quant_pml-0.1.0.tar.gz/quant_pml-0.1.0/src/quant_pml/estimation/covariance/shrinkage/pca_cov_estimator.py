from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from quant_pml.estimation.covariance.base_cov_estimator import BaseCovEstimator
from quant_pml.features.covar import var_covar_from_corr_array_mac

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData


class PCACovEstimator(BaseCovEstimator):
    def __init__(self, k: int = 3) -> None:
        super().__init__()
        self.k = k

        self._fitted_vols = None
        self._fitted_corr = None
        self._fitted_cov = None

        self._obs_cov = None

        self._pca = PCA()

    def _fit(self, training_data: TrainingData) -> None:
        ret = training_data.simple_excess_returns

        self._obs_cov = ret.cov()
        self._fitted_vols = np.eye(ret.shape[1]) * ret.std().to_numpy()
        corr = ret.corr().fillna(0).to_numpy()

        self._pca.fit(corr)

        components = self._pca.components_
        components = components[: self.k, :]

        reduced_data = self._pca.transform(corr)[:, : self.k]

        reconstr_corr = reduced_data @ components + self._pca.mean_
        self._fitted_corr = reconstr_corr.clip(min=-1, max=1)
        np.fill_diagonal(self._fitted_corr, 1)

        cov = var_covar_from_corr_array_mac(self._fitted_corr, self._fitted_vols)
        self._fitted_cov = pd.DataFrame(cov, index=self.available_assets, columns=self.available_assets)

    def _predict(self, prediction_data: PredictionData) -> pd.DataFrame:  # noqa: ARG002
        return self._fitted_cov
