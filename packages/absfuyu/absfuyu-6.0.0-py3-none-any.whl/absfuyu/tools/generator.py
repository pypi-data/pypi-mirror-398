"""
Absfuyu: Generator
------------------
This generate stuff (Not python's ``generator``)

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Features:
---------
- Generate random string
- Generate key
- Generate check digit
- Generate combinations of list in range
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Charset", "Generator"]


# Library
# ---------------------------------------------------------------------------
import string
from collections.abc import Collection, Sequence
from itertools import chain, combinations
from random import choice
from typing import Literal, TypeVar, cast, overload

from absfuyu.core.baseclass import GetClassMembersMixin
from absfuyu.core.docstring import deprecated
from absfuyu.util import set_min_max

# Type
# ---------------------------------------------------------------------------
T = TypeVar("T")


# Class
# ---------------------------------------------------------------------------
class Charset:
    """
    Character set data class
    """

    DEFAULT: str = string.ascii_letters + string.digits
    ALPHABET: str = string.ascii_letters
    FULL: str = string.ascii_letters + string.digits + string.punctuation
    UPPERCASE: str = string.ascii_uppercase
    LOWERCASE: str = string.ascii_lowercase
    DIGIT: str = string.digits
    SPECIAL: str = string.punctuation
    ALL: str = string.printable
    PRODUCT_KEY: str = (
        "BCDFGHJKMNPQRTVWXY2346789"  # Charset that various key makers use
    )

    def __str__(self) -> str:
        charset = [x for x in self.__class__.__dict__.keys() if not x.startswith("__")]
        return f"List of Character set: {charset}"

    def __repr__(self) -> str:
        charset = [x for x in self.__class__.__dict__.keys() if not x.startswith("__")]
        clsname = self.__class__.__name__
        return f"{clsname}({', '.join(charset)})"


class Generator(GetClassMembersMixin):
    """
    Generator that generate stuffs

    Features:
    ---------
    - Generate random string
    - Generate key
    - Generate check digit
    - Generate combinations of list in range
    """

    # Generate string
    @overload
    @staticmethod
    def generate_string(  # type: ignore
        charset: str = Charset.DEFAULT,
        size: int = 8,
        times: int = 1,
        unique: bool = False,
    ) -> list[str]: ...

    @overload
    @staticmethod
    def generate_string(
        charset: str = Charset.DEFAULT,
        size: int = 8,
        times: int = 1,
        unique: bool = False,
        string_type_if_1: Literal[True] = ...,
    ) -> str: ...

    @staticmethod
    @deprecated("5.2.0", reason="Use generate_string2() instead.")
    def generate_string(
        charset: str = Charset.DEFAULT,
        size: int = 8,
        times: int = 1,
        unique: bool = False,
        string_type_if_1: bool = False,
    ) -> str | list[str]:
        """
        Generate a list of random string from character set (Random string generator).
        Deprecated

        Parameters
        ----------
        charset : str, optional
            - Use custom character set or character sets already defined in ``Charset``
            - ``Charset.DEFAULT``: character in [a-zA-Z0-9] (default)
            - ``Charset.ALPHABET``: character in [a-zA-Z]
            - ``Charset.FULL``: character in [a-zA-Z0-9] + special characters
            - ``Charset.UPPERCASE``: character in [A-Z]
            - ``Charset.LOWERCASE``: character in [a-z]
            - ``Charset.DIGIT``: character in [0-9]
            - ``Charset.SPECIAL``: character in [!@#$%^&*()_+=-]
            - ``Charset.ALL``: character in every printable character

        size : int, optional
            Length of each string in list, by default ``8``

        times : int, optional
            How many random string generated, by default ``1``

        unique : bool, optional
            Each generated text is unique, by default ``False``

        string_type_if_1 : bool, optional
            Return a ``str`` type result if ``times == 1``,
            by default ``False``

        Returns
        -------
        list
            List of random string generated

        str
            When ``string_type_if_1`` is ``True``
        """

        try:
            char_lst = list(charset)
        except Exception:
            char_lst = charset  # type: ignore # ! review this sometime

        unique_string = []
        count = 0

        while count < times:
            s = "".join(choice(char_lst) for _ in range(size))
            if not unique:
                unique_string.append(s)
                count += 1
            else:
                if s not in unique_string:
                    unique_string.append(s)
                    count += 1

        if string_type_if_1 and times == 1:
            return unique_string[0]
        else:
            return unique_string

    @overload
    @staticmethod
    def generate_string2() -> list[str]: ...

    @overload
    @staticmethod
    def generate_string2(
        charset: str = Charset.DEFAULT,
        length: int = 8,
        times: int = 1,
        unique: bool = False,
    ) -> list[str]: ...

    @overload
    @staticmethod
    def generate_string2(
        charset: Sequence[str],
        length: int = 8,
        times: int = 1,
        unique: bool = False,
    ) -> list[str]: ...

    @staticmethod
    def generate_string2(
        charset: Sequence[str] | Charset | str = Charset.DEFAULT,
        length: int = 8,
        times: int = 1,
        unique: bool = False,
    ) -> list[str]:
        """
        Generate a list of random string from character set (Random string generator).
        Improved version.

        Parameters
        ----------
        charset : Sequence[str] | Charset | str, optional
            - Use custom character set or character sets already defined in ``Charset``
            - ``Charset.DEFAULT``: character in [a-zA-Z0-9] (default)
            - ``Charset.ALPHABET``: character in [a-zA-Z]
            - ``Charset.FULL``: character in [a-zA-Z0-9] + special characters
            - ``Charset.UPPERCASE``: character in [A-Z]
            - ``Charset.LOWERCASE``: character in [a-z]
            - ``Charset.DIGIT``: character in [0-9]
            - ``Charset.SPECIAL``: character in [!@#$%^&*()_+=-]
            - ``Charset.ALL``: character in every printable character

        length : int, optional
            Length of each string in list, by default ``8``

        times : int, optional
            How many random string generated, by default ``1``

        unique : bool, optional
            Each generated text is unique, by default ``False``

        Returns
        -------
        list[str]
            List of random generated string.

        Raises
        ------
        TypeError
            When ``charset`` not in correct type.


        Example:
        --------
        >>> Generator.generate_string2(times=3)
        ['67Xfh1fv', 'iChcGz9P', 'u82fNzlm']
        """

        # Type check
        if isinstance(charset, str):
            character_list: list[str] = list(charset)
        elif isinstance(charset, Sequence):
            character_list = cast(list, charset)
        else:
            raise TypeError("Not a valid type.")

        # Setup
        generated_strings: list[str] = []
        unique_generated_strings: set[str] = set[str]()
        times_ = max(1, times)

        while True:
            random_string = "".join(choice(character_list) for _ in range(length))
            if unique:
                unique_generated_strings.add(random_string)
            else:
                generated_strings.append(random_string)

            # Break condition
            if (
                len(unique_generated_strings) >= times_
                or len(generated_strings) >= times_
            ):
                break

        return list(unique_generated_strings) if unique else generated_strings

    # Generate key
    @overload
    @classmethod
    def generate_key(cls) -> str: ...

    @overload
    @classmethod
    def generate_key(
        cls,
        charset: str = Charset.PRODUCT_KEY,
        letter_per_block: int = 5,
        number_of_block: int = 5,
        sep: str = "-",
    ) -> str: ...

    @classmethod
    def generate_key(
        cls,
        charset: str = Charset.PRODUCT_KEY,
        letter_per_block: int = 5,
        number_of_block: int = 5,
        sep: str = "-",
    ) -> str:
        """
        Generate custom key.

        Parameters
        ----------
        charset : Charset | str, optional
            Character set, by default ``Charset.PRODUCT_KEY``

        letter_per_block : int, optional
            Number of letter per key block, by default ``5``

        number_of_block : int, optional
            Number of key block, by default ``5``

        sep : str, optional
            Key block separator, by default ``-``

        Returns
        -------
        str
            Generated key


        Example:
        --------
        >>> Generator.generate_key(letter_per_block=10, number_of_block=2)
        'VKKPJVYD2H-M7R687QCV2'
        """
        out = sep.join(
            cls.generate_string2(
                charset,
                length=letter_per_block,
                times=number_of_block,
                unique=False,
            )
        )
        return out

    # Generate check digit
    @overload
    @staticmethod
    def generate_check_digit(number: int) -> int: ...

    @overload
    @staticmethod
    def generate_check_digit(number: list[int]) -> int: ...

    @overload
    @staticmethod
    def generate_check_digit(number: str) -> int: ...

    @staticmethod
    def generate_check_digit(number: int | list[int] | str) -> int:
        """
        Check digit generator.

        "A check digit is a form of redundancy check used for
        error detection on identification numbers, such as
        bank account numbers, which are used in an application
        where they will at least sometimes be input manually.
        It is analogous to a binary parity bit used to
        check for errors in computer-generated data.
        It consists of one or more digits (or letters) computed
        by an algorithm from the other digits (or letters) in the sequence input.
        With a check digit, one can detect simple errors in
        the input of a series of characters (usually digits)
        such as a single mistyped digit or some permutations
        of two successive digits." (Wikipedia)

        This function use Luhn's algorithm to calculate.

        Parameters
        ----------
        number : int
            Number to calculate check digit

        Returns
        -------
        int
            Check digit


        Example:
        --------
        >>> Generator.generate_check_digit(4129984562545)
        7
        """

        # Type handle
        if isinstance(number, int):
            # Turn into list[int] then reverse the order
            num = [int(x) for x in list(str(number))][::-1]
        elif isinstance(number, str):
            num = [int(x) for x in list(number)][::-1]
        elif isinstance(number, list):
            num = number[::-1]
        else:
            raise TypeError("Variable `number` is not correct type.")

        sum = 0

        # for i in range(len(num)):
        for idx, _ in enumerate(num):
            if idx % 2 == 0:
                # double value of the even-th digit
                num[idx] *= 2
                # sum the character of digit if it's >= 10
                if num[idx] >= 10:
                    num[idx] -= 9
            sum += num[idx]

        out = (10 - (sum % 10)) % 10
        return out

    # Generate combinations range
    @overload
    @staticmethod
    def combinations_range(collection: Collection[T]) -> list[tuple[T, ...]]: ...

    @overload
    @staticmethod
    def combinations_range(collection: Collection[T], *, min_len: int = 1, max_len: int = 0) -> list[tuple[T, ...]]: ...

    @staticmethod
    def combinations_range(
        collection: Collection[T], *, min_len: int = 1, max_len: int = 0
    ) -> list[tuple[T, ...]]:
        """
        Generate all combinations of a ``collection`` from ``min_len`` to ``max_len``

        Parameters
        ----------
        collection : Collection[T]
            A collection (Iterable with ``__len__``) that need to generate combination

        min_len : int, optional
            Minimum ``r`` of ``combinations``, by default ``1``

        max_len : int, optional
            Maximum ``r`` of ``combinations``, by default ``0`` (len of ``collection``)

        Returns
        -------
        list[tuple]
            A list of all combinations from range(``min_len``, ``max_len``) of ``collection``


        Example:
        --------
        >>> Generator.combinations_range([1, 2, 3], min_len=2)
        [(1, 2), (1, 3), (2, 3), (1, 2, 3)]
        """
        # Restrain
        len_iter = len(
            collection
        )  # with collection.abc.Iterable, use len(list(collection))
        if max_len < 1:
            max_len = len_iter
        max_len = int(min(max_len, len_iter))
        min_len = int(set_min_max(min_len, min_value=1, max_value=max_len))

        # Return
        return list(
            chain.from_iterable(
                combinations(collection, i) for i in range(min_len, max_len + 1)
            )
        )
