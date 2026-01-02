"""
Absfuyu: Data Analysis
----------------------
Data Analyst DataFrame

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "DADF",
    "DataAnalystDataFrameColumnMethodMixin",
    "DataAnalystDataFrameRowMethodMixin",
    "DataAnalystDataFrameInfoMixin",
    "DataAnalystDataFrameNAMixin",
    "DataAnalystDataFrameOtherMixin",
    "DataAnalystDataFrameDateMixin",
    "DataAnalystDataFrameExportMixin",
    "DataAnalystDataFrameCityMixin",
]


# Library
# ---------------------------------------------------------------------------
import random
import string
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, Literal, Self, cast, override

import numpy as np
import pandas as pd
from xlsxwriter import Workbook
from xlsxwriter.worksheet import Worksheet

from absfuyu.core.baseclass import GetClassMembersMixin
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.core.dummy_func import unidecode
from absfuyu.extra.da.dadf_base import CityData
from absfuyu.extra.da.dadf_base import DataAnalystDataFrameBase as DFBase
from absfuyu.extra.da.dadf_base import SplittedDF
from absfuyu.typings import R as _R
from absfuyu.typings import T as _T
from absfuyu.util import set_min_max


# Column method
# ---------------------------------------------------------------------------
class DataAnalystDataFrameColumnMethodMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Column method

    - Rearrange rightmost column
    - Drop columns
    - Drop rightmost column
    - Add blank column
    - Split str column
    - Get column name unidecoded
    - Get column unidecoded
    """

    def rearrange_rightmost_column(
        self, insert_to_col: str, num_of_cols: int = 1
    ) -> Self:
        """
        Move right-most columns to selected position

        Parameters
        ----------
        insert_to_col : str
            Name of the column that the right-most column will be moved next to

        num_of_cols : int
            Number of columns moved, by default ``1``

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0 -1.583590         756          700            NaN  eqklyckc 2023-05-20
        1  0.203968         167          100            NaN  wzrsxinb 2011-02-27
        >>> df.rearrange_rightmost_column("number")
             number       date  number_big number_range  missing_value      text
        0 -1.583590 2023-05-20         756          700            NaN  eqklyckc
        1  0.203968 2011-02-27         167          100            NaN  wzrsxinb
        """
        cols: list[str] = self.columns.to_list()  # List of columns
        num_of_cols = int(set_min_max(num_of_cols, min_value=1, max_value=len(cols)))
        col_index: int = cols.index(insert_to_col)
        new_cols: list[str] = (
            cols[: col_index + 1]
            + cols[-num_of_cols:]
            + cols[col_index + 1 : len(cols) - num_of_cols]
        )
        self = self.__class__(self[new_cols])
        return self

    def drop_columns(self, columns: Sequence[str]) -> Self:
        """
        Drop columns in DataFrame

        Parameters
        ----------
        columns : Iterable[str]
            List of columns need to drop

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0 -0.283019         666          600            NaN  ztoeeblx 2022-11-13
        1  1.194725         939          900            NaN  fxardqvh 2005-08-04
        >>> df.drop_columns(["date", "text"])
             number  number_big number_range  missing_value
        0 -0.283019         666          600            NaN
        1  1.194725         939          900            NaN
        """
        for column in columns:
            try:
                self.drop(columns=[column], inplace=True)
            except KeyError:
                # logger.debug(f"{column} column does not exist")
                pass
        return self

    def drop_rightmost(self, num_of_cols: int = 1) -> Self:
        """
        Drop ``num_of_cols`` right-most columns

        Parameters
        ----------
        num_of_cols : int
            Number of columns to drop

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0  0.851953         572          500              5  ncpbnzef 2020-08-15
        1  0.381643         595          500             53  iojogbgj 2011-12-04
        >>> df.drop_rightmost(5)
             number
        0  0.851953
        1  0.381643
        """
        # Restrain
        # if num_of_cols < 1:
        #     num_of_cols = 1
        # if num_of_cols > self.shape[1]:
        #     num_of_cols = self.shape[1]
        num_of_cols = int(
            set_min_max(num_of_cols, min_value=1, max_value=self.shape[1])
        )

        # Logic
        for _ in range(num_of_cols):
            self.drop(self.columns[len(self.columns) - 1], axis=1, inplace=True)
        return self

    @deprecated("5.1.0", reason="Use pd.DataFrame.assign(...) method instead")
    def add_blank_column(self, column_name: str, fill: Any = np.nan, /) -> Self:
        """
        [DEPRECATED] Add a blank column.

        E.g: Use `pd.DataFrame.assign(new_col=lambda x: x['old_col'])` instead

        Parameters
        ----------
        column_name : str
            Name of the column to add

        fill : Any
            Fill the column with data

        Returns
        -------
        Self
            Modified DataFrame
        """
        self[column_name] = [fill] * self.shape[0]
        return self

    @versionadded("5.2.0")  # No test cases
    def split_str_column(
        self,
        col: str,
        pattern: str = " ",
        *,
        n: int | None = None,
        regex: bool = False,
    ) -> Self:
        """
        Split column with dtype[str] into other columns.

        Parameters
        ----------
        col : str
            Column name

        pattern : str, optional
            Split pattern, by default ``" "``

        n : int | None, optional
            Split by how many times, by default ``None``

        regex : bool, optional
            Regex mode, by default ``False``

        Returns
        -------
        Self
            DataFrame


        Example:
        --------
        >>> df = DADF(DADF.sample_df(5)[["text"]])
        >>> df.split_str_column("text", "s"))
               text    text_0 text_1
        0  uwfzbsgj     uwfzb     gj
        1  lxlskayx       lxl   kayx
        2  fzgpzjtp  fzgpzjtp   None
        3  lxnytktz  lxnytktz   None
        4  onryaxtt  onryaxtt   None
        """
        if n is None:
            pass
        splited_data: pd.DataFrame = self[col].str.split(pat=pattern, n=n, expand=True, regex=regex)  # type: ignore
        num_of_splitted_cols = splited_data.shape[1]
        new_col_names = [f"{col}_{x}" for x in range(num_of_splitted_cols)]
        self[new_col_names] = splited_data
        return self

    @versionadded("5.12.0")  # No test cases
    def get_column_name_unidecoded(self, col_name: str, /, *, mode: Literal["start", "end", "in"] = "start") -> str:
        """
        Get column name from lowercase unidecode'd version name

        Parameters
        ----------
        col_name : str
            Column name to find

        mode : Literal["start", "end", "in"], optional
            Which mode to find, by default "start"
            - "start": str.startswith()
            - "end": str.endswith()
            - "in": if x in y

        Returns
        -------
        str
            Column name

        Raises
        ------
        ValueError
            Column not found
        """
        for x in self.columns.to_list():
            col_name_mod = cast(str, unidecode(x.strip().lower()))
            if mode == "start":
                if col_name_mod.startswith(col_name):
                    return x
            elif mode == "end":
                if col_name_mod.endswith(col_name):
                    return x
            elif mode == "in":
                if col_name_mod in col_name:
                    return x

        raise ValueError(f"Column not found: {col_name}")

    @versionadded("5.12.0")  # No test cases
    def get_column_unidecoded(self, col_name: str, /, *, mode: Literal["start", "end", "in"] = "start") -> pd.Series:
        """
        Get column from lowercase unidecode'd version column name

        Parameters
        ----------
        col_name : str
            Column name to find

        mode : Literal["start", "end", "in"], optional
            Which mode to find, by default "start"
            - "start": str.startswith()
            - "end": str.endswith()
            - "in": if x in y

        Returns
        -------
        Series
            Column data
        """
        return self[self.get_column_name_unidecoded(col_name, mode=mode)]


