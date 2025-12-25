from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from sklearn.linear_model import LinearRegression

from quant_pml.cov_estimators.rl.base_rl_estimator import BaseRLCovEstimator


class ARCovEstimator(BaseRLCovEstimator):
    def __init__(self, shrinkage_type: str, window_size: int | None = None) -> None:
        super().__init__(shrinkage_type=shrinkage_type, window_size=window_size)

        self.last_pred = None
        self.encountered_nan = False

    def _fit_shrinkage(self, features: pd.DataFrame, shrinkage_target: pd.Series) -> None:
        features = features.ffill()
        merged_df = features.merge(shrinkage_target, left_index=True, right_index=True).dropna(axis=0, how="any")
        features = merged_df[features.columns]
        shrinkage_target = merged_df[merged_df.columns.difference(features.columns)].iloc[:, 0]
        if shrinkage_target.isna().any():
            self.encountered_nan = True
        else:
            self.lr = LinearRegression()
            self.lr.fit(X=features[["lagged_target"]], y=shrinkage_target)
            self.encountered_nan = False

    def _predict_shrinkage(self, features: pd.DataFrame) -> float:
        if not self.encountered_nan:
            pred = self.lr.predict(features[["lagged_target"]]).item()
            self.last_pred = pred
            return pred

        return self.last_pred
