"""
Absfuyu: Data Extension
-----------------------
list extension

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from __future__ import annotations

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["ListExt"]


# Library
# ---------------------------------------------------------------------------
import operator
import random
from collections import Counter
from collections.abc import Callable, Iterable
from heapq import heapreplace
from itertools import accumulate, chain, count, groupby, zip_longest
from typing import Any, Literal, Self, TypeVar, cast, overload

from absfuyu.core.baseclass import GetClassMembersMixin
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.util import set_min_max

# Type
# ---------------------------------------------------------------------------
T = TypeVar("T")
R = TypeVar("R")  # Return type - Can be anything

# Class
# ---------------------------------------------------------------------------
class ListExt(GetClassMembersMixin, list):
    """
    ``list`` extension

    >>> # For a list of new methods
    >>> ListExt.show_all_methods()
    """

    # Deprecated
    @deprecated("5.2.0", reason="Use ListExt.apply(str) instead")
    def stringify(self) -> Self:
        """
        Convert all item in ``list`` into string

        Returns
        -------
        Self
            A list with all items with type <str`>


        Example:
        --------
        >>> test = ListExt([1, 1, 1, 2, 2, 3])
        >>> test.stringify()
        ['1', '1', '1', '2', '2', '3']
        """
        return self.__class__(map(str, self))

    # Info
    def head(self, number_of_items: int = 5) -> list:
        """
        Show first ``number_of_items`` items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            | Number of items to shows at once
            | (Default: ``5``)

        Returns
        -------
        list
            Filtered list


        Example:
        --------
        >>> ListExt(range(10)).head(2)
        [0, 1]
        """
        number_of_items = int(set_min_max(number_of_items, min_value=0, max_value=len(self)))
        return self[:number_of_items]

    def tail(self, number_of_items: int = 5) -> list:
        """
        Show last ``number_of_items`` items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            | Number of items to shows at once
            | (Default: ``5``)

        Returns
        -------
        list
            Filtered list


        Example:
        --------
        >>> ListExt(range(10)).tail(2)
        [8, 9]
        """
        number_of_items = int(set_min_max(number_of_items, min_value=0, max_value=len(self)))
        return self[::-1][:number_of_items][::-1]

    # Misc
    def apply(self, func: Callable[[Any], Any]) -> Self:
        """
        Apply function to each entry

        Parameters
        ----------
        func : Callable
            Callable function

        Returns
        -------
        Self
            ListExt


        Example:
        --------
        >>> test = ListExt([1, 2, 3])
        >>> test.apply(str)
        ['1', '2', '3']
        """
        # return self.__class__(map(func, self))
        return self.__class__(func(x) for x in self)

    def sorts(self, reverse: bool = False) -> Self:
        """
        Sort all items (with different type) in ``list``

        Parameters
        ----------
        reverse : bool
            - ``True`` then sort in descending order
            - ``False`` then sort in ascending order (default value)

        Returns
        -------
        Self
            A sorted list


        Example:
        --------
        >>> test = ListExt([9, "abc", 3.5, "aaa", 1, 1.4])
        >>> test.sorts()
        [1, 9, 'aaa', 'abc', 1.4, 3.5]
        """
        lst = self.copy()
        type_weights: dict = {}
        for x in lst:
            if type(x) not in type_weights:
                type_weights[type(x)] = len(type_weights)
        # logger.debug(f"Type weight: {type_weights}")

        output = sorted(lst, key=lambda x: (type_weights[type(x)], str(x)), reverse=reverse)

        # logger.debug(output)
        return self.__class__(output)

    @overload
    def freq(self) -> dict: ...  # type: ignore

    @overload
    def freq(
        self,
        sort: bool = False,
        num_of_first_char: int | None = None,
    ) -> dict: ...

    @overload
    def freq(
        self,
        sort: bool = False,
        num_of_first_char: int | None = None,
        appear_increment: Literal[True] = ...,
    ) -> list[int]: ...

    def freq(
        self,
        sort: bool = False,
        num_of_first_char: int | None = None,
        appear_increment: bool = False,
    ) -> dict | list[int]:
        """
        Find frequency of each item in list

        Parameters
        ----------
        sort : bool, optional
            - ``True``: Sorts the output in ascending order
            - ``False``: No sort (default value)

        num_of_first_char : int | None, optional
            | Number of first character taken into account to sort, by default ``None``
            | Eg: ``num_of_first_char = 1``: first character of each item

        appear_increment : bool, optional
            Returns incremental index list of each item when sort,
            by default ``False``

        Returns
        -------
        dict
            A dict that show frequency

        list[int]
            Incremental index list


        Example:
        --------
        >>> test = ListExt([1, 1, 2, 3, 5, 5])
        >>> test.freq()
        {1: 2, 2: 1, 3: 1, 5: 2}

        >>> test = ListExt([1, 1, 2, 3, 3, 4, 5, 6])
        >>> test.freq(appear_increment=True)
        [2, 3, 5, 6, 7, 8]
        """
        if sort:
            data = self.sorts().copy()
        else:
            data = self.copy()

        if num_of_first_char is None:
            temp = Counter(data)
        else:
            max_char: int = min([len(str(x)) for x in data])
            # logger.debug(f"Max character: {max_char}")
            if num_of_first_char not in range(1, max_char):
                # logger.debug(f"Not in {range(1, max_char)}. Using default value...")
                temp = Counter(data)
            else:
                # logger.debug(f"Freq of first {num_of_first_char} char")
                temp = Counter([str(x)[:num_of_first_char] for x in data])

        try:
            times_appear = dict(sorted(temp.items()))
        except TypeError:
            times_appear = dict(self.__class__(temp.items()).sorts())
        # logger.debug(times_appear)

        if appear_increment:
            times_appear_increment: list[int] = list(accumulate(times_appear.values(), operator.add))
            # logger.debug(times_appear_increment)
            return times_appear_increment  # incremental index list
        else:
            return times_appear  # character frequency

    @versionchanged("5.2.0", reason="New ``recursive`` parameter")
    def flatten(self, recursive: bool = False) -> Self:
        """
        Flatten the list

        Parameters
        ----------
        recursive : bool
            Recursively flatten the list, by default ``False``

        Returns
        -------
        Self
            Flattened list


        Example:
        --------
        >>> test = ListExt([["test"], ["test", "test"], ["test"]])
        >>> test.flatten()
        ['test', 'test', 'test', 'test']
        """

        def instance_checking(item):
            if isinstance(item, str):
                return [item]
            if isinstance(item, Iterable):
                return item
            return [item]

        # Flatten
        list_of_list = (instance_checking(x) for x in self)
        flattened = self.__class__(chain(*list_of_list))

        # Recursive
        if recursive:

            def _condition(item) -> bool:
                if isinstance(item, str):
                    return False
                return isinstance(item, Iterable)

            while any(flattened.apply(_condition)):
                flattened = flattened.flatten()

        # Return
        return flattened

    @versionadded("5.2.0")
    def join(self, sep: str = " ", /) -> str:
        """
        Join every element in list to str (``str.join()`` wrapper).

        Parameters
        ----------
        sep : str, optional
            Separator between each element, by default ``" "``

        Returns
        -------
        str
            Joined list


        Example:
        --------
        >>> ListExt(["a", "b", "c"]).join()
        a b c

        >>> # Also work with non-str type
        >>> ListExt([1, 2, 3]).join()
        1 2 3
        """
        try:
            return sep.join(self)
        except TypeError:
            return sep.join(self.apply(str))

    @overload
    def numbering(self) -> Self: ...

    @overload
    def numbering(self, start: int | float = 0) -> Self: ...

    @overload
    def numbering(self, *, step: int | float = 1) -> Self: ...

    @overload
    def numbering(self, start: int | float = 0, step: int | float = 1) -> Self: ...

    @versionchanged("5.5.0", "Use itertools.count to wrap")
    def numbering(self, start: int | float = 0, step: int | float = 1) -> Self:
        """
        Number the item in list
        (``itertools.count`` wrapper)

        Parameters
        ----------
        start : int | float, optional
            Start from which number, by default ``0``

        step : int | float, optional
            Step, by default ``1``

        Returns
        -------
        Self
            Counted list


        Example:
        --------
        >>> test = ListExt([9, 9, 9])
        >>> test.numbering()
        [(0, 9), (1, 9), (2, 9)]
        """
        nums = count(start=start, step=step)
        # return self.__class__(enumerate(self, start=start))
        return self.__class__(zip(nums, self))

    @versionadded("5.3.0")  # no test case yet
    def transpose(self, fillvalue: Any | None = None, /) -> Self:
        """
        Transpose a list of iterable.

        Parameters
        ----------
        fillvalue : Any, optional
            A fill value, by default ``None``

        Returns
        -------
        Self | list[list[T]]
            Transposed list.


        Example:
        --------
        >>> ListExt([1, 1, 1, 1]).transpose()
        [(1, 1, 1, 1)]

        >>> ListExt([[1, 1, 1, 1], [1, 1, 1, 1]]).transpose()
        [(1, 1), (1, 1), (1, 1), (1, 1)]

        >>> ListExt([[1, 1, 1, 1], [1, 1, 1, 1], [1]]).transpose()
        [(1, 1, 1), (1, 1, None), (1, 1, None), (1, 1, None)]
        """
        try:
            return self.__class__(zip_longest(*self, fillvalue=fillvalue)).apply(list)
        except TypeError:  # Dimension of 1
            mod_dat = self.apply(lambda x: [x])
            # return self.__class__(zip_longest(*mod_dat, fillvalue=fillvalue)).apply(list)
            return mod_dat

    # Random
    def pick_one(self) -> Any:
        """
        Pick one random items from ``list``

        Returns
        -------
        Any
            Random value


        Example:
        --------
        >>> test = ListExt(["foo", "bar"])
        >>> test.pick_one()
        'bar'
        """
        if len(self) != 0:
            out = random.choice(self)
            # logger.debug(out)
            return out
        else:
            # logger.debug("List empty!")
            raise IndexError("List empty!")

    def get_random(self, number_of_items: int = 5) -> list:
        """
        Get ``number_of_items`` random items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            Number random of items, by default ``5``

        Returns
        -------
        list
            Filtered list
        """
        return [self.pick_one() for _ in range(number_of_items)]

    @versionadded("5.10.0")
    def shuffle(self) -> Self:
        random.shuffle(self)
        return self

    # Len
    @versionchanged("5.2.0", reason="Handle more type")
    def len_items(self) -> Self:
        """
        ``len()`` for every item in ``self``

        Returns
        -------
        Self
            List of ``len()``'ed value


        Example:
        --------
        >>> test = ListExt(["foo", "bar", "pizza"])
        >>> test.len_items()
        [3, 3, 5]
        """

        def _len(item: Any) -> int:
            try:
                return len(item)
            except TypeError:
                return len(str(item))

        return self.__class__([_len(x) for x in self])

    @versionchanged("5.2.0", reason="New ``recursive`` parameter")
    def mean_len(self, recursive: bool = False) -> float:
        """
        Average length of every item. Returns zero if failed (empty list, ZeroDivisionError).

        Parameters
        ----------
        recursive : bool
            Recursively find the average length of items in nested lists, by default ``False``

        Returns
        -------
        float
            Average length


        Example:
        --------
        >>> test = ListExt(["foo", "bar", "pizza"])
        >>> test.mean_len()
        3.6666666666666665
        """

        if recursive:
            dat = self.flatten(recursive=recursive)
        else:
            dat = self

        try:
            return sum(dat.len_items()) / len(dat)
        except ZeroDivisionError:
            return 0.0

    @versionadded("5.2.0")
    def max_item_len(self, recursive: bool = False) -> int:
        """
        Find the maximum length of items in the list.

        Parameters
        ----------
        recursive : bool
            Recursively find the maximum length of items in nested lists, by default ``False``

        Returns
        -------
        int
            Maximum length of items


        Example:
        --------
        >>> test = ListExt(["test", "longer_test"])
        >>> test.max_item_len()
        11

        >>> test = ListExt([["short"], ["longer_test"]])
        >>> test.max_item_len(recursive=True)
        11
        """
        if recursive:
            return cast(int, max(self.flatten(recursive=True).len_items()))
        return cast(int, max(self.len_items()))

    # Group/Unique
    def unique(self) -> Self:
        """
        Remove duplicates

        Returns
        -------
        Self
            Duplicates removed list


        Example:
        --------
        >>> test = ListExt([1, 1, 1, 2, 2, 3])
        >>> test.unique()
        [1, 2, 3]
        """
        return self.__class__(set(self))

    def group_by_unique(self) -> Self:
        """
        Group duplicated elements into list

        Returns
        -------
        Self
            Grouped value


        Example:
        --------
        >>> test = ListExt([1, 2, 3, 1, 3, 3, 2])
        >>> test.group_by_unique()
        [[1, 1], [2, 2], [3, 3, 3]]
        """
        # Old
        # out = self.sorts().slice_points(self.freq(appear_increment=True))
        # return __class__(out[:-1])

        # New
        temp = groupby(self.sorts())
        return self.__class__([list(g) for _, g in temp])

    def group_by_pair_value(self, max_loop: int = 3) -> list[list]:
        """
        Assume each ``list`` in ``list`` is a pair value,
        returns a ``list`` contain all paired value

        Parameters
        ----------
        max_loop : int
            Times to run functions (minimum: ``3``)

        Returns
        -------
        list[list]
            Grouped value


        Example:
        --------
        >>> test = ListExt([[1, 2], [2, 3], [4, 3], [5, 6]])
        >>> test.group_by_pair_value()
        [[1, 2, 3, 4], [5, 6]]

        >>> test = ListExt([[8, 3], [4, 6], [6, 3], [5, 2], [7, 2]])
        >>> test.group_by_pair_value()
        [[8, 3, 4, 6], [2, 5, 7]]

        >>> test = ListExt([["a", 4], ["b", 4], [5, "c"]])
        >>> test.group_by_pair_value()
        [['a', 4, 'b'], ['c', 5]]
        """

        iter = self.copy()

        # Init loop
        for _ in range(max(max_loop, 3)):
            temp: dict[Any, list] = {}
            # Make dict{key: all `item` that contains `key`}
            for item in iter:
                for x in item:
                    if temp.get(x, None) is None:
                        temp[x] = [item]
                    else:
                        temp[x].append(item)

            # Flatten dict.values
            temp = {k: list(set(chain(*v))) for k, v in temp.items()}

            iter = list(temp.values())

        return list(x for x, _ in groupby(iter))

    @versionadded("5.5.0")
    def split_equal(self, n: int, sort: bool = True) -> Self:
        """
        Try to equally split a list of number into ``n`` equal sum parts.

        **Note:** Element in list must be a number.

        Parameters
        ----------
        n : int
            Split into how many parts. Must be >= 1.

        sort : bool, optional
            Sort the instance before split, by default ``True``

        Returns
        -------
        Self
            Splitted (list[list])


        Example:
        --------
        >>> ListExt(range(1, 11)).split_equal(2)
        [[10, 7, 5, 4, 1], [9, 8, 6, 3, 2]]
        """

        # https://stackoverflow.com/a/61649667
        bins: list[list[int]] = [[0] for _ in range(max(n, 1))]
        if sort:
            # self = self.sorts(reverse=True)
            self = self.__class__(sorted(self, reverse=True))
        for x in self:
            least = bins[0]
            least[0] += x
            least.append(x)
            heapreplace(bins, least)
        return self.__class__(x[1:] for x in bins)

    # Slicing
    def slice_points(self, points: list[int]) -> Self:
        """
        Splits a list into sublists based on specified split points (indices).

        This method divides the original list into multiple sublists. The ``points``
        argument provides the indices at which the list should be split.  The resulting
        list of lists contains the sublists created by these splits. The original
        list is not modified.

        Parameters
        ----------
        points : list
            A list of integer indices representing the points at which to split
            the list. These indices are *exclusive* of the starting sublist
            but *inclusive* of the ending sublist.

        Returns
        -------
        Self | list[list]
            A list of lists, where each inner list is a slice of the original list
            defined by the provided split points.


        Example:
        --------
        >>> test = ListExt([1, 1, 2, 3, 3, 4, 5, 6])
        >>> test.slice_points([2, 5])
        [[1, 1], [2, 3, 3], [4, 5, 6]]
        >>> test.slice_points([0, 1, 2, 3, 4, 5, 6, 7, 8])
        [[], [1], [1], [2], [3], [3], [4], [5], [6]]
        >>> test.slice_points([])
        [[1, 1, 2, 3, 3, 4, 5, 6]]
        """
        points.append(len(self))
        data = self.copy()
        # return [data[points[i]:points[i+1]] for i in range(len(points)-1)]
        return self.__class__(data[i1:i2] for i1, i2 in zip([0] + points[:-1], points))

    @versionadded("5.1.0")
    def split_chunk(self, chunk_size: int, /) -> Self:
        """
        Split list into smaller chunks

        Parameters
        ----------
        chunk_size : int
            Chunk size, minimum: ``1``

        Returns
        -------
        Self | list[list]
            List of chunk


        Example:
        --------
        >>> ListExt([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).split_chunk(5)
        [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1]]
        """
        slice_points = list(range(0, len(self), max(chunk_size, 1)))[1:]
        return self.slice_points(slice_points)

    @versionadded("5.3.0")  # no test case yet
    def to_column(self, ncols: int, fillvalue: Any | None = None) -> Self:
        """
        Smart convert 1 dimension list to 2 dimension list,
        in which, number of columns = ``ncols``.

        Parameters
        ----------
        ncols : int
            Number of columns

        fillvalue : Any | None, optional
            Fill value, by default ``None``

        Returns
        -------
        Self
            Coulumned list.


        Example:
        --------
        >>> ins = ListExt(range(1, 20))

        >>> # Normal split chunk
        >>> ins.split_chunk(10)
        [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [11, 12, 13, 14, 15, 16, 17, 18, 19]
        ]

        >>> # Column split chunk
        >>> ins.to_column(10)
        [
            [1, 3, 5, 7, 9, 11, 13, 15, 17, 19],
            [2, 4, 6, 8, 10, 12, 14, 16, 18, None]
        ]
        """
        num_of_col = max(ncols, 1)
        len_cols = len(self.split_chunk(num_of_col))
        return self.split_chunk(len_cols).transpose(fillvalue)

    @overload
    def wrap_to_column(self, width: int, /) -> Self: ...

    @overload
    def wrap_to_column(
        self,
        width: int,
        /,
        *,
        margin: int = 4,
        sep: str = "",
        fill: str = " ",
        transpose: bool = False,
    ) -> Self: ...

    @versionchanged("5.3.0", reason="New `sep`, `fill`, `transpose` parameters")
    @versionadded("5.2.0")  # no test case yet
    def wrap_to_column(
        self,
        width: int,
        /,
        *,
        margin: int = 4,
        sep: str = "",
        fill: str = " ",
        transpose: bool = False,
    ) -> Self:
        """
        Arrange list[str] items into aligned text columns (for printing)
        with automatic column count calculation.

        Parameters
        ----------
        width : int
            Total available display width (must be >= ``margin``)

        margin : int, optional
            Reserved space for borders/padding, should be an even number, by default ``4``

        sep : str, optional
            Separator between each element, by default ``""``

        fill : str, optional
            Fill character for spacing, must have the length of 1, by default ``" "``

        transpose : bool, optional
            Smart transpose the columns, by default ``False``

        Returns
        -------
        Self
            New instance type[list[str]] with formatted column strings.


        Example:
        --------
        >>> items = ListExt(["apple", "banana", "cherry", "date"])
        >>> print(items.wrap_to_column(30))
        ['apple  banana cherry ', 'date   ']

        >>> items.wrap_to_column(15)
        ['apple  ', 'banana ', 'cherry ', 'date   ']
        """

        max_item_length = self.max_item_len() + max(len(sep), 1)
        available_width = max(width, 4) - max(margin, 0)  # Set boundary
        if len(fill) != 1:
            fill = " "

        # Calculate how many columns of text
        column_count = max(1, available_width // max_item_length) if max_item_length > 0 else 1

        # splitted_chunk: list[list[str]] = self.split_chunk(cols)
        # mod_chunk = self.__class__(
        #     [[x.ljust(max_name_len, " ") for x in chunk] for chunk in splitted_chunk]
        # ).apply(lambda x: "".join(x))

        def mod_item(item: list[str]) -> str:
            # Set width for str item and join them together
            return sep.join(x.ljust(max_item_length, fill) for x in item)

        if transpose:
            mod_chunk = self.to_column(column_count, fillvalue="").apply(mod_item)
        else:
            mod_chunk = self.split_chunk(column_count).apply(mod_item)

        return mod_chunk


class ListExt2(GetClassMembersMixin, list[T]):
    """
    ``list`` extension (with generic - W.I.P)

    >>> # For a list of new methods
    >>> ListExt2.show_all_methods()
    """

    # MARK: Info
    def head(self, number_of_items: int = 5, /) -> list[T]:
        """
        Show first ``number_of_items`` items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            | Number of items to shows at once
            | (Default: ``5``)

        Returns
        -------
        list
            Filtered list


        Example:
        --------
        >>> ListExt(range(10)).head(2)
        [0, 1]
        """
        number_of_items = int(set_min_max(number_of_items, min_value=0, max_value=len(self)))
        return self[:number_of_items]

    def tail(self, number_of_items: int = 5, /) -> list[T]:
        """
        Show last ``number_of_items`` items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            | Number of items to shows at once
            | (Default: ``5``)

        Returns
        -------
        list
            Filtered list


        Example:
        --------
        >>> ListExt(range(10)).tail(2)
        [8, 9]
        """
        number_of_items = int(set_min_max(number_of_items, min_value=0, max_value=len(self)))
        return self[::-1][:number_of_items][::-1]

    # MARK: Misc
    def apply(self, func: Callable[[T], R]) -> ListExt2[R]:
        """
        Apply function to each entry

        Parameters
        ----------
        func : Callable[[Any], Any]
            Callable function

        Returns
        -------
        Self
            ListExt


        Example:
        --------
        >>> test = ListExt([1, 2, 3])
        >>> test.apply(str)
        ['1', '2', '3']
        """
        # return self.__class__(map(func, self))
        return self.__class__(func(x) for x in self)  # type: ignore

    def sorts(self, reverse: bool = False) -> Self:
        """
        Sort all items (with different type) in ``list``

        Parameters
        ----------
        reverse : bool
            - ``True`` then sort in descending order
            - ``False`` then sort in ascending order (default value)

        Returns
        -------
        Self
            A sorted list


        Example:
        --------
        >>> test = ListExt([9, "abc", 3.5, "aaa", 1, 1.4])
        >>> test.sorts()
        [1, 9, 'aaa', 'abc', 1.4, 3.5]
        """
        lst = self.copy()
        type_weights: dict = {}
        for x in lst:
            if type(x) not in type_weights:
                type_weights[type(x)] = len(type_weights)
        # logger.debug(f"Type weight: {type_weights}")

        output = sorted(lst, key=lambda x: (type_weights[type(x)], str(x)), reverse=reverse)

        # logger.debug(output)
        return self.__class__(output)

    @versionchanged("5.2.0", reason="New ``recursive`` parameter")
    def flatten(self, recursive: bool = False) -> Self:
        """
        Flatten the list

        Parameters
        ----------
        recursive : bool
            Recursively flatten the list, by default ``False``

        Returns
        -------
        Self
            Flattened list


        Example:
        --------
        >>> test = ListExt([["test"], ["test", "test"], ["test"]])
        >>> test.flatten()
        ['test', 'test', 'test', 'test']
        """

        def instance_checking(item):
            if isinstance(item, str):
                return [item]
            if isinstance(item, Iterable):
                return item
            return [item]

        # Flatten
        list_of_list = (instance_checking(x) for x in self)
        flattened = self.__class__(chain(*list_of_list))

        # Recursive
        if recursive:

            def _condition(item) -> bool:
                if isinstance(item, str):
                    return False
                return isinstance(item, Iterable)

            while any(flattened.apply(_condition)):
                flattened = flattened.flatten()

        # Return
        return flattened

    @versionadded("5.2.0")
    def join(self, sep: str = " ", /) -> str:
        """
        Join every element in list to str (``str.join()`` wrapper).

        Parameters
        ----------
        sep : str, optional
            Separator between each element, by default ``" "``

        Returns
        -------
        str
            Joined list


        Example:
        --------
        >>> ListExt(["a", "b", "c"]).join()
        a b c

        >>> # Also work with non-str type
        >>> ListExt([1, 2, 3]).join()
        1 2 3
        """
        try:
            return sep.join(self)  # type: ignore
        except TypeError:
            return sep.join(self.apply(str))

    def group_by_pair_value(self, max_loop: int = 3):
        """
        Assume each ``list`` in ``list`` is a pair value,
        returns a ``list`` contain all paired value

        Parameters
        ----------
        max_loop : int
            Times to run functions (minimum: ``3``)

        Returns
        -------
        list[list]
            Grouped value


        Example:
        --------
        >>> test = ListExt([[1, 2], [2, 3], [4, 3], [5, 6]])
        >>> test.group_by_pair_value()
        [[1, 2, 3, 4], [5, 6]]

        >>> test = ListExt([[8, 3], [4, 6], [6, 3], [5, 2], [7, 2]])
        >>> test.group_by_pair_value()
        [[8, 3, 4, 6], [2, 5, 7]]

        >>> test = ListExt([["a", 4], ["b", 4], [5, "c"]])
        >>> test.group_by_pair_value()
        [['a', 4, 'b'], ['c', 5]]
        """

        iter = self.copy()

        # Init loop
        for _ in range(max(max_loop, 3)):
            temp: dict[Any, list] = {}
            # Make dict{key: all `item` that contains `key`}
            for item in iter:
                for x in item:
                    if temp.get(x, None) is None:
                        temp[x] = [item]
                    else:
                        temp[x].append(item)

            # Flatten dict.values
            temp = {k: list(set(chain(*v))) for k, v in temp.items()}

            iter = list(temp.values())

        return list(x for x, _ in groupby(iter))

    def split_equal(self, n: int, sort: bool = True) -> ListExt2[list[T]]:
        """
        Try to equally split a list of number into ``n`` equal sum parts.

        **Note:** Element in list must be a number.

        Parameters
        ----------
        n : int
            Split into how many parts. Must be >= 1.

        sort : bool, optional
            Sort the instance before split, by default ``True``

        Returns
        -------
        Self
            Splitted (list[list])


        Example:
        --------
        >>> ListExt(range(1, 11)).split_equal(2)
        [[10, 7, 5, 4, 1], [9, 8, 6, 3, 2]]
        """

        # https://stackoverflow.com/a/61649667
        bins: list[list[int]] = [[0] for _ in range(max(n, 1))]
        if sort:
            # self = self.sorts(reverse=True)
            self = self.__class__(sorted(self, reverse=True))
        for x in self:
            least = bins[0]
            least[0] += x
            least.append(x)
            heapreplace(bins, least)
        return self.__class__(x[1:] for x in bins)

    # MARK: Random
    def pick_one(self) -> T:
        """
        Pick one random items from ``list``

        Returns
        -------
        Any
            Random value


        Example:
        --------
        >>> test = ListExt(["foo", "bar"])
        >>> test.pick_one()
        'bar'
        """
        if len(self) != 0:
            out = random.choice(self)
            # logger.debug(out)
            return out
        else:
            # logger.debug("List empty!")
            raise IndexError("List empty!")

    def get_random(self, number_of_items: int = 5, /) -> list[T]:
        """
        Get ``number_of_items`` random items in ``ListExt``

        Parameters
        ----------
        number_of_items : int
            Number random of items, by default ``5``

        Returns
        -------
        list
            Filtered list
        """
        return [self.pick_one() for _ in range(number_of_items)]

    @versionadded("5.10.0")
    def shuffle(self) -> Self:
        """
        Shuffle the list itself

        Returns
        -------
        Self
            Shuffled list
        """
        random.shuffle(self)
        return self

    # MARK: Len
    @versionchanged("5.2.0", reason="Handle more type")
    def len_items(self) -> ListExt2[int]:
        """
        ``len()`` for every item in ``self``

        Returns
        -------
        Self
            List of ``len()``'ed value


        Example:
        --------
        >>> test = ListExt(["foo", "bar", "pizza"])
        >>> test.len_items()
        [3, 3, 5]
        """

        def _len(item: Any) -> int:
            try:
                return len(item)
            except TypeError:
                return len(str(item))

        return self.__class__([_len(x) for x in self])  # type: ignore

    @versionchanged("5.2.0", reason="New ``recursive`` parameter")
    def mean_len(self, recursive: bool = False) -> float:
        """
        Average length of every item. Returns zero if failed (empty list, ZeroDivisionError).

        Parameters
        ----------
        recursive : bool
            Recursively find the average length of items in nested lists, by default ``False``

        Returns
        -------
        float
            Average length


        Example:
        --------
        >>> test = ListExt(["foo", "bar", "pizza"])
        >>> test.mean_len()
        3.6666666666666665
        """

        if recursive:
            dat = self.flatten(recursive=recursive)
        else:
            dat = self

        try:
            return sum(dat.len_items()) / len(dat)
        except ZeroDivisionError:
            return 0.0

    @versionadded("5.2.0")
    def max_item_len(self, recursive: bool = False) -> int:
        """
        Find the maximum length of items in the list.

        Parameters
        ----------
        recursive : bool
            Recursively find the maximum length of items in nested lists, by default ``False``

        Returns
        -------
        int
            Maximum length of items


        Example:
        --------
        >>> test = ListExt(["test", "longer_test"])
        >>> test.max_item_len()
        11

        >>> test = ListExt([["short"], ["longer_test"]])
        >>> test.max_item_len(recursive=True)
        11
        """
        if recursive:
            return cast(int, max(self.flatten(recursive=True).len_items()))
        return cast(int, max(self.len_items()))

    # MARK: Group/Unique
    def unique(self) -> Self:
        """
        Remove duplicates

        Returns
        -------
        Self
            Duplicates removed list


        Example:
        --------
        >>> test = ListExt([1, 1, 1, 2, 2, 3])
        >>> test.unique()
        [1, 2, 3]
        """
        return self.__class__(set(self))

    def group_by_unique(self) -> ListExt2[list[T]]:
        """
        Group duplicated elements into list

        Returns
        -------
        Self
            Grouped value


        Example:
        --------
        >>> test = ListExt([1, 2, 3, 1, 3, 3, 2])
        >>> test.group_by_unique()
        [[1, 1], [2, 2], [3, 3, 3]]
        """
        temp = groupby(self.sorts())
        return self.__class__([list(g) for _, g in temp])


if __name__ == "__main__":
    test = ListExt2([1, 2, 3, 4, 5, "s"])
    a = test.group_by_unique()
    print(a, type(a))