# Row method
# ---------------------------------------------------------------------------
class DataAnalystDataFrameRowMethodMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Row method

    - Get different rows
    - Add blank row
    """

    @versionadded("4.0.0")
    def get_different_rows(self, other: Self | pd.DataFrame) -> Self:
        """
        Subtract DataFrame to find the different rows

        Parameters
        ----------
        other : Self | pd.DataFrame
            DataFrame to subtract

        Returns
        -------
        Self
            Different row DataFrame


        Example:
        --------
        >>> df1 = DADF({"A": [1, 2, 3, 4], "B": [5, 6, 7, 8]})
        >>> df2 = DADF({"A": [1, 2, 3, 4], "B": [7, 6, 6, 8]})
        >>> df1.get_different_rows(df2)
           A  B
        0  1  7
        2  3  6
        """
        df = self.copy()
        out = (
            df.merge(other, indicator=True, how="right")
            .query("_merge=='right_only'")
            .drop("_merge", axis=1)
        )
        return self.__class__(out)

    @versionchanged("6.0.0", reason="Improved logic")
    @versionadded("5.7.0")
    def add_blank_row(self, fill: Any = np.nan, /) -> Self:
        """
        Add a new row to the end of a DataFrame.

        Parameters
        ----------
        fill : Any, default np.nan
            Value to fill in the new row (e.g., np.nan, None, "", 0).

        Returns
        -------
        Self
            DataFrame with the new row appended.
        """
        # Create a dict with all columns filled with fill
        new_row = {col: fill for col in self.columns}
        safe_types = self._safe_dtypes(df.dtypes)
        blank_row_df = pd.DataFrame([new_row], columns=df.columns).astype(safe_types)

        # self.loc[len(self)] = new_row  # type: ignore
        # return self
        out = cast(pd.DataFrame, pd.concat([self, blank_row_df], ignore_index=True))
        return self.__class__(out)

    @versionadded("6.0.0")  # Support
    def _safe_dtypes(self, dtypes: pd.Series) -> dict[str, Any]:
        """
        Convert DataFrame dtypes into a safe mapping for operations involving
        missing values (NA), especially during row insertion or concatenation.

        This function is primarily used to prevent pandas errors when inserting
        rows containing missing values (``NaN``) into columns with non-nullable
        integer dtypes (e.g. ``int64``). Since standard NumPy integer dtypes do not
        support missing values, they are converted to pandas' nullable integer
        dtype (``Int64``).

        All non-integer dtypes are preserved without modification.

        - Pandas nullable integer dtypes (``Int64``, ``Int32``, etc.) allow missing
        values via ``pd.NA``, unlike NumPy integer dtypes.
        - This function is commonly used before calling ``DataFrame.astype`` to
        avoid ``IntCastingNaNError`` when NA values are present.
        - The function does **not** modify floating-point, boolean, datetime,
        categorical, or object dtypes.

        Parameters
        ----------
        dtypes : Series
            A Series mapping column names to their pandas dtypes, typically obtained
            from ``DataFrame.dtypes``.

        Returns
        -------
        dict
            A dictionary mapping column names to safe dtypes. Integer dtypes are
            converted to pandas nullable integer dtype (``"Int64"``), while all
            other dtypes remain unchanged.


        Example:
        --------
        Basic usage with a DataFrame::

            >>> df.dtypes
            id        int64
            name     object
            amount  float64
            dtype: object

            >>> _safe_dtypes(df.dtypes)
            {
                "id": "Int64",
                "name": dtype("O"),
                "amount": dtype("float64"),
            }

        Typical integration with ``astype``::

            >>> safe_types = _safe_dtypes(df.dtypes)
            >>> new_df = df.astype(safe_types)

        This is especially useful when inserting rows with missing values::

            >>> sep_row = {"id": pd.NA, "name": "---", "amount": pd.NA}
            >>> sep_df = pd.DataFrame([sep_row]).astype(_safe_dtypes(df.dtypes))
        """
        out = {}
        for col, dt in dtypes.items():
            if pd.api.types.is_integer_dtype(dt):
                out[col] = "Int64"  # nullable integer
            else:
                out[col] = dt
        return out

    @versionadded("6.0.0")  # Better version of add_blank_row()
    def add_separator_row(
        self,
        group_cols: str | Iterable[str],
        *,
        separator: Mapping[str, object] | None = None,
        drop_last: bool = True,
    ) -> Self:
        """
        Insert a separator row after each group in a DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame (must be pre-sorted by ``group_cols``).

        group_cols : str | Iterable[str]
            Column(s) used to define grouping boundaries.

        separator : Mapping[str, object] | None, optional
            Custom separator row values (e.g. {"col": "---"}).
            Columns not provided will be filled with NaN.
            If None, a fully blank row is inserted.

        drop_last : bool, optional
            If True, do not insert a separator after the last group.

        Returns
        -------
        Self
            DataFrame with separator rows inserted.
        """
        df = self.copy()

        if isinstance(group_cols, str):
            group_cols = [group_cols]

        # Validate columns
        missing = set(group_cols) - set(df.columns)
        if missing:
            raise KeyError(f"Missing columns: {missing}")

        # Build separator row template
        if separator is None:
            sep_row = {c: np.nan for c in df.columns}
        else:
            sep_row = {c: separator.get(c, np.nan) for c in df.columns}

        rows = []

        safe_types = self._safe_dtypes(df.dtypes)

        # Group while preserving order
        for _, g in df.groupby(group_cols, sort=False):
            rows.append(g)

            sep_df = pd.DataFrame([sep_row], columns=df.columns).astype(safe_types)
            rows.append(sep_df)

        out = cast(pd.DataFrame, pd.concat(rows, ignore_index=True))

        if drop_last:
            out = out.iloc[:-1].reset_index(drop=True)

        return self.__class__(out)


# Info
# ---------------------------------------------------------------------------
class DataAnalystDataFrameInfoMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Info

    - Quick info
    - Quick describe
    - Show distribution
    - Threshold filter
    """

    # Quick info
    @versionadded("3.2.0")
    def qinfo(self) -> str:
        """
        Show quick infomation about DataFrame

        Example:
        --------
        >>> DADF.sample_df().qinfo()
        Dataset Information:
        - Number of Rows: 100
        - Number of Columns: 6
        - Total observation: 600
        - Missing value: 13 (2.17%)

        Column names:
        ['number', 'number_big', 'number_range', 'missing_value', 'text', 'date']
        """
        missing_values = self.isnull().sum().sum()
        total_observation = self.shape[0] * self.shape[1]
        mv_rate = missing_values / total_observation * 100
        info = (
            f"Dataset Information:\n"
            f"- Number of Rows: {self.shape[0]:,}\n"
            f"- Number of Columns: {self.shape[1]:,}\n"
            f"- Total observation: {total_observation:,}\n"
            f"- Missing value: {missing_values:,} ({mv_rate:.2f}%)\n\n"
            f"Column names:\n{self.columns.to_list()}"
        )
        return info

    @override
    def describe(self, percentiles=None, include=None, exclude=None) -> Self:  # type: ignore
        """pd.DataFrame.describe() override"""
        return self.__class__(super().describe(percentiles, include, exclude))  # type: ignore [no-any-return]

    # Quick describe
    @versionadded("3.2.0")
    def qdescribe(self) -> Self:
        """
        Quick ``describe()`` that exclude ``object`` and ``datetime`` dtype

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> DADF.sample_df().qdescribe()
                   number  number_big  missing_value
        count  100.000000  100.000000      48.000000
        mean    -0.052935  586.750000      22.916667
        std      0.954170  237.248596      11.987286
        min     -2.392952  105.000000       3.000000
        25%     -0.738311  407.500000      13.000000
        50%     -0.068014  607.000000      23.500000
        75%      0.614025  790.250000      36.000000
        max      2.512533  988.000000      42.000000
        """
        return self.__class__(  # type: ignore [no-any-return]
            self[self.select_dtypes(exclude=["object", "datetime"]).columns].describe()
        )

    @versionadded("3.2.0")
    def show_distribution(
        self,
        column_name: str,
        dropna: bool = True,
        *,
        show_percentage: bool = True,
        percentage_round_up: int = 2,
    ) -> Self:
        """
        Show distribution of a column

        Parameters
        ----------
        column_name : str
            Column to show distribution

        dropna : bool
            Count N/A when ``False``
            (Default: ``True``)

        show_percentage : bool
            Show proportion in range 0% - 100% instead of [0, 1]
            (Default: ``True``)

        percentage_round_up : int
            Round up to which decimals
            (Default: ``2``)

        Returns
        -------
        Self
            Distribution DataFrame


        Example:
        --------
        >>> DADF.sample_df().show_distribution("number_range")
          number_range  count  percentage
        0          900     16        16.0
        1          700     15        15.0
        2          300     12        12.0
        3          200     12        12.0
        4          400     11        11.0
        5          600     11        11.0
        6          800     10        10.0
        7          100      9         9.0
        8          500      4         4.0
        """
        out = self[column_name].value_counts(dropna=dropna).to_frame().reset_index()
        if show_percentage:
            out["percentage"] = (out["count"] / self.shape[0] * 100).round(
                percentage_round_up
            )
        else:
            out["percentage"] = (out["count"] / self.shape[0]).round(
                percentage_round_up
            )
        return self.__class__(out)

    @deprecated("5.1.0", reason="Rework THIS")
    def threshold_filter(
        self,
        destination_column: str,
        threshold: int | float = 10,
        *,
        top: int | None = None,
        replace_with: Any = "Other",
    ) -> Self:
        """
        Filter out percentage of data that smaller than the ``threshold``,
        replace all of the smaller data to ``replace_with``.
        As a result, pie chart is less messy.

        Parameters
        ----------
        destination_column : str
            Column to be filtered

        threshold : int | float
            Which percentage to cut-off
            (Default: 10%)

        top : int
            Only show top ``x`` categories in pie chart
            (replace threshold mode)
            (Default: ``None``)

        replace_with : Any
            Replace all of the smaller data with specified value

        Returns
        -------
        Self
            Modified DataFrame
        """
        # Clean
        try:
            self[destination_column] = self[
                destination_column
            ].str.strip()  # Remove trailing space
        except Exception:
            pass

        # Logic
        col_df = self.show_distribution(destination_column)

        # Rename
        if top is not None:
            list_of_keep: list = (
                col_df[destination_column]
                .head(set_min_max(top - 1, min_value=1, max_value=col_df.shape[0]))  # type: ignore
                .to_list()
            )
            # logger.debug(list_of_keep)
        else:
            list_of_keep = col_df[col_df["percentage"] >= threshold][
                destination_column
            ].to_list()  # values that will not be renamed
        self[f"{destination_column}_filtered"] = self[destination_column].apply(
            lambda x: replace_with if x not in list_of_keep else x
        )

        # Return
        return self


