"""
Absfuyu: Data Extension
-----------------------
Base type expansion

Version: 6.0.0
Date updated: 28/11/2025 (dd/mm/yyyy)
"""

# from __future__ import annotations

# Module Package
# ---------------------------------------------------------------------------
__all__ = []


# Library
# ---------------------------------------------------------------------------
from abc import ABC
from typing import Generic, Self, TypeVar

# Class
# ---------------------------------------------------------------------------
T = TypeVar("T")


class BaseType(Generic[T], ABC):
    """
    A universal base class for creating custom immutable type wrappers.

    Features:
    ----------
    - Works with any immutable type (int, str, float, etc.)
    - Provides validation hook via `_validate`
    - Automatically infers the base type from generic argument


    Example:
    --------
    >>> class NonNegativeInt(BaseType[int], int):
    >>>     @classmethod
    >>>     def _validate(cls, value: int) -> None:
    >>>         if value < 0:
    >>>             raise ValueError("Value must be non-negative")
    """

    # Automatically infer `_base_type` when subclassed
    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)

        # print(getattr(cls, "__orig_bases__", []))
        for base in getattr(cls, "__orig_bases__", []):
            if hasattr(base, "__args__") and base.__args__:
                cls._base_type: type[T] = base.__args__[0]
                break
        else:
            raise TypeError(f"{cls.__name__} must specify a generic base type, e.g. BaseType[int]")

    def __new__(cls, value: T) -> Self:
        base_type = cls._base_type
        if not isinstance(value, base_type):
            raise TypeError(f"{cls.__name__} must be initialized with {base_type.__name__}, got {type(value).__name__}")
        cls._validate(value)
        return base_type.__new__(cls, value)  # type: ignore

    @classmethod
    def _validate(cls, value: T) -> None:
        """Override this in subclasses to add custom validation."""
        pass

    def __repr__(self) -> str:
        # base_name = self._base_type.__name__
        # return f"{self.__class__.__name__}({base_name}={self._base_type(self)!r})"  # type: ignore
        return f"{self.__class__.__name__}({self._base_type(self)!r})"  # type: ignore


class IntBase(BaseType[int], int):
    """
    A base class for creating custom integer-like types.
    Provides a hook for validation and extension.

    Parameters
    ----------
    value : int
        Int value


    Usage:
    ------
    Use ``_validate(cls, value: int) -> None:`` classmethod to create custom validator
    """

    pass
