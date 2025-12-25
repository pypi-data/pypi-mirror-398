from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from quant_pml.config.trading_config import TradingConfig

np.seterr(all="raise")


class TransactionCostCharger:
    def __init__(self, trading_config: TradingConfig) -> None:
        super().__init__()

        self.trading_config = trading_config

        self._strategy_total_r = None
        self._strategy_excess_r = None
        self._strategy_turnover = None

    @staticmethod
    def get_turnover(rebal_weights: pd.DataFrame, daily_weights: pd.DataFrame) -> pd.Series:
        rebal_weights = daily_weights.loc[rebal_weights.index]
        period_end_weights = daily_weights.shift(-1).loc[rebal_weights.index]
        turnover = rebal_weights.sub(period_end_weights).abs().sum(axis=1).rename("turnover").astype(np.float64)

        return turnover  # type: ignore[no-any-return]

    def _get_trading_costs(self, rebal_weights: pd.DataFrame, daily_weights: pd.DataFrame) -> pd.Series:
        turnover = self.get_turnover(rebal_weights, daily_weights)
        self._strategy_turnover = turnover

        trading_costs = pd.Series(index=daily_weights.index, name="trading_costs", dtype=np.float64)
        # TODO(@V): Bid and Ask commission
        tc = (self.trading_config.broker_fee + self.trading_config.bid_ask_spread / 2) * turnover
        tc = tc.iloc[1:]
        trading_costs.loc[tc.index] = tc

        return trading_costs

    def _get_success_costs(self, returns: pd.DataFrame) -> pd.Series:
        success_costs = pd.Series(np.zeros(len(returns)), index=returns.index, name="success_costs")
        success_costs.iloc[-1] = (np.maximum(returns.add(1).prod().add(-1), 0) * self.trading_config.success_fee).sum()
        return success_costs

    def _get_transaction_costs(
        self, rebal_weights: pd.DataFrame, daily_weights: pd.DataFrame, returns: pd.DataFrame
    ) -> pd.Series:
        trading_costs = self._get_trading_costs(rebal_weights=rebal_weights, daily_weights=daily_weights)
        mf_costs = self._get_mf_costs(returns=returns)
        success_costs = self._get_success_costs(returns=returns)

        costs = pd.merge_asof(
            trading_costs,
            mf_costs,
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta("1D"),
        )
        costs = pd.merge_asof(
            costs,
            success_costs,
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta("1D"),
        )

        return costs.sum(axis=1)

    def _get_mf_costs(self, returns: pd.DataFrame) -> pd.Series:
        # TODO(V): fix to mf_freq parameterizable
        mf_costs = pd.Series(np.zeros(returns.shape[0]), index=returns.index, name="management_fee").resample("YE").sum()
        mf_costs = mf_costs + self.trading_config.management_fee
        return mf_costs.add(1).cumprod().add(-1)

    def __call__(self, rebal_weights: pd.DataFrame, daily_weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
        return self._get_transaction_costs(rebal_weights, daily_weights, returns)

    @property
    def turnover(self) -> pd.Series:
        return self._strategy_turnover
