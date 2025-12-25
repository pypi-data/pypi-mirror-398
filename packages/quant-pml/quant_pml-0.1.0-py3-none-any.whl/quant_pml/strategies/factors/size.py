from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quant_pml.strategies.optimization_data import TrainingData

import pandas as pd

from quant_pml.strategies.factors.sorting_strategy import SortingStrategy


class Size(SortingStrategy):
    def __init__(
        self,
        mode: str,
        quantile: float | None = None,
        n_holdings: int | None = None,
        weighting_scheme: str = "equally_weighted",
    ) -> None:
        super().__init__(
            quantile=quantile,
            mode=mode,
            n_holdings=n_holdings,
            weighting_scheme=weighting_scheme,
        )

    def get_scores(self, data: TrainingData) -> pd.Series:
        mkt_caps = data.market_cap

        return -self._get_last_available_values(mkt_caps)

    @staticmethod
    def _get_last_available_values(mkt_caps: pd.DataFrame) -> pd.Series:
        if mkt_caps.empty:
            return pd.Series(dtype=float)

        last_row = mkt_caps.iloc[-1]

        # If the entire last row is None/NaN, use last available values
        if last_row.isna().all():
            # For each asset, find the last non-NaN value
            last_values = mkt_caps.ffill().iloc[-1]
        else:
            # Use last row, but fill any NaN values with last available values for those assets
            last_values = last_row.copy()
            nan_mask = last_values.isna()
            if nan_mask.any():
                # Fill NaN values with last available values
                filled_data = mkt_caps.ffill()
                last_values.loc[nan_mask] = filled_data.iloc[-1].loc[nan_mask]

        return last_values
