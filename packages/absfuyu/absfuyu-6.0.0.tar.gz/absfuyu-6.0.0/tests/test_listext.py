"""
Test: Data extension - ListExt

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.dxt import ListExt


@pytest.fixture
def list_example():
    return ListExt([3, 8, 5, "Test", "String", "ABC", [1, 2, 3], [0, 8, 6]])


@pytest.fixture
def list_example_2():
    return ListExt(["Test", "String", "ABC", "Tension", "Tent", "Strong"])


@pytest.mark.abs_dxt
class TestListExt:
    """absfuyu.dxt.ListExt"""

    # stringify
    def test_stringify(self, list_example: ListExt) -> None:
        assert all([isinstance(x, str) for x in list_example.stringify()]) is True

    # sorts
    def test_sorts(self, list_example: ListExt) -> None:
        assert list_example.sorts() == [
            3,
            5,
            8,
            "ABC",
            "String",
            "Test",
            [0, 8, 6],
            [1, 2, 3],
        ]

    # freq
    def test_freq(self, list_example_2: ListExt) -> None:
        assert list_example_2.freq(sort=True) == {
            "ABC": 1,
            "String": 1,
            "Strong": 1,
            "Tension": 1,
            "Tent": 1,
            "Test": 1,
        }

    def test_freq_2(self, list_example_2: ListExt) -> None:
        assert list_example_2.freq(sort=True, num_of_first_char=2) == {
            "AB": 1,
            "St": 2,
            "Te": 3,
        }

    def test_freq_3(self, list_example_2: ListExt) -> None:
        assert list_example_2.freq(
            sort=True, num_of_first_char=2, appear_increment=True
        ) == [1, 3, 6]

    # slice_points
    def test_slice_points(self, list_example_2: ListExt) -> None:
        assert list_example_2.slice_points([1, 3]) == [
            ["Test"],
            ["String", "ABC"],
            ["Tension", "Tent", "Strong"],
        ]

    # pick_one
    def test_pick_one(self, list_example_2: ListExt) -> None:
        assert len([list_example_2.pick_one()]) == 1

    def test_pick_one_error(self) -> None:
        """Empty list"""
        with pytest.raises(IndexError) as excinfo:
            ListExt([]).pick_one()
            assert str(excinfo.value)

    # len_items
    def test_len_items(self, list_example_2: ListExt) -> None:
        assert list_example_2.len_items() == [4, 6, 3, 7, 4, 6]

    # mean_len
    def test_mean_len(self, list_example_2: ListExt) -> None:
        assert list_example_2.mean_len() == 5.0

    # apply
    def test_apply(self, list_example: ListExt) -> None:
        assert list_example.apply(str) == list_example.stringify()

    # unique
    def test_unique(self) -> None:
        assert ListExt([1, 1, 1, 1]).unique() == [1]

    # head
    def test_head(self, list_example: ListExt) -> None:
        assert list_example.head(3) == [3, 8, 5]

    def test_head_2(self, list_example: ListExt) -> None:
        """Max head len"""
        assert list_example.head(100) == list(list_example)

    def test_head_3(self) -> None:
        """Empty list"""
        assert ListExt([]).head(9) == []

    # tail
    def test_tail(self, list_example_2: ListExt) -> None:
        assert list_example_2.tail(2) == ["Tent", "Strong"]

    def test_tail_2(self, list_example_2: ListExt) -> None:
        assert list_example_2.tail(100) == list(list_example_2)

    def test_tail_3(self) -> None:
        """Empty list"""
        assert ListExt([]).tail(9) == []

    # get_random
    def test_get_random(self, list_example_2: ListExt) -> None:
        test = list_example_2.get_random(20)
        assert len(test) == 20

    # flatten
    def test_flatten(self, list_example: ListExt) -> None:
        test = list_example.flatten()
        assert test

    def test_flatten_2(self) -> None:
        test = ListExt([[[[1]]]])
        assert test.flatten(recursive=True) == [1]

    # split chunk
    @pytest.mark.parametrize(
        ["value", "output"],
        [
            (-1, [[1], [1], [1], [1], [1], [1], [1], [1], [1]]),
            (1, [[1], [1], [1], [1], [1], [1], [1], [1], [1]]),
            (2, [[1, 1], [1, 1], [1, 1], [1, 1], [1]]),
            (5, [[1, 1, 1, 1, 1], [1, 1, 1, 1]]),
            (100, [[1, 1, 1, 1, 1, 1, 1, 1, 1]]),
        ],
    )
    def test_split_chunk(self, value: int, output: list[list]) -> None:
        test = ListExt([1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert test.split_chunk(value) == output

    # max item len
    def test_max_item_len(self) -> None:
        ins = ListExt(["test", "longer_test"])
        assert ins.max_item_len() == 11

    def test_max_item_len_2(self) -> None:
        ins = ListExt([["short"], [[["longer_test"]]]])
        assert ins.max_item_len(recursive=True) == 11
