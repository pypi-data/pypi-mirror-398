from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from quant_pml.config.base_experiment_config import BaseExperimentConfig
    from quant_pml.config.topn_experiment_config import TopNExperimentConfig

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from tqdm import tqdm

from quant_pml.data_handlers.dataset_builder_functions import DatasetData, build_dataset
from quant_pml.utils.data import read_data_df
from quant_pml.utils.linalg import avg_corr


def create_gw_features(
    start_date: pd.Timestamp | str | None = None,
    end_date: pd.Timestamp | str | None = None,
    path: Path | str = "../data/input/",
    feature_selection: list[str] | None = None,  # pyright: ignore[reportArgumentType]
) -> pd.DataFrame:
    if isinstance(path, str):
        path = Path(path)

    gw_features = pd.read_excel(path / "Data2023.xlsx", sheet_name="Monthly", engine="openpyxl")
    gw_features = gw_features.rename(columns={"yyyymm": "date"})
    gw_features["date"] = pd.to_datetime(gw_features["date"], format="%Y%m")
    gw_features.loc[:, "date"] = gw_features["date"] - pd.Timedelta(days=1)
    gw_features = gw_features.set_index("date")

    if feature_selection is not None:
        gw_features = gw_features[feature_selection]

    if start_date is None or end_date is None:
        return gw_features
    return gw_features.loc[start_date:end_date]


def build_dnk_gw_dataset(
    config: TopNExperimentConfig,
    *,
    verbose: bool = True,
    feature_selection: list[str] | None = None,
) -> DatasetData:
    """Build dataset for DnK experiment."""
    dataset_data = build_dataset(config)
    _, targets = create_dnk_features_targets(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=False,
    )
    dataset_data.targets = targets

    macro_features = create_gw_features(
        start_date=dataset_data.data.index.min(),
        end_date=dataset_data.data.index.max(),
        feature_selection=feature_selection,
    )
    dataset_data.macro_features = macro_features

    return dataset_data


def build_dnk_repl_dataset(
    config: TopNExperimentConfig,
    path: Path | str = "../data/input/",
    *,
    verbose: bool = True,
    feature_selection: list[str] | None = None,
) -> DatasetData:
    """Build dataset for DnK experiment."""
    dataset_data = build_dataset(config)
    _, targets = create_dnk_features_targets(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=False,
    )
    dataset_data.targets = targets

    macro_features = create_repl_features(
        start_date=dataset_data.data.index.min(),
        end_date=dataset_data.data.index.max(),
        feature_selection=feature_selection,
        path=path,
    )
    dataset_data.macro_features = macro_features

    return dataset_data


def build_curve_dnk_dataset(
    config: TopNExperimentConfig,
    *,
    verbose: bool = True,
) -> DatasetData:
    """Build dataset for DNK experiment."""
    dataset_data = build_dataset(config)
    features, targets = create_dnk_features_samples(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=True,
    )
    dataset_data.targets = targets
    dataset_data.macro_features = features

    return dataset_data


def build_curve_repl_dataset(
    config: TopNExperimentConfig,
    path: Path | str = "../data/input/",
    *,
    verbose: bool = True,
    feature_selection: list[str] | None = None,
) -> DatasetData:
    """Build dataset for DNK experiment."""
    dataset_data = build_dataset(config)
    _, targets = create_dnk_features_samples(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=False,
    )
    dataset_data.targets = targets

    macro_features = create_repl_features(
        start_date=dataset_data.data.index.min(),
        end_date=dataset_data.data.index.max(),
        feature_selection=feature_selection,
        path=path,
    )
    dataset_data.macro_features = macro_features

    return dataset_data


def create_repl_features(
    start_date: pd.Timestamp | str | None = None,
    end_date: pd.Timestamp | str | None = None,
    path: Path | str = "../data/input/",
    feature_selection: list[str] | None = None,  # pyright: ignore[reportArgumentType]
) -> pd.DataFrame:
    if isinstance(path, str):
        path = Path(path)

    repl_features = pd.read_csv(path / "repl_features.csv")
    repl_features["date"] = pd.to_datetime(repl_features["date"])
    repl_features = repl_features.set_index("date")
    repl_features = repl_features.sort_index()

    if feature_selection is not None:
        repl_features = repl_features[feature_selection]

    if start_date is None or end_date is None:
        return repl_features
    return repl_features.loc[start_date:end_date]


