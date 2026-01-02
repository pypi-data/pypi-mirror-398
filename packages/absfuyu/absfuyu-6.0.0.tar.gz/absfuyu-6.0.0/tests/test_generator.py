"""
Test: Generator

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import random
import re
import string
from math import comb

import pytest

from absfuyu.tools.generator import Charset, Generator


class TestGenerator:
    """absfuyu.general.generator.Generator"""

    # Charset
    @pytest.mark.parametrize(
        ["value", "output"],
        [
            (Charset.PRODUCT_KEY, "BCDFGHJKMNPQRTVWXY2346789"),
            (Charset.DEFAULT, string.ascii_letters + string.digits),
        ],
    )
    def test_Charset(self, value: Charset, output: str) -> None:
        assert value == output

    # generate_string
    def test_generate_string(self) -> None:
        """Correct len and a list"""
        temp = Generator.generate_string(
            charset=Charset.DEFAULT,
            size=8,
            times=1,
            unique=False,
            string_type_if_1=False,
        )
        assert isinstance(temp, list) and len(temp[0]) == 8

    def test_generate_string_2(self) -> None:
        """Correct len and a str"""
        temp = Generator.generate_string(
            charset=Charset.DEFAULT,
            size=8,
            times=1,
            unique=False,
            string_type_if_1=True,
        )
        assert isinstance(temp, str) and len(temp) == 8

    def test_generate_string_3(self) -> None:
        """Unique generate"""
        temp = Generator.generate_string(
            charset=Charset.DEFAULT,
            size=2,
            times=600,
            unique=True,
        )
        assert len(temp) == len(list(set(temp)))

    # generate_key
    def test_generate_key(self) -> None:
        """Check if key generate correctly"""
        key = Generator.generate_key(
            charset=Charset.PRODUCT_KEY, letter_per_block=5, number_of_block=5, sep="-"
        )
        key_pattern = r"[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}"
        check_result = re.search(key_pattern, key)  # Correct default key pattern
        correct_len = len(key) == 29  # Correct default key length
        assert check_result is not None and correct_len

    # generate_check_digit
    @pytest.mark.parametrize(
        ["value", "output"],
        [
            (95489683516944151927, 0),
            (15392479156575151882, 1),
            (74662116892282572844, 2),
            (91274812716671415644, 3),
            (94984564168167844561, 4),
            (94273419372476632513, 5),
            (78985469454121383396, 6),
            (34458526632449856638, 7),
            (95486688921998713381, 8),
            (48981383446354864289, 9),
            ("95489683516944151927", 0),
            ([1, 5, 3, 9, 2, 4, 7, 9, 1, 5, 6, 5, 7, 5, 1, 5, 1, 8, 8, 2], 1),
        ],
    )
    def test_generate_check_digit(self, value: int, output: int) -> None:
        assert Generator.generate_check_digit(value) == output

    # combinations range
    def test_combinations_range(self) -> None:
        min_len = random.randrange(1, 3 + 1)
        max_len = random.randrange(3, 5 + 1)
        random_list = [
            Generator.generate_string(times=1, string_type_if_1=True)
            for _ in range(max_len)
        ]
        # print(min_len, max_len, random_list, comb(max_len, min_len))
        test = Generator.combinations_range(
            random_list, min_len=min_len, max_len=max_len
        )
        len_of_generated_combinations = len(test)
        calculated_total_combinations = sum(
            [comb(max_len, i) for i in range(min_len, max_len + 1)]
        )
        assert len_of_generated_combinations == calculated_total_combinations
