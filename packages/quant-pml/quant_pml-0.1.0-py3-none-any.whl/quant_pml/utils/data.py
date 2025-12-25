from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable


def read_data_df(
    path: str | Path,
    filename: str,
    date_column: str = "date",
    *,
    rename_column: bool = False,
) -> pd.DataFrame:
    if filename.endswith(".parquet"):
        return read_parquet(path, filename)
    if filename.endswith(".csv"):
        return read_csv(path, filename, date_column, rename_column=rename_column)
    msg = f"File extension {filename.split('.')[-1]} not supported."
    raise ValueError(msg)


def read_csv(
    path: str | Path,
    filename: str,
    date_column: str = "date",
    *,
    rename_column: bool = False,
) -> pd.DataFrame:
    path = Path(path) if isinstance(path, str) else path
    data = pd.read_csv(path / filename)
    data[date_column] = pd.to_datetime(data[date_column])
    if rename_column:
        data = data.rename(columns={date_column: "date"})
        date_column = "date"
    data.columns = data.columns.astype(str)
    return data.set_index(date_column).sort_index()


def read_parquet(
    path: str | Path,
    filename: str,
) -> pd.DataFrame:
    path = Path(path) if isinstance(path, str) else path
    data = pd.read_parquet(path / filename)
    data.columns = data.columns.astype(str)
    return data.sort_index()


def create_presence_matrix(
    universe_builder_fn: Callable[
        [
            pd.DataFrame,
        ],
        pd.DataFrame,
    ],
    crsp_data: pd.DataFrame,
) -> pd.DataFrame:
    presence_matrix = universe_builder_fn(crsp_data)

    presence_matrix = presence_matrix.reset_index()
    presence_matrix["date"] = pd.to_datetime(presence_matrix["date"])
    presence_matrix = presence_matrix.set_index("date").iloc[1:]

    return presence_matrix.resample("D").ffill()


def build_panel_dataset(data: pd.DataFrame) -> pd.DataFrame:
    data_no_duplicates = data.loc[:, ~data.columns.duplicated()]
    data_unstacked = data_no_duplicates.stack()
    data_unstacked.index = data_unstacked.index.set_names(["date", "pmpid"])
    return data_unstacked.sort_index().to_frame("variable")
