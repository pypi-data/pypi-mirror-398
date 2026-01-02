"""
Absfuyu: Data Analysis
----------------------
DF Function

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "equalize_df",
    "compare_2_list",
    "rename_with_dict",
    "merge_data_files",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Mapping
from itertools import chain
from pathlib import Path
from typing import Literal, cast

import numpy as np
import pandas as pd

from absfuyu.core.docstring import versionadded
from absfuyu.core.dummy_func import tqdm


# Function
# ---------------------------------------------------------------------------
def equalize_df(data: dict[str, list], fillna=np.nan) -> dict[str, list]:
    """
    Make all list in dict have equal length to make pd.DataFrame

    :param data: `dict` data that ready for `pd.DataFrame`
    :param fillna: Fill N/A value (Default: `np.nan`)
    """
    max_len = max(map(len, data.values()))
    for _, v in data.items():
        if len(v) < max_len:
            missings = max_len - len(v)
            for _ in range(missings):
                v.append(fillna)
    return data


def compare_2_list(*arr) -> pd.DataFrame:
    """
    Compare 2 lists then create DataFrame
    to see which items are missing

    Parameters
    ----------
    arr : list
        List

    Returns
    -------
    DataFrame
        Compare result
    """
    # Setup
    col_name = "list"
    arr = [sorted(x) for x in arr]  # type: ignore # map(sorted, arr)

    # Total array
    tarr = sorted(list(set(chain.from_iterable(arr))))
    # max_len = len(tarr)

    # Temp dataset
    temp_dict = {"base": tarr}
    for idx, x in enumerate(arr):
        name = f"{col_name}{idx}"

        # convert list
        temp = [item if item in x else np.nan for item in tarr]

        temp_dict.setdefault(name, temp)

    df = pd.DataFrame(temp_dict)
    df["Compare"] = np.where(
        df[f"{col_name}0"].apply(lambda x: str(x).lower()) == df[f"{col_name}1"].apply(lambda x: str(x).lower()),
        df[f"{col_name}0"],  # Value when True
        np.nan,  # Value when False
    )
    return df


def rename_with_dict(df: pd.DataFrame, col: str, rename_dict: dict) -> pd.DataFrame:
    """
    Version: 2.0.0

    :param df: DataFrame
    :param col: Column name
    :param rename_dict: Rename dictionary
    """

    name = f"{col}_filtered"
    df[name] = df[col]
    rename_val = list(rename_dict.keys())
    df[name] = df[name].apply(lambda x: "Other" if x in rename_val else x)
    return df


@versionadded("6.0.0")
def merge_data_files(
    work_dir: Path | str,
    file_type: Literal[".csv", ".xls", ".xlsx"] = ".xlsx",
    output_file: Path | str | None = None,
    *,
    tqdm_enabled: bool = True,
) -> None:
    """
    Merge all data-sheet-like (.csv, .xls, .xlsx) in a folder/directory.
    Also remove duplicate rows

    Parameters
    ----------
    work_dir : Path | str
        Files in which folder/directory

    file_type : Literal[".csv", ".xls", ".xlsx"], optional
        File format, by default ``".xlsx"``

    output_file : Path | str | None, optional
        | Output file location, by default ``None``
        | File will be export in ``.xlsx`` format
        | Default export name is ``data_merged.xlsx``

    tqdm_enabled : bool, optional
        Use ``tqdm`` package to show progress bar (if available), by default ``True``
    """

    default_name = "data_merged.xlsx"
    paths = [x for x in Path(work_dir).glob(f"**/*{file_type}") if x.name != default_name]
    output_path = Path(output_file) if output_file is not None else Path(work_dir).joinpath(default_name)

    dfs = []
    if tqdm_enabled:
        for x in tqdm(paths, desc="Merging files", unit_scale=True):
            dfs.append(pd.read_excel(x))
    else:
        for x in paths:
            dfs.append(pd.read_excel(x))

    df = cast(pd.DataFrame, pd.concat(dfs, axis=0, join="inner")).drop_duplicates().reset_index()
    df.drop(columns=["index"], inplace=True)

    df.to_excel(output_path, index=False)


@versionadded("6.0.0")
def export_dfs_to_excel(
    path: str,
    dfs: Mapping[str, pd.DataFrame],
    *,
    index: bool = False,
) -> None:
    """
    Export multiple DataFrames into one Excel file.

    Parameters
    ----------
    path : str
        Output Excel file path.

    dfs : Mapping[str, DataFrame]
        Sheet name -> DataFrame mapping.

    index : bool, default False
        Whether to include DataFrame index, by default ``False``
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in dfs.items():
            name = name[:31]  # Excel sheet name length limit
            df.to_excel(writer, sheet_name=name, index=index)
