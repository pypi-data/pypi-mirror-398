"""
Test: Tools - Converter

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import base64

import pytest

from absfuyu.tools.converter import Base64EncodeDecode, Text2Chemistry
from absfuyu.tools.generator import Charset, Generator


@pytest.mark.abs_tools
class TestBase64:
    """absfuyu.tools.converter.Base64EncodeDecode"""

    def test_base64_encode(self) -> None:
        test = Base64EncodeDecode.encode("Hello, World!")
        assert test == "SGVsbG8sIFdvcmxkIQ=="

    def test_base64_decode(self) -> None:
        test = Base64EncodeDecode.decode("SGVsbG8sIFdvcmxkIQ==")
        assert test == "Hello, World!"

    def test_base64_multiple(self) -> None:
        """Run multiple times"""
        TIMES = 100
        test = []
        for x in Generator.generate_string(Charset.FULL, times=TIMES):
            encode = Base64EncodeDecode.encode(x)
            test.append(x == Base64EncodeDecode.decode(encode))
        assert all(test)


@pytest.mark.abs_tools
class TestChemistryConvert:
    """absfuyu.tools.converter.Text2Chemistry"""

    @pytest.mark.parametrize(["value", "output"], [("jump", []), ("queen", [])])
    def test_convert_not_work(self, value: str, output: list) -> None:
        instance = Text2Chemistry()
        assert instance.convert(value) == output

    def test_convert(self) -> None:
        instance = Text2Chemistry()
        assert instance.convert("bakery") != []
