"""
Test: Config

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import random

import pytest

from absfuyu.config import ABSFUYU_CONFIG, Setting


# Setting
def test_from_dict():
    _ = Setting.from_dict({"test": {"default": False, "help": "HELP", "value": True}})
    assert True


# Config
class TestConfig:
    def test_add_and_del_setting(self) -> None:
        # Make random name
        name = f"test_add_setting_{random.randint(100_000, 999_999)}"

        # Test add
        old = len(ABSFUYU_CONFIG.settings)
        ABSFUYU_CONFIG.add_setting(name, True, True)
        new = len(ABSFUYU_CONFIG.settings)
        add_result = old < new

        # Test del
        ABSFUYU_CONFIG.del_setting(name)
        new2 = len(ABSFUYU_CONFIG.settings)
        del_result = old == new2

        # Output
        assert all([add_result, del_result])

    def test_toggle_setting(self) -> None:
        setting = "test"
        test_before = ABSFUYU_CONFIG._get_setting(setting).value
        ABSFUYU_CONFIG.toggle_setting(setting)
        test_after = ABSFUYU_CONFIG._get_setting(setting).value
        ABSFUYU_CONFIG.toggle_setting(setting)  # Back to original value
        assert test_before != test_after

    def test_reset_config(self) -> None:
        ABSFUYU_CONFIG.reset_config()
        test = [setting.value == setting.default for setting in ABSFUYU_CONFIG.settings]
        assert all(test)
