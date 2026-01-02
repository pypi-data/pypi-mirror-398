"""
Absfuyu: Keygen
---------------
Mod7 product key generator (90's)

This is for educational and informative purposes only.

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Keygen"]


# Library
# ---------------------------------------------------------------------------
import random

from absfuyu.core import BaseClass


# Class
# ---------------------------------------------------------------------------
class Keygen(BaseClass):
    """Key generator"""

    @staticmethod
    def _is_mod7(text: str) -> bool:
        """
        Check if sum of elements in a string is divisible by 7

        :param text: number in str type to check
        """
        text = str(text)  # Safety convert
        try:
            res = sum(map(int, text)) % 7
            # logger.debug(f"Sum value: {res}")
            return res == 0
        except Exception:
            raise ValueError("Invalid string")  # noqa: B904

    @classmethod
    def _mod7_gen(cls, num_of_digits: int, *, fillchar: str = "0") -> str:
        """
        Generate a number with desired length that is divisible by 7

        Parameters
        ----------
        num_of_digits : int
            Length of number

        fillchar : str
            filled character when `len(generated number)` < `num_of_digits`

        Returns
        -------
        str:
            Mod7 number
        """

        # Init
        mod7_num: int = 0

        # Conditions
        max_value = 10**num_of_digits - 1
        mod7_valid = False
        invalid_digits = [0, 8, 9]  # Invalid last digit

        # Loop
        while not mod7_valid:
            # Gen num
            mod7_num = random.randint(0, max_value)

            # Check last digit
            if int(str(mod7_num)[-1]) in invalid_digits:
                continue

            # Check divide by 7
            if cls._is_mod7(str(mod7_num)):
                mod7_valid = True

        # Output
        return str(mod7_num).rjust(num_of_digits, fillchar)

    @classmethod
    def mod7_cd_key(cls, fast: bool = False) -> str:
        """
        CD Key generator

        Format: ``XXX-XXXXXXX``

        Rules:

        - Last seven digits must add to be divisible by ``7``
        - First 3 digits cannot be ``333``, ``444``,..., ``999``
        - Last digit of last seven digits cannot be ``0``, ``8`` or ``9``

        Parameters
        ----------
        fast : bool
            Use pre-generated key
            (Default: ``False``)

        Returns
        -------
        str:
            Mod7 Key
        """

        # Fast mode: pre-generated key
        if fast:
            return "111-1111111"

        # PART 01
        part1_valid = False
        part1_not_valid_digits = [333, 444, 555, 666, 777, 888]
        part1: str = ""
        while not part1_valid:  # Loop check
            part1_num = random.randint(0, 998)  # Gen random int from 0 to 998
            # part1_num = random.randint(100,300) # or just use this
            if part1_num not in part1_not_valid_digits:
                part1 = str(part1_num).rjust(3, "0")  # Convert into string
                part1_valid = True  # Break loop

        # PART 02
        part2 = cls._mod7_gen(num_of_digits=7)

        # OUTPUT
        return f"{part1}-{part2}"

    @classmethod
    def mod7_11_digit_key(cls, fast: bool = False) -> str:
        """
        11-digit CD Key generator

        Format: ``XXXX-XXXXXXX``

        - ``XXXX``: Can be anything from ``0001`` to ``9991``. The last digit must be 3rd digit + ``1`` or ``2``. When the result is > ``9``, it overflows to ``0`` or ``1``.
        - ``XXXXXXX``: Same as CD Key

        Parameters
        ----------
        fast : bool
            Use pre-generated key
            (Default: ``False``)

        Returns
        -------
        str:
            Mod7 Key
        """

        # Fast mode: pre-generated key
        if fast:
            return "0001-0000007"

        # PART 01
        part1_valid = False
        part1: str = ""
        while not part1_valid:
            part1_1_num = random.randint(0, 999)  # Random 3-digit number
            last_digit_choice = [1, 2]  # Choice for last digit
            part1_2_num = int(str(part1_1_num)[-1]) + random.choice(
                last_digit_choice
            )  # Make last digit
            if part1_2_num > 9:  # Check condition then overflow
                part1_2_num = int(str(part1_2_num)[-1])
            part1_str = f"{part1_1_num}{part1_2_num}"  # Concat string
            if int(part1_str) < 9991:  # Check if < 9991
                part1 = part1_str.rjust(4, "0")
                part1_valid = True

        # PART 02
        part2 = cls._mod7_gen(num_of_digits=7)

        # OUTPUT
        return f"{part1}-{part2}"

    @classmethod
    def mod7_oem_key(cls, fast: bool = False) -> str:
        """
        OEM Key generator

        Format: ``ABCYY-OEM-0XXXXXX-XXXXX``

        - ``ABC``: The day of the year. It can be any value from ``001`` to ``366``
        - ``YY``: The last two digits of the year. It can be anything from ``95`` to ``03``
        - ``0XXXXXX``: A random number that has a sum that is divisible by ``7`` and does not end with ``0``, ``8`` or ``3``.
        - ``XXXXX``: A random 5-digit number

        Parameters
        ----------
        fast : bool
            Use pre-generated key
            (Default: ``False``)

        Returns
        -------
        str:
            Mod7 Key
        """

        # Fast mode: pre-generated key
        if fast:
            return "00100-OEM-0000007-00000"

        # PART ABC
        abc_part = str(random.randint(1, 365)).rjust(3, "0")

        # PART YY
        year_choice = ["95", "96", "97", "98", "99", "00", "01", "02"]
        # isleap = [False, True, False, False, False, True, False, False]
        # year_choice = ["95", "96", "97", "98", "99", "00", "01", "02", "03"] # "03" not wotk on win95
        y_part = random.choice(year_choice)

        # NUM PART
        num_part = cls._mod7_gen(num_of_digits=6)

        # NUM PART 02
        num_part_2 = str(random.randint(0, 99999)).rjust(5, "0")

        # OUTPUT
        return f"{abc_part}{y_part}-OEM-0{num_part}-{num_part_2}"

    @classmethod
    def mod7_combo(cls, fast: bool = False):
        """
        A combo that consist of CD, 11-digit, and OEM Key

        Parameters
        ----------
        fast : bool
            Use pre-generated key
            (Default: ``False``)

        Returns
        -------
        dict:
            Mod7 Key combo
        """
        out = {
            "CD Key": cls.mod7_cd_key(fast=fast),
            "OEM Key": cls.mod7_oem_key(fast=fast),
            "11-digit Key": cls.mod7_11_digit_key(fast=fast),
        }
        return out
