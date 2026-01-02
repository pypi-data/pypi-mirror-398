"""
Absfuyu: Sort
-------------
Sort Module

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Sort
    "selection_sort",
    "insertion_sort",
    # Search
    "linear_search",
    "binary_search",
]


# Library
# ---------------------------------------------------------------------------
from typing import Any


# Functions
# ---------------------------------------------------------------------------
def selection_sort[T](iterable: list[T], reverse: bool = False) -> list[T]:
    """
    Sort the list with selection sort (bubble sort) algorithm

    Parameters
    ----------
    iterable : list
        List that want to be sorted

    reverse : bool
        | if ``True``: sort in descending order
        | if ``False``: sort in ascending order
        | (default: ``False``)

    Returns
    -------
    list
        sorted list
    """

    if reverse:  # descending order
        for i in range(len(iterable)):
            for j in range(i + 1, len(iterable)):
                if iterable[i] < iterable[j]:
                    iterable[i], iterable[j] = iterable[j], iterable[i]
        return iterable

    else:  # ascending order
        for i in range(len(iterable)):
            for j in range(i + 1, len(iterable)):
                if iterable[i] > iterable[j]:
                    iterable[i], iterable[j] = iterable[j], iterable[i]
        return iterable


def insertion_sort[T](iterable: list[T]) -> list[T]:
    """
    Sort the list with insertion sort algorithm

    Parameters
    ----------
    iterable : list
        List that want to be sorted

    Returns
    -------
    list
        sorted list (ascending order)
    """

    for i in range(1, len(iterable)):
        key = iterable[i]
        j = i - 1
        while j >= 0 and key < iterable[j]:
            iterable[j + 1] = iterable[j]
            j -= 1
        iterable[j + 1] = key
    return iterable


def linear_search(iterable: list, key: Any) -> int:
    """
    Returns the position of ``key`` in the list

    Parameters
    ----------
    iterable : list
        List want to search

    key: Any
        Item want to find

    Returns
    -------
    int
        The position of ``key`` in the list if found, ``-1`` otherwise
    """
    for i, item in enumerate(iterable):
        if item == key:
            return i
    return -1


def binary_search(iterable: list, key: Any) -> int:
    """
    Returns the position of ``key`` in the list (list must be sorted)

    Parameters
    ----------
    iterable : list
        List want to search

    key: Any
        Item want to find

    Returns
    -------
    int
        The position of ``key`` in the list if found, ``-1`` otherwise
    """
    left = 0
    right = len(iterable) - 1
    while left <= right:
        middle = (left + right) // 2

        if iterable[middle] == key:
            return middle
        if iterable[middle] > key:
            right = middle - 1
        if iterable[middle] < key:
            left = middle + 1
    return -1
