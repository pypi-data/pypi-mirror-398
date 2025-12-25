from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Final

import pandas as pd

if TYPE_CHECKING:
    from quant_pml.base.currencies import Currencies
    from quant_pml.strategies.optimization_data import PredictionData, TrainingData

DEFAULT_NOTIONAL_PRECISION: Final[int] = 2


class BaseStrategy(ABC):
    """Abstract base class for trading strategies.

    Defines the interface for implementing custom strategies with methods for:
    - Fitting models on historical data
    - Generating portfolio weights for predictions
    - Converting weights to notional orders

    Subclasses must implement:
        - _fit(training_data): Train the strategy
        - _get_weights(prediction_data, weights_): Generate portfolio weights

    Attributes:
        universe: List of asset identifiers in the investment universe
        all_assets: Complete list of assets in the data
        available_assets: Assets available for trading (after filtering)
        currencies: Currency information for assets

    """

    universe: list[str]
    all_assets: list[str] | None
    available_assets: list[str]
    _weights_template: pd.DataFrame | None
    currencies: Currencies | None

    def __init__(self) -> None:
        """Initialize strategy with empty universe."""
        self.universe = []
        self.all_assets = None
        self.available_assets = []
        self._weights_template = None
        self.currencies = None

    def fit(self, training_data: TrainingData) -> None:
        """Fit the strategy on training data.

        This method filters available assets based on the universe and data
        availability, then calls the subclass-specific _fit method.

        Args:
            training_data: Historical data for model training

        """
        prices = training_data.prices

        available_stocks = prices.loc[:, ~prices.iloc[-1].isna()].columns.tolist() if len(prices > 0) else prices.columns.tolist()

        if self.universe is not None:
            available_stocks = list(set(available_stocks) & set(self.universe))

        self.all_assets = prices.columns.tolist()
        self.available_assets = prices[available_stocks].columns.tolist()

        training_data.simple_excess_returns = (
            training_data.simple_excess_returns[available_stocks] if training_data.simple_excess_returns is not None else None
        )
        training_data.log_excess_returns = (
            training_data.log_excess_returns[available_stocks] if training_data.log_excess_returns is not None else None
        )

        self._fit(training_data=training_data)

    def get_weights(self, prediction_data: PredictionData) -> pd.DataFrame:
        """Generate portfolio weights for a prediction date.

        Args:
            prediction_data: Current period data for generating predictions

        Returns:
            DataFrame of portfolio weights indexed by date

        """
        rebal_date = prediction_data.pred_date
        init_weights = pd.DataFrame(0.0, index=[rebal_date], columns=self.all_assets)
        return self._get_weights(prediction_data=prediction_data, weights_=init_weights.copy())

    @abstractmethod
    def _fit(self, training_data: TrainingData) -> None:
        raise NotImplementedError

    @abstractmethod
    def _get_weights(self, prediction_data: PredictionData, weights_: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def __call__(self, prediction_data: PredictionData) -> pd.DataFrame:
        """Convenience method to get weights."""  # noqa: D401
        return self.get_weights(prediction_data=prediction_data)

    def get_orders(
        self,
        prediction_data: PredictionData,
        risk_notional: float,
        code_mapping: dict[str, str] | None = None,
        currencies: Currencies | None = None,
        ccy_precision: float | None = None,
    ) -> pd.DataFrame:
        if currencies is not None:
            self.currencies = currencies

        if self.currencies is None:
            msg = "Currencies must be provided."
            raise ValueError(msg)

        notionals = self._get_notionals(prediction_data, risk_notional, ccy_precision)
        if code_mapping is not None:
            transformed_index = [code_mapping.get(asset, asset) for asset in notionals.index]
        else:
            transformed_index = notionals.index

        return pd.DataFrame(
            {
                "internal_code": transformed_index,
                "currency": [self.currencies[asset] for asset in notionals.index],
                "target_notional": notionals.to_numpy(),
            },
        )

    def _get_notionals(
        self, prediction_data: PredictionData, risk_notional: float, ccy_precision: float = DEFAULT_NOTIONAL_PRECISION
    ) -> pd.Series:
        weights = self.get_weights(prediction_data=prediction_data).iloc[0, :]
        notionals = (risk_notional * weights).round(ccy_precision)

        while notionals.sum() > risk_notional:
            notionals.loc[:] -= 10 ** (-ccy_precision)

        return notionals
