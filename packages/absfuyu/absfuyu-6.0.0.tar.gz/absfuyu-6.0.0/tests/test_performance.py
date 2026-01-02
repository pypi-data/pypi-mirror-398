"""
Test: Util - Performance

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import pytest

from absfuyu.util.performance import retry


@pytest.mark.abs_util
class TestUtilPerformance:
    """absfuyu.util.performance"""

    # retry
    def test_retry_invalid_parameters(self):
        with pytest.raises(
            ValueError, match="retries must be >= 1, delay must be >= 0"
        ):

            @retry(retries=0)
            def invalid_function():
                pass

        with pytest.raises(
            ValueError, match="retries must be >= 1, delay must be >= 0"
        ):

            @retry(retries=3, delay=-1)
            def invalid_function():
                pass

    def test_retry_success(self) -> None:
        @retry(retries=3, delay=0.1)
        def success_function():
            return "Success"

        result = success_function()
        assert result == "Success"

    @pytest.mark.xfail
    def test_retry_failure(self) -> None:
        with pytest.raises(Exception, match="Function error") as excinfo:

            @retry(retries=3, delay=0.1)
            def failing_function():
                raise Exception("Function error")

            failing_function()
        assert str(excinfo.value)

    def test_retry_with_valid_retries(self) -> None:
        @retry(retries=2, delay=0.1)
        def intermittent_failure():
            if intermittent_failure.call_count < 1:
                intermittent_failure.call_count += 1
                raise Exception("Temporary failure")
            return "Success"

        intermittent_failure.call_count = 0  # Initialize call count

        result = intermittent_failure()

        assert result == "Success"
