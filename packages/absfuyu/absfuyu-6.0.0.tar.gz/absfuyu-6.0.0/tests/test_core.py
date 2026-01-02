"""
Test: Core

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from inspect import getdoc
from typing import Any

import pytest

from absfuyu import __version__
from absfuyu.core import BaseClass
from absfuyu.core.baseclass import (
    AutoREPRMixin,
    ClassMembers,
    ClassMembersResult,
    GetClassMembersMixin,
)
from absfuyu.core.decorator import dummy_decorator, dummy_decorator_with_args
from absfuyu.core.docstring import (
    _SPHINX_DOCS_TEMPLATE,
    SphinxDocstring,
    SphinxDocstringMode,
)


class ClassToTestDocs:
    clsattr = None

    def method(self, *args, **kwargs):
        """Normal method"""
        pass

    @classmethod
    def cmethod(cls, *args, **kwargs):
        """classmethod"""
        pass

    @staticmethod
    def stmethod(*args, **kwargs):
        """staticmethod"""
        pass

    @property
    def prop(self) -> None:
        pass


# MARK: fixture
@pytest.fixture
def clsmember_test() -> ClassMembers:
    return ClassMembers(["a"], ["b"], ["c"], ["d"], ["e"], ["f"])


@pytest.fixture
def clsmemres_test() -> ClassMembersResult:
    return ClassMembersResult(
        ABC=ClassMembers(["a"], ["b"], ["c"], ["d"]),
        DEF=ClassMembers(["e"], ["f"], ["g"], ["h"]),
    )


# MARK: core.baseclass
@pytest.mark.abs_core
class TestClassMembers:
    """
    ``absfuyu.core.baseclass.ClassMembers``
    """

    def test_repr(self, clsmember_test: ClassMembers) -> None:
        assert (
            repr(clsmember_test)
            == "ClassMembers(methods=['a'], classmethods=['b'], staticmethods=['c'], properties=['d'], attributes=['e'], classattributes=['f'])"
        )

    @pytest.mark.parametrize(
        ["value", "output"],
        [
            (([], [], [], [], [], []), True),
            ((["a"], [], [], [], [], []), False),
            (([], ["b"], [], [], [], []), False),
            (([], [], ["c"], [], [], []), False),
            (([], [], [], ["d"], [], []), False),
            (([], [], [], [], ["e"], []), False),
            (([], [], [], [], [], ["f"]), False),
        ],
    )
    def test_is_empty(self, value: tuple[list, list, list, list], output: bool) -> None:
        assert ClassMembers(*value).is_empty() == output

    @pytest.mark.parametrize(
        ["include_method", "include_classmethod", "include_staticmethod", "expected"],
        [
            (True, True, True, ["a", "b <cls>", "c <stc>"]),
            (False, True, True, ["b <cls>", "c <stc>"]),
            (True, False, True, ["a", "c <stc>"]),
            (True, True, False, ["a", "b <cls>"]),
        ],
    )
    def test_pack(
        self,
        clsmember_test: ClassMembers,
        include_method: bool,
        include_classmethod: bool,
        include_staticmethod: bool,
        expected,
    ) -> None:
        packed = clsmember_test.pack(
            include_method=include_method,
            include_classmethod=include_classmethod,
            include_staticmethod=include_staticmethod,
        )
        assert packed.methods == expected

    @pytest.mark.parametrize(
        ["include_attribute", "include_classattribute", "expected"],
        [
            (True, True, ["e", "f <cls>"]),
            (False, True, ["f <cls>"]),
            (True, False, ["e"]),
            (False, False, []),
        ],
    )
    def test_pack_2(
        self,
        clsmember_test: ClassMembers,
        include_attribute: bool,
        include_classattribute: bool,
        expected,
    ) -> None:
        packed = clsmember_test.pack(
            include_attribute=include_attribute,
            include_classattribute=include_classattribute,
        )
        assert packed.attributes == expected

    def test_pack_custom_indicators(self, clsmember_test: ClassMembers) -> None:
        packed = clsmember_test.pack(
            classmethod_indicator="(classmethod)",
            staticmethod_indicator="(staticmethod)",
        )
        assert packed == ClassMembers(
            ["a", "b (classmethod)", "c (staticmethod)"],
            [],
            [],
            ["d"],
            ["e", "f <cls>"],
        )


@pytest.mark.abs_core
class TestClassMembersResult:
    """
    ``absfuyu.core.baseclass.ClassMembersResult``
    """

    @pytest.mark.parametrize(
        ["value", "output"],
        [
            ("methods", ["a", "e"]),
            ("classmethods", ["b", "f"]),
            ("staticmethods", ["c", "g"]),
            ("properties", ["d", "h"]),
        ],
    )
    def test_merge_value(
        self,
        clsmemres_test: ClassMembersResult,
        value: str,
        output: list[str],
    ) -> None:
        assert clsmemres_test._merge_value(value) == output

    def test_flatten_value(self, clsmemres_test: ClassMembersResult) -> None:
        flattened = clsmemres_test.flatten_value()
        assert flattened == ClassMembers(["a", "e"], ["b", "f"], ["c", "g"], ["d", "h"])

    @pytest.mark.parametrize(
        ["include_method", "include_classmethod", "include_staticmethod", "expected"],
        [
            (True, True, True, ["a", "b <classmethod>", "c <staticmethod>"]),
            (False, True, True, ["b <classmethod>", "c <staticmethod>"]),
            (True, False, True, ["a", "c <staticmethod>"]),
            (True, True, False, ["a", "b <classmethod>"]),
        ],
    )
    def test_pack_value_parameterized(
        self,
        clsmemres_test: ClassMembersResult,
        include_method: bool,
        include_classmethod: bool,
        include_staticmethod: bool,
        expected: list[str],
    ) -> None:
        packed = clsmemres_test.pack_value(
            include_method=include_method,
            include_classmethod=include_classmethod,
            include_staticmethod=include_staticmethod,
        )
        assert packed["ABC"].methods == expected

    @pytest.mark.parametrize(
        ["value", "output"],
        [
            ("methods", {"ABC": ["a"], "DEF": ["e"]}),
            ("classmethods", {"ABC": ["b"], "DEF": ["f"]}),
            ("staticmethods", {"ABC": ["c"], "DEF": ["g"]}),
            ("properties", {"ABC": ["d"], "DEF": ["h"]}),
        ],
    )
    def test_prioritize_value(
        self,
        clsmemres_test: ClassMembersResult,
        value: str,
        output: dict[str, list[str]],
    ) -> None:
        prioritized_methods = clsmemres_test.prioritize_value(value)
        assert prioritized_methods == output


@pytest.mark.abs_core
class TestGetClassMembersMixin:
    """
    ``absfuyu.core.baseclass.GetClassMembersMixin``
    """

    def test_get_method_prop(self) -> None:
        class TestClass(ClassToTestDocs, GetClassMembersMixin): ...

        result = TestClass._get_members(dunder=False)
        assert isinstance(result, ClassMembersResult)
        m = result.flatten_value()
        assert "method" in m.methods
        assert "cmethod" in m.classmethods
        assert "stmethod" in m.staticmethods
        assert "prop" in m.properties
        assert "clsattr" in m.classattributes


@pytest.mark.abs_core
class TestAutoREPRMixin:
    """
    ``absfuyu.core.baseclass.AutoREPRMixin``
    """

    def test_class_no_slots(self) -> None:
        class ClassNoSlots(AutoREPRMixin):
            def __init__(self, a) -> None:
                self.a = a

        instance = ClassNoSlots(1)
        name = instance.__class__.__name__
        expected = f"{name}(a={instance.a!r})"
        assert repr(instance) == expected

    def test_class_with_slots(self) -> None:
        class ClassWithSlots(AutoREPRMixin):
            __slots__ = ("a",)

            def __init__(self, a) -> None:
                self.a = a

        instance = ClassWithSlots(1)
        name = instance.__class__.__name__
        expected = f"{name}(a={instance.a!r})"
        assert repr(instance) == expected


@pytest.mark.abs_core
class TestBaseClass:
    """
    ``absfuyu.core.BaseClass``
    """

    def test_BaseClass(self) -> None:
        _ = BaseClass.show_all_methods(print_result=True)


# MARK: core.decorator
@pytest.mark.abs_core
class TestCoreDecorator:
    def test_dummy_decorator(self) -> None:
        # Define a dummy function to decorate
        def add(a, b):
            return a + b

        # Apply the decorator
        decorated_add = dummy_decorator(add)

        # Test if the decorated function behaves as expected
        assert decorated_add(2, 3) == 5

    def test_dummy_decorator_class(self) -> None:
        # Define a class to decorate (which does nothing)
        class MyClass:
            pass

        # Apply the decorator to the class (should return unchanged)
        DecoratedClass = dummy_decorator(MyClass)

        assert DecoratedClass is MyClass

    def test_dummy_decorator_with_args(self) -> None:
        def multiply(a, b):
            return a * b

        decorator_instance = dummy_decorator_with_args("arg1", kwarg="value")

        decorated_multiply = decorator_instance(multiply)

        assert decorated_multiply(4, 5) == 20

    def test_dummy_decorator_with_args_class(self) -> None:
        class MyOtherClass:
            pass

        decorator_instance_for_class = dummy_decorator_with_args("arg1", kwarg="value")
        DecoratedOtherClass = decorator_instance_for_class(MyOtherClass)

        assert DecoratedOtherClass is MyOtherClass


# MARK: core.docstring
@pytest.mark.abs_core
class TestSphinxDocstring:
    """
    ``absfuyu.core.docstring.SphinxDocstring``
    """

    @pytest.mark.parametrize(
        ["reason", "mode"],
        [
            (None, SphinxDocstringMode.ADDED),
            (None, SphinxDocstringMode.CHANGED),
            (None, SphinxDocstringMode.DEPRECATED),
            ("test", SphinxDocstringMode.ADDED),
            ("test", SphinxDocstringMode.CHANGED),
            ("test", SphinxDocstringMode.DEPRECATED),
        ],
    )
    def test_SphinxDocstring_function(
        self, reason: str | None, mode: SphinxDocstringMode
    ) -> None:
        # Create a function with decorator
        @SphinxDocstring(__version__, reason=reason, mode=mode)
        def demo_function(parameter: Any) -> Any:
            return parameter

        @SphinxDocstring(__version__, reason=reason, mode=mode)
        def demo_function_2(parameter: Any) -> Any:
            """This already has docs"""
            return parameter

        # Get template
        _reason = f": {reason}" if reason else ""
        template = _SPHINX_DOCS_TEMPLATE.substitute(
            line_break="",
            mode=mode.value,
            version=__version__,
            reason=_reason,
        )

        for func in [demo_function, demo_function_2]:
            # Get docstring
            docs: str = getdoc(func)
            # Assert
            assert docs.endswith(template)

    @pytest.mark.parametrize(
        ["reason", "mode"],
        [
            (None, SphinxDocstringMode.ADDED),
            (None, SphinxDocstringMode.CHANGED),
            (None, SphinxDocstringMode.DEPRECATED),
            ("test", SphinxDocstringMode.ADDED),
            ("test", SphinxDocstringMode.CHANGED),
            ("test", SphinxDocstringMode.DEPRECATED),
        ],
    )
    def test_SphinxDocstring_class(
        self, reason: str | None, mode: SphinxDocstringMode
    ) -> None:
        @SphinxDocstring(__version__, reason=reason, mode=mode)
        class KlassNoDoc(ClassToTestDocs): ...

        @SphinxDocstring(__version__, reason=reason, mode=mode)
        class KlassWithDoc(ClassToTestDocs):
            """
            This is a doc
            """

            pass

        @SphinxDocstring(__version__, reason=reason, mode=mode)
        class SubClass(KlassNoDoc): ...

        test_list: list[ClassToTestDocs] = [KlassNoDoc, KlassWithDoc, SubClass]
        for k in test_list:
            docs: str = getdoc(k)  # Get docstring
            _reason = f": {reason}" if reason else ""
            template = _SPHINX_DOCS_TEMPLATE.substitute(
                line_break="",
                mode=mode.value,
                version=__version__,
                reason=_reason,
            )  # Retrive template str

            to_test = all(
                [
                    k.__doc__.endswith(template),
                    k().__doc__.endswith(template),
                    k.cmethod.__doc__ == ClassToTestDocs.cmethod.__doc__,
                    k().cmethod.__doc__ == ClassToTestDocs().cmethod.__doc__,
                    k.stmethod.__doc__ == ClassToTestDocs.stmethod.__doc__,
                    k().stmethod.__doc__ == ClassToTestDocs().stmethod.__doc__,
                    k.method.__doc__ == ClassToTestDocs.method.__doc__,
                    k().method.__doc__ == ClassToTestDocs().method.__doc__,
                ]
            )
            assert docs.endswith(template)
            assert to_test