def _build_dnk_bound_dataset(
    config: TopNExperimentConfig,
    *,
    verbose: bool = True,
    with_features: bool = True,
) -> DatasetData:
    """Build dataset for DnK experiment."""
    dataset_data = build_dataset(config)
    features, targets = create_dnk_features_targets(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=with_features,
    )
    dataset_data.macro_features = features
    dataset_data.targets = targets.shift(-1)
    return dataset_data


def build_dnk_dataset(
    config: TopNExperimentConfig,
    *,
    verbose: bool = True,
    with_features: bool = True,
) -> DatasetData:
    """Build dataset for DnK experiment."""
    dataset_data = build_dataset(config)
    features, targets = create_dnk_features_targets(
        config=config,
        data=dataset_data.data,
        presence_matrix=dataset_data.presence_matrix,
        verbose=verbose,
        with_features=with_features,
    )
    dataset_data.macro_features = features
    dataset_data.targets = targets
    return dataset_data


def _load_data(config: BaseExperimentConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    filename = config.PREFIX + config.DF_FILENAME
    pm_filename = config.PREFIX + str(config.PRESENCE_MATRIX_FILENAME)
    data = read_data_df(config.PATH_OUTPUT, filename)

    if not data.index.is_unique:
        msg = "Returns have non-unique dates!"
        raise ValueError(msg)

    presence_matrix = read_data_df(config.PATH_OUTPUT, pm_filename)

    return data, presence_matrix


def _rolling_feature(
    df: pd.DataFrame,
    feature_fn: Callable,  # pyright: ignore[reportMissingTypeArgument]
    presense_matrix: pd.DataFrame,
    feature_name: str | None = None,
    *,
    verbose: bool = False,
) -> pd.DataFrame:
    # Initialize a list to store results
    results = []

    # Perform calculation for each rolling window
    for end in tqdm(df.index[252:]) if verbose else df.index:
        start = end - pd.DateOffset(months=1)

        curr_matrix = presense_matrix.loc[:end].iloc[-1]
        selection = curr_matrix[curr_matrix == 1].index.tolist()
        rolling_window = df[selection].loc[start:end]

        feature = feature_fn(rolling_window)

        results.append([end, feature])

    # Create a series with the results
    feature_name = "feature" if feature_name is None else feature_name
    rolling_feat = pd.DataFrame(results, columns=["date", feature_name])
    rolling_feat["date"] = pd.to_datetime(rolling_feat["date"])
    return rolling_feat.set_index("date")


def _generate_dnk_features(
    ret: pd.DataFrame,
    presence_matrix: pd.DataFrame,
    filename: Path,
    *,
    verbose: bool = False,
) -> pd.DataFrame:
    # 1. Avg Corr.
    # Calculate rolling average correlation of non-diagonal elements
    rolling_avg_corr = _rolling_feature(ret, avg_corr, presence_matrix, "avg_corr", verbose=verbose)

    # 2. Average volatility.
    avg_vol = _rolling_feature(ret, lambda s: s.std(axis=0).mean(), presence_matrix, "avg_vol", verbose=verbose)

    # 3. EW Portfolio.
    ew = _rolling_feature(
        ret,
        lambda s: np.prod(1 + np.nanmean(s, axis=1)) - 1,
        presence_matrix,
        "ew",
        verbose=verbose,
    )

    # 4. EW Portfolio Moving Average.
    ewma = []
    for end in tqdm(ew.index) if verbose else ew.index:
        start = end - pd.DateOffset(months=1)

        if end > ew.index[-1]:
            break

        sample = ew.loc[start:end]

        ma = sample.ewm(alpha=0.1).mean().iloc[-1].item()

        ewma.append([end, ma])
    ewma = pd.DataFrame(ewma, columns=["date", "ewma"])
    ewma["date"] = pd.to_datetime(ewma["date"])
    ewma = ewma.set_index("date")

    # 4. Ledoit-Wolf Shrinkage Intensity.
    def get_intensity(s: pd.DataFrame) -> float:
        s = s.copy().fillna(0)
        lw_estimator = LedoitWolf()
        lw_estimator.fit(s)
        return lw_estimator.shrinkage_

    lw = _rolling_feature(
        ret,
        lambda s: get_intensity(s),
        presence_matrix,
        "lw_shrinkage",
        verbose=verbose,
    )

    # 5. Momentum
    momentum = _rolling_feature(
        ret,
        lambda s: np.nanmean(np.where(s, s > 0, 1), axis=0).mean(),
        presence_matrix,
        "momentum_feature",
        verbose=verbose,
    )

    # 6. Trace.
    trace = _rolling_feature(
        ret,
        lambda s: np.trace(s.fillna(0).cov()),
        presence_matrix,
        "trace",
        verbose=verbose,
    )

    # 7. Universe Volatility.
    ew_vol = ew.rolling(window=252, min_periods=1).std().fillna(0)

    # Merge all features.
    features = rolling_avg_corr.merge(avg_vol, how="inner", left_index=True, right_index=True)

    features = features.merge(ewma, how="inner", left_index=True, right_index=True)
    features = features.merge(lw, how="inner", left_index=True, right_index=True)
    features = features.merge(momentum, how="inner", left_index=True, right_index=True)
    features = features.merge(trace, how="inner", left_index=True, right_index=True)
    features = features.merge(
        ew_vol.rename(columns={"ew": "universe_vol"}),
        how="inner",
        left_index=True,
        right_index=True,
    )

    if rolling_avg_corr.shape[0] != features.shape[0]:
        msg = "The dates of created features do not match!"
        raise ValueError(msg)

    features.to_csv(filename)

    return features


def create_dnk_features_samples(
    config: TopNExperimentConfig,
    data: pd.DataFrame,
    presence_matrix: pd.DataFrame,
    *,
    verbose: bool = False,
    with_features: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ret = data[presence_matrix.columns].pct_change().iloc[1:]

    targets = pd.read_csv(config.PATH_TARGETS / f"samples_{config.TOPN}.csv")
    targets = targets.rename(columns={"start_date": "date", "shrinkage": "target"})
    targets["date"] = pd.to_datetime(targets["date"])
    targets = targets.set_index("date")
    targets["end_date"] = pd.to_datetime(targets["end_date"])

    if with_features:
        features_filename = config.PREFIX + config.DNK_FEATURES_TMP_FILENAME
        if features_filename not in os.listdir(config.PATH_TMP):
            _generate_dnk_features(
                ret,
                presence_matrix,
                filename=config.PATH_TMP / features_filename,
                verbose=verbose,
            )

        dnk_features = read_data_df(config.PATH_TMP, features_filename)
        dnk_data = targets.merge(dnk_features, how="right", left_index=True, right_index=True)
    else:
        dnk_data = targets

    features = dnk_data[dnk_data.columns.difference(targets.columns)]
    targets = dnk_data[targets.columns]

    return features, targets


def create_dnk_features_targets(
    config: TopNExperimentConfig,
    data: pd.DataFrame,
    presence_matrix: pd.DataFrame,
    *,
    verbose: bool = False,
    with_features: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ret = data[presence_matrix.columns].pct_change().iloc[1:]

    targets = pd.read_csv(config.PATH_TARGETS / f"targets_{config.TOPN}.csv")
    targets = targets.rename(columns={"start_date": "date", "shrinkage": "target"})
    targets["date"] = pd.to_datetime(targets["date"])
    targets = targets.set_index("date")
    targets["end_date"] = pd.to_datetime(targets["end_date"])

    if with_features:
        features_filename = config.PREFIX + config.DNK_FEATURES_TMP_FILENAME
        if features_filename not in os.listdir(config.PATH_TMP):
            _generate_dnk_features(
                ret,
                presence_matrix,
                filename=config.PATH_TMP / features_filename,
                verbose=verbose,
            )

        dnk_features = read_data_df(config.PATH_TMP, features_filename)
        dnk_data = targets.merge(dnk_features, how="right", left_index=True, right_index=True)
    else:
        dnk_data = targets

    features = dnk_data[dnk_data.columns.difference(targets.columns)]
    targets = dnk_data[targets.columns]

    return features, targets
