from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from quant_pml.backtest.transaction_costs_charger import TransactionCostCharger
    from quant_pml.base.prices import Prices
    from quant_pml.base.returns import Returns
    from quant_pml.config.trading_config import TradingConfig
    from quant_pml.hedge.base_hedger import BaseHedger
    from quant_pml.strategies.base_strategy import BaseStrategy

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BusinessDay
from tqdm import tqdm

from quant_pml.strategies.optimization_data import PredictionData, TrainingData

np.seterr(all="raise")

FREQ_MAPPING = {
    "WE": "W",  # Week End -> Week
    "WE-SUN": "W-SUN",
    "WE-MON": "W-MON",
    "WE-TUE": "W-TUE",
    "WE-WED": "W-WED",
    "WE-THU": "W-THU",
    "WE-FRI": "W-FRI",
    "WE-SAT": "W-SAT",
}


class Backtester:
    def __init__(  # noqa: PLR0913, PLR0913, RUF100
        self,
        prices: Prices,
        hedging_prices: Prices | None,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        stocks_returns: Returns,
        targets: pd.DataFrame,
        macro_features: pd.DataFrame,
        asset_features: pd.DataFrame,
        mkt_caps: pd.DataFrame,
        rf: pd.Series,
        factors: pd.DataFrame,
        tc_charger: TransactionCostCharger,
        trading_config: TradingConfig,
        n_lookback_periods: int,
        min_rolling_periods: int | None,
        rebal_freq: int | str | None,
        hedge_freq: int | str | None,
        dividends: pd.DataFrame | None = None,
        presence_matrix: pd.DataFrame | None = None,
        causal_window_end_date_field: str | None = None,
        causal_window_size: int | None = None,
        *,
        verbose: bool = False,
    ) -> None:
        super().__init__()

        self.prices = prices
        self.hedging_prices = hedging_prices

        self.start_date = start_date
        self.end_date = end_date

        self.stocks_returns = stocks_returns
        self.macro_features = macro_features
        self.asset_features = asset_features
        self.asset_features_dates = asset_features.index.get_level_values("date")
        self.targets = targets
        self.mkt_caps = mkt_caps
        self.rf = rf
        self.factors = factors
        self.tc_charger = tc_charger
        self.trading_config = trading_config
        self.trading_lag = trading_config.trading_lag_days
        self.n_lookback_periods = n_lookback_periods
        self.min_rolling_periods = n_lookback_periods if min_rolling_periods is None else min_rolling_periods
        self.rebal_freq = rebal_freq
        self.hedge_freq = hedge_freq
        self.presence_matrix = presence_matrix
        self.dividends = dividends
        self.causal_window_size = causal_window_size

        if self.presence_matrix is not None:
            self.avg_num_stocks_in_universe = self.presence_matrix.sum(axis=1).mean()
        else:
            self.avg_num_stocks_in_universe = None

        self.causal_window_end_date_field = causal_window_end_date_field
        if self.causal_window_end_date_field is not None:
            self.causal_window_size = None
        self.verbose = verbose

        self._strategy_total_r = None
        self._strategy_unhedged_total_r = None
        self._strategy_excess_r = None
        self._strategy_transac_costs = None

        self._rebal_bool = None
        self._first_rebal_date = None

        self._hedge_total_r = None
        self._hedge_excess_r = None

        self._strategy_rebal_weights = None
        self._hedge_rebal_weights = None
        self._strategy_daily_weights = None
        self._hedge_daily_weights = None

        self._rolling_strategy_tuples = None
        self._rolling_hedge_tuples = None

        self._prepare()

    def __call__(self, strategy: BaseStrategy, hedger: BaseHedger | None = None) -> None:
        self.run(strategy, hedger)

    def generate_rebal_schedule(self, freq: int | str | None) -> pd.DatetimeIndex:  # noqa: C901, PLR0912
        prices = self.prices.df.loc[self.start_date : self.end_date]
        date_index = prices.index

        if freq is None:
            schedule = [date_index[0]]
        elif freq == "from_presence":
            pm_changes = self.presence_matrix.fillna(0).diff().abs().iloc[1:].sum(axis=1)
            schedule = pm_changes[pm_changes > 0].index
        elif isinstance(freq, str):
            # Use mapped frequency if available, otherwise use original
            mapped_freq = FREQ_MAPPING.get(freq, freq)

            # Generate dates at the specified frequency
            generated_dates = pd.date_range(start=date_index.min(), end=date_index.max(), freq=mapped_freq)

            # Find closest future date in date_index for each generated date
            closest_dates_indices = []
            for gen_date in generated_dates:
                future_dates = date_index[date_index >= gen_date]
                if len(future_dates) > 0:
                    closest_dates_indices.append(date_index.get_loc(future_dates[0]))
            schedule = date_index[closest_dates_indices].drop_duplicates()
        elif isinstance(freq, int):
            generated_dates = pd.date_range(start=date_index.min(), end=date_index.max(), freq=f"{freq}B")

            closest_dates_indices = date_index.get_indexer(generated_dates, method="nearest")

            schedule = date_index[closest_dates_indices]
        else:
            msg = f"Unknown rebalancing frequency type: {freq}."
            raise NotImplementedError(msg)

        if self.min_rolling_periods is not None and freq is not None:
            for i, date in enumerate(schedule):
                n_points = self.prices.df.loc[:date].shape[0]
                if n_points >= self.min_rolling_periods:
                    schedule = schedule[i:]
                    break

        if schedule[-1] == self.end_date:
            schedule = schedule[:-1]

        if len(schedule) > 1:
            start_date = self.start_date if self.start_date is not None else self.presence_matrix.index[0]
            while schedule[0] < start_date:
                schedule = schedule[1:]
                if len(schedule) == 0:
                    break

        return pd.DatetimeIndex(schedule)

    def _prepare(self) -> None:
        self.rebal_schedule = self.generate_rebal_schedule(freq=self.rebal_freq)
        self.hedge_schedule = self.generate_rebal_schedule(freq=self.hedge_freq)

        if self.verbose:
            print(f"Backtest on {self.rebal_schedule[0]} to {self.prices.df.index[-1]}")  # noqa: T201
            print(f"Num Train Iterations: {len(self.rebal_schedule)}")  # noqa: T201
            print(f"Num Hedge Iterations: {len(self.hedge_schedule)}")  # noqa: T201
            print(f"Num OOS Daily Points: {len(self.macro_features.loc[self.rebal_schedule[0] :])}")  # noqa: T201
            if self.avg_num_stocks_in_universe is not None:
                print(f"Avg Num Stocks in Universe: {self.avg_num_stocks_in_universe:.2f}")  # noqa: T201

    def get_data(self, pred_date: pd.Timestamp) -> tuple[TrainingData, PredictionData]:
        # Each slice => n - lag goes into training -> 1 last for predict
        available_macro_features = self.macro_features.loc[:pred_date]
        train_macro_features = available_macro_features
        pred_macro_features = available_macro_features.iloc[-1:]

        if self.asset_features.shape[1] > 0:
            available_dates = self.asset_features_dates[self.asset_features_dates <= pred_date].unique().sort_values()
            asset_features_pred_date = available_dates[-1]
            train_asset_features = self.asset_features.loc[:, available_dates, :]
            # List to preserve the shape
            pred_asset_features = self.asset_features.loc[:, [asset_features_pred_date], :]
        else:
            train_asset_features = None
            pred_asset_features = None

        available_prices = self.prices.df.loc[:pred_date]
        train_prices = available_prices
        pred_prices = available_prices.iloc[-1:]

        available_mkt_caps = self.mkt_caps.loc[:pred_date]
        train_mkt_caps = available_mkt_caps
        pred_mkt_caps = available_mkt_caps.iloc[-1:]

        train_factors = self.factors.loc[:pred_date]
        train_targets = self.targets.loc[:pred_date]

        if self.causal_window_end_date_field is not None and train_targets.shape[1] > 0:
            train_targets.loc[:, self.causal_window_end_date_field] = pd.to_datetime(
                train_targets.loc[:, self.causal_window_end_date_field]
            )
            train_targets = train_targets.reset_index().set_index(self.causal_window_end_date_field)
            train_targets = train_targets[train_targets.index <= pred_date]
            train_targets = train_targets.reset_index().drop(columns=[self.causal_window_end_date_field]).set_index("date")
        elif self.causal_window_size is not None:
            train_targets = train_targets.iloc[: -self.causal_window_size]

        train_rf = self.rf.loc[:pred_date]

        simple_train_total_r = self.stocks_returns.simple_returns.loc[:pred_date]
        simple_train_xs_r = simple_train_total_r.sub(train_rf, axis=0)

        log_train_total_r = self.stocks_returns.log_returns.loc[:pred_date]
        log_train_xs_r = log_train_total_r.sub(train_rf, axis=0)

        training_data = TrainingData(
            pred_date=pred_date,
            macro_features=train_macro_features,
            asset_features=train_asset_features,
            targets=train_targets,
            prices=train_prices,
            market_cap=train_mkt_caps,
            factors=train_factors,
            simple_total_returns=simple_train_total_r,
            log_total_returns=log_train_total_r,
            simple_excess_returns=simple_train_xs_r,
            log_excess_returns=log_train_xs_r,
        )

        prediction_data = PredictionData(
            pred_date=pred_date,
            macro_features=pred_macro_features,
            asset_features=pred_asset_features,
            prices=pred_prices,
            market_cap=pred_mkt_caps,
        )

        return training_data, prediction_data

    def get_strategy_weights(self, strategy: BaseStrategy, pred_date: pd.Timestamp) -> np.array:
        if self.presence_matrix is not None:
            curr_matrix = self.presence_matrix.loc[:pred_date].iloc[-1]
            strategy.universe = curr_matrix[curr_matrix == 1].index.tolist()

        training_data, prediction_data = self.get_data(pred_date)

        # Whether the strategy has a memory or retrains from scratch is handled inside the strategy obj
        strategy.fit(training_data=training_data)

        weights = strategy(prediction_data=prediction_data)
        weights = np.clip(
            weights,
            self.trading_config.min_exposure,
            self.trading_config.max_exposure,
        )

        return weights.to_numpy()

    def get_hedger_weights(self, hedger: BaseHedger, strategy_weights: pd.DataFrame) -> pd.DataFrame:  # noqa: PLR0915, PLR0912
        requires_features = hedger.requires_features

        # TODO(@V): Deprecate and use calc_rolling_weights(lambda pred_date: get_hedger_weights(...))
        rolling_weights = []
        last_hedge_date = None
        n_hedges = 0
        for rebal_date in tqdm(
            self.hedge_schedule,
            desc="Computing Hedging Weights",
            disable=not self.verbose,
        ):
            if rebal_date < self._first_rebal_date:
                should_hedge = False
            elif self.hedge_freq is None:
                should_hedge = last_hedge_date is None
            elif isinstance(self.hedge_freq, int | float):
                if last_hedge_date is None:
                    should_hedge = True
                else:
                    n_days_change = (rebal_date - last_hedge_date).days if last_hedge_date is not None else 0
                    should_hedge = n_days_change >= self.hedge_freq
            elif isinstance(self.hedge_freq, str):
                should_hedge = rebal_date >= self.hedge_schedule[n_hedges]
            else:
                msg = f"Unknown hedging frequency type: {self.hedge_freq}."
                raise NotImplementedError(msg)

            if should_hedge:
                period_end_weights = strategy_weights.loc[rebal_date].copy()
                picked_assets = period_end_weights[(period_end_weights > 0) | (period_end_weights < 0)].index

                pred_date = rebal_date - BusinessDay(n=self.trading_lag)

                if requires_features:
                    # Each slice => n - lag goes into training -> 1 last for predict
                    available_macro_features = self.macro_features.loc[:pred_date]
                    train_macro_features = available_macro_features
                    pred_macro_features = available_macro_features.iloc[-1:]
                else:
                    train_macro_features = None
                    pred_macro_features = None

                if requires_features and self.asset_features.shape[1] > 0:
                    available_dates = self.asset_features_dates[self.asset_features_dates <= pred_date]
                    asset_features_pred_date = available_dates[-1]
                    train_asset_features = self.asset_features.loc[:, available_dates, :]
                    # List to preserve the shape
                    pred_asset_features = self.asset_features.loc[:, [asset_features_pred_date], :]
                else:
                    train_asset_features = None
                    pred_asset_features = None

                available_mkt_caps = self.mkt_caps.loc[:pred_date]
                train_mkt_caps = available_mkt_caps
                pred_mkt_caps = available_mkt_caps.iloc[-1:]

                train_factors = self.factors.loc[:pred_date]
                train_rf = self.rf.loc[:pred_date]

                simple_train_xs_r = self.stocks_returns.simple_returns.loc[:pred_date].sub(train_rf, axis=0)
                log_train_xs_r = self.stocks_returns.log_returns.loc[:pred_date].sub(train_rf, axis=0)

                train_hedging_assets_r = self.hedging_prices.to_returns().simple_returns.loc[:pred_date]

                training_data = TrainingData(
                    pred_date=pred_date,
                    macro_features=train_macro_features,
                    asset_features=train_asset_features,
                    prices=None,
                    market_cap=train_mkt_caps[picked_assets] if len(train_mkt_caps) > 0 else train_mkt_caps,
                    factors=train_factors,
                    simple_excess_returns=simple_train_xs_r[picked_assets],
                    log_excess_returns=log_train_xs_r[picked_assets],
                )

                prediction_data = PredictionData(
                    pred_date=pred_date,
                    macro_features=pred_macro_features,
                    asset_features=pred_asset_features,
                    prices=None,
                    market_cap=pred_mkt_caps[picked_assets] if len(pred_mkt_caps) > 0 else pred_mkt_caps,
                )

                hedger.fit(
                    training_data=training_data,
                    hedge_assets=train_hedging_assets_r,
                )
                hedge_weights = hedger(
                    prediction_data=prediction_data,
                    asset_weights=period_end_weights[picked_assets],
                )

                rolling_weights.append([rebal_date, *hedge_weights.to_numpy().flatten().tolist()])

                last_hedge_date = rebal_date
                n_hedges += 1

        hedge_columns = ["date", *list(self.hedging_prices.df.columns)]
        self._hedge_rebal_weights = pd.DataFrame(rolling_weights, columns=hedge_columns).set_index("date")

        return self._hedge_rebal_weights

    def get_rolling_weights(self, get_weights_fn: Callable[[pd.Timestamp], np.ndarray[float]]) -> list[np.ndarray]:
        rolling_weights = []
        last_rebal_date = None
        n_rebals = 0
        for rebal_date in tqdm(self.rebal_schedule, desc="Computing Weights", disable=not self.verbose):
            if last_rebal_date is None:
                self._first_rebal_date = rebal_date

            if self.rebal_freq is None:
                should_rebal = last_rebal_date is None
            elif isinstance(self.rebal_freq, int | float):
                if last_rebal_date is None:
                    should_rebal = True
                else:
                    n_days_change = (rebal_date - last_rebal_date).days if last_rebal_date is not None else 0
                    should_rebal = n_days_change >= self.rebal_freq
            elif isinstance(self.rebal_freq, str):
                should_rebal = rebal_date >= self.rebal_schedule[n_rebals]
            else:
                msg = f"Unknown rebalancing frequency type: {self.rebal_freq}."
                raise NotImplementedError(msg)

            if should_rebal:
                pred_date = rebal_date - BusinessDay(n=self.trading_lag)

                weights = get_weights_fn(pred_date)

                rolling_weights.append([rebal_date, *weights.flatten().tolist()])

                last_rebal_date = rebal_date
                n_rebals += 1

        return rolling_weights

    def run(self, strategy: BaseStrategy, hedger: BaseHedger | None = None) -> None:
        strategy_weights = self.get_rolling_weights(
            lambda pred_date: self.get_strategy_weights(strategy=strategy, pred_date=pred_date)
        )
        stocks_columns = ["date", *list(self.stocks_returns.simple_returns.columns)]
        strategy_weights = pd.DataFrame(strategy_weights, columns=stocks_columns).set_index("date").fillna(0.0)
        self._strategy_rebal_weights = strategy_weights

        daily_prices = self.prices.df

        daily_navs, daily_weights = self.get_daily_navs(
            rebal_weights=strategy_weights,
            daily_prices=daily_prices,
            rf=self.rf,
        )

        self._strategy_daily_weights = daily_weights

        strategy_unhedged_total_r = daily_navs.infer_objects(copy=False).pct_change().iloc[1:]
        self._strategy_unhedged_total_r = strategy_unhedged_total_r

        if hedger is not None:
            daily_hedge_prices = self.hedging_prices.df
            self._hedge_rebal_weights = self.get_hedger_weights(hedger, daily_weights)
            daily_hedge_navs, daily_hedge_weights = self.get_daily_navs(
                rebal_weights=self._hedge_rebal_weights,
                daily_prices=daily_hedge_prices,
                rf=None,
            )

            self._hedge_daily_weights = daily_hedge_weights

            daily_hedge_navs = daily_hedge_navs.loc[daily_navs.index.min() : daily_navs.index.max()]

            hedge_r = daily_hedge_navs.infer_objects(copy=False).fillna(1).pct_change().iloc[1:, 0]

            self._hedge_excess_r = hedge_r

            strategy_total_r = strategy_unhedged_total_r.add(hedge_r, axis=0)
        else:
            strategy_total_r = strategy_unhedged_total_r

        # TODO(@V): Add transac costs for hedging
        strategy_transac_costs = self.tc_charger(
            rebal_weights=strategy_weights,
            daily_weights=daily_weights,
            returns=self.stocks_returns.simple_returns.loc[strategy_total_r.index.min() : strategy_total_r.index.max()],
        )
        strategy_total_r = (
            strategy_total_r.sub(strategy_transac_costs, axis=0).rename(columns={"strategy_nav": "total_r"}).fillna(0.0)
        )

        rf = self.rf.loc[strategy_total_r.index.min() : strategy_total_r.index.max()]
        strategy_excess_r = strategy_total_r.sub(rf, axis=0).rename(
            columns={"total_r": "excess_r"},
        )

        self._strategy_transac_costs = strategy_transac_costs
        self._strategy_total_r = strategy_total_r
        self._strategy_excess_r = strategy_excess_r

        self._rebal_bool = pd.Series(1, index=self.strategy_rebal_weights.index, name="rebal")
        self._rebal_bool = self._rebal_bool.reindex(self.strategy_daily_weights.index).fillna(0).astype(bool)

    def run_one_step(
        self,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        strategy: BaseStrategy,
        hedger: BaseHedger | None = None,
    ) -> pd.DataFrame:
        pred_date = start_date - BusinessDay(n=self.trading_lag)
        weights = self.get_strategy_weights(strategy=strategy, pred_date=pred_date)
        strategy_weights = [[start_date, *weights.flatten().tolist()]]

        stocks_columns = ["date", *list(self.stocks_returns.simple_returns.columns)]
        strategy_weights = pd.DataFrame(strategy_weights, columns=stocks_columns).set_index("date").fillna(0.0)

        daily_prices = self.prices.df.loc[start_date:end_date]
        rf = self.rf.loc[start_date:end_date]

        daily_navs, _daily_weights = self.get_daily_navs(
            rebal_weights=strategy_weights,
            daily_prices=daily_prices,
            rf=rf,
        )

        strategy_unhedged_total_r = daily_navs.infer_objects(copy=False).pct_change().iloc[1:]

        # TODO(@V): Add hedger (!!!)
        if hedger is not None:
            msg = "Hedged one step is not supported yet!"
            raise NotImplementedError(msg)

        return strategy_unhedged_total_r

    @staticmethod
    def rebal_weights_to_daily_qtys(strategy_weights: pd.DataFrame, dates: pd.Index) -> pd.DataFrame:
        return strategy_weights.resample("D").ffill().loc[dates]

    def get_daily_navs(
        self,
        rebal_weights: pd.DataFrame,
        daily_prices: pd.DataFrame,
        dividends: pd.DataFrame | None = None,
        rf: pd.Series | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        rebal_dates = rebal_weights.index

        last_rebal_date = rebal_dates[0]
        prev_total_nav = 1_000_000.0
        daily_navs = pd.DataFrame(index=daily_prices.index, columns=["strategy_nav"]).loc[last_rebal_date:]
        daily_weights = pd.DataFrame(index=daily_prices.index, columns=rebal_weights.columns).loc[last_rebal_date:]
        for rebal_date in tqdm(
            [*rebal_dates[1:].tolist(), None],
            desc="Computing NAVs",
            disable=not self.verbose,
        ):
            prices = daily_prices.loc[last_rebal_date:rebal_date]

            qtys = (prev_total_nav * rebal_weights.loc[last_rebal_date].to_numpy()) / prices.iloc[0]

            if dividends is not None:
                divs = self.dividends.loc[last_rebal_date:rebal_date]
                divs = (qtys * divs).fillna(0)

            long_stocks = qtys > 0
            short_stocks = qtys < 0
            long_qtys = qtys[long_stocks]
            short_qtys = qtys[short_stocks]

            if dividends is not None:
                divs.loc[:, long_stocks] = divs.loc[:, long_stocks] * (1 - self.trading_config.long_dividend_tax)

            long_allocs = (long_qtys * prices.loc[:, long_stocks]).ffill()
            if dividends is not None:
                long_allocs = long_allocs.add(divs.loc[:, long_stocks], axis=0)
            long_nav = long_allocs.sum(axis=1)

            excess_cash_position = prev_total_nav - long_nav.loc[last_rebal_date]
            if excess_cash_position != 0 or sum(short_stocks) > 0:
                if sum(short_stocks) > 0:
                    short_allocs = (short_qtys * prices.loc[:, short_stocks]).ffill()
                    if dividends is not None:
                        short_allocs = short_allocs.sub(divs.loc[:, short_stocks], axis=0)
                    short_nav = short_allocs.sum(axis=1)

                    excess_cash_position += -(short_qtys * prices.loc[last_rebal_date]).sum()
                    total_nav = long_nav.add(short_nav, axis=0)
                else:
                    total_nav = long_nav.copy()

                prev_date = daily_prices.index[daily_prices.index <= last_rebal_date].max()
                if rf is not None:
                    rf_income = rf.loc[prev_date:rebal_date].add(1)
                else:
                    rf_income = pd.Series(1.0, index=total_nav.loc[last_rebal_date:rebal_date].index)
                rf_income.iloc[0] = excess_cash_position
                rf_income = rf_income.cumprod()
                total_nav.loc[last_rebal_date:rebal_date] = (
                    total_nav.loc[last_rebal_date:rebal_date] + rf_income.loc[last_rebal_date:rebal_date]
                )
            else:
                total_nav = long_nav.copy()

            daily_weights.loc[last_rebal_date:rebal_date, long_stocks] = long_allocs.div(total_nav, axis=0)
            if sum(short_stocks) > 0:
                daily_weights.loc[last_rebal_date:rebal_date, short_stocks] = short_allocs.div(total_nav, axis=0)
            prev_total_nav = total_nav.iloc[-1].item()

            assert not np.isnan(prev_total_nav)
            assert np.isfinite(total_nav).all()

            daily_navs.loc[last_rebal_date:rebal_date] = total_nav.to_numpy().reshape(-1, 1)
            last_rebal_date = rebal_date

        return daily_navs / daily_navs.iloc[0], daily_weights

    @staticmethod
    def daily_qtys_to_weights(daily_qtys: pd.DataFrame, daily_prices: pd.DataFrame, daily_navs: pd.DataFrame) -> pd.DataFrame:
        daily_allocs = daily_qtys.mul(daily_prices.loc[daily_qtys.index[0] :], axis=0).infer_objects(copy=False).ffill()
        return daily_allocs.div(daily_navs.to_numpy(), axis=1)

    @property
    def strategy_total_r(self) -> pd.Series:
        return self._strategy_total_r

    @property
    def strategy_unhedged_total_r(self) -> pd.Series:
        return self._strategy_unhedged_total_r

    @property
    def strategy_excess_r(self) -> pd.Series:
        return self._strategy_excess_r

    @property
    def rebal_bool(self) -> pd.Series:
        return self._rebal_bool

    @property
    def rebal_dates(self) -> pd.Index:
        rebal_dates = self.rebal_bool
        return rebal_dates[rebal_dates].index

    @property
    def strategy_transaction_costs(self) -> pd.DataFrame:
        return self._strategy_transac_costs

    @property
    def hedge_total_r(self) -> pd.Series:
        return self._hedge_total_r

    @property
    def hedge_excess_r(self) -> pd.Series:
        return self._hedge_excess_r

    @property
    def turnover(self) -> pd.Series:
        return self.tc_charger.turnover

    @property
    def strategy_rebal_weights(self) -> pd.DataFrame:
        return self._strategy_rebal_weights

    @property
    def strategy_daily_weights(self) -> pd.DataFrame:
        return self._strategy_daily_weights

    @property
    def hedge_rebal_weights(self) -> pd.DataFrame:
        return self._hedge_rebal_weights

    @property
    def hedge_daily_weights(self) -> pd.DataFrame:
        return self._hedge_daily_weights
