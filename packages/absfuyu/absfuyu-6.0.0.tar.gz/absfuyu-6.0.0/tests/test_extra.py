"""
Test: Extra

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import pytest

from absfuyu import extra as ext


def test_ext_load():
    assert ext.is_loaded() is True
