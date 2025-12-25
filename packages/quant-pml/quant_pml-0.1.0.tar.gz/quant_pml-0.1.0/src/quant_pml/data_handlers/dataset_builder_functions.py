from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from os import listdir

import pandas as pd

from quant_pml.config.base_experiment_config import BaseExperimentConfig
from quant_pml.config.jkp_experiment_config import JKPExperimentConfig
from quant_pml.config.spx_experiment_config import SPXExperimentConfig
from quant_pml.config.topn_experiment_config import TopNExperimentConfig
from quant_pml.data_handlers.create_compustat_dataset import create_compustat_dataset
from quant_pml.data_handlers.create_crsp_dataset import create_crsp_dataset
from quant_pml.data_handlers.universe_builder_functions import (
    avg_volume_filter_universe_builder_fn,
    mkt_cap_quantile_universe_builder_fn,
    mkt_cap_topn_universe_builder_fn,
)
from quant_pml.utils.data import read_data_df


@dataclass
class DatasetData:
    data: pd.DataFrame
    presence_matrix: pd.DataFrame
    mkt_caps: pd.DataFrame | None = None
    dividends: pd.DataFrame | None = None

    targets: pd.DataFrame | None = None

    # Macro features are (T x P_macro), i.e., shared across all assets
    macro_features: pd.DataFrame | None = None
    # Asset-specific features are (T x N x P_asset), i.e., panel data with MultiIndex (asset, date)
    asset_features: pd.DataFrame | None = None


def build_dataset(
    config: BaseExperimentConfig,
) -> DatasetData:
    # TODO(@V): Refactor to accommodate `build_crsp_dataset`
    df_filename = config.PREFIX + config.DF_FILENAME
    pm_filename = config.PREFIX + config.PRESENCE_MATRIX_FILENAME
    mkt_caps_filename = config.PREFIX + config.MKT_CAPS_FILENAME
    dividends_filename = config.PREFIX + config.DIVIDENDS_FILENAME

    data_df = read_data_df(config.PATH_OUTPUT, df_filename)
    presence_matrix = read_data_df(config.PATH_OUTPUT, pm_filename)

    if mkt_caps_filename in listdir(config.PATH_OUTPUT):
        mkt_caps = read_data_df(config.PATH_OUTPUT, mkt_caps_filename)
    else:
        mkt_caps = None

    if dividends_filename in listdir(config.PATH_OUTPUT):
        dividends = read_data_df(config.PATH_OUTPUT, dividends_filename)
    else:
        dividends = None

    return DatasetData(
        data=data_df,
        presence_matrix=presence_matrix,
        mkt_caps=mkt_caps,
        dividends=dividends,
    )


def build_crsp_dataset(
    config: BaseExperimentConfig,
    universe_builder_fn: Callable[
        [
            pd.DataFrame,
        ],
        pd.DataFrame,
    ],
    features_targets_fn: Callable[[BaseExperimentConfig, bool], None] | None = None,
    verbose: bool = True,
) -> DatasetData:
    if not config.PATH_OUTPUT.exists():
        raise FileNotFoundError(f"Output directory {config.PATH_OUTPUT} does not exist.")

    df_filename = config.PREFIX + config.DF_FILENAME
    pm_filename = config.PREFIX + config.PRESENCE_MATRIX_FILENAME
    available_files = listdir(config.PATH_OUTPUT)

    if df_filename not in available_files or pm_filename not in available_files:
        if verbose:
            print("Creating returns dataset...")
        create_crsp_dataset(config=config, universe_builder_fn=universe_builder_fn)

        if features_targets_fn is not None:
            if verbose:
                print("Calculating features and targets...")
            features_targets_fn(config, verbose)

    data_df = read_data_df(config.PATH_OUTPUT, df_filename)
    presence_matrix = read_data_df(config.PATH_OUTPUT, pm_filename)

    return DatasetData(data=data_df, presence_matrix=presence_matrix)


def build_compustat_dataset(
    config: BaseExperimentConfig,
    universe_builder_fns: list[
        Callable[
            [
                pd.DataFrame,
            ],
            pd.DataFrame,
        ]
    ],
    features_targets_fn: Callable[[BaseExperimentConfig, bool], None] | None = None,
    verbose: bool = True,
) -> DatasetData:
    if not config.PATH_OUTPUT.exists():
        raise FileNotFoundError(f"Output directory {config.PATH_OUTPUT} does not exist.")

    df_filename = config.PREFIX + config.DF_FILENAME
    pm_filename = config.PREFIX + config.PRESENCE_MATRIX_FILENAME
    available_files = listdir(config.PATH_OUTPUT)

    if df_filename not in available_files or pm_filename not in available_files:
        if verbose:
            print("Creating returns dataset...")
        create_compustat_dataset(config=config, universe_builder_fns=universe_builder_fns)

        if features_targets_fn is not None:
            if verbose:
                print("Calculating features and targets...")
            features_targets_fn(config, verbose)

    data_df = read_data_df(config.PATH_OUTPUT, df_filename)
    presence_matrix = read_data_df(config.PATH_OUTPUT, pm_filename)

    return DatasetData(data=data_df, presence_matrix=presence_matrix)


def build_topn_dataset(config: TopNExperimentConfig, verbose: bool = True) -> DatasetData:
    return build_compustat_dataset(
        config=config,
        universe_builder_fns=[lambda data: mkt_cap_topn_universe_builder_fn(data, topn=config.TOPN)],
        features_targets_fn=None,
        verbose=verbose,
    )


def build_russell3000_dataset(config: TopNExperimentConfig, verbose: bool = True) -> DatasetData:
    return build_compustat_dataset(
        config=config,
        universe_builder_fns=[
            lambda data: mkt_cap_topn_universe_builder_fn(data, topn=config.TOPN),
            lambda data: avg_volume_filter_universe_builder_fn(
                data,
                min_volume=5_000_000,
            ),
        ],
        features_targets_fn=None,
        verbose=verbose,
    )


def build_jkp_dataset(config: JKPExperimentConfig, verbose: bool = True) -> DatasetData:
    return build_crsp_dataset(
        config=config,
        universe_builder_fn=lambda data: mkt_cap_quantile_universe_builder_fn(
            data,
            quantile=config.MCAP_SELECTION_QUANTILE,
        ),
        features_targets_fn=None,
        verbose=verbose,
    )


def build_spx_dataset(
    config: SPXExperimentConfig,
    spx_presence_matrix: pd.DataFrame,
    verbose: bool = True,
) -> DatasetData:
    return build_crsp_dataset(
        config=config,
        universe_builder_fn=lambda data: spx_presence_matrix,
        features_targets_fn=None,
        verbose=verbose,
    )


if __name__ == "__main__":
    from quant_pml.data_handlers.dataset import Dataset

    TOP_N = 500
    dataset = Dataset.TOPN_US

    settings = dataset.value(topn=TOP_N)
    dataset = build_russell3000_dataset(settings, verbose=True)
