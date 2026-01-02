"""
Absfuyu: Shorten number
-----------------------
Short number base on suffixes

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "UnitSuffixFactory",
    "CommonUnitSuffixesFactory",
    "Decimal",
    "shorten_number",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Annotated, NamedTuple, ParamSpec, Self, TypeVar

from absfuyu.core import versionadded

# Type
# ---------------------------------------------------------------------------
P = ParamSpec("P")  # Parameter type
N = TypeVar("N", int, float)  # Number type


# Class - Decimal
# ---------------------------------------------------------------------------
@versionadded("4.1.0")
class UnitSuffixFactory(NamedTuple):
    base: int
    short_name: list[str]
    full_name: list[str]


@versionadded("4.1.0")
class CommonUnitSuffixesFactory:
    NUMBER = UnitSuffixFactory(
        1000,
        [
            "",
            "K",
            "M",
            "B",
            "T",
            "Qa",
            "Qi",
            "Sx",
            "Sp",
            "Oc",
            "No",
            "Dc",
            "Ud",
            "Dd",
            "Td",
            "Qad",
            "Qid",
            "Sxd",
            "Spd",
            "Ocd",
            "Nod",
            "Vg",
            "Uvg",
            "Dvg",
            "Tvg",
            "Qavg",
            "Qivg",
            "Sxvg",
            "Spvg",
            "Ovg",
            "Nvg",
            "Tg",
            "Utg",
            "Dtg",
            "Ttg",
            "Qatg",
            "Qitg",
            "Sxtg",
            "Sptg",
            "Otg",
            "Ntg",
        ],
        [
            "",  # < Thousand
            "Thousand",
            "Million",
            "Billion",  # 1e9
            "Trillion",
            "Quadrillion",
            "Quintillion",
            "Sextillion",
            "Septillion",
            "Octillion",
            "Nonillion",
            "Decillion",  # 1e33
            "Undecillion",
            "Duodecillion",
            "Tredecillion",
            "Quattuordecillion",
            "Quindecillion",
            "Sexdecillion",
            "Septendecillion",
            "Octodecillion",
            "Novemdecillion",
            "Vigintillion",  #  1e63
            "Unvigintillion",
            "Duovigintillion",
            "Tresvigintillion",
            "Quattuorvigintillion",
            "Quinvigintillion",
            "Sesvigintillion",
            "Septemvigintillion",
            "Octovigintillion",
            "Novemvigintillion",
            "Trigintillion",  # 1e93
            "Untrigintillion",
            "Duotrigintillion",
            "Trestrigintillion",
            "Quattuortrigintillion",
            "Quintrigintillion",
            "Sestrigintillion",
            "Septentrigintillion",
            "Octotrigintillion",
            "Noventrigintillion",  #  1e120
        ],
    )
    DATA_SIZE = UnitSuffixFactory(
        1024,
        ["b", "Kb", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "BB"],
        [
            "byte",
            "kilobyte",
            "megabyte",
            "gigabyte",
            "terabyte",
            "petabyte",
            "exabyte",
            "zetabyte",
            "yottabyte",
            "brontobyte",
        ],
    )


@dataclass
@versionadded("4.1.0")
class Decimal:
    """
    Shorten large number

    Parameters
    ----------
    original_value : int | float
        Value to shorten

    base : int
        Short by base (must be > 0)

    suffixes : list[str]
        List of suffixes to use (ascending order)

    factory : UnitSuffixFactory | None
        ``UnitSuffixFactory`` to use
        (will overwrite ``base`` and ``suffixes``)

    suffix_full_name : bool
        Use suffix full name (available with ``UnitSuffixFactory``), by default ``False``

    Returns
    -------
    Decimal
        Decimal instance
    """

    original_value: int | float = field(repr=False)
    base: Annotated[int, "positive", "not_zero"] = field(repr=False, default=1000)
    suffixes: list[str] = field(repr=False, default_factory=list)
    factory: UnitSuffixFactory | None = field(repr=False, default=None)
    suffix_full_name: bool = field(repr=False, default=False)
    # Post init
    value: int | float = field(init=False)
    suffix: str = field(init=False)

    def __post_init__(self) -> None:
        self.base = max(1, self.base)  # Make sure that base >= 1
        self._get_factory()
        self.value, self.suffix = self._convert_decimal()

    def __str__(self) -> str:
        return self.to_text().strip()

    @classmethod
    def number(cls, value: int | float, suffix_full_name: bool = False) -> Self:
        """Decimal for normal large number"""
        return cls(
            value,
            factory=CommonUnitSuffixesFactory.NUMBER,
            suffix_full_name=suffix_full_name,
        )

    @classmethod
    def data_size(cls, value: int | float, suffix_full_name: bool = False) -> Self:
        """Decimal for data size"""
        return cls(
            value,
            factory=CommonUnitSuffixesFactory.DATA_SIZE,
            suffix_full_name=suffix_full_name,
        )

    @staticmethod
    def scientific_short(value: int | float) -> str:
        """Short number in scientific format"""
        return f"{value:.2e}"

    def _get_factory(self) -> None:
        if self.factory is not None:
            self.base = self.factory.base
            self.suffixes = self.factory.full_name if self.suffix_full_name else self.factory.short_name

    def _convert_decimal(self) -> tuple[float, str]:
        """Convert to smaller number"""
        suffix = self.suffixes[0] if len(self.suffixes) > 0 else ""
        unit = 1
        for i, suffix in enumerate(self.suffixes):
            unit = self.base**i
            if self.original_value < unit * self.base:
                break
        output = self.original_value / unit
        return output, suffix

    def to_text(self, decimal: int = 2, *, separator: str = " ", float_only: bool = True) -> str:
        """
        Convert to string

        Parameters
        ----------
        decimal : int, optional
            Round up to which decimal, by default ``2``

        separator : str, optional
            Character between value and suffix, by default ``" "``

        float_only : bool, optional
            Returns value as <float> instead of <int> when ``decimal = 0``, by default ``True``

        Returns
        -------
        str
            Decimal string
        """
        val = self.value.__round__(decimal)
        formatted_value = f"{val:,}"
        if not float_only and decimal == 0:
            formatted_value = f"{int(val):,}"
        return f"{formatted_value}{separator}{self.suffix}"


# Decorator
# ---------------------------------------------------------------------------
@versionadded("5.0.0")
def shorten_number(f: Callable[P, N]) -> Callable[P, Decimal]:
    """
    Shorten the number value by name

    Parameters
    ----------
    f : Callable[P, N]
        Function that return ``int`` or ``float``

    Returns
    -------
    Callable[P, Decimal]
        Function that return ``Decimal``


    Usage
    -----
    Use this as a decorator (``@shorten_number``)

    Example:
    --------
    >>> import random
    >>> @shorten_number
    >>> def big_num() -> int:
    ...     random.randint(100000000, 10000000000)
    >>> big_num()
    4.20 B
    """

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Decimal:
        value = Decimal.number(f(*args, **kwargs))
        return value

    return wrapper
