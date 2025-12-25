from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

import numpy as np

from quant_pml.features.ols_betas import get_window_betas
from quant_pml.hedge.base_hedger import BaseHedger


class MarketFuturesHedge(BaseHedger):
    def __init__(
        self,
        market_name: str = "MKT",
        window_days: int = 250,
        beta_smoothing: float = 0.2,
    ) -> None:
        super().__init__(market_name=market_name, requires_features=False)

        self.window_days = window_days
        self.beta_smoothing = beta_smoothing

        self._betas = None
        self.hedge_assets = None

    def _fit(self, training_data: TrainingData, hedge_assets: pd.DataFrame) -> None:  # noqa: ARG002
        self._betas = get_window_betas(
            market_index=training_data.factors[self.market_name],
            targets=training_data.simple_excess_returns,
            window_days=self.window_days,
            as_trading_days=True,
        )
        self._betas = self.beta_smoothing + (1 - self.beta_smoothing) * self._betas

    def _get_weights(
        self,
        prediction_data: PredictionData,  # noqa: ARG002
        asset_weights: pd.DataFrame,
        hedge_weights_: pd.DataFrame,
    ) -> pd.DataFrame:
        hedge_weights = -np.dot(self._betas.to_numpy().T, asset_weights.to_numpy().T)
        hedge_weights_.loc[:, self.hedge_assets] = hedge_weights

        return hedge_weights_

    @property
    def betas(self) -> pd.DataFrame:
        return self._betas
