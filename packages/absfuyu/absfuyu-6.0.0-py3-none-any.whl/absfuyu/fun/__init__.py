"""
Absfuyu: Fun
------------
Some fun or weird stuff

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["zodiac_sign", "happy_new_year", "human_year_to_dog_year"]


# Library
# ---------------------------------------------------------------------------
from datetime import date

from absfuyu.core import deprecated, versionadded, versionchanged
from absfuyu.logger import logger
from absfuyu.tools.shutdownizer import ShutDownizer
from absfuyu.util.lunar import LunarCalendar


# Function
# ---------------------------------------------------------------------------
@versionchanged("5.0.0", reason="Updated functionality")
def zodiac_sign(day: int, month: int, zodiac13: bool = False) -> str:
    """
    Calculate zodiac sign

    Parameters
    ----------
    day : int
        Day (in range [1, 31])

    month : int
        Month (in range [1, 12])

    zodiac13 : bool
        13 zodiacs mode (Default: ``False``)

    Returns
    -------
    str
        Zodiac sign
    """

    # Condition check
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        raise ValueError("Value out of range")

    if zodiac13:
        zodiac_dates = {
            "Capricorn": ((1, 21), (2, 16)),
            "Aquarius": ((2, 17), (3, 11)),
            "Pisces": ((3, 12), (4, 18)),
            "Aries": ((4, 19), (5, 13)),
            "Taurus": ((5, 14), (6, 21)),
            "Gemini": ((6, 22), (7, 20)),
            "Cancer": ((7, 21), (8, 10)),
            "Leo": ((8, 11), (9, 16)),
            "Virgo": ((9, 17), (10, 30)),
            "Libra": ((10, 31), (11, 23)),
            "Scorpio": ((11, 24), (11, 29)),
            "Ophiuchus": ((11, 30), (12, 17)),
            "Sagittarius": ((12, 18), (1, 20)),
        }
    else:
        zodiac_dates = {
            "Capricorn (E)": ((12, 22), (1, 19)),
            "Aquarius (A)": ((1, 20), (2, 18)),
            "Pisces (W)": ((2, 19), (3, 20)),
            "Aries (F)": ((3, 21), (4, 19)),
            "Taurus (E)": ((4, 20), (5, 20)),
            "Gemini (A)": ((5, 21), (6, 20)),
            "Cancer (W)": ((6, 21), (7, 22)),
            "Leo (F)": ((7, 23), (8, 22)),
            "Virgo (E)": ((8, 23), (9, 22)),
            "Libra (A)": ((9, 23), (10, 22)),
            "Scorpio (W)": ((10, 23), (11, 21)),
            "Sagittarius (F)": ((11, 22), (12, 21)),
        }

    result = ""
    for sign, (start_date, end_date) in zodiac_dates.items():
        start_month, start_day = start_date
        end_month, end_day = end_date

        if (month == start_month and day >= start_day) or (
            month == end_month and day <= end_day
        ):
            result = sign
            break
    return result


# For new year only
def happy_new_year(forced: bool = False, include_lunar: bool = False) -> None:
    """
    Only occurs on 01/01 every year

    Parameters
    ----------
    forced : bool
        Shutdown ASAP (Default: ``False``)

    include_lunar : bool
        Include Lunar New Year (Default: ``False``)
    """

    if forced:
        return ShutDownizer().shutdown()

    today = date.today()
    m = today.month
    d = today.day
    solar_new_year = m == 1 and d == 1
    logger.debug(f"Solar: {today}")

    if include_lunar:
        lunar = LunarCalendar.now().date
        lunar_new_year = lunar.month == 1 and lunar.day == 1
        logger.debug(f"Lunar: {lunar}")
    else:
        lunar_new_year = False

    if solar_new_year or lunar_new_year:
        print("Happy New Year! You should take rest now.")
        return ShutDownizer().shutdown()
    else:
        raise SystemExit("The time has not come yet")


@versionadded("5.0.0")
def human_year_to_dog_year(
    human_year: int | float, is_small: bool = True
) -> int | float:
    """
    Convert human's year to dog's year

    General Guidelines:
    1. First Year: The first year of a dog's life
    is roughly equal to 15 human years.
    2. Second Year: The second year adds about 9 human years,
    making a 2-year-old dog equivalent to about 24 human years.
    3. Subsequent Years: After the second year,
    each additional yeartypically equals about 4-5 human years,
    depending on the dog's size and breed. (Small-4, Large-5)

    Parameters
    ----------
    human_year : int | float
        Dog's age in human year

    is_small : bool, optional
        Is the dog small or not, by default ``True``

    Returns
    -------
    int | float
        Dog's year/age

    Raises
    ------
    ValueError
        When ``human_year`` < 0
    """

    if human_year < 0:
        raise ValueError("Value must be positive")
    if human_year <= 1:
        return human_year * 15
    elif human_year <= 2:
        return 15 + (human_year - 1) * 9
    else:
        if is_small:
            return 24 + (human_year - 2) * 4
        else:
            return 24 + (human_year - 2) * 5
