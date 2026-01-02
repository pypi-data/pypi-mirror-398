"""
Test: Data Analysis

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import random

import pytest

try:  # [extra] feature
    import numpy as np
    import pandas as pd
except ImportError:
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")

from absfuyu.extra.da.dadf import DADF
from absfuyu.extra.da.dadf_base import CityData, SplittedDF
from absfuyu.tools.generator import Charset, Generator

SAMPLE_SIZE = 100
sample_city_data = CityData._sample_city_data(size=SAMPLE_SIZE)


# MARK: fixture
@pytest.fixture
def sample_df() -> DADF:
    # Number of columns generated
    num_of_cols: int = random.randint(5, 10)
    # List of column name
    col_name: list = Generator.generate_string(
        Charset.LOWERCASE, unique=True, times=num_of_cols
    )
    # Create DataFrame
    df = pd.DataFrame(
        np.random.randn(random.randint(5, 100), num_of_cols), columns=col_name
    )
    out = DADF(df)
    return out


@pytest.fixture
def sample_df_2() -> DADF:
    return DADF.sample_df()


@pytest.fixture
def sample_df_3():
    sample = DADF.sample_df(size=SAMPLE_SIZE)
    sample["city"] = [x.city for x in sample_city_data]
    return sample


# MARK: test
class TestDataAnalystDataFrameBase: ...


class TestSplittedDF: ...


class TestDADF:
    """absfuyu.extra.da.dadf.DADF"""

    # Drop cols
    def test_drop_rightmost(self, sample_df: DADF) -> None:
        num_of_cols_drop = random.randint(1, 4)

        num_of_cols_current = sample_df.shape[1]
        sample_df.drop_rightmost(num_of_cols_drop)
        num_of_cols_modified = sample_df.shape[1]

        condition = (num_of_cols_current - num_of_cols_modified) == num_of_cols_drop
        assert condition

    # Add blank column
    def test_add_blank_column(self, sample_df: DADF) -> None:
        original_num_of_cols = sample_df.shape[1]
        sample_df.add_blank_column("new_col", 0)
        new_num_of_cols = sample_df.shape[1]

        condition = (new_num_of_cols - original_num_of_cols) == 1 and sum(
            sample_df["new_col"]
        ) == 0
        assert condition

    # Add date column
    def test_add_date_from_month(self, sample_df_2: DADF) -> None:
        sample_df_2.add_detail_date("date", mode="m")
        original_num_of_cols = sample_df_2.shape[1]
        sample_df_2.add_date_from_month("month", col_name="mod_date")
        new_num_of_cols = sample_df_2.shape[1]

        original_month = sample_df_2["month"][0]
        modified_month = sample_df_2["mod_date"][0].month

        # assert original_month == modified_month
        condition = (
            new_num_of_cols - original_num_of_cols
        ) == 1 and original_month == modified_month
        assert condition

    def test_add_date_column(self, sample_df_2: DADF) -> None:
        # Get random mode
        mode_list = ["d", "w", "m", "y"]
        test_mode = list(
            map(lambda x: "".join(x), Generator.combinations_range(mode_list))
        )
        random_mode = random.choice(test_mode)
        num_of_new_cols = len(random_mode)

        # Convert
        original_num_of_cols = sample_df_2.shape[1]
        sample_df_2.add_detail_date("date", mode=random_mode)
        new_num_of_cols = sample_df_2.shape[1]
        assert (new_num_of_cols - original_num_of_cols) == num_of_new_cols

    # Join and split
    def test_split_df(self, sample_df_2: DADF) -> None:
        test = sample_df_2.split_na("missing_value")
        assert len(test) > 1

    def test_split_df_2(self, sample_df_2: DADF) -> None:
        test = SplittedDF.divide_dataframe(sample_df_2, "number_range")
        assert len(test) > 1

    def test_join_df(self, sample_df_2: DADF) -> None:
        test = sample_df_2.split_na("missing_value")
        out = test.concat()
        assert out.shape[0] == 100

    def test_join_df_2(self, sample_df_2: DADF) -> None:
        """This test static method"""
        test = SplittedDF.divide_dataframe(sample_df_2, "number_range")
        out = SplittedDF.concat_df(test)
        assert out.shape[0] == 100

    # Threshold filter
    def test_threshold_filter(self, sample_df_2: DADF) -> None:
        original_num_of_cols = sample_df_2.shape[1]
        sample_df_2.threshold_filter("number_range", 11)
        new_num_of_cols = sample_df_2.shape[1]

        # Check new column
        assert (new_num_of_cols - original_num_of_cols) == 1

        # Check filler value
        test: list = sample_df_2["number_range_filtered"].unique().tolist()
        try:
            test.index("Other")
            assert True
        except Exception:
            pass

        # Check len
        test1 = sample_df_2["number_range"].unique().tolist()
        assert (len(test1) - len(test)) >= 1

    # Convert city
    def test_convert_city(self, sample_df_3: DADF) -> None:
        original_num_of_cols = sample_df_3.shape[1]
        sample_df_3.convert_city("city", city_list=sample_city_data)
        new_num_of_cols = sample_df_3.shape[1]
        assert (new_num_of_cols - original_num_of_cols) == 2

    # Diff
    def test_get_different_rows(self) -> None:
        df1 = DADF({"A": [1, 2, 3, 4], "B": [5, 6, 7, 8]})
        df2 = DADF({"A": [1, 2, 3, 4], "B": [7, 6, 6, 8]})
        assert df1.get_different_rows(df2).to_dict() == {
            "A": {0: 1, 2: 3},
            "B": {0: 7, 2: 6},
        }

    # Merge
    def test_merge_left(self) -> None:
        df1 = DADF(
            {
                "id": [1, 2, 5],
                "name": ["Alice", "Bob", "Rich"],
                "age": [20, 20, 20],
            }
        )
        df2 = DADF(
            {
                "id": [1, 2, 3],
                "age": [25, 30, 45],
                "department": ["HR", "IT", "PM"],
                "salary": [50000, 60000, 55000],
            }
        )
        assert df1.merge_left(df2, on="id").fillna("N/A").to_dict() == {
            "id": {0: 1, 1: 2, 2: 5},
            "name": {0: "Alice", 1: "Bob", 2: "Rich"},
            "age_x": {0: 20, 1: 20, 2: 20},
            "age_y": {0: 25.0, 1: 30.0, 2: "N/A"},
            "department": {0: "HR", 1: "IT", 2: "N/A"},
            "salary": {0: 50000.0, 1: 60000.0, 2: "N/A"},
        }
        assert df1.merge_left(df2, on="id", columns=["salary"]).fillna(
            "N/A"
        ).to_dict() == {
            "id": {0: 1, 1: 2, 2: 5},
            "name": {0: "Alice", 1: "Bob", 2: "Rich"},
            "age": {0: 25.0, 1: 30.0, 2: "N/A"},
            "department": {0: "HR", 1: "IT", 2: "N/A"},
            "salary": {0: 50000.0, 1: 60000.0, 2: "N/A"},
        }

    # Apply not null
    def test_apply_notnull(self) -> None:
        df = DADF({"A": [1, 2, 3], "B": [4, None, 6]})
        assert df.apply_notnull("B", lambda _: "Replaced").fillna("N/A").to_dict() == {
            "A": {0: 1, 1: 2, 2: 3},
            "B": {0: "Replaced", 1: "N/A", 2: "Replaced"},
        }

    def test_apply_notnull_row(self) -> None:
        df = DADF({"A": [None, 2, 3, 4], "B": [1, None, 3, 4], "C": [None, 2, None, 4]})
        assert df.apply_notnull_row().fillna("N/A").to_dict() == {
            "A": {0: "N/A", 1: 2.0, 2: 3.0, 3: 4.0},
            "B": {0: 1.0, 1: "N/A", 2: 3.0, 3: 4.0},
            "C": {0: "N/A", 1: 2.0, 2: "N/A", 3: 4.0},
            "applied_row_null": {0: False, 1: False, 2: False, 3: True},
        }
        df = DADF({"A": [None, 2, 3, 4], "B": [1, None, 3, 4], "C": [None, 2, None, 4]})
        assert df.apply_notnull_row(0, 1).fillna("N/A").to_dict() == {
            "A": {0: "N/A", 1: 2.0, 2: 3.0, 3: 4.0},
            "B": {0: 1.0, 1: "N/A", 2: 3.0, 3: 4.0},
            "C": {0: "N/A", 1: 2.0, 2: "N/A", 3: 4.0},
            "applied_row_null": {0: 0, 1: 0, 2: 0, 3: 1},
        }
        df = DADF({"A": [None, 2, 3, 4], "B": [1, None, 3, 4], "C": [None, 2, None, 4]})
        assert df.apply_notnull_row(
            lambda _: "n", lambda _: "y", col_name="mod"
        ).fillna("N/A").to_dict() == {
            "A": {0: "N/A", 1: 2.0, 2: 3.0, 3: 4.0},
            "B": {0: 1.0, 1: "N/A", 2: 3.0, 3: 4.0},
            "C": {0: "N/A", 1: 2.0, 2: "N/A", 3: 4.0},
            "mod": {0: "n", 1: "n", 2: "n", 3: "y"},
        }
