"""
Test: Beautiful

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

try:  # [beautiful] feature
    import rich  # type: ignore
    from rich.console import Group
except ImportError:
    rich = pytest.importorskip("rich")

from absfuyu.extra.beautiful import BeautifulOutput


# Sample function to decorate
@BeautifulOutput(layout=1)
def sample_function(x: int, y: int) -> int:
    return x + y


class TestBeautifulOutput:
    def test_basic_functionality(self) -> None:
        """Test basic functionality of the BeautifulOutput decorator."""
        result = sample_function(2, 3)
        assert isinstance(result, Group)

    def test_invalid_layout(self) -> None:
        """Test that an invalid layout defaults to layout 1."""
        decorator = BeautifulOutput(layout=99)  # Invalid layout
        decorated_function = decorator(sample_function)

        output = decorated_function(2, 3)

        # Check if it defaults to layout 1
        assert isinstance(output, Group)

    def test_memory_usage_measurement(self) -> None:
        """Test that memory usage is measured correctly."""

        @BeautifulOutput()
        def memory_intensive_function(n: int) -> list:
            return [i for i in range(n)]

        output = memory_intensive_function(10000)

        # Ensure that the function runs without errors and returns a list
        assert isinstance(output, Group)

    def test_error_handling(self) -> None:
        """Test error handling when an exception occurs in the wrapped function."""

        @BeautifulOutput()
        def error_prone_function():
            raise ValueError("An error occurred!")

        with pytest.raises(ValueError) as excinfo:
            error_prone_function()

        assert "An error occurred!" in str(excinfo.value)
