from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import numpy as np


class Currencies:
    def __init__(self, currencies_dict: dict[str, str] | None = None) -> None:
        if currencies_dict is None:
            currencies_dict = {}
        self._ccys = pd.Series(currencies_dict)

    def from_single_currency(self, assets: list[str], ccy: str) -> Currencies:
        self._ccys = pd.Series(ccy, index=assets)
        return self

    def from_series(self, currencies: pd.Series) -> Currencies:
        self._ccys = currencies
        return self

    def __getitem__(self, asset: str) -> np.ndarray:
        return self._ccys.loc[asset]

    def currencies(self) -> pd.Series:
        return self._ccys.copy()
