"""
Absfuyu: Data Analysis
----------------------
Data Analyst DataFrame - Base/Core

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["DataAnalystDataFrameBase", "SplittedDF", "CityData"]


# Library
# ---------------------------------------------------------------------------
import random
from collections import deque
from typing import ClassVar, Literal, NamedTuple

import pandas as pd


# Class
# ---------------------------------------------------------------------------
class DataAnalystDataFrameBase(pd.DataFrame):
    """
    Data Analyst ``pd.DataFrame`` - Base

    Set class variable ``_DADF_INCLUDE`` to ``False`` to exclude from ``DADF_METHODS``
    """

    # Custom attribute
    _DADF_INCLUDE: ClassVar[bool] = True  # Include in DADF_METHODS
    DADF_METHODS: ClassVar[dict[str, list[str]]] = {}

    def __init_subclass__(cls, *args, **kwargs) -> None:
        """
        This create a dictionary with:
        - key   (str)      : Subclass
        - value (list[str]): List of available methods
        """
        super().__init_subclass__(*args, **kwargs)

        if cls._DADF_INCLUDE and not any(
            [x.endswith(cls.__name__) for x in cls.DADF_METHODS.keys()]
        ):
            # if not any([x.endswith(cls.__name__) for x in cls.DADF_METHODS.keys()]):
            methods_list: list[str] = [
                k for k, v in cls.__dict__.items() if callable(v)
            ]
            if len(methods_list) > 0:
                name = f"{cls.__module__}.{cls.__name__}"
                cls.DADF_METHODS.update({name: sorted(methods_list)})


class SplittedDF(NamedTuple):
    """
    DataFrame splitted into contains
    missing values only and vice versa

    Parameters
    ----------
    df : DataFrame
        DataFrame without missing values

    df_na : DataFrame
        DataFrame with missing values only
    """

    df: pd.DataFrame
    df_na: pd.DataFrame

    @staticmethod
    def concat_df(
        df_list: list[pd.DataFrame], join: Literal["inner", "outer"] = "inner"
    ) -> pd.DataFrame:
        """
        Concat the list of DataFrame (static method)

        Parameters
        ----------
        df_list : list[DataFrame]
            A sequence of DataFrame

        join : str
            Join type
            (Default: ``"inner"``)

        Returns
        -------
        DataFrame
            Joined DataFrame
        """
        df: pd.DataFrame = pd.concat(df_list, axis=0, join=join).reset_index()
        df.drop(columns=["index"], inplace=True)
        return df

    def concat(self, join: Literal["inner", "outer"] = "inner") -> pd.DataFrame:
        """
        Concat the splitted DataFrame

        Parameters
        ----------
        join : str
            Join type
            (Default: ``"inner"``)

        Returns
        -------
        DataFrame
            Joined DataFrame
        """
        return self.concat_df(self, join=join)  # type: ignore

    @staticmethod
    def divide_dataframe(df: pd.DataFrame, by_column: str) -> list[pd.DataFrame]:
        """
        Divide DataFrame into a list of DataFrame

        Parameters
        ----------
        df : DataFrame
            DataFrame

        by_column : str
            By which column

        Returns
        -------
        list[DataFrame]
            Splitted DataFrame
        """
        divided = [x for _, x in df.groupby(by_column)]
        return divided


class CityData(NamedTuple):
    """
    Parameters
    ----------
    city : str
        City name

    region : str
        Region of the city

    area : str
        Area of the region
    """

    city: str
    region: str
    area: str

    @staticmethod
    def _sample_city_data(size: int = 100):
        """
        Generate sample city data (testing purpose)
        """
        sample_range = 10 ** len(str(size))

        # Serial list
        serials: list[str] = []
        while len(serials) != size:  # Unique serial
            serial = random.randint(0, sample_range - 1)
            serial = str(serial).rjust(len(str(size)), "0")  # type: ignore
            if serial not in serials:  # type: ignore
                serials.append(serial)  # type: ignore

        ss2 = deque(serials[: int(len(serials) / 2)])  # Cut half for region
        ss2.rotate(random.randrange(1, 5))
        [ss2.extend(ss2) for _ in range(2)]  # type: ignore # Extend back

        ss3 = deque(serials[: int(len(serials) / 4)])  # Cut forth for area
        ss3.rotate(random.randrange(1, 5))
        [ss3.extend(ss3) for _ in range(4)]  # type: ignore # Extend back

        serials = ["city_" + x for x in serials]
        ss2 = ["region_" + x for x in ss2]  # type: ignore
        ss3 = ["area_" + x for x in ss3]  # type: ignore

        ss = list(zip(serials, ss2, ss3))  # Zip back
        out = list(map(CityData._make, ss))

        return out
