"""
Absfuyu: Core
-------------
Pre-defined typing

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # Type
    "T",
    "T_co",
    "T_contra",
    "KT",
    "VT",
    "P",
    "R",
    "_CALLABLE",
    "CT",
    "N",
    "_Number",
    "override",
    # Protocol
    "SupportsShowMethods",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from typing import Any, ParamSpec, Protocol, TypeVar, overload

# Type
# ---------------------------------------------------------------------------
# Types where neither is possible are invariant
# Type safety must be strict
T = TypeVar("T")  # Type invariant
# Type variables that are covariant can be substituted
# with a more specific type without causing errors
# Safe to treat a Box[int] as a Box[object]
T_co = TypeVar("T_co", covariant=True)  # Type covariant
# Type variables that are contravariant can be substituted
# with a more general type without causing errors
# Safe to use a Box[object] where a Box[int] is needed
T_contra = TypeVar("T_contra", contravariant=True)  # Type contravariant

KT = TypeVar("KT")
VT = TypeVar("VT")

# Callable
P = ParamSpec("P")  # Parameter type
R = TypeVar("R")  # Return type - Can be anything
_CALLABLE = Callable[P, R]

# Class type - Can be any subtype of `type`
CT = TypeVar("CT", bound=type)

# Number type
N = TypeVar("N", int, float)  # Must be int or float
_Number = int | float


# Protocol
# ---------------------------------------------------------------------------
class SupportsShowMethods(Protocol):
    """
    Support class with ``show_all_methods()``
    and ``show_all_properties()`` method
    from ``absfuyu.core.basclass.ShowAllMethodsMixin``
    """

    @overload
    @classmethod
    def show_all_methods(cls) -> dict[str, list[str]]: ...

    @overload
    @classmethod
    def show_all_methods(
        cls,
        print_result: bool = False,
        include_classmethod: bool = True,
        classmethod_indicator: str = "<classmethod>",
        include_staticmethod: bool = True,
        staticmethod_indicator: str = "<staticmethod>",
        include_private_method: bool = False,
    ) -> dict[str, list[str]]: ...

    @classmethod
    def show_all_methods(cls, *args, **kwargs) -> Any: ...

    @overload
    @classmethod
    def show_all_properties(cls) -> dict[str, list[str]]: ...

    @overload
    @classmethod
    def show_all_properties(
        cls, print_result: bool = False
    ) -> dict[str, list[str]]: ...

    @classmethod
    def show_all_properties(cls, *args, **kwargs) -> Any: ...


# Note
# ---------------------------------------------------------------------------
# Iterable                               : __iter__
# Iterator(Iterable)                     : __next__, __iter__
# Reversible(Iterable)                   : __reversed__, __iter__
# Sized                                  : __len__
# Container                              : __contains__
# Collection(Sized, Iterable, Container) : __len__, __iter__, __contains__
# Set(Collection)                        : __contains__, __iter__, __len__
# MutableSet(Set)                        : __contains__, __iter__, __len__
# Mapping(Collection)                    : __getitem__, __iter__, and __len__
# MutableMapping(Mapping)                : __getitem__, __setitem__, __delitem__,__iter__, __len__
# Sequence(Reversible, Collection)       : __reversed__, __len__, __iter__, __contains__
# MutableSequence(Sequence)              : __getitem__, __setitem__, __delitem__, __reversed__, __len__, __iter__, __contains__

# Iterable                               : str, dict, list, tuple, set
# Iterator(Iterable)                     : Generator
# Reversible(Iterable)                   : str, dict, list, tuple
# Sized                                  : str, dict, list, tuple, set
# Container                              : str, dict, list, tuple, set
# Collection(Sized, Iterable, Container) : str, dict, list, tuple, set
# Set(Collection)                        : set
# MutableSet(Set)                        : set
# Mapping(Collection)                    : dict
# MutableMapping(Mapping)                : dict
# Sequence(Reversible, Collection)       : str, list, tuple
# MutableSequence(Sequence)              : list

# __iter__: for <...> in <...>
# __len__: len(<...>)
# __contains__: if <...> in <...>
