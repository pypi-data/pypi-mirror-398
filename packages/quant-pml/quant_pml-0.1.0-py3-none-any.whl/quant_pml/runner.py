from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from quant_pml.config.base_experiment_config import BaseExperimentConfig
    from quant_pml.config.trading_config import TradingConfig
    from quant_pml.hedge.base_hedger import BaseHedger
    from quant_pml.strategies.base_strategy import BaseStrategy

import pandas as pd

from quant_pml.backtest.assessor import Assessor, StrategyStatistics
from quant_pml.backtest.backtester import Backtester
from quant_pml.backtest.plot import (
    plot_cumulative_pnls,
    plot_histogram,
    plot_outperformance,
    plot_turnover,
)
from quant_pml.backtest.transaction_costs_charger import TransactionCostCharger
from quant_pml.base.currencies import Currencies
from quant_pml.base.prices import Prices
from quant_pml.config.base_experiment_config import BaseExperimentConfig
from quant_pml.data_handlers.dataset_builder_functions import DatasetData, build_dataset
from quant_pml.features.preprocessor import Preprocessor


def build_backtest[T: BaseExperimentConfig](  # noqa: PLR0913
    experiment_config: T,
    trading_config: TradingConfig,
    rebal_freq: str,
    dataset_builder_fn: Callable[[T], DatasetData] = build_dataset,
    start: str | None = None,
    end: str | None = None,
    *,
    with_causal_window: bool = False,
    verbose: bool = True,
) -> tuple[Preprocessor, Runner]:
    experiment_config.N_LOOKBEHIND_PERIODS = None
    experiment_config.REBALANCE_FREQ = rebal_freq

    if not with_causal_window:
        experiment_config.CAUSAL_WINDOW_SIZE = None

    if start is not None:
        assert start >= experiment_config.START_DATE, (
            f"Start date is before first available start date: {experiment_config.START_DATE}"
        )
        assert start <= experiment_config.END_DATE, f"Start date is after end date: {experiment_config.END_DATE}"

        experiment_config.START_DATE = pd.Timestamp(start)
    if end is not None:
        assert end >= experiment_config.START_DATE, (
            f"End date is before first available start date: {experiment_config.START_DATE}"
        )
        assert end <= experiment_config.END_DATE, f"End date is after end date: {experiment_config.END_DATE}"
        experiment_config.END_DATE = pd.Timestamp(end)

    preprocessor = Preprocessor()

    runner = Runner(
        experiment_config=experiment_config,
        dataset_builder_fn=dataset_builder_fn,
        trading_config=trading_config,
        verbose=verbose,
    )

    return preprocessor, runner


