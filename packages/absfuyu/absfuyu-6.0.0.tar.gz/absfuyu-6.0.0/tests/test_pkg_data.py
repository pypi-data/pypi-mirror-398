"""
Test: Package Data

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import lzma

import pytest

from absfuyu.pkg_data import BasicLZMAOperation, DataList, DataLoader, Pickler


def test_loadData():
    assert True


class TestPickler:
    def test_load(self) -> None:
        Pickler.load(DataList.CHEMISTRY.value)


class TestBasicLZMAOperation:
    def test_load(self) -> None:
        data = "Test"
        compressed = lzma.compress(data.encode(encoding="utf-8"))
        loaded = BasicLZMAOperation.load(compressed).decode()
        assert loaded == data


class TestDataLoader:
    def test_load(self) -> None:
        DataLoader(DataList.CHEMISTRY).load()
        DataLoader(DataList.TAROT).load()
        DataLoader(DataList.PASSWORDLIB).load()
