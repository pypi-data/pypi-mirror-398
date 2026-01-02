"""
Test: Data extension - IntExt

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.dxt import IntExt


@pytest.fixture
def num_a():
    return IntExt(5)


@pytest.fixture
def num_b():
    return IntExt(10)


@pytest.fixture
def num_prime():
    return IntExt(79)


@pytest.mark.abs_dxt
class TestIntExt:
    """absfuyu.dxt.IntExt"""

    # operation
    def test_operation(self, num_a: IntExt, num_b: IntExt) -> None:
        assert num_a + num_b == 15  # add
        assert num_a - num_b == -5  # subtract
        assert num_a * num_b == 50  # multiply
        assert num_a / num_b == 0.5  # divide
        assert (num_a > num_b) is False  # comparison

    # binary
    @pytest.mark.parametrize(
        ["number", "output"], [(10, "1010"), (10, format(10, "b"))]
    )
    def test_to_binary(self, number: int, output: str) -> None:
        instance: IntExt = IntExt(number)
        assert instance.to_binary() == output

    # reverse
    @pytest.mark.parametrize(["number", "output"], [(10, 1), (5, 5), (79, 97)])
    def test_to_reverse(self, number: int, output: int) -> None:
        instance: IntExt = IntExt(number)
        assert instance.reverse() == output

    # prime
    @pytest.mark.parametrize(["number", "output"], [(79, True), (33, False)])
    def test_is_prime(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_prime() is output

    @pytest.mark.parametrize(["number", "output"], [(79, True), (53, False)])
    def test_is_twisted_prime(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_twisted_prime() is output

    @pytest.mark.parametrize(["number", "output"], [(797, True), (79, False)])
    def test_is_palindromic_prime(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_palindromic_prime() is output

    # perfect
    @pytest.mark.parametrize(["number", "output"], [(28, True), (22, False)])
    def test_is_perfect(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_perfect() is output

    # narcissistic
    @pytest.mark.parametrize(["number", "output"], [(371, True), (46, False)])
    def test_is_narcissistic(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_narcissistic() is output

    # palindromic
    @pytest.mark.parametrize(["number", "output"], [(12321, True), (1231, False)])
    def test_is_palindromic(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_palindromic() is output

    # degree
    def test_convert_degree(self, num_a: IntExt) -> None:
        assert num_a.to_celcius_degree() == -15.0
        assert num_a.to_fahrenheit_degree() == 41.0

    # even
    @pytest.mark.parametrize(["number", "output"], [(2, True), (3, False)])
    def test_is_even(self, number: int, output: bool) -> None:
        instance: IntExt = IntExt(number)
        assert instance.is_even() is output

    # lcm
    def test_lcm(self, num_a: IntExt) -> None:
        assert num_a.lcm(6) == 30

    # gcd
    def test_gcd(self, num_a: IntExt) -> None:
        assert num_a.gcd(25) == 5

    # add_to_one_digit
    def test_add_to_one_digit(self, num_prime: IntExt) -> None:
        assert num_prime.add_to_one_digit() == 7

    @pytest.mark.parametrize(["number", "output"], [(1091, 11), (994, 22)])
    def test_add_to_one_digit_2(self, number: int, output: int) -> None:
        instance = IntExt(number)
        assert instance.add_to_one_digit(master_number=True) == output

    # analyze
    def test_analyze(self) -> None:
        assert IntExt(51564).analyze()

    # prime factor
    def test_prime_factor(self) -> None:
        assert IntExt(884652).prime_factor(short_form=False) == [2, 2, 3, 73721]

    # divisible_list
    def test_divisible_list(self) -> None:
        assert IntExt(884652).divisible_list() == [
            1,
            2,
            3,
            4,
            6,
            12,
            73721,
            147442,
            221163,
            294884,
            442326,
            884652,
        ]

    # split
    @pytest.mark.parametrize(
        ["parts", "output"],
        [
            (-10, [5]),
            (1, [5]),
            (2, [2, 3]),
            (5, [1, 1, 1, 1, 1]),
            (6, [0, 1, 1, 1, 1, 1]),
        ],
    )
    def test_split(self, num_a: IntExt, parts: int, output: list[int]) -> None:
        assert num_a.split(parts=parts) == output
