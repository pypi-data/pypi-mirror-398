"""
Test: Fun

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.fun import human_year_to_dog_year, zodiac_sign
from absfuyu.fun.tarot import Tarot, TarotCard


@pytest.mark.abs_fun
class TestFunZodiac:
    """absfuyu.fun.zodiac_sign()"""

    def test_zodiac(self) -> None:
        assert zodiac_sign(1, 1) == "Capricorn (E)"

    def test_zodiac_2(self) -> None:
        assert zodiac_sign(1, 1, zodiac13=True) == "Sagittarius"


@pytest.mark.abs_fun
class TestFunHumanYearToDogYear:
    """absfuyu.fun.human_year_to_dog_year()"""

    def test_first_year(self) -> None:
        assert human_year_to_dog_year(1) == 15

    def test_second_year(self) -> None:
        assert human_year_to_dog_year(2) == 24

    def test_small_dog_after_second_year(self) -> None:
        assert human_year_to_dog_year(3, is_small=True) == 28
        assert human_year_to_dog_year(10, is_small=True) == 56

    def test_large_dog_after_second_year(self) -> None:
        assert human_year_to_dog_year(3, is_small=False) == 29
        assert human_year_to_dog_year(10, is_small=False) == 64

    def test_float_input(self) -> None:
        assert human_year_to_dog_year(1.5) == 19.5
        assert human_year_to_dog_year(2.5) == 26.0
        assert human_year_to_dog_year(3.5, is_small=True) == 30
        assert human_year_to_dog_year(3.5, is_small=False) == 31.5

    def test_negative_input(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            human_year_to_dog_year(-1)
        assert "Value must be positive" in str(excinfo.value)

    def test_zero_input(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            human_year_to_dog_year(-0.1)
        assert "Value must be positive" in str(excinfo.value)


@pytest.mark.abs_fun
class TestFunTarot:
    """absfuyu.fun.tarot.Tarot"""

    def test_tarot(self) -> None:
        assert isinstance(Tarot().random_card(), TarotCard)