# Missing value
# ---------------------------------------------------------------------------
class DataAnalystDataFrameNAMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Missing value

    - Fill missing values
    - Get missing values
    - Split N/A
    - Apply not null
    - Apply not null row
    """

    def fill_missing_values(
        self, column_name: str, fill: Any = np.nan, *, fill_when_not_exist: Any = np.nan
    ) -> Self:
        """
        Fill missing values in specified column

        Parameters
        ----------
        column_name : str
            Column name

        fill : Any
            Fill the missing values with, by default ``np.nan``

        fill_when_not_exist : Any
            When ``column_name`` does not exist,
            create a new column and fill with
            ``fill_when_not_exist``, by default ``np.nan``

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0  0.174303         926          900            NaN  tenkiakh 2006-09-08
        1  0.305137         140          100            NaN  jzuddamf 2012-04-04
        >>> df.fill_missing_values("missing_value", 0)
             number  number_big number_range  missing_value      text       date
        0  0.174303         926          900            0.0  tenkiakh 2006-09-08
        1  0.305137         140          100            0.0  jzuddamf 2012-04-04
        >>> df.fill_missing_values("missing_column", 0, fill_when_not_exist=0)
             number  number_big number_range  missing_value      text       date  missing_column
        0  0.174303         926          900            0.0  tenkiakh 2006-09-08               0
        1  0.305137         140          100            0.0  jzuddamf 2012-04-04               0
        """
        try:
            self[column_name] = self[column_name].fillna(fill)
        except KeyError:
            if getattr(self, "add_blank_column", None) is not None:
                # Compatible with DataAnalystDataFrameColumnMethodMixin
                self.add_blank_column(column_name, fill_when_not_exist)  # type: ignore
        return self

    def get_missing_values(
        self, hightlight: bool = True, *, percentage_round_up: int = 2
    ) -> Self:
        """
        Get a DataFrame contains count of missing values for each column

        Parameters
        ----------
        hightlight : bool
            Shows only columns with missing values when ``True``, by default ``True``

        percentage_round_up : int
            Round up to which decimals, by default ``2``

        Returns
        -------
        Self
            Missing value DataFrame


        Example:
        --------
        >>> DADF.sample_df(152).get_missing_values()
                       Num of N/A  Percentage
        missing_value          42       27.63
        """
        # Check for missing value
        df_na = self.isnull().sum().sort_values(ascending=False)
        if hightlight:
            out = df_na[df_na != 0].to_frame()
        else:
            out = df_na.to_frame()
        out.rename(columns={0: "Num of N/A"}, inplace=True)
        out["Percentage"] = (out["Num of N/A"] / self.shape[0] * 100).round(
            percentage_round_up
        )

        # logger.debug(
        #     f"Percentage of N/A over entire DF: "
        #     f"{(self.isnull().sum().sum() / (self.shape[0] * self.shape[1]) * 100).round(percentage_round_up)}%"
        # )
        return self.__class__(out)

    @versionadded("3.1.0")
    def split_na(self, by_column: str) -> SplittedDF:
        """
        Split DataFrame into 2 parts:
            - Without missing value in specified column
            - With missing value in specified column

        Parameters
        ----------
        by_column : str
            Split by column

        Returns
        -------
        SplittedDF
            Splitted DataFrame


        Example:
        --------
        >>> DADF.sample_df(10).split_na("missing_value")
        SplittedDF(
            df=     number  number_big number_range  missing_value      text       date
        0         0.643254         690          600            3.0  cinvofwj 2018-08-15
        2         0.499345         255          200           13.0  jasifzez 2005-06-01
        3        -1.727036         804          800           38.0  esxjmger 2009-07-24
        4         0.873058         690          600           32.0  htewfpld 2022-07-22
        5        -2.389884         442          400           30.0  hbcnfogu 2006-02-25
        8         0.264584         432          400            2.0  ejbvbmwn 2013-05-11
        9         0.813655         137          100           20.0  oecttada 2024-11-22,
            df_na=     number  number_big number_range  missing_value      text       date
        1           -0.411354         363          300            NaN  juzecani 2014-12-02
        6           -0.833857         531          500            NaN  ybnntryh 2023-11-03
        7            1.355589         472          400            NaN  zjltghjr 2024-10-09
        )
        """
        out = SplittedDF(
            # df=self[~self[by_column].isna()],  # DF
            df=self[self[by_column].notna()],  # DF
            df_na=self[self[by_column].isna()],  # DF w/o NA
        )
        return out

    @versionadded("5.1.0")
    def apply_notnull(self, col: str, callable: Callable[[Any], _R]) -> Self:
        """
        Only apply callable to not NaN value in column

        Parameters
        ----------
        col : str
            Column to apply

        callable : Callable[[Any], _R]
            Callable

        Returns
        -------
        Self
            Applied DataFrame


        Example:
        --------
        >>> DADF.sample_df(5).apply_notnull("missing_value", lambda _: "REPLACED")
             number  number_big number_range missing_value      text       date
        0  0.852218         157          100      REPLACED  dqzxaxxs 2006-03-08
        1  1.522428         616          600           NaN  mivkaooe 2018-12-27
        2  0.108506         745          700      REPLACED  qanwwjet 2005-07-14
        3 -1.435079         400          400      REPLACED  ywahcasi 2024-05-20
        4  0.118993         861          800      REPLACED  saoupuby 2019-04-28
        """
        self[col] = self[col].apply(lambda x: callable(x) if pd.notnull(x) else x)  # type: ignore
        return self

    @versionadded("5.1.0")  # type: ignore
    def apply_notnull_row(
        self,
        apply_when_null: Callable[[Any], _R] | _T | None = None,
        apply_when_not_null: Callable[[Any], _R] | _T | None = None,
        col_name: str | None = None,
    ) -> Self:
        """
        Apply to DataFrame's row with missing value.

        Parameters
        ----------
        apply_when_null : Callable[[Any], R] | T | None, optional
            Callable or Any, by default ``None``: returns if entire row is not null

        apply_when_not_null : Callable[[Any], R] | T | None, optional
            Callable or Any, by default ``None``: returns if entire row is not null

        col_name : str | None, optional
            Output column name, by default ``None`` (uses custom name)

        Returns
        -------
        Self
            Modified DataDrame


        Example:
        --------
        >>> df = DADF({"A": [None, 2, 3, 4], "B": [1, None, 3, 4], "C": [None, 2, None, 4]})
        >>> df.apply_notnull_row()
             A    B    C  applied_row_null
        0  NaN  1.0  NaN             False
        1  2.0  NaN  2.0             False
        2  3.0  3.0  NaN             False
        3  4.0  4.0  4.0              True
        >>> df.apply_notnull_row(0, 1)
             A    B    C  applied_row_null
        0  NaN  1.0  NaN                 0
        1  2.0  NaN  2.0                 0
        2  3.0  3.0  NaN                 0
        3  4.0  4.0  4.0                 1
        >>> df.apply_notnull_row(lambda _: "n", lambda _: "y", col_name="mod")
             A    B    C mod
        0  NaN  1.0  NaN   n
        1  2.0  NaN  2.0   n
        2  3.0  3.0  NaN   n
        3  4.0  4.0  4.0   y
        """

        def apply_func(row: pd.Series):
            # Both None
            if apply_when_null is None and apply_when_not_null is None:
                return row.notnull().all()

            # When all values in row are not null
            if row.notnull().all():
                if callable(apply_when_not_null):
                    return apply_when_not_null(row)
                return apply_when_not_null

            # When any value in row is null
            if callable(apply_when_null):
                return apply_when_null(row)
            return apply_when_null

        # Column name
        cname = "applied_row_null" if col_name is None else col_name
        self[cname] = self.apply(apply_func, axis=1)  # type: ignore

        return self


# Other
# ---------------------------------------------------------------------------
class DataAnalystDataFrameOtherMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Other method/Stuff

    - Merge left
    """

    @versionadded("4.0.0")
    def merge_left(
        self,
        other: Self | pd.DataFrame,
        on: str,
        columns: list[str] | None = None,
    ) -> Self:
        """
        Merge left of 2 DataFrame

        Parameters
        ----------
        other : Self | pd.DataFrame
            DataFrame to merge

        on : str
            Merge on which column

        columns : list[str] | None, optional
            Columns to take from other DataFrame, by default ``None``
            (Take all columns)

        Returns
        -------
        Self
            Merged DataFrame


        Example:
        --------
        >>> df1 = DADF({
        ...     "id": [1, 2, 5],
        ...     "name": ["Alice", "Bob", "Rich"],
        ...     "age": [20, 20, 20],
        ... })
        >>> df2 = DADF({
        ...     "id": [1, 2, 3],
        ...     "age": [25, 30, 45],
        ...     "department": ["HR", "IT", "PM"],
        ...     "salary": [50000, 60000, 55000],
        ... })
        >>> df1.merge_left(df2, on="id")
           id   name  age_x  age_y department   salary
        0   1  Alice     20   25.0         HR  50000.0
        1   2    Bob     20   30.0         IT  60000.0
        2   5   Rich     20    NaN        NaN      NaN
        >>> df1.merge_left(df2, on="id", columns=["salary"])
           id   name   age department   salary
        0   1  Alice  25.0         HR  50000.0
        1   2    Bob  30.0         IT  60000.0
        2   5   Rich   NaN        NaN      NaN
        """

        if columns is not None:
            current_col = [on]
            current_col.extend(columns)
            col = other.columns.to_list()
            cols = list(set(col) - set(current_col))

            if getattr(self, "drop_columns", None) is not None:
                # Compatible with DataAnalystDataFrameColumnMethodMixin
                self.drop_columns(cols)  # type: ignore

        out = self.merge(other, how="left", on=on)
        return self.__class__(out)


