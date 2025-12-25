from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime as dt

import numpy as np
import pandas as pd

PRE_DEFINED_FACTOR_ANNUAL = (5, 12, 252)


def create_dates_df(
    start: str | dt.datetime,
    end: str | dt.datetime,
    freq: str = "D",
    name: str = "date",
) -> pd.DataFrame:
    return pd.date_range(start=start, end=end, freq=freq).to_frame(name=name, index=False)


def get_factor_annual(dates: pd.DatetimeIndex, from_predefined: bool = True) -> int:
    day_diff = dates.diff().days[1:]
    factor_annual_rounded = round(np.nanmean(365 // day_diff))
    if not from_predefined:
        return factor_annual_rounded
    return min(
        list(PRE_DEFINED_FACTOR_ANNUAL),
        key=lambda x: abs(x - factor_annual_rounded),
    )
