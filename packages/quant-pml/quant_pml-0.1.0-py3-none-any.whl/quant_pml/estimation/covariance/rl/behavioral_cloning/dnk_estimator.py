from __future__ import annotations

import pandas as pd
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import TimeSeriesSplit

from quant_pml.cov_estimators.rl.base_rl_estimator import BaseRLCovEstimator


class DNKCovEstimator(BaseRLCovEstimator):
    def __init__(
        self,
        shrinkage_type: str,
        window_size: int | None = None,
        refit_days: int | None = 30,
    ) -> None:
        super().__init__(
            shrinkage_type=shrinkage_type,
            window_size=window_size,
        )

        self.refit_days = refit_days

        self.last_pred = None
        self.encountered_nan = False
        self._last_fitted_enet = None

    def _should_refit(self, date: pd.Timestamp) -> bool:
        if self._last_fitted_enet is None or self.last_pred is None:
            return True

        if self.refit_days is None:
            return False

        if date - pd.Timedelta(self.refit_days) >= self._last_fitted_enet:
            return True
        return False

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        if not self._should_refit(features.index[-1]):
            return

        if shrinkage_target.isna().any():
            self.encountered_nan = True
        else:
            self.enet = ElasticNetCV(
                cv=TimeSeriesSplit(n_splits=5),
                alphas=[0.5, 1.0, 1.5, 2.0, 5.0],
                l1_ratio=[0.1, 0.25, 0.5, 0.75, 0.9],
            )
            self.enet.fit(X=features, y=shrinkage_target)
            self.encountered_nan = False
            self._last_fitted_enet = features.index[-1]

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        if not self.encountered_nan:
            pred = self.enet.predict(features).item()
            self.last_pred = pred
            return pred

        return self.last_pred
