"""
Test: Data extension - Text

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.dxt import Text, TextAnalyzeDictFormat


@pytest.fixture
def example_long_text():
    return Text(
        "This is an extremely long text that even surpass my expectation and the rest of this text probably contains some useless stuff"
    )


@pytest.mark.abs_dxt
class TestText:
    """absfuyu.dxt.Text"""

    # analyze
    @pytest.mark.parametrize(
        ["value", "output"],
        [
            (
                "Lmao",
                {
                    "digit": 0,
                    "uppercase": 1,
                    "lowercase": 3,
                    "other": 0,
                },
            ),
            ("Lmao$$TEST.", {"digit": 0, "uppercase": 5, "lowercase": 3, "other": 3}),
        ],
    )
    def test_analyze(self, value: str, output: TextAnalyzeDictFormat) -> None:
        assert Text(value).analyze() == output

    # hex
    def test_to_hex(self) -> None:
        assert Text("Hello World").to_hex(raw=True) == "48656c6c6f20576f726c64"
        assert (
            Text("Hello World").to_hex()
            == "\\x48\\x65\\x6c\\x6c\\x6f\\x20\\x57\\x6f\\x72\\x6c\\x64"
        )

    # pangram
    @pytest.mark.parametrize(
        ["value", "output"],
        [
            ("abcdeFghijklmnopqrstuvwxyz", True),
            ("abcdefghijklmnOpqrstuvwxy", False),
            ("abcdeFghijklmnopqrstuvwxyzsdsd", True),
            ("abcdeFghijklmnopqrs tuvwxyzsdsd0", True),
        ],
    )
    def test_is_pangram(self, value: str, output: bool) -> None:
        assert Text(value).is_pangram() is output

    def test_is_pangram_custom(self) -> None:
        custom_alphabet = {"a", "b", "c"}
        assert Text("abc").is_pangram(custom_alphabet) is True
        assert Text("ab").is_pangram(custom_alphabet) is False
        assert Text("abcd").is_pangram(custom_alphabet) is True

    # palindrome
    @pytest.mark.parametrize(
        ["value", "output"], [("madam", True), ("racecar", True), ("bomb", False)]
    )
    def test_is_palindrome(self, value: str, output: bool) -> None:
        assert Text(value).is_palindrome() is output

    # reverse
    def test_reverse(self) -> None:
        assert Text("abc").reverse() == "cba"

    # random capslock
    @pytest.mark.parametrize("value", ["random", "capslock"])
    def test_random_capslock(self, value: str) -> None:
        test_0_percent: list[Text] = [
            Text(value).random_capslock(0) for _ in range(1000)
        ]
        test_50_percent: list[Text] = [
            Text(value).random_capslock(50) for _ in range(1000)
        ]
        test_100_percent: list[Text] = [
            Text(value).random_capslock(100) for _ in range(1000)
        ]
        assert len(list(set(test_0_percent))) == 1
        assert len(list(set(test_100_percent))) == 1
        assert Text(value).random_capslock(0) == value.lower()
        assert Text(value).random_capslock(100) == value.upper()

        try:
            assert len(list(set(test_50_percent))) != 1
            assert (
                Text(value).random_capslock(50) != value.lower()
                and Text(value).random_capslock(50) != value.upper()
            )
        except Exception as e:
            assert str(e)

    # divide
    def test_divide(self, example_long_text: Text) -> None:
        assert example_long_text.divide().__len__() == 3
        assert example_long_text.divide(string_split_size=10).__len__() == 13

    def test_divide_with_variable(self, example_long_text: Text) -> None:
        assert example_long_text.divide_with_variable(
            split_size=60, custom_var_name="abc"
        ) == [
            "abc1='This is an extremely long text that even surpass my expectat'",
            "abc2='ion and the rest of this text probably contains some useless'",
            "abc3=' stuff'",
            "abc=abc1+abc2+abc3",
            "abc",
        ]

    def test_divide_with_variable_2(self, example_long_text: Text) -> None:
        """Check for list len"""
        assert (
            example_long_text.divide_with_variable(
                split_size=60, custom_var_name="abc"
            ).__len__()
            == 5
        )

    # to list
    def test_to_list(self) -> None:
        assert isinstance(Text("test").to_list(), list)
        # assert isinstance(Text("test").to_listext(), ListExt)

    # count pattern
    @pytest.mark.parametrize("value", ["Test sentence"])
    @pytest.mark.parametrize(
        ["pattern", "output"],
        [("ten", 1), ("t", 2), ("a", 0)],
    )
    def test_count_pattern(self, value: str, pattern: str, output: int) -> None:
        assert Text(value).count_pattern(pattern) == output

    def test_count_pattern_2(self) -> None:
        assert Text("Test sentence").count_pattern("t", ignore_capslock=True) == 3

    def test_count_pattern_error(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            Text("Test").count_pattern("tenss")
        assert str(excinfo.value)

    # hapax
    def test_hapax(self) -> None:
        assert Text("A a. a, b c c= C| d d").hapax() == [
            "a",
            "a.",
            "a,",
            "b",
            "c",
            "c=",
            "c|",
        ]

    def test_hapax_2(self) -> None:
        assert Text("A a. a, b c c= C| d d").hapax(strict=True) == ["b"]

    # shorten
    def test_shorten(self, example_long_text: Text) -> None:
        example_long_text.shorten()

    def test_shorten_negative_parameter(self, example_long_text: Text) -> None:
        example_long_text.shorten(-99)