# Date
# ---------------------------------------------------------------------------
class DataAnalystDataFrameDateMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Date

    - Add date column from month column
    - Add detail date
    - Delta date (How many days inbetween)
    """

    def add_date_from_month(self, month_column: str, *, col_name: str = "date") -> Self:
        """
        Add dummy ``date`` column from ``month`` column

        Parameters
        ----------
        month_column : str
            Month column

        col_name : str
            New date column name, by default: ``"date"``

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = (
        ...     DADF.sample_df(2)
        ...     .add_detail_date("date", mode="m")
        ...     .drop_columns(["date", "number", "number_range"])
        ... )
        >>> df
           number_big  missing_value      text  month
        0         755            NaN  lincgqzl      4
        1         907            NaN  gxltrjku     10
        >>> df.add_date_from_month("month")
           number_big  missing_value      text  month       date
        0         755            NaN  lincgqzl      4 2025-04-01
        1         907            NaN  gxltrjku     10 2025-10-01
        """
        _this_year = datetime.now().year
        self[col_name] = pd.to_datetime(
            f"{_this_year}-" + self[month_column].astype(int).astype(str) + "-1",
            format="%Y-%m-%d",
        )

        # Rearrange
        if getattr(self, "rearrange_rightmost_column", None) is not None:
            # Compatible with DataAnalystDataFrameColumnMethodMixin
            return self.rearrange_rightmost_column(month_column)  # type: ignore [no-any-return]
        return self

    def add_detail_date(self, date_column: str, mode: str = "dwmy") -> Self:
        """
        Add these columns from ``date_column``:
            - ``date`` (won't add if ``date_column`` value is ``"date"``)
            - ``day`` (overwrite if already exist)
            - ``week`` (overwrite if already exist)
            - ``month`` (overwrite if already exist)
            - ``year``  (overwrite if already exist)

        Parameters
        ----------
        date_column : str
            Date column

        mode : str
            | Detailed column to add
            | ``d``: day
            | ``w``: week number
            | ``m``: month
            | ``y``: year
            | (Default: ``"dwmy"``)

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0  0.331195         902          900             20  fgyanxik 2021-10-18
        1 -0.877727         378          300             13  dqvaggjo 2007-03-06
        >>> df.add_detail_date("date")
             number  number_big number_range  missing_value      text       date  day  week  month  year
        0  0.331195         902          900             20  fgyanxik 2021-10-18   18    42     10  2021
        1 -0.877727         378          300             13  dqvaggjo 2007-03-06    6    10      3  2007
        """
        # Convert to datetime
        self["date"] = pd.to_datetime(self[date_column])

        # Logic
        col_counter = 0
        # self["weekday"] = self["day"].dt.isocalendar().day # Weekday
        if mode.find("d") != -1:
            # logger.debug("Mode: 'day'")
            self["day"] = self["date"].dt.day
            col_counter += 1
        if mode.find("w") != -1:
            # logger.debug("Mode: 'weekday'")
            self["week"] = self["date"].dt.isocalendar().week
            col_counter += 1
        if mode.find("m") != -1:
            # logger.debug("Mode: 'month'")
            self["month"] = self["date"].dt.month
            col_counter += 1
        if mode.find("y") != -1:
            # logger.debug("Mode: 'year'")
            self["year"] = self["date"].dt.year
            col_counter += 1

        # Return
        if getattr(self, "rearrange_rightmost_column", None) is not None:
            # Compatible with DataAnalystDataFrameColumnMethodMixin
            return self.rearrange_rightmost_column(date_column, col_counter)  # type: ignore [no-any-return]
        return self

    def delta_date(
        self,
        date_column: str,
        mode: Literal["now", "between_row"] = "now",
        *,
        col_name: str = "delta_date",
    ) -> Self:
        """
        Calculate date interval

        Parameters
        ----------
        date_column : str
            Date column

        mode : str
            | Mode to calculate
            | ``"between_row"``: Calculate date interval between each row
            | ``"now"``: Calculate date interval to current date
            | (Default: ``"now"``)

        col_name : str
            | New delta date column name
            | (Default: ``"delta_date"``)

        Returns
        -------
        Self
            Modified DataFrame


        Example:
        --------
        >>> df = DADF.sample_df(2)
        >>> df
             number  number_big number_range  missing_value      text       date
        0 -0.729988         435          400             21  xkrqqouf 2014-08-01
        1 -0.846031         210          200              5  rbkmiqxt 2024-07-10
        >>> df.delta_date("date")
             number  number_big number_range  missing_value      text       date  delta_date
        0 -0.729988         435          400             21  xkrqqouf 2014-08-01        3873
        1 -0.846031         210          200              5  rbkmiqxt 2024-07-10         242
        """
        if mode.lower().startswith("between_row"):
            dated = self[date_column].to_list()
            cal: list[timedelta] = []
            for i in range(len(dated)):
                if i == 0:
                    cal.append(dated[i] - dated[i])
                    # cal.append(relativedelta(dated[i], dated[i]))
                else:
                    cal.append(dated[i] - dated[i - 1])
                    # cal.append(relativedelta(dated[i], dated[i - 1]))
            self[col_name] = [x.days for x in cal]
        else:  # mode="now"
            self[col_name] = self[date_column].apply(
                lambda x: (datetime.now() - x).days
            )
        return self

    @versionadded("6.0.0")
    def normalize_datetime_column(
        self,
        col: str,
        *,
        inplace: bool = False,
    ) -> Self:
        """
        Normalize a datetime column by removing the time component.

        This function converts the specified column to pandas datetime (``datetime64[ns]``)
        (if not already), then normalizes all values so that the time
        component is set to ``00:00:00``. The date component is preserved.

        The function safely handles missing or invalid values by coercing
        them to ``NaT``.

        Parameters
        ----------
        col : str
            Name of the column to normalize. The column may contain
            datetime-like values, strings, or mixed types.

        inplace : bool, default False
            | If ``True``, modify the input DataFrame in place.
            | If ``False``, operate on a copy and return the modified DataFrame.

        Returns
        -------
        Self
            DataFrame with the normalized datetime column.


        Example:
        --------
        Basic usage::

            >>> df = DADF({
            ...     "created_at": ["2024-01-01 10:15:30", "2024-01-02 23:59:59"]
            ... })
            >>> normalize_datetime_column(df, "created_at")
            created_at
            0 2024-01-01 00:00:00
            1 2024-01-02 00:00:00

        In-place modification::

            >>> normalize_datetime_column(df, "created_at", inplace=True)

        Handling invalid values::

            >>> df = DADF({"dt": ["2024-01-01 10:00", "invalid"]})
            >>> normalize_datetime_column(df, "dt")
                    dt
            0 2024-01-01 00:00:00
            1                NaT

        """
        if not inplace:
            df = self.copy()
        else:
            df = self

        # Using ``df.loc[:, col]`` avoids ``SettingWithCopyWarning`` when the input DataFrame is a slice.
        df.loc[:, col] = pd.to_datetime(df[col], errors="coerce").dt.normalize()
        return df


# Export
# ---------------------------------------------------------------------------
class DataAnalystDataFrameExportMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - Export method

    - da_export
    """

    @versionchanged("5.8.0", "New parameter")
    def da_export(
        self,
        path: str,
        sheet_name: str = "Sheet1",
        *,
        auto_width: bool = True,
        cols_contain_centered_text: list[str] | None = None,
        cols_contain_number: list[str] | None = None,
        cols_contain_percentage: list[str] | None = None,
    ) -> None:
        """
        Export DataFrame with `xlsxwriter` engine

        Parameters
        ----------
        path : Path | str
            Path to export

        sheet_name : str, optional
            Sheet name, by default "Sheet1"

        auto_width : bool, optional
            Auto resize column width, by default ``True``

        cols_contain_centered_text : list[str] | None, optional
            Columns that contain centered text (Align center), by default None

        cols_contain_number : list[str] | None, optional
            Columns that contain number value (to format as number - int), by default None

        cols_contain_percentage : list[str] | None, optional
            Columns that contain percentage value (to format as percentage), by default None
        """

        # Using xlsxwriter engine
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            self.to_excel(writer, sheet_name=sheet_name, index=False, float_format="%.2f", na_rep="")

            # Format style
            workbook: Workbook = writer.book  # type: ignore
            header_fmt = workbook.add_format(
                {
                    "bold": True,
                    "text_wrap": True,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    # "bg_color": "#A0BEFD",
                }
            )
            number_fmt = workbook.add_format(
                {"num_format": "#,##0", "align": "center", "valign": "vcenter"}
            )  # 1,000,000
            percent_fmt = workbook.add_format({"num_format": "0.00%", "align": "center", "valign": "vcenter"})  # 1.00%
            text_fmt = workbook.add_format({"valign": "vcenter"})
            text_center_fmt = workbook.add_format({"align": "center", "valign": "vcenter"})

            # Format sheet
            worksheet: Worksheet = writer.sheets[sheet_name]

            # Format header - First row
            for col_num, value in enumerate(self.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

            rules = [
                (cols_contain_number, number_fmt),
                (cols_contain_percentage, percent_fmt),
                (cols_contain_centered_text, text_center_fmt),
            ]

            # Auto width + col format
            for i, col in enumerate(self.columns):
                # Max str len of each column
                max_len = None if auto_width is None else max(self[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_len)  # Set width

                # Format style
                fmt = text_fmt  # default
                for cols, f in rules:
                    if cols is not None and col in cols:
                        fmt = f
                        break
                worksheet.set_column(i, i, max_len, fmt)

            # if cols_contain_number is not None:
            #     for x in cols_contain_number:
            #         self[x] = pd.to_numeric(self[x], errors="coerce")


# City
# ---------------------------------------------------------------------------
class DataAnalystDataFrameCityMixin(DFBase):
    """
    Data Analyst ``pd.DataFrame`` - City

    - Convert city
    """

    def convert_city(
        self,
        city_column: str,
        city_list: list[CityData],
        *,
        mode: str = "ra",
    ) -> Self:
        """
        Get ``region`` and ``area`` of a city

        Parameters
        ----------
        city_column : str
            Column contains city data

        city_list : list[CityData]
            List of city in correct format
            (Default: ``None``)

        mode : str
            | Detailed column to add
            | ``r``: region
            | ``a``: area
            | (Default: ``"ra"``)

        Returns
        -------
        DataAnalystDataFrame
            Modified DataFrame
        """

        # Support function
        def _convert_city_support(value: str) -> CityData:
            for x in city_list:
                if x.city.lower().startswith(value.lower()):
                    return x
            return CityData(city=value, region=np.nan, area=np.nan)  # type: ignore

        # Convert
        col_counter = 0
        if mode.find("r") != -1:
            # logger.debug("Mode: 'region'")
            self["region"] = self[city_column].apply(
                lambda x: _convert_city_support(x).region
            )
            col_counter += 1
        if mode.find("a") != -1:
            # logger.debug("Mode: 'area'")
            self["area"] = self[city_column].apply(
                lambda x: _convert_city_support(x).area
            )
            col_counter += 1

        # Rearrange
        if getattr(self, "rearrange_rightmost_column", None) is not None:
            return self.rearrange_rightmost_column(city_column, col_counter)  # type: ignore [no-any-return]
        return self


# Main
# ---------------------------------------------------------------------------
class DADF(
    GetClassMembersMixin,
    DataAnalystDataFrameCityMixin,
    DataAnalystDataFrameExportMixin,
    DataAnalystDataFrameDateMixin,
    DataAnalystDataFrameOtherMixin,
    DataAnalystDataFrameNAMixin,
    DataAnalystDataFrameInfoMixin,
    DataAnalystDataFrameRowMethodMixin,
    DataAnalystDataFrameColumnMethodMixin,
):
    """
    Data Analyst ``pd.DataFrame``

    For a list of extra methods:
    >>> print(DADF.DADF_METHODS)
    """

    @classmethod
    @deprecated("5.1.0")
    @versionadded("3.2.0")
    def dadf_help(cls) -> list[str]:
        """
        Show all available method of DataAnalystDataFrame
        """
        list_of_method = list(set(dir(cls)) - set(dir(pd.DataFrame)))
        return sorted(list_of_method)

    @classmethod
    def sample_df(cls, size: int = 100) -> Self:
        """
        Create sample DataFrame

        Parameters
        ----------
        size : int
            Number of observations, by default ``100``

        Returns
        -------
        Self
            DataFrame with these columns:
            [number, number_big, number_range, missing_value, text, date]


        Example:
        --------
        >>> DataAnalystDataFrame.sample_df()
              number  number_big number_range  missing_value      text       date
        0  -2.089770         785          700            NaN  vwnlqoql 2013-11-20
        1  -0.526689         182          100           24.0  prjjcvqc 2007-04-13
        2  -1.596514         909          900            8.0  cbcpzlac 2023-05-24
        3   2.982191         989          900           21.0  ivwqwuvd 2022-04-28
        4   1.687803         878          800            NaN  aajtncum 2005-10-05
        ..       ...         ...          ...            ...       ...        ...
        95 -1.295145         968          900           16.0  mgqunkhi 2016-04-12
        96  1.296795         255          200            NaN  lwvytego 2014-05-10
        97  1.440746         297          200            5.0  lqsoykun 2010-04-03
        98  0.327702         845          800            NaN  leadkvsy 2005-08-05
        99  0.556720         981          900           36.0  bozmxixy 2004-02-22
        [100 rows x 6 columns]
        """
        # Restrain
        size = max(size, 1)

        # Number col
        df = cls(np.random.randn(size, 1), columns=["number"])
        df["number_big"] = [
            random.choice(range(100, 999)) for _ in range(size)
        ]  # Big number in range 100-999
        df["number_range"] = df["number_big"].apply(lambda x: str(x)[0] + "00")

        # Missing value col
        na_rate = random.randint(1, 99)
        d = [random.randint(1, 99) for _ in range(size)]
        df["missing_value"] = list(map(lambda x: x if x < na_rate else np.nan, d))
        # df["missing_value"] = [random.choice([random.randint(1, 99), np.nan]) for _ in range(observations)]

        # Text col
        df["text"] = [
            "".join([random.choice(string.ascii_lowercase) for _ in range(8)])
            for _ in range(size)
        ]

        # Random date col
        df["date"] = [
            datetime(
                year=random.randint(datetime.now().year - 20, datetime.now().year),
                month=random.randint(1, 12),
                day=random.randint(1, 28),
            )
            for _ in range(size)
        ]

        # Return
        return df


class DADF_WIP(DADF):
    """
    W.I.P - No test cases written
    """

    pass

if __name__ == "__main__":
    from pathlib import Path

    # t = DADF.sample_df().show_distribution("number_range", show_percentage=False)
    # t.da_export(
    #     Path(__file__).parent.joinpath("a.xlsx").resolve().__str__(),
    #     cols_contain_number=["number_range"],
    #     cols_contain_percentage=["percentage"],
    # )
    # print(t)

    df = DADF.sample_df(10)
    print(df.add_blank_row())
