"""
Test: Inspector

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from typing import Any

import pytest

from absfuyu.core import BaseClass
from absfuyu.tools.inspector import Inspector
from absfuyu.typings import T as _T


def dummy_function(param: _T, *args, **kwargs):
    """This is a docstring"""
    pass


@pytest.fixture
def test_class():
    class TestClass(BaseClass):
        """a docs

        Extra part
        that very longgggggggggggggggggggggggggggggggggggggg
        gggggggggggggggggggggggggggggggggggggggggggggggggggg
        """

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.help = True
            self._hidden = True
            self.__hidden = True
            self.args = args

            for k, v in kwargs.items():
                setattr(self, k, v)

        @property
        def property_name(self): ...

        @property
        def _property_name(self): ...

        @property
        def __property_name(self): ...

        @classmethod
        def class_method_name(cls): ...

        @classmethod
        def _class_method_name(cls): ...

        @classmethod
        def __class_method_name(cls): ...

        @staticmethod
        def static_method_name(): ...

        @staticmethod
        def _static_method_name(): ...

        @staticmethod
        def __static_method_name(): ...

        def normal_method(self): ...
        def _normal_method(self): ...
        def __normal_method(self): ...

    return TestClass


@pytest.mark.abs_tools
class TestInspector:
    def test_1(self, test_class) -> None:
        pass
