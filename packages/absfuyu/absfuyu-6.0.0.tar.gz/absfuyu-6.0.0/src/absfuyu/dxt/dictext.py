"""
Absfuyu: Data Extension
-----------------------
dict extension

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from __future__ import annotations

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["DictExt", "DictAnalyzeResult"]


# Library
# ---------------------------------------------------------------------------
import operator
from collections.abc import Callable
from typing import Any, Literal, NamedTuple, Self, TypeVar, overload

from absfuyu.core import GetClassMembersMixin, versionadded, versionchanged

# from absfuyu.typings import KT as _KT
# from absfuyu.typings import VT as _VT


# Type
# ---------------------------------------------------------------------------
KT = TypeVar("KT")
VT = TypeVar("VT")
VT2 = TypeVar("VT2")
R = TypeVar("R")  # Return type - Can be anything


# Class
# ---------------------------------------------------------------------------
class DictAnalyzeResult(NamedTuple):
    """
    Result for ``DictExt.analyze()``
    """

    max_value: int | float
    min_value: int | float
    max_list: list
    min_list: list


class DictExtLegacy(GetClassMembersMixin, dict[KT, VT]):
    """
    ``dict`` extension (with no generic type-hints)

    >>> # For a list of new methods
    >>> DictExt.show_all_methods()
    """

    @versionchanged("3.3.0", reason="Updated return type")
    def analyze(self) -> DictAnalyzeResult:
        """
        Analyze all the key values (``int``, ``float``)
        in ``dict`` then return highest/lowest index

        Returns
        -------
        dict
            Analyzed data


        Example:
        --------
        >>> test = DictExt({"abc": 9, "def": 9, "ghi": 8, "jkl": 1, "mno": 1})
        >>> test.analyze()
        DictAnalyzeResult(max_value=9, min_value=1, max_list=[('abc', 9), ('def', 9)], min_list=[('jkl', 1), ('mno', 1)])
        """
        try:
            dct: dict = self.copy()

            max_val: int | float = max(list(dct.values()))
            min_val: int | float = min(list(dct.values()))
            max_list = []
            min_list = []

            for k, v in dct.items():
                if v == max_val:
                    max_list.append((k, v))
                if v == min_val:
                    min_list.append((k, v))

            return DictAnalyzeResult(max_val, min_val, max_list, min_list)

        except TypeError:
            err_msg = "Value must be int or float"
            # logger.error(err_msg)
            raise ValueError(err_msg)  # noqa: B904

    def swap_items(self) -> Self:
        """
        Swap ``dict.keys()`` with ``dict.values()``

        Returns
        -------
        DictExt
            Swapped dict


        Example:
        --------
        >>> test = DictExt({"abc": 9})
        >>> test.swap_items()
        {9: 'abc'}
        """
        # return self.__class__(zip(self.values(), self.keys()))
        return self.__class__({v: k for k, v in self.items()})  # type: ignore

    def apply(self, func: Callable[[Any], Any], apply_to_value: bool = True) -> Self:
        """
        Apply function to ``DictExt.keys()`` or ``DictExt.values()``

        Parameters
        ----------
        func : Callable
            Callable function

        apply_to_value : bool
            | ``True``: Apply ``func`` to ``DictExt.values()``
            | ``False``: Apply ``func`` to ``DictExt.keys()``

        Returns
        -------
        DictExt
            DictExt


        Example:
        --------
        >>> test = DictExt({"abc": 9})
        >>> test.apply(str)
        {'abc': '9'}
        """
        if apply_to_value:
            new_dict = {k: func(v) for k, v in self.items()}
        else:
            new_dict = {func(k): v for k, v in self.items()}
        return self.__class__(new_dict)

    @versionchanged("5.0.0", reason="Updated to handle more types and operator")
    @versionadded("3.4.0")
    def aggregate(
        self,
        other_dict: dict[KT, VT],
        default_value: Any = 0,
        operator_func: Callable[[Any, Any], Any] = operator.add,  # operator add
    ) -> Self:
        """
        Aggregates the values of the current dictionary with another dictionary.

        For each unique key, this method applies the specified operator to the values
        from both dictionaries. If a key exists in only one dictionary, its value is used.
        If an error occurs during aggregation (e.g., incompatible types), the values
        from both dictionaries are returned as a list.

        Parameters
        ----------
        other_dict : dict
            The dictionary to aggregate with.

        default_value : Any, optional
            The value to use for missing keys, by default ``0``


        operator_func : Callable[[Any, Any], Any], optional
            A function that takes two arguments and returns a single value,
            by default ``operator.add``

        Returns
        -------
        Self
            A new instance of the aggregated dictionary.


        Example:
        --------
        >>> test = DictExt({"test": 5, "test2": 9})
        >>> agg = {"test1": 10, "test2": 1}
        >>> print(test.aggregate(agg))
        {'test1': 10, 'test': 5, 'test2': 10}

        >>> test = DictExt({"test": 5, "test2": 9})
        >>> agg = {"test1": 10, "test2": "1"}
        >>> print(test.aggregate(agg))
        {'test1': 10, 'test': 5, 'test2': [9, '1']}
        """
        merged_output = {}

        # Create a set of all unique keys from both dictionaries
        all_keys = set(self) | set(other_dict)

        for k in all_keys:
            # Retrieve values with default fallback
            value_self = self.get(k, default_value)
            value_other = other_dict.get(k, default_value)

            try:
                # Attempt to apply the operator for existing keys
                merged_output[k] = operator_func(value_self, value_other)
            except TypeError:
                # If a TypeError occurs (e.g., if values are not compatible), store values as a list
                merged_output[k] = [value_self, value_other]

        return self.__class__(merged_output)


# Type-hints are hard coded, no work around Self[KT, VT] yet
class DictExt(GetClassMembersMixin, dict[KT, VT]):
    """
    ``dict`` extension

    >>> # For a list of new methods
    >>> DictExt.show_all_methods()
    """

    # Analyze
    @versionchanged("3.3.0", reason="Updated return type")
    def analyze(self) -> DictAnalyzeResult:
        """
        Analyze all the key values (``int``, ``float``)
        in ``dict`` then return highest/lowest index

        Returns
        -------
        dict
            Analyzed data


        Example:
        --------
        >>> test = DictExt({"abc": 9, "def": 9, "ghi": 8, "jkl": 1, "mno": 1})
        >>> test.analyze()
        DictAnalyzeResult(max_value=9, min_value=1, max_list=[('abc', 9), ('def', 9)], min_list=[('jkl', 1), ('mno', 1)])
        """
        try:
            dct: dict = self.copy()

            max_val: int | float = max(list(dct.values()))
            min_val: int | float = min(list(dct.values()))
            max_list = []
            min_list = []

            for k, v in dct.items():
                if v == max_val:
                    max_list.append((k, v))
                if v == min_val:
                    min_list.append((k, v))

            return DictAnalyzeResult(max_val, min_val, max_list, min_list)

        except TypeError:
            err_msg = "Value must be int or float"
            # logger.error(err_msg)
            raise ValueError(err_msg)  # noqa: B904

    # Swap
    def swap_items(self) -> DictExt[VT, KT]:
        """
        Swap ``dict.keys()`` with ``dict.values()``

        Returns
        -------
        DictExt
            Swapped dict


        Example:
        --------
        >>> test = DictExt({"abc": 9})
        >>> test.swap_items()
        {9: 'abc'}
        """
        # return self.__class__(zip(self.values(), self.keys()))
        out: dict[VT, KT] = {v: k for k, v in self.items()}
        # return self.__class__({v: k for k, v in self.items()})  # type: ignore
        return self.__class__(out)  # type: ignore

    # Apply
    @overload
    def apply(self, func: Callable[[VT], R]) -> DictExt[KT, R]: ...

    @overload
    def apply(self, func: Callable[[KT], R], apply_to_value: Literal[False] = ...) -> DictExt[R, VT]: ...

    def apply(self, func: Callable[[KT | VT], R], apply_to_value: bool = True) -> DictExt[KT | R, VT | R]:  # type: ignore
        """
        Apply function to ``DictExt.keys()`` or ``DictExt.values()``

        Parameters
        ----------
        func : Callable
            Callable function

        apply_to_value : bool
            | ``True``: Apply ``func`` to ``DictExt.values()``
            | ``False``: Apply ``func`` to ``DictExt.keys()``

        Returns
        -------
        DictExt
            DictExt


        Example:
        --------
        >>> test = DictExt({"abc": 9})
        >>> test.apply(str)
        {'abc': '9'}
        """
        if apply_to_value:
            new_dict_v: dict[KT, R] = {k: func(v) for k, v in self.items()}
            return self.__class__(new_dict_v)  # type: ignore
        else:
            new_dict_k: dict[R, VT] = {func(k): v for k, v in self.items()}
            return self.__class__(new_dict_k)  # type: ignore

    # Aggregate
    @versionchanged("5.0.0", reason="Updated to handle more types and operator")
    @versionadded("3.4.0")
    def aggregate(
        self,
        other_dict: dict[KT, VT | VT2],
        default_value: Any = 0,
        operator_func: Callable[[Any, Any], R] = operator.add,  # operator add
    ):
        """
        Aggregates the values of the current dictionary with another dictionary.

        For each unique key, this method applies the specified operator to the values
        from both dictionaries. If a key exists in only one dictionary, its value is used.
        If an error occurs during aggregation (e.g., incompatible types), the values
        from both dictionaries are returned as a list.

        Parameters
        ----------
        other_dict : dict
            The dictionary to aggregate with.

        default_value : Any, optional
            The value to use for missing keys, by default ``0``


        operator_func : Callable[[Any, Any], Any], optional
            A function that takes two arguments and returns a single value,
            by default ``operator.add``

        Returns
        -------
        Self
            A new instance of the aggregated dictionary.


        Example:
        --------
        >>> test = DictExt({"test": 5, "test2": 9})
        >>> agg = {"test1": 10, "test2": 1}
        >>> print(test.aggregate(agg))
        {'test1': 10, 'test': 5, 'test2': 10}

        >>> test = DictExt({"test": 5, "test2": 9})
        >>> agg = {"test1": 10, "test2": "1"}
        >>> print(test.aggregate(agg))
        {'test1': 10, 'test': 5, 'test2': [9, '1']}
        """
        merged_output: dict[KT, VT | R | list[VT | VT2]] = {}

        # Create a set of all unique keys from both dictionaries
        all_keys = set(self) | set(other_dict)

        for k in all_keys:
            # Retrieve values with default fallback
            value_self = self.get(k, default_value)
            value_other = other_dict.get(k, default_value)

            try:
                # Attempt to apply the operator for existing keys
                merged_output[k] = operator_func(value_self, value_other)
            except TypeError:
                # If a TypeError occurs (e.g., if values are not compatible), store values as a list
                merged_output[k] = [value_self, value_other]  # type: ignore

        return self.__class__(merged_output)  # type: ignore
