"""
Absufyu: Utilities
------------------
Some random utilities

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # util
    "get_installed_package",
    "set_min",
    "set_max",
    "set_min_max",
    "stop_after_day",
    "convert_to_raw_unicode",
    # shorten number
    "Decimal",
]


# Library
# ---------------------------------------------------------------------------
import pkgutil
import subprocess
from datetime import datetime
from string import printable

from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.util.shorten_number import Decimal


# Function
# ---------------------------------------------------------------------------
@versionchanged("2.7.1", reason="Use ``pkgutil`` lib")
def get_installed_package():
    """
    Return a list of installed packages

    Returns
    -------
    list[str]
        List of installed packages
    """
    iter_modules = list(
        {module.name for module in pkgutil.iter_modules() if module.ispkg}
    )
    return sorted(iter_modules)


@deprecated("5.0.0")
def set_min(
    current_value: int | float,
    *,
    min_value: int | float = 0,
) -> int | float:
    """
    Return ``min_value`` when ``current_value`` < ``min_value``

    Parameters
    ----------
    current_value : int | float
        Current value

    min_value : int | float
        Minimum value
        (Default: ``0``)

    Returns
    -------
    int | float
        Analyzed value


    Example:
    --------
    >>> set_min(-1)
    0
    """
    # if current_value < min_value:
    #     current_value = min_value
    # return current_value
    return max(min_value, current_value)


@deprecated("5.0.0")
def set_max(
    current_value: int | float,
    *,
    max_value: int | float = 100,
) -> int | float:
    """
    Return ``max_value`` when ``current_value`` > ``max_value``

    Parameters
    ----------
    current_value : int | float
        Current value

    max_value : int | float
        Maximum value
        (Default: ``100``)

    Returns
    -------
    int | float
        Analyzed value


    Example:
    --------
    >>> set_max(101)
    100
    """
    # if current_value > max_value:
    #     current_value = max_value
    # return current_value
    return min(max_value, current_value)


def set_min_max(
    current_value: int | float,
    *,
    min_value: int | float = 0,
    max_value: int | float = 100,
) -> int | float:
    """
    Return ``min_value`` | ``max_value`` when ``current_value``
    is outside ``[min_value, max_value]``

    Parameters
    ----------
    current_value : int | float
        Current value

    min_value : int | float
        Minimum value
        (Default: ``0``)

    max_value : int | float
        Maximum value
        (Default: ``100``)

    Returns
    -------
    int | float
        Analyzed value


    Example:
    --------
    >>> set_min_max(808)
    100
    """
    # Set min
    # current_value = set_min(current_value, min_value=min_value)
    current_value = max(current_value, min_value)
    # Set max
    # current_value = set_max(current_value, max_value=max_value)
    current_value = min(current_value, max_value)
    return current_value


@versionchanged("5.6.0", reason="New `custom_msg` parameter")
@versionadded("3.2.0")
def stop_after_day(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    *,
    custom_msg: str | None = None,
) -> None:
    """
    Stop working after specified day.
    Put the function at the begining of the code is recommended.

    Parameters
    ----------
    year : int
        Desired year
        (Default: ``None``)

    month : int
        Desired month
        (Default: ``None``)

    day : int
        Desired day
        (Default: ``None`` - 1 day trial)

    custom_msg : str
        Custom exit message
        (Default: ``None``)
    """
    # None checking - By default: 1 day trial
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    if day is None:
        day = now.day + 1

    # Logic
    end_date = datetime(year, month, day)
    result = end_date - now
    if result.days < 0:
        if custom_msg:
            raise SystemExit(custom_msg)
        raise SystemExit("End of time")


@versionadded("5.4.0")
def convert_to_raw_unicode(text: str, partial: bool = True) -> str:
    r"""
    Convert text to raw unicode variant.

    Parameters
    ----------
    text : str
        Text to convert

    partial : bool, optional
        Only convert characters that not in ``string.printable``,
        by default ``True``

    Returns
    -------
    str
        Converted text.


    Example:
    --------
    >>> convert_to_raw_unicode("résumé")
    r\u00E9sum\u00E9

    >>> convert_to_raw_unicode("résumé", partial=False)
    \u0072\u00E9\u0073\u0075\u006D\u00E9
    """

    character_set = printable

    def _convert(character: str) -> str:
        """Get unicode value"""
        # ord(c): Returns the Unicode code point for a one-character string c.
        _ord = ord(character)
        # f"\\u{_ord:04X}": Formats the Unicode code point as a four-digit
        # hexadecimal number for code points less than 0x10000.
        # f"\\U{_ord:08X}": Formats the Unicode code point as an eight-digit
        # hexadecimal number for code points greater than or equal to 0x10000.
        return f"\\u{_ord:04X}" if _ord < 0x10000 else f"\\U{_ord:08X}"

    return "".join(
        character if character in character_set and partial else _convert(character)
        for character in text
    )


@versionadded("5.9.0")
def is_command_available(cmd: list[str] | str, err_msg: str = "") -> None:
    """
    Checks if the desired command available

    Parameters
    ----------
    cmd : list[str] | str
        Command to check

    err_msg : str, optional
        Custom error message, by default ""

    Raises
    ------
    ValueError
        When command is unvailable
    """
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        raise ValueError(err_msg)
