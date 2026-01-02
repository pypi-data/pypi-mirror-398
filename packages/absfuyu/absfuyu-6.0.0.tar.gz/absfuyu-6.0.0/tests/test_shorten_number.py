"""
Test: Util - Shorten number

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.util.shorten_number import CommonUnitSuffixesFactory, Decimal


@pytest.mark.abs_util
class TestUtilShortenNumber:
    """absfuyu.util.shorten_number"""

    @pytest.mark.parametrize(["value", "output"], [(1000, 1.0), (1000000, 1.0)])
    def test_number(self, value: int | float, output: float) -> None:
        ins = Decimal.number(value)
        assert ins.value == output

    def test_number2(self) -> None:
        fac = CommonUnitSuffixesFactory.NUMBER
        unit = 1
        for i, suffix in enumerate(fac.short_name):
            unit = fac.base**i
            assert Decimal.number(unit).suffix == suffix

    def test_data_size(self) -> None:
        fac = CommonUnitSuffixesFactory.DATA_SIZE
        unit = 1
        for i, suffix in enumerate(fac.short_name):
            unit = fac.base**i
            assert Decimal.data_size(unit).suffix == suffix
