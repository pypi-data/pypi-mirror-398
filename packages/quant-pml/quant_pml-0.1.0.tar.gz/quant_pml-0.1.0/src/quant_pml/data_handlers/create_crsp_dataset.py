from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from quant_pml.data_handlers.additional_data import (
    add_factors,
    add_hedging_assets,
    add_rf_rate_and_market_index,
)
from quant_pml.utils.data import create_presence_matrix, read_data_df

if TYPE_CHECKING:
    from collections.abc import Callable

    from quant_pml.config.base_experiment_config import BaseExperimentConfig

import numpy as np

CRSP_IGNORED_PLACEHOLDERS = [-66, -77, -88, -99]


def _filter_invalid(crsp_data: pd.DataFrame) -> pd.DataFrame:
    crsp_data = crsp_data[
        (crsp_data["ret"] != CRSP_IGNORED_PLACEHOLDERS[0])
        & (crsp_data["ret"] != CRSP_IGNORED_PLACEHOLDERS[1])
        & (crsp_data["ret"] != CRSP_IGNORED_PLACEHOLDERS[2])
        & (crsp_data["ret"] != CRSP_IGNORED_PLACEHOLDERS[3])
    ]
    crsp_data["ret"] = crsp_data["ret"].replace("C", np.nan).astype(float)

    return crsp_data


def _load_crsp_data(config: BaseExperimentConfig) -> pd.DataFrame:
    crsp_data = pd.read_csv(config.CRSP_PATH / config.CRSP_FILENAME, low_memory=False)
    crsp_data = crsp_data.rename(columns={col: col.lower() for col in crsp_data.columns})
    crsp_data = _filter_invalid(crsp_data)

    crsp_data["date"] = pd.to_datetime(crsp_data["date"])
    crsp_data["pmpid"] = crsp_data["permno"].astype(str)

    return crsp_data


def _create_full_data(
    config: BaseExperimentConfig,
    universe_builder_fns: list[
        Callable[
            [
                pd.DataFrame,
            ],
            pd.DataFrame,
        ]
    ],
) -> None:
    crsp_data = _load_crsp_data(config)
    starting_prices = crsp_data.groupby("pmpid")["prc"].first().abs()
    crsp_data["div_dollar"] = 0
    crsp_data["mktcap"] = crsp_data["prc"] * crsp_data["shrout"] * 1_000

    rets = pd.pivot_table(crsp_data, index="date", columns="pmpid", values="ret").add(1).cumprod()

    prices = starting_prices * rets
    dividends = pd.pivot_table(crsp_data, index="date", columns="pmpid", values="div_dollar")
    mkt_caps = pd.pivot_table(crsp_data, index="date", columns="pmpid", values="mktcap")

    presence_matrix = create_presence_matrix(universe_builder_fns[0], crsp_data)
    if len(universe_builder_fns) > 1:
        for universe_builder_fn in universe_builder_fns[1:]:
            presence_matrix_filter = create_presence_matrix(universe_builder_fn, crsp_data)
            selection = presence_matrix_filter.columns.intersection(presence_matrix.columns)
            presence_matrix_filter = (
                presence_matrix_filter.loc[presence_matrix.index.min() : presence_matrix.index.max(), selection]
                .reindex(presence_matrix.index)
                .ffill()
            )
            presence_matrix = presence_matrix[selection] * presence_matrix_filter.to_numpy()

    selection = prices.columns.intersection(presence_matrix.columns)
    prices = prices[selection]
    presence_matrix = presence_matrix[selection]
    dividends = dividends[selection]
    mkt_caps = mkt_caps[selection]

    prices = prices.loc[presence_matrix.index.min() : presence_matrix.index.max()]
    dividends = dividends.loc[presence_matrix.index.min() : presence_matrix.index.max()]
    mkt_caps = mkt_caps.loc[presence_matrix.index.min() : presence_matrix.index.max()]

    prices.to_parquet(config.PATH_TMP / (config.PREFIX + config.RAW_DATA_FILENAME))
    presence_matrix.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.PRESENCE_MATRIX_FILENAME))
    dividends.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.DIVIDENDS_FILENAME))
    mkt_caps.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.MKT_CAPS_FILENAME))


def create_crsp_dataset(
    config: BaseExperimentConfig,
    universe_builder_fns: list[
        Callable[
            [
                pd.DataFrame,
            ],
            pd.DataFrame,
        ]
    ],
) -> None:
    _create_full_data(
        config=config,
        universe_builder_fns=universe_builder_fns,
    )

    crsp_prices = read_data_df(config.PATH_TMP, config.PREFIX + config.RAW_DATA_FILENAME)

    crsp_prices = add_factors(crsp_prices, config=config)
    crsp_prices = add_rf_rate_and_market_index(crsp_prices, config=config)
    crsp_prices = add_hedging_assets(crsp_prices, config=config)

    crsp_prices.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.DF_FILENAME))


if __name__ == "__main__":
    from quant_pml.data_handlers.dataset import Dataset
    from quant_pml.data_handlers.universe_builder_functions import (
        avg_volume_filter_universe_builder_fn,
        mkt_cap_topn_universe_builder_fn,
    )

    TOP_N = 3_000
    dataset = Dataset.TOPN_US

    settings = dataset.value(topn=TOP_N)

    universe_builder_fns = [
        lambda data: mkt_cap_topn_universe_builder_fn(data, topn=TOP_N),
        lambda data: avg_volume_filter_universe_builder_fn(data, min_volume=5_000_000),
    ]

    create_crsp_dataset(
        config=settings,
        universe_builder_fns=universe_builder_fns,
    )
