"""
Test: Data extension - DictExt

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.dxt import DictAnalyzeResult, DictExt


@pytest.fixture
def dict_example():
    return DictExt({"Line 1": 99, "Line 2": 50})


@pytest.fixture
def dict_example_2():
    return DictExt({"Line 1": 99, "Line 2": "test"})


@pytest.mark.abs_dxt
class TestDictExt:
    """absfuyu.dxt.DictExt"""

    # analyze
    def test_analyze(self, dict_example: DictExt) -> None:
        # assert example.analyze() == {'max_value': 99, 'min_value': 50, 'max': [('Line 1', 99)], 'min': [('Line 2', 50)]}
        assert dict_example.analyze() == DictAnalyzeResult(
            99, 50, [("Line 1", 99)], [("Line 2", 50)]
        )

    def test_analyze_error(self, dict_example_2: DictExt) -> None:
        """When values are not int or float"""
        with pytest.raises(ValueError) as excinfo:
            dict_example_2.analyze()
        assert str(excinfo.value)

    # swap
    def test_swap(self, dict_example: DictExt) -> None:
        assert dict_example.swap_items() == {99: "Line 1", 50: "Line 2"}

    # apply
    def test_apply(self, dict_example: DictExt) -> None:
        """Values"""
        assert dict_example.apply(str) == {"Line 1": "99", "Line 2": "50"}

    def test_apply_2(self) -> None:
        """Keys"""
        assert DictExt({1: 1}).apply(str, apply_to_value=False) == {"1": 1}

    # aggregate
    def test_aggregate(self, dict_example: DictExt) -> None:
        agg = {"Line 1": 1, "Line 3": 1}
        new_dict = dict_example.aggregate(agg)
        assert new_dict == {"Line 1": 100, "Line 2": 50, "Line 3": 1}

    def test_aggregate_2(self, dict_example: DictExt) -> None:
        """Empty dict"""
        new_dict = DictExt().aggregate(dict_example)
        assert new_dict == dict_example

    def test_aggregate_3(self, dict_example: DictExt) -> None:
        """Different type of data"""
        agg = {"Line 1": "1", "Line 3": 1}
        new_dict = dict_example.aggregate(agg)
        assert new_dict == {"Line 1": [99, "1"], "Line 2": 50, "Line 3": 1}
