"""
Absfuyu: Shorten number
-----------------------
Short number base on suffixes (deprecated, use absfuyu.numbers instead)

WILL BE REMOVED IN VERSION 7.0.0

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

from __future__ import annotations

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "UnitSuffixFactory",
    "CommonUnitSuffixesFactory",
    "Decimal",
    "shorten_number",
    "Duration",
    "SupportDurationFormatPreset",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Annotated, NamedTuple, ParamSpec, Protocol, Self, TypeVar

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


# Class - Duration
# ---------------------------------------------------------------------------
# Format preset
class SupportDurationFormatPreset(Protocol):
    def __call__(self, duration: Duration, /) -> str: ...


@dataclass
@versionadded("5.16.0")
class Duration:
    """
    Convert duration in seconds to a more readable form. Eg: 3 mins 2 secs

    Parameters
    ----------
    total_seconds : int | float
        Seconds to convert to
    """

    total_seconds: int | float

    years: int = field(init=False)
    months: int = field(init=False)
    days: int = field(init=False)
    hours: int = field(init=False)
    minutes: int = field(init=False)
    seconds: int = field(init=False)

    _formats: dict[str, SupportDurationFormatPreset] = field(init=False)

    # Calculate duration
    def _calculate_duration(self) -> None:
        SEC_PER_MIN = 60
        SEC_PER_HOUR = 3600
        SEC_PER_DAY = 86400
        SEC_PER_MONTH = 30 * SEC_PER_DAY
        SEC_PER_YEAR = 365 * SEC_PER_DAY

        secs = self.total_seconds

        self.years, secs = divmod(secs, SEC_PER_YEAR)
        self.months, secs = divmod(secs, SEC_PER_MONTH)
        self.days, secs = divmod(secs, SEC_PER_DAY)
        self.hours, secs = divmod(secs, SEC_PER_HOUR)
        self.minutes, self.seconds = divmod(secs, SEC_PER_MIN)

    # Format handling
    def _init_format(self) -> None:

        def duration_compact_preset(duration: Self, /) -> str:
            """
            Example: "1y 2m 3d 4h 5m 6s"
            (fields = hidden when = 0).
            """
            parts = []
            if duration.years:
                parts.append(f"{duration.years}y")
            if duration.months:
                parts.append(f"{duration.months}m")
            if duration.days:
                parts.append(f"{duration.days}d")
            if duration.hours:
                parts.append(f"{duration.hours}h")
            if duration.minutes:
                parts.append(f"{duration.minutes}m")
            if duration.seconds:
                parts.append(f"{duration.seconds}s")
            return " ".join(parts) if parts else "0s"

        def duration_HMS_only_preset(duration: Self, /) -> str:
            """
            Example: "02:15:09" (HH:MM:SS only).
            """
            total = duration.total_seconds
            h, m = divmod(total, 3600)
            m, s = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        def duration_digital_preset(duration: Self, /) -> str:
            """
            Examples:
            - If >= 1 day: "1d 02:03:04"
            - else: "02:03:04"
            """
            total = duration.total_seconds
            days, sec = divmod(total, 86400)
            h, sec = divmod(sec, 3600)
            m, s = divmod(sec, 60)

            if days:
                return f"{days}d {h:02d}:{m:02d}:{s:02d}"
            return f"{h:02d}:{m:02d}:{s:02d}"

        self._formats = {
            "compact": duration_compact_preset,
            "hms": duration_HMS_only_preset,
            "digital": duration_digital_preset,
        }

    @versionadded("5.17.0")
    def add_format(self, name: str, format_func: SupportDurationFormatPreset) -> None:
        """
        Add format style to Duration

        Parameters
        ----------
        name : str
            Name of the style (name will be lowercased)

        format_func : SupportDurationFormatPreset
            Format function
        """
        self._formats[name.lower().strip()] = format_func

    @property
    def available_formats(self) -> list[str]:
        """
        Available style format

        Returns
        -------
        list[str]
            All available style formats
        """
        return list(self._formats)

    def __format__(self, format_spec: str) -> str:
        """
        Change format of an object.

        Usage
        -----
        >>> print(f"{<object>:<format_spec>}")
        >>> print(<object>.__format__(<format_spec>))
        >>> print(format(<object>, <format_spec>))
        """

        func = self._formats.get(format_spec.lower().strip(), None)

        if func is None:
            return self.__str__()
        else:
            return func(self)

    # POST INIT
    def __post_init__(self) -> None:
        if not isinstance(self.total_seconds, (int, float)) or self.total_seconds < 0:
            raise ValueError("seconds must be a non-negative number")
        self._calculate_duration()
        self._init_format()

    def __str__(self) -> str:

        def _plural(n: int | float, word: str):
            return f"{n} {word}{'s' if n != 1 else ''}"

        parts = []
        if self.years:
            parts.append(_plural(self.years, "year"))
        if self.months:
            parts.append(_plural(self.months, "month"))
        if self.days:
            parts.append(_plural(self.days, "day"))
        if self.hours:
            parts.append(_plural(self.hours, "hour"))
        if self.minutes:
            parts.append(_plural(self.minutes, "minute"))
        if self.seconds:
            parts.append(_plural(self.seconds, "second"))
        return " ".join(parts) if parts else "0 second"

    # From other type of duration
    @classmethod
    def from_minute(cls, minutes: int | float) -> Self:
        return cls(minutes * 60)

    @classmethod
    def from_hour(cls, hours: int | float) -> Self:
        return cls(hours * 3600)

    @classmethod
    def from_day(cls, days: int | float) -> Self:
        return cls(days * 86400)

    @classmethod
    def from_month(cls, months: int | float) -> Self:
        return cls(months * 86400 * 30)

    @classmethod
    def from_year(cls, years: int | float) -> Self:
        return cls(years * 86400 * 365)