class Runner:
    def __init__(
        self,
        experiment_config: BaseExperimentConfig,
        trading_config: TradingConfig,
        dataset_builder_fn: Callable[[BaseExperimentConfig], DatasetData] = build_dataset,
        ml_metrics: list[Callable] | None = None,
        *,
        verbose: bool = False,
    ) -> None:
        self.dataset_builder_fn = dataset_builder_fn
        self.experiment_config = experiment_config
        self.trading_config = trading_config

        self.ml_metrics = ml_metrics
        self.verbose = verbose

        self.tc_charger = TransactionCostCharger(
            trading_config=self.trading_config,
        )

        self._is_hedged = None
        self._prepare()

    def _prepare(self) -> None:
        dataset = self.dataset_builder_fn(self.experiment_config)
        asset_universe = dataset.presence_matrix.columns.tolist()

        if self.experiment_config.ASSET_UNIVERSE is not None and len(self.experiment_config.ASSET_UNIVERSE) > 0:
            universe_restriction = self.experiment_config.ASSET_UNIVERSE
            asset_universe = list(set(asset_universe) & set(universe_restriction))

        self.data = dataset.data.loc[self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE]
        self.data.columns = self.data.columns.astype(str)
        self.presence_matrix = dataset.presence_matrix.loc[
            self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE,
            asset_universe,
        ]
        if dataset.dividends is not None:
            self.dividends = dataset.dividends.loc[
                self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE,
                asset_universe,
            ].fillna(0)
        else:
            self.dividends = None

        if len(self.data) == 0:
            msg = "Backtesting data is empty!"
            raise ValueError(msg)

        self.prices = Prices(self.data.loc[:, asset_universe])
        self.ccys = Currencies({}).from_single_currency(asset_universe, self.experiment_config.CCY)

        if dataset.mkt_caps is not None:
            self.mkt_caps = dataset.mkt_caps
        else:
            self.mkt_caps = pd.DataFrame(index=self.data.index, columns=asset_universe)

        self.returns = self.prices.to_returns()
        self.rf = self.data[self.experiment_config.RF_NAME]

        if dataset.targets is not None:
            self.targets = dataset.targets.loc[
                self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE
            ]
        else:
            self.targets = pd.DataFrame(index=self.data.index)

        if dataset.macro_features is not None:
            self.macro_features = dataset.macro_features.loc[
                self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE
            ]
        else:
            self.macro_features = pd.DataFrame(index=self.data.index)

        if dataset.asset_features is not None:
            self.asset_features = dataset.asset_features.loc[
                :,
                self.experiment_config.DATA_PROCESSING_START_DATE : self.experiment_config.END_DATE,
                :,
            ]
        else:
            self.asset_features = pd.DataFrame(
                index=pd.MultiIndex.from_product([self.prices.df.columns, self.data.index], names=["pmpid", "date"])
            )

        # Factors are passed as excess returns
        self.factors = self.data.loc[:, self.experiment_config.FACTORS]

        # Hedging assets should be passed as prices
        self.hedging_prices = (
            self.data.loc[:, self.experiment_config.HEDGING_ASSETS]
            if self.data.columns.isin(self.experiment_config.HEDGING_ASSETS).any()
            else pd.DataFrame(index=self.data.index)
        )

        self._strategy_backtester = self.init_backtester()

    def available_features(self) -> list[str]:
        return self.macro_features.columns.tolist()

    def init_backtester(self) -> Backtester:
        hedging_prices = Prices(self.hedging_prices) if self.hedging_prices is not None else self.hedging_prices
        hedge_freq = (
            self.experiment_config.HEDGE_FREQ
            if self.experiment_config.HEDGE_FREQ is not None
            else self.experiment_config.REBALANCE_FREQ
        )

        return Backtester(
            prices=self.prices,
            hedging_prices=hedging_prices,
            start_date=self.experiment_config.START_DATE,
            end_date=self.experiment_config.END_DATE,
            stocks_returns=self.returns,
            macro_features=self.macro_features,
            asset_features=self.asset_features,
            targets=self.targets,
            mkt_caps=self.mkt_caps,
            rf=self.rf,
            factors=self.factors,
            tc_charger=self.tc_charger,
            trading_config=self.trading_config,
            n_lookback_periods=self.experiment_config.N_LOOKBEHIND_PERIODS,
            min_rolling_periods=self.experiment_config.MIN_ROLLING_PERIODS,
            rebal_freq=self.experiment_config.REBALANCE_FREQ,
            hedge_freq=hedge_freq,
            presence_matrix=self.presence_matrix,
            dividends=self.dividends,
            causal_window_size=self.experiment_config.CAUSAL_WINDOW_SIZE,
            causal_window_end_date_field=self.experiment_config.CAUSAL_WINDOW_END_DATE_FIELD,
            verbose=self.verbose,  # TODO(@V): Fix verbose in backtest .run()
        )

    def run(
        self,
        feature_processor: Preprocessor,  # noqa: ARG002
        strategy: BaseStrategy,
        hedger: BaseHedger | None = None,
    ) -> StrategyStatistics:
        strategy.currencies = self.ccys

        if hedger is None:
            self._is_hedged = False
        else:
            self._is_hedged = True
            hedger.market_name = self.experiment_config.MKT_NAME

        self._strategy_backtester(strategy, hedger)

        return self.get_metrics()

    def get_metrics(
        self, start_date: pd.Timestamp | str | None = None, end_date: pd.Timestamp | str | None = None
    ) -> StrategyStatistics:
        if start_date is None:
            start_date = self.strategy_total_r.index.min()
        if end_date is None:
            end_date = self.strategy_total_r.index.max()

        assessor = Assessor(
            rf_rate=self.rf.loc[start_date:end_date],
            factors=self.factors.loc[start_date:end_date, self.experiment_config.FACTORS],
            mkt_name=self.experiment_config.MKT_NAME,
        )

        return assessor(self.strategy_total_r.loc[start_date:end_date])

    def run_one_step(
        self,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        feature_processor: Preprocessor,  # noqa: ARG002
        strategy: BaseStrategy,
        hedger: BaseHedger | None = None,
    ) -> pd.DataFrame:
        strategy.currencies = self.ccys
        return self._strategy_backtester.run_one_step(
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            hedger=hedger,
        )

    def __call__(
        self,
        feature_processor: Preprocessor,
        strategy: BaseStrategy,
        hedger: BaseHedger | None = None,
    ) -> StrategyStatistics:
        return self.run(
            feature_processor=feature_processor,
            strategy=strategy,
            hedger=hedger,
        )

    def plot_returns_histogram(
        self,
        start_date: pd.Timestamp | None = None,
        end_date: pd.Timestamp | None = None,
    ) -> None:
        if start_date is None:
            start_date = self.strategy_total_r.index.min()

        if end_date is None:
            end_date = self.strategy_total_r.index.max()

        plot_histogram(
            strategy_total=self.strategy_total_r.loc[start_date:end_date],
        )

    def plot_cumulative(  # noqa: PLR0913
        self,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        strategy_name: str | None = None,
        mkt_name: str | None = None,
        *,
        include_factors: bool = False,
        plot_log: bool = True,
    ) -> None:
        if start_date is None:
            start_date = self.strategy_total_r.index.min()

        if end_date is None:
            end_date = self.strategy_total_r.index.max()

        factors_total_r = self.factors.add(self.rf, axis=0).copy()

        if mkt_name is not None:
            factors_total_r = factors_total_r.rename(columns={self.experiment_config.MKT_NAME: mkt_name})

        plot_cumulative_pnls(
            strategy_total=self.strategy_total_r.loc[start_date:end_date],
            buy_hold=factors_total_r.loc[start_date:end_date] if include_factors else None,
            plot_log=plot_log,
            name_strategy=strategy_name if strategy_name is not None else "Strategy",
            mkt_name=mkt_name if mkt_name is not None else self.experiment_config.MKT_NAME,
        )

    def plot_turnover(
        self,
        start_date: pd.Timestamp | None = None,
        end_date: pd.Timestamp | None = None,
    ) -> None:
        if start_date is None:
            start_date = self.strategy_total_r.index.min()

        if end_date is None:
            end_date = self.strategy_total_r.index.max()

        plot_turnover(self.strategy_turnover.loc[start_date:end_date])

    def plot_outperformance(
        self,
        start_date: pd.Timestamp | None = None,
        end_date: pd.Timestamp | None = None,
        *,
        mkt_only: bool = False,
    ) -> None:
        if start_date is None:
            start_date = self.strategy_total_r.index.min()

        if end_date is None:
            end_date = self.strategy_total_r.index.max()

        strategy_total_r = self.strategy_total_r.loc[start_date:end_date]
        factors = self.factors.loc[start_date:end_date].add(self.rf.loc[start_date:end_date], axis=0)

        if mkt_only:
            plot_outperformance(
                strategy_total=strategy_total_r,
                baseline=factors[self.experiment_config.MKT_NAME],
                baseline_name=self.experiment_config.MKT_NAME,
            )
        else:
            for factor_name in factors.columns:
                plot_outperformance(
                    strategy_total=strategy_total_r,
                    baseline=factors[factor_name],
                    baseline_name=factor_name,
                )

    def save(self, strategy_name: str) -> None:
        if self._strategy_backtester.strategy_excess_r is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)

        filename = strategy_name + ".csv"
        strategy_xs_r = self._strategy_backtester.strategy_excess_r.rename(columns={"excess_r": "strategy_xs_r"})
        start, end = strategy_xs_r.index.min(), strategy_xs_r.index.max()
        factors = self._strategy_backtester.factors.loc[start:end]
        rf = self._strategy_backtester.rf.loc[start:end]
        rebal_bool = self._strategy_backtester.rebal_bool.loc[start:end]

        run_result = strategy_xs_r.merge(factors, left_index=True, right_index=True)
        run_result = run_result.merge(rf, left_index=True, right_index=True)
        run_result = run_result.merge(rebal_bool, left_index=True, right_index=True)

        run_result.to_csv(self.experiment_config.SAVE_PATH / filename)

    def load(self, strategy_name: str) -> pd.DataFrame:
        filename = strategy_name + ".csv"

        return pd.read_csv(self.experiment_config.SAVE_PATH / filename)

    @property
    def strategy_backtester(self) -> Backtester:
        return self._strategy_backtester

    @property
    def strategy_total_r(self) -> pd.Series[float]:
        if self._strategy_backtester.strategy_total_r is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)
        return self._strategy_backtester.strategy_total_r

    @property
    def strategy_excess_r(self) -> pd.Series[float]:
        if self._strategy_backtester.strategy_excess_r is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)
        return self._strategy_backtester.strategy_excess_r

    @property
    def strategy_daily_weights(self) -> pd.DataFrame:
        if self._strategy_backtester.strategy_daily_weights is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)
        return self._strategy_backtester.strategy_daily_weights

    @property
    def strategy_rebal_weights(self) -> pd.DataFrame:
        if self._strategy_backtester.strategy_rebal_weights is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)
        return self._strategy_backtester.strategy_rebal_weights

    @property
    def strategy_turnover(self) -> pd.Series:
        if self._strategy_backtester.turnover is None:
            msg = "Strategy is not backtested yet!"
            raise ValueError(msg)
        return self._strategy_backtester.turnover
