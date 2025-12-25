from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Data:
    pred_date: pd.Timestamp | str

    macro_features: pd.DataFrame | None = None
    asset_features: pd.DataFrame | None = None

    prices: pd.DataFrame | None = None
    market_cap: pd.DataFrame | None = None
    factors: pd.DataFrame | None = None

    @staticmethod
    def _append(df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Efficiently append new_df to df, optimized for single-row appends.

        - Returns new_df if df is None or empty.
        - Uses .loc single-row assignment when possible to avoid expensive concat copies.
        - Falls back to pd.concat for multi-row appends.
        """
        if new_df is None or len(new_df) == 0:
            return df
        if df is None or len(df) == 0:
            # Keep a copy to avoid referencing external objects that may mutate
            return new_df.copy()

        # If it's a single-row append, use fast path
        if len(new_df) == 1:
            idx = new_df.index[0]
            # If index already exists, keep previous behavior by concatenating
            if idx in df.index:
                return pd.concat([df, new_df], axis=0, sort=False, copy=False)
            # union columns to avoid missing columns on either side
            all_cols = df.columns.union(new_df.columns)
            if not df.columns.equals(all_cols):
                df = df.reindex(columns=all_cols)
            # build aligned row
            row = new_df.reindex(columns=all_cols).iloc[0]
            # Assign via .loc (pandas will extend index if needed)
            df.loc[idx] = row
            return df

        # Fallback for multi-row appends
        return pd.concat([df, new_df], axis=0, sort=False, copy=False)

    def add_macro_features(self, new_features: pd.DataFrame) -> None:
        if new_features.empty:
            return
        self.macro_features = self._append(self.macro_features, new_features)

    def add_factors(self, new_factors: pd.DataFrame) -> None:
        self.factors = self._append(self.factors, new_factors)

    def add_prices(self, new_prices: pd.DataFrame) -> None:
        self.prices = self._append(self.prices, new_prices)

    def add_market_caps(self, new_market_caps: pd.DataFrame) -> None:
        self.market_cap = self._append(self.market_cap, new_market_caps)


@dataclass
class TrainingData(Data):
    simple_total_returns: pd.DataFrame | None = None
    log_total_returns: pd.DataFrame | None = None

    simple_excess_returns: pd.DataFrame | None = None
    log_excess_returns: pd.DataFrame | None = None

    targets: pd.DataFrame | None = None

    def add_targets(self, new_targets: pd.DataFrame) -> None:
        self.targets = self._append(self.targets, new_targets)


@dataclass
class PredictionData(Data):
    pass
