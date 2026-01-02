"""
Absfuyu: Data Extension
-----------------------
int extension

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["IntExt", "Pow"]


# Library
# ---------------------------------------------------------------------------
import math
from abc import ABC
from collections import Counter
from typing import Any, Literal, Self, overload, override

from absfuyu.core.baseclass import GetClassMembersMixin
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.dxt.dxt_support import DictBoolTrue


# Class
# ---------------------------------------------------------------------------
class Pow:
    """Number power by a number"""

    def __init__(self, number: int | float, power_by: int) -> None:
        self.number = number
        self.power_by = power_by

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        if self.power_by == 1:
            return str(self.number)
        else:
            return f"{self.number}^{self.power_by}"
        # return f"{self.__class__.__name__}({self.number}, {self.power_by})"

    def to_list(self) -> list[int]:
        """
        Convert into list

        Returns
        -------
        list[int | float]
            list
        """
        return [self.number] * self.power_by  # type: ignore

    def calculate(self) -> float:
        """
        Calculate the ``self.number`` to the power of ``self.power_by``

        Returns
        -------
        float
            Result
        """
        # return self.number**self.power_by
        return math.pow(self.number, self.power_by)


class IntExt(GetClassMembersMixin, int):
    """
    ``int`` extension

    >>> # For a list of new methods
    >>> IntExt.show_all_methods()
    """

    # convert
    @deprecated("5.4.0", reason="Use format(...) instead")
    def to_binary(self) -> str:
        """
        Convert to binary number

        Returns
        -------
        str
            Binary number


        Example:
        --------
        >>> test = IntExt(10)
        >>> test.to_binary()
        '1010'
        """
        return format(self, "b")

    def to_celcius_degree(self) -> float:
        """
        Convert into Celcius degree as if ``self`` is Fahrenheit degree

        Returns
        -------
        float
            Celcius degree


        Example:
        --------
        >>> test = IntExt(10)
        >>> test.to_celcius_degree()
        -12.222222222222221
        """
        c_degree = (self - 32) / 1.8
        return c_degree

    def to_fahrenheit_degree(self) -> float:
        """
        Convert into Fahrenheit degree as if ``self`` is Celcius degree

        Returns
        -------
        float
            Fahrenheit degree


        Example:
        --------
        >>> test = IntExt(10)
        >>> test.to_fahrenheit_degree()
        50.0
        """
        f_degree = (self * 1.8) + 32
        return f_degree

    def reverse(self) -> Self:
        """
        Reverse a number. Reverse ``abs(number)`` if ``number < 0``

        Returns
        -------
        Self
            Reversed number.


        Example:
        --------
        >>> test = IntExt(102)
        >>> test.reverse()
        201
        """
        number = int(self)
        if number <= 1:
            number *= -1
        return self.__class__(str(number)[::-1])

    # is_stuff
    def is_even(self) -> bool:
        """
        An even number is a number which divisible by 2

        Returns
        -------
        bool
            | ``True`` if an even number
            | ``False`` if not an even number
        """
        return self % 2 == 0

    def is_prime(self) -> bool:
        """
        Check if the integer is a prime number or not

            A prime number is a natural number greater than ``1``
            that is not a product of two smaller natural numbers.
            A natural number greater than ``1`` that is not prime
            is called a composite number.

        Returns
        -------
        bool
            | ``True`` if a prime number
            | ``False`` if not a prime number
        """
        number = self

        if number <= 1:
            return False
        for i in range(2, int(math.sqrt(number)) + 1):  # divisor range
            if number % i == 0:
                return False
        return True

    def is_twisted_prime(self) -> bool:
        """
        A number is said to be twisted prime if
        it is a prime number and
        reverse of the number is also a prime number

        Returns
        -------
        bool
            | ``True`` if a twisted prime number
            | ``False`` if not a twisted prime number
        """
        prime = self.is_prime()
        rev = self.reverse().is_prime()
        return prime and rev

    def is_perfect(self) -> bool:
        """
        Check if integer is perfect number

            Perfect number: a positive integer that is
            equal to the sum of its proper divisors.
            The smallest perfect number is ``6``, which is
            the sum of ``1``, ``2``, and ``3``.
            Other perfect numbers are ``28``, ``496``, and ``8,128``.

        Returns
        -------
        bool
            | ``True`` if a perfect number
            | ``False`` if not a perfect number
        """
        # ---
        """
        # List of known perfect number
        # Source: https://en.wikipedia.org/wiki/List_of_Mersenne_primes_and_perfect_numbers
        perfect_number_index = [
            2, 3, 5, 7,
            13, 17, 19, 31, 61, 89,
            107, 127, 521, 607,
            1279, 2203, 2281, 3217, 4253, 4423, 9689, 9941,
            11_213, 19_937, 21_701, 23_209, 44_497, 86_243,
            110_503, 132_049, 216_091, 756_839, 859_433,
            # 1_257_787, 1_398_269, 2_976_221, 3_021_377, 6_972_593,
            # 13_466_917, 20_996_011, 24_036_583, 25_964_951,
            # 30_402_457, 32_582_657, 37_156_667, 42_643_801,
            # 43_112_609, 57_885_161,
            ## 74_207_281, 77_232_917, 82_589_933
        ]
        perfect_number = []
        for x in perfect_number_index:
            # a perfect number have a form of (2**(n-1))*((2**n)-1)
            perfect_number.append((2**(x-1))*((2**x)-1))
        """
        number = int(self)

        perfect_number = [
            6,
            28,
            496,
            8128,
            33_550_336,
            8_589_869_056,
            137_438_691_328,
            2_305_843_008_139_952_128,
        ]

        if number in perfect_number:
            return True

        elif number < perfect_number[-1]:
            return False

        else:
            # Faster way to check
            perfect_number_index: list[int] = [
                61,
                89,
                107,
                127,
                521,
                607,
                1279,
                2203,
                2281,
                3217,
                4253,
                4423,
                9689,
                9941,
                11_213,
                19_937,
                21_701,
                23_209,
                44_497,
                86_243,
                110_503,
                132_049,
                216_091,
                756_839,
                859_433,
                1_257_787,
                # 1_398_269,
                # 2_976_221,
                # 3_021_377,
                # 6_972_593,
                # 13_466_917,
                # 20_996_011,
                # 24_036_583,
                # 25_964_951,
                # 30_402_457,
                # 32_582_657,
                # 37_156_667,
                # 42_643_801,
                # 43_112_609,
                # 57_885_161,
                ## 74_207_281,
                ## 77_232_917,
                ## 82_589_933
            ]
            for x in perfect_number_index:
                # a perfect number have a form of (2**(n-1))*((2**n)-1)
                perfect_number = (2 ** (x - 1)) * ((2**x) - 1)
                if number < perfect_number:  # type: ignore
                    return False
                elif number == perfect_number:  # type: ignore
                    return True

            # Manual way when above method not working
            # sum
            s = 1
            # add all divisors
            i = 2
            while i * i <= number:
                if number % i == 0:
                    s += +i + number / i  # type: ignore
                i += 1
            # s == number -> perfect
            return True if s == number and number != 1 else False

    def is_narcissistic(self) -> bool:
        """
        Check if a narcissistic number

            In number theory, a narcissistic number
            (also known as a pluperfect digital invariant (PPDI),
            an Armstrong number (after Michael F. Armstrong)
            or a plus perfect number) in a given number base ``b``
            is a number that is the sum of its own digits
            each raised to the power of the number of digits.

        Returns
        -------
        bool
            | ``True`` if a narcissistic number
            | ``False`` if not a narcissistic number
        """
        try:
            check = sum([int(x) ** len(str(self)) for x in str(self)])
            res = int(self) == check
            return res  # type: ignore
        except Exception:
            return False

    def is_palindromic(self) -> bool:
        """
        A palindromic number (also known as a numeral palindrome
        or a numeric palindrome) is a number (such as ``16461``)
        that remains the same when its digits are reversed.

        Returns
        -------
        bool
            | ``True`` if a palindromic number
            | ``False`` if not a palindromic number
        """
        return self == self.reverse()

    def is_palindromic_prime(self) -> bool:
        """
        A palindormic prime is a number which is both palindromic and prime

        Returns
        -------
        bool
            | ``True`` if a palindormic prime number
            | ``False`` if not a palindormic prime number
        """
        return self.is_palindromic() and self.is_prime()

    # calculation stuff
    def lcm(self, with_number: int) -> Self:
        """
        Least common multiple of ``self`` and ``with_number``

        Parameters
        ----------
        with_number : int
            The number that want to find LCM with

        Returns
        -------
        Self
            Least common multiple.


        Example:
        --------
        >>> test = IntExt(102)
        >>> test.lcm(5)
        510
        """
        return self.__class__(math.lcm(self, with_number))

    @versionchanged("3.3.0", reason="Updated functionality")
    def gcd(self, with_number: int) -> Self:
        """
        Greatest common divisor of ``self`` and ``with_number``

        Parameters
        ----------
        with_number : int
            The number that want to find GCD with

        Returns
        -------
        Self
            Greatest common divisor.


        Example:
        --------
        >>> test = IntExt(1024)
        >>> test.gcd(8)
        8
        """
        return self.__class__(math.gcd(self, with_number))

    def add_to_one_digit(self, master_number: bool = False) -> Self:
        """
        Convert ``self`` into 1-digit number
        by adding all of the digits together

        Parameters
        ----------
        master_number : bool
            | Break when sum = ``22`` or ``11`` (numerology)
            | (Default: ``False``)

        Returns
        -------
        Self
            IntExt


        Example:
        --------
        >>> test = IntExt(119)
        >>> test.add_to_one_digit()
        2

        >>> test = IntExt(119)
        >>> test.add_to_one_digit(master_number=True)
        11
        """

        number = int(self)
        if number < 0:  # Convert positive
            number *= -1

        while len(str(number)) != 1:
            number = sum(map(int, str(number)))
            if master_number:
                if number == 22 or number == 11:
                    break  # Master number

        return self.__class__(number)

    @versionchanged("5.0.0", reason="Removed ``short_form`` parameter")
    def divisible_list(self) -> list[int]:
        """
        A list of divisible number

        Returns
        -------
        list[int]
            A list of divisible number


        Example:
        --------
        >>> test = IntExt(1024)
        >>> test.divisible_list()
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        """

        if self <= 1:
            return [1]
        divi_list = [x for x in range(1, int(self / 2) + 1) if self % x == 0] + [self]

        return divi_list

    @overload
    def prime_factor(self) -> list[Pow]: ...  # type: ignore

    @overload
    def prime_factor(self, short_form: Literal[False] = ...) -> list[int]: ...

    def prime_factor(self, short_form: bool = True) -> list[int] | list[Pow]:
        """
        Prime factor

        Parameters
        ----------
        short_form : bool
            | Show prime list in short form
            | Normal example: ``[2, 2, 2, 3, 3]``
            | Short form example: ``[2^3, 3^2]``
            | (Default: ``True``)

        Returns
        -------
        list[int] | list[Pow]
            | List of prime number that when multiplied together == ``self``
            | list[int]: Long form
            | list[Pow]: Short form


        Example:
        --------
        >>> test = IntExt(1024)
        >>> test.prime_factor()
        [2^10]

        >>> test = IntExt(1024)
        >>> test.prime_factor(short_form=False)
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        """

        # Generate list
        factors = []
        divisor = 2
        number = int(self)
        if number <= 1:
            return [number]
        while divisor <= number:
            if number % divisor == 0:
                factors.append(divisor)
                number //= divisor  # number = number // divisor
            else:
                divisor += 1

        # Output
        if short_form:
            temp = dict(Counter(factors))
            return [Pow(k, v) for k, v in temp.items()]
        return factors

    # analyze
    def analyze(self, short_form: bool = True) -> dict[str, dict[str, Any]]:
        """
        Analyze the number with almost all ``IntExt`` method

        Parameters
        ----------
        short_form : bool
            | Enable short form for some items
            | (Default: ``True``)

        Returns
        -------
        dict[str, dict[str, Any]]
            Detailed analysis


        Example:
        --------
        >>> test = IntExt(1024)
        >>> test.analyze()
        {
            'summary': {'number': 1024, 'length': 4, 'even': True, 'prime factor': [2^10], 'divisible': [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]},
            'convert': {'binary': '10000000000', 'octa': '2000', 'hex': '400', 'reverse': 4201, 'add to one': 7},
            'characteristic': {'prime': False, 'twisted prime': False, 'perfect': False, 'narcissistic': False, 'palindromic': False, 'palindromic prime': False}
        }
        """
        output = {
            "summary": {
                "number": self,
                "length": len(str(self)),
                "even": self.is_even(),
                "prime factor": self.prime_factor(short_form=short_form),  # type: ignore[call-overload]
                "divisible": self.divisible_list(),
            },
            "convert": {
                "binary": bin(self)[2:],
                "octa": oct(self)[2:],
                "hex": hex(self)[2:],
                # "hash": hash(self),
                "reverse": self.reverse(),
                "add to one": self.add_to_one_digit(),
            },
        }
        characteristic = {
            "prime": self.is_prime(),
            "twisted prime": self.is_twisted_prime(),
            "perfect": self.is_perfect(),
            "narcissistic": self.is_narcissistic(),
            "palindromic": self.is_palindromic(),
            "palindromic prime": self.is_palindromic_prime(),
        }
        if short_form:
            characteristic = DictBoolTrue(characteristic)

        output["characteristic"] = characteristic
        return output  # type: ignore

    @versionadded("5.1.0")
    def split(self, parts: int) -> list[int]:
        """
        Evenly split the number into ``parts`` parts

        Parameters
        ----------
        parts : int
            Split by how many parts

        Returns
        -------
        list[int]
            List of evenly splitted numbers


        Example:
        --------
        >>> IntExt(10).split(4)
        [2, 2, 3, 3]
        """
        p = max(1, parts)
        if p == 1:
            return [int(self)]

        quotient, remainder = divmod(self, p)
        return [quotient + (i >= (p - remainder)) for i in range(p)]


# Class
# ---------------------------------------------------------------------------
class IntBase(int, ABC):
    """
    A base class for creating custom integer-like types.
    Provides a hook for validation and extension.

    Usage:
    ------
    Use ``_validate(cls, value: int) -> None:`` classmethod to create custom validator
    """

    def __new__(cls, value: int = 0) -> Self:
        # Ensure the value is an integer
        if not isinstance(value, int):
            raise TypeError(f"{cls.__name__} must be initialized with an int, got {type(value).__name__}")
        # Optional validation hook
        cls._validate(value)
        return int.__new__(cls, value)

    @classmethod
    def _validate(cls, value: int) -> None:
        """Override in subclasses to add custom validation."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({int(self)})"


class PositiveInt(IntBase):
    """Only allows positive int"""

    @classmethod
    @override
    def _validate(cls, value: int) -> None:
        if value < 0:
            raise ValueError(f"{cls.__name__} must be non-negative")


class NegativeInt(IntBase):
    """Only allows negative int"""

    @classmethod
    @override
    def _validate(cls, value: int) -> None:
        if value >= 0:
            raise ValueError(f"{cls.__name__} must be non-positive")


class IntWithNote(IntBase):
    """Int with additional note"""

    def __new__(cls, value: int = 0) -> Self:
        ins = super().__new__(cls, value)
        ins.note = ""
        return ins

    def __repr__(self) -> str:
        if self.note == "":
            return f"{int(self)}"
            # return super().__repr__()
        return f"{self.__class__.__name__}({int(self)}, note={repr(self.note)})"

    def add_note(self, note: str) -> None:
        self.note = note
