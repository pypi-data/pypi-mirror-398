"""
Test: Util - API

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import sys

import pytest

try:
    import requests  # type: ignore
except ImportError:
    requests = pytest.importorskip("requests")

from absfuyu.util.api import APIRequest, PingResult, ping_windows


@pytest.mark.abs_util
class TestUtilAPI:
    """absfuyu.util.api"""

    def test_API(self, mocker) -> None:
        mock_APIRequest = mocker.Mock(spec=APIRequest)  # Mock APIRequest
        mock_APIRequest.fetch_data_only.return_value.json.return_value = {
            "quotes": ["a", "b"]
        }

        instance: APIRequest = mock_APIRequest
        assert isinstance(instance.fetch_data_only().json()["quotes"], list)

    @pytest.mark.skipif(
        sys.platform not in ["win32", "cygwin"],
        reason="Not applicable on Linux and MacOS",
    )  # windows only
    def test_ping_windows(self, mocker) -> None:
        mock_ping = mocker.patch("absfuyu.util.api.ping_windows")
        mock_ping.return_value = [PingResult("", "")]
        res = mock_ping(["google.com"], 1)
        assert isinstance(res[0], PingResult)
