"""
Absfuyu: Core
-------------
Decorator

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    "dummy_decorator",
    "dummy_decorator_with_args",
    "add_subclass_methods_decorator",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast, overload

# Type
# ---------------------------------------------------------------------------
P = ParamSpec("P")  # Parameter type
R = TypeVar("R")  # Return type - Can be anything
T = TypeVar("T", bound=type)  # Type type - Can be any subtype of `type`


# Decorator
# ---------------------------------------------------------------------------
@overload
def dummy_decorator(obj: T) -> T: ...
@overload
def dummy_decorator(obj: Callable[P, R]) -> Callable[P, R]: ...
def dummy_decorator(obj: Callable[P, R] | T) -> Callable[P, R] | T:
    """
    This is a decorator that does nothing. Normally used as a placeholder
    """
    if isinstance(obj, type):
        return obj

    @wraps(obj)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return obj(*args, **kwargs)

    return wrapper


def dummy_decorator_with_args(*args, **kwargs):
    """
    This is a decorator with args and kwargs that does nothing. Normally used as a placeholder
    """

    @overload
    def decorator(obj: T) -> T: ...

    @overload
    def decorator(obj: Callable[P, R]) -> Callable[P, R]: ...

    def decorator(obj: Callable[P, R] | T) -> Callable[P, R] | T:
        if isinstance(obj, type):
            return obj

        @wraps(obj)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return obj(*args, **kwargs)

        return wrapper

    return decorator


def add_subclass_methods_decorator(cls: T) -> T:
    """
    Class decorator replace the ``__init_subclass__`` method.

    This method populates a dictionary with subclass names as keys
    and their available methods as values.

    - Create 2 class attributes: ``_METHOD_INCLUDE`` (bool) and ``SUBCLASS_METHODS`` (dict[str, list[str]])
    - Automatically add subclass methods to class variable: ``SUBCLASS_METHODS``
    - Set class attribute ``_METHOD_INCLUDE`` to ``False`` to exclude from ``SUBCLASS_METHODS``

    Example:
    --------
    >>> # Normal behavior
    >>> @add_subclass_methods_decorator
    >>> class TestParent: ...
    >>> class TestChild(TestParent):
    ...     def method1(self): ...
    >>> TestChild.SUBCLASS_METHODS
    {'__main__.TestChild': ['method1']}

    >>> # Hidden from ``SUBCLASS_METHODS``
    >>> @add_subclass_methods_decorator
    >>> class TestParent: ...
    >>> class TestChildHidden(TestParent):
    ...     _METHOD_INCLUDE = False
    ...     def method1(self): ...
    >>> TestChildHidden.SUBCLASS_METHODS
    {}
    """

    # Check for class
    if not isinstance(cls, type):
        raise ValueError("Object is not a class")

    class AutoSubclassMixin:
        _METHOD_INCLUDE: bool = True  # Include in SUBCLASS_METHODS
        SUBCLASS_METHODS: dict[str, list[str]] = {}

        def __init_subclass__(cls, *args, **kwargs) -> None:
            """
            This create a dictionary with:
            - key   (str)      : Subclass
            - value (list[str]): List of available methods
            """
            super().__init_subclass__(*args, **kwargs)

            if cls._METHOD_INCLUDE and not any(
                [x.endswith(cls.__name__) for x in cls.SUBCLASS_METHODS.keys()]
            ):
                methods_list: list[str] = [
                    k for k, v in cls.__dict__.items() if callable(v)
                ]
                if len(methods_list) > 0:
                    name = f"{cls.__module__}.{cls.__name__}"
                    cls.SUBCLASS_METHODS.update({name: sorted(methods_list)})

    return cast(T, type("AutoSubclass", (AutoSubclassMixin, cls), {}))
