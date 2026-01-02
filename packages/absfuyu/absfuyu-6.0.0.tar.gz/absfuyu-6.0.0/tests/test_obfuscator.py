"""
Test: Tools - Obfuscator

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import base64

import pytest

from absfuyu.tools.obfuscator import Obfuscator, StrShifter


@pytest.fixture
def obfuscator_instance():
    code = "print('Hello World')"
    return Obfuscator(code=code)


@pytest.fixture
def str_shifter():
    """Fixture for creating a StrShifter instance."""
    return StrShifter("abcde", shift_by=2)


@pytest.mark.abs_tools
class TestObfuscator:
    """absfuyu.tools.obfuscator"""

    def test_convert_to_base64_decode(self) -> None:
        assert eval(Obfuscator._convert_to_base64_decode("rot_13")) == "rot_13"

    def test_obfuscate(self, obfuscator_instance: Obfuscator) -> None:
        assert obfuscator_instance.obfuscate()


@pytest.mark.abs_tools
class TestStrShifter:
    """absfuyu.tools.obfuscator.StrShifter"""

    def test_shift(self, str_shifter: StrShifter) -> None:
        """Test shifting characters."""
        result = str_shifter.shift()
        assert result == "deabc"

    def test_shift_with_different_shift(self, str_shifter: StrShifter) -> None:
        """Test shifting with a different shift value."""
        str_shifter.shift_by = 1
        result = str_shifter.shift()
        assert result == "eabcd"

    def test_shift_with_large_shift_value(self) -> None:
        """Test shifting with a shift value larger than string length."""
        shifter = StrShifter("abcde", shift_by=7)
        result = shifter.shift()
        assert result == "deabc"  # Same as shifting by 2

    def test_shift_with_zero_shift(self) -> None:
        """Test shifting with a zero shift value."""
        shifter = StrShifter("abcde", shift_by=0)
        result = shifter.shift()
        assert result == "abcde"  # No change

    def test_empty_string(self) -> None:
        """Test behavior with an empty string."""
        shifter = StrShifter("", shift_by=3)
        result = shifter.shift()
        assert result == ""  # Should remain empty

    def test_single_character(self) -> None:
        """Test behavior with a single character string."""
        shifter = StrShifter("a", shift_by=5)
        result = shifter.shift()
        assert result == "a"  # Should remain the same

    def test_special_characters(self) -> None:
        """Test shifting with special characters."""
        shifter = StrShifter("!@#$%", shift_by=3)
        result = shifter.shift()
        assert result == "$#%@!"  # Shift special characters

    def test_numeric_characters(self) -> None:
        """Test shifting with numeric characters."""
        shifter = StrShifter("12345", shift_by=2)
        result = shifter.shift()
        assert result == "45123"  # Shift numeric characters

    def test_invalid_type(self) -> None:
        """Test behavior with invalid input type."""
        with pytest.raises(TypeError, match="Value must be an instance of str"):
            StrShifter(123, shift_by=2)  # Should raise TypeError for non-string input
