from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import PredictionData

import pandas as pd

from quant_pml.strategies.timing.vol_timing import VolTiming


class VolTimingVsBonds(VolTiming):
    def __init__(self, target_asset: str, target_weight: float, lookback: int | str) -> None:
        super().__init__(
            lookback=lookback,
            max_exposure=1.0,
        )

        self.target_asset = target_asset
        self.target_weight = target_weight

    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:  # noqa: ARG002
        trailing_vars = pd.DataFrame(self.trailing_variances)
        trailing_vars = trailing_vars.mean(axis=0)

        tgt_weight = trailing_vars[self.target_asset] / self.current_variances[self.target_asset]
        tgt_weight *= self.target_weight
        tgt_weight = min(tgt_weight, self.max_exposure)

        resid_assets = pd.Index(self.available_assets).difference([self.target_asset])
        resid_weight = (1 - tgt_weight) / len(resid_assets)

        weights_.loc[:, self.target_asset] = tgt_weight
        weights_.loc[:, resid_assets] = resid_weight

        return weights_
