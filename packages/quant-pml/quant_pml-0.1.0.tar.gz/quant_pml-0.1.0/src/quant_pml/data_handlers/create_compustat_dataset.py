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


def _load_compustat_data(config: BaseExperimentConfig) -> pd.DataFrame:
    cstat_data = pd.read_csv(config.COMPUSTAT_PATH / config.COMPUSTAT_FILENAME, low_memory=False)
    cstat_data = cstat_data.rename(columns={"datadate": "date"})
    cstat_data["date"] = pd.to_datetime(cstat_data["date"])

    cstat_data = cstat_data[cstat_data["secstat"] == "A"]
    cstat_data = cstat_data[cstat_data["prccd"] >= 1]
    cstat_data = cstat_data.dropna(subset=["cshoc"])
    cstat_data = cstat_data[(cstat_data["stko"] == 0) | (cstat_data["stko"] == 1)]
    cstat_data = cstat_data[cstat_data["tpci"] == 0]
    cstat_data["pmpid"] = cstat_data["gvkey"].astype(str) + "_" + cstat_data["iid"].astype(str)

    return cstat_data


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
    cstat_data = _load_compustat_data(config)
    cstat_data["adj_price"] = cstat_data["prccd"] / cstat_data["ajexdi"] * cstat_data["trfd"]

    cstat_data["div_percent"] = cstat_data["trfd"].fillna(1).ffill().pct_change().fillna(0)
    cstat_data["div_dollar"] = cstat_data["div_percent"] * cstat_data["adj_price"]
    cstat_data["mktcap"] = cstat_data["cshoc"] * cstat_data["prccd"]

    prices = pd.pivot_table(cstat_data, index="date", columns="pmpid", values="adj_price")
    dividends = pd.pivot_table(cstat_data, index="date", columns="pmpid", values="div_dollar")
    mkt_caps = pd.pivot_table(cstat_data, index="date", columns="pmpid", values="mktcap")

    presence_matrix = create_presence_matrix(universe_builder_fns[0], cstat_data)
    if len(universe_builder_fns) > 1:
        for universe_builder_fn in universe_builder_fns[1:]:
            presence_matrix_filter = create_presence_matrix(universe_builder_fn, cstat_data)
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

    prices.to_parquet(config.PATH_TMP / (config.PREFIX + config.RAW_DATA_FILENAME))
    presence_matrix.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.PRESENCE_MATRIX_FILENAME))
    dividends.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.DIVIDENDS_FILENAME))
    mkt_caps.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.MKT_CAPS_FILENAME))


def create_compustat_dataset(
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

    cstat_prices = read_data_df(config.PATH_TMP, config.PREFIX + config.RAW_DATA_FILENAME)

    cstat_prices = add_factors(cstat_prices, config=config)
    cstat_prices = add_rf_rate_and_market_index(cstat_prices, config=config)
    cstat_prices = add_hedging_assets(cstat_prices, config=config)

    cstat_prices.to_parquet(config.PATH_OUTPUT / (config.PREFIX + config.DF_FILENAME))


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
        lambda data: avg_volume_filter_universe_builder_fn(
            data,
            min_volume=5_000_000,
        ),
    ]

    create_compustat_dataset(
        config=settings,
        universe_builder_fns=universe_builder_fns,
    )
