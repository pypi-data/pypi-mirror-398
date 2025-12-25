from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from pathlib import Path

import numpy as np
import pandas as pd

from quant_pml.utils.data import read_data_df


def _mkt_cap_universe_builder_fn(
    full_data: pd.DataFrame,
    mkt_cap_filter_fn: Callable[
        [
            pd.Series,
        ],
        bool,
    ],
    resampling_freq: str = "ME",
) -> pd.DataFrame:
    mktcap_init = full_data.reset_index().pivot_table(index="date", columns="pmpid", values="mktcap")
    mktcap = mktcap_init.resample(resampling_freq).last()
    if resampling_freq != "D":
        mktcap = pd.concat([mktcap_init.iloc[:1], mktcap], axis=0)

    presence_matrix = mktcap.apply(lambda x: mkt_cap_filter_fn(x), axis=1).astype(float)
    presence_matrix[presence_matrix == 0] = np.nan

    return presence_matrix.dropna(axis=1, how="all")


def mkt_cap_topn_universe_builder_fn(full_data: pd.DataFrame, topn: int) -> pd.DataFrame:
    return _mkt_cap_universe_builder_fn(full_data, lambda x: x >= x.nlargest(topn).min())


def mkt_cap_quantile_universe_builder_fn(full_data: pd.DataFrame, quantile: float) -> pd.DataFrame:
    return _mkt_cap_universe_builder_fn(full_data, lambda x: x >= x.quantile(quantile))


def avg_volume_filter_universe_builder_fn(
    full_data: pd.DataFrame,
    min_volume: float,
    window_size: int = 21 * 3,
    resampling_freq: str = "D",
) -> pd.DataFrame:
    full_data["volume"] = full_data["vol"] * full_data["prc"]

    full_data["avg_volume"] = (
        full_data["volume"].rolling(window=window_size, min_periods=1, closed="left").apply(lambda x: np.nanmean(x))
    )

    avg_vol_init = full_data.reset_index().pivot_table(index="date", columns="pmpid", values="avg_volume")
    avg_vol = avg_vol_init.resample(resampling_freq).last()
    if resampling_freq != "D":
        avg_vol = pd.concat([avg_vol_init.iloc[:1], avg_vol], axis=0)

    presence_matrix = avg_vol.apply(lambda x: x >= min_volume, axis=1).astype(float)
    presence_matrix[presence_matrix == 0] = np.nan

    return presence_matrix.dropna(axis=1, how="all")


def load_precomputed_builder_fn(
    full_data: pd.DataFrame,
    filename: str,
    path: Path = Path("../data/precomputed_pms/"),
) -> pd.DataFrame:
    return read_data_df(path, filename)
