"""
Test: Logger

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import pytest

from absfuyu.logger import compress_for_log


# Test
# ---------------------------------------------------------------------------
def test_list():
    test_list = ["test"] * 200
    assert compress_for_log(test_list)


def test_set():
    test_set = set(range(200))
    assert compress_for_log(test_set)


def test_tuple():
    test_tuple = tuple(["test"] * 200)
    assert compress_for_log(test_tuple)


def test_dict():
    test_dict = dict(zip(range(200), range(200)))
    assert compress_for_log(test_dict)


def test_str():
    test_string = "test\n\n" * 200
    assert compress_for_log(test_string)


def test_object():
    import absfuyu

    assert compress_for_log(absfuyu)
