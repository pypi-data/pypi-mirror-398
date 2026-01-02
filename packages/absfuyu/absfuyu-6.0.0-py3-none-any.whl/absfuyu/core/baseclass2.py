"""
Absfuyu: Core
-------------
Bases for other features (with library)

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # Class
    "ShowAllMethodsMixinInspectVer",
    # Metaclass
    "PerformanceTrackingMeta",
    # Class decorator
    "positive_class_init_args",
]


# Library
# ---------------------------------------------------------------------------
import time
import tracemalloc
from collections.abc import Callable
from functools import wraps
from inspect import getmro, isfunction
from types import MethodType
from typing import Any, ParamSpec, TypeVar

# Type
# ---------------------------------------------------------------------------
P = ParamSpec("P")  # Parameter type
T = TypeVar("T", bound=type)  # Type type - Can be any subtype of `type`
# R = TypeVar("R")  # Return type


# Class
# ---------------------------------------------------------------------------
class ShowAllMethodsMixinInspectVer:
    @classmethod
    def show_all_methods(
        cls,
        include_classmethod: bool = True,
        classmethod_indicator: str = "<classmethod>",
    ) -> dict[str, list[str]]:
        result = {}
        for base in getmro(cls)[::-1]:
            methods = []
            # for name, attr in inspect.getmembers(base, predicate=callable):
            for name, attr in base.__dict__.items():
                if name.startswith("__"):
                    continue
                if isfunction(attr):
                    methods.append(name)
                # if inspect.ismethod(attr):
                if isinstance(attr, (classmethod, MethodType)) and include_classmethod:
                    methods.append(f"{name} {classmethod_indicator}")
            if methods:
                result[base.__name__] = sorted(methods)
        return result


class UniversalConfigMixin:
    """
    Universal config Mixin

    This use these attributes:
    - _instance_config
    - config

    Example:
    --------
    >>> class Test(UniversalConfigMixin):
    >>>     DEFAULT_CONFIG = {"test": True}
    >>> test = Test(config={"new_key": True})
    >>> print(test.config)
    {'test': True, 'new_key': True}
    """

    DEFAULT_CONFIG = {}

    def __init__(self, **kwargs) -> None:
        try:
            super().__init__(**kwargs)
        except TypeError:
            pass
        # instance override
        self._instance_config = kwargs.get("config", {})

    @property
    def config(self):
        # Priority: instance > class > default
        merged = dict(self.DEFAULT_CONFIG)

        try:
            # merged.update(getattr(self, "CLASS_CONFIG", {}))
            merged.update(self._instance_config)
        except Exception:
            pass

        return merged


# Metaclass
# ---------------------------------------------------------------------------
class PerformanceTrackingMeta(type):
    """
    A metaclass that tracks the instantiation time of classes.

    Usage:
    ------
    >>> class Demo(metaclass=PerformanceTrackingMeta):
    ...     def __init__(self): ...
    >>> Demo()
    --------------------------------------
    Class: Demo
    Memory usage:            0.000000 MB
    Peak memory usage:       0.000008 MB
    Time elapsed:            0.000001 s
    --------------------------------------
    """

    def __new__(mcs, name: str, bases: tuple, attrs: dict[str, Any]):
        """
        Intercepts class creation to wrap the ``__init__`` method.

        Parameters
        ----------
        mcs
            The metaclass

        name : str
            The class name

        bases : tuple
            Tuple of base classes

        attrs : dict[str, Any]
            Dictionary of attributes
        """
        if "__init__" in attrs:
            original_init = attrs["__init__"]

            @wraps(original_init)
            def wrapped_init(self, *args, **kwargs):
                # Performance check
                tracemalloc.start()
                start_time = time.perf_counter()

                # Run __init__()
                original_init(self, *args, **kwargs)

                # Performance stop
                current, peak = tracemalloc.get_traced_memory()
                end_time = time.perf_counter()
                tracemalloc.stop()
                creation_time = end_time - start_time

                # Print output
                print(
                    f"{''.ljust(38, '-')}\n"
                    f"Class: {name}\n"
                    f"Memory usage:\t\t {current / 10**6:,.6f} MB\n"
                    f"Peak memory usage:\t {peak / 10**6:,.6f} MB\n"
                    f"Time elapsed:\t\t {creation_time:,.6f} s\n"
                    f"{''.ljust(38, '-')}"
                )

            attrs["__init__"] = wrapped_init
        return super().__new__(mcs, name, bases, attrs)


# Decorator
# ---------------------------------------------------------------------------
def positive_class_init_args(cls: T):
    """
    A class decorator that ensures all arguments in the ``__init__()`` method are positive.
    """
    # original_init: Callable[P, None] | None = getattr(cls, "__init__", None)
    # if original_init is None:
    #     return cls
    try:
        original_init: Callable[P, None] = cls.__init__  # type: ignore
    except AttributeError:
        return cls

    @wraps(original_init)
    def new_init(self, *args: P.args, **kwargs: P.kwargs):
        # Check if all positional arguments are positive
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError(f"Argument {arg} must be positive")

        # Check if all keyword arguments are positive
        for key, value in kwargs.items():
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"Argument {key}={value} must be positive")

        # Call the original __init__ method
        original_init(self, *args, **kwargs)

    # setattr(cls, "__init__", new_init)
    cls.__init__ = new_init  # type: ignore
    return cls
