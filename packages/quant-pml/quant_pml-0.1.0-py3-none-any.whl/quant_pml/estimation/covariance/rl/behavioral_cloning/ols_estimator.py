from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from quant_pml.estimation.covariance.rl.base_rl_estimator import BaseRLCovEstimator


class OLSCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size)

        self.last_pred = None
        self.encountered_nan = False

        self.scaler = StandardScaler()

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        # TODO(@V): Fix lagged target
        features = features.dropna(axis=1, how="any")
        merged_df = features.merge(shrinkage_target, left_index=True, right_index=True)
        features = merged_df[features.columns]
        shrinkage_target = merged_df[merged_df.columns.difference(features.columns)]
        if shrinkage_target.isna().any().any():
            self.encountered_nan = True
        else:
            features = self.scaler.fit_transform(features)
            self.ridge = LinearRegression()
            self.ridge.fit(X=features, y=shrinkage_target.iloc[:, 0])
            self.encountered_nan = False

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        features = features.drop(columns=["lagged_target", "target_rolling_mean", "target_rolling_vol"])
        features = self.scaler.transform(features)
        if not self.encountered_nan:
            pred = self.ridge.predict(features).item()
            self.last_pred = pred
            return pred

        return self.last_pred
