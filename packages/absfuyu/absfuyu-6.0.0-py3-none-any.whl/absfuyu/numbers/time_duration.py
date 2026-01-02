"""
Absfuyu: Time duration
----------------------
Short time

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

from __future__ import annotations

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "Duration",
]


# Library
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field
from typing import Protocol, Self

from absfuyu.core import versionadded


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
