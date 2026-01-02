"""
Absfuyu: Number to word
-----------------------
Convert number to word

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["NumberToWords"]


# Library
# ---------------------------------------------------------------------------
from abc import ABC, abstractmethod
from decimal import Decimal


# Class
# ---------------------------------------------------------------------------
class NumberToWordsBase(ABC):
    """
    Base abstract class for Number to words
    """

    @abstractmethod
    def convert(self, number: int) -> str:
        """
        Convert number to words

        Parameters
        ----------
        number : int
            Number to convert to

        Returns
        -------
        str
            Number in word form
        """
        pass


class NumberToWordsEN(NumberToWordsBase):
    """
    Number to words - English

    Support up to 10^120
    """

    _ones = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    ]

    _tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    _scales = [
        "",  # 10^0
        "thousand",  # 10^3
        "million",  # 10^6
        "billion",  # 10^9
        "trillion",  # 10^12
        "quadrillion",  # 10^15
        "quintillion",
        "sextillion",
        "septillion",
        "octillion",
        "nonillion",
        "decillion",
        "undecillion",
        "duodecillion",
        "tredecillion",
        "quattuordecillion",
        "quindecillion",
        "sexdecillion",
        "septendecillion",
        "octodecillion",
        "novemdecillion",
        "vigintillion",
        "unvigintillion",
        "duovigintillion",
        "tresvigintillion",
        "quattuorvigintillion",
        "quinvigintillion",
        "sesvigintillion",
        "septemvigintillion",
        "octovigintillion",
        "novemvigintillion",
        "trigintillion",
        "untrigintillion",
        "duotrigintillion",
        "trestrigintillion",
        "quattuortrigintillion",
        "quintrigintillion",
        "sestrigintillion",
        "septentrigintillion",
        "octotrigintillion",
        "noventrigintillion",
    ]

    def convert(self, number) -> str:
        dec = Decimal(str(number))

        if dec == 0:
            return "zero"

        sign = ""
        if dec < 0:
            sign = "minus "
            dec = abs(dec)

        integer_part = int(dec)
        fractional_part = dec - integer_part

        words = sign + self._convert_integer(integer_part)

        if fractional_part != 0:
            frac_digits = str(fractional_part).split(".")[1]
            frac_words = " ".join(self._ones[int(d)] for d in frac_digits)
            words += f" point {frac_words}"

        return words

    def _convert_integer(self, number: int) -> str:
        if number == 0:
            return "zero"

        parts = []
        scale_index = 0

        try:
            while number > 0:
                number, group = divmod(number, 1000)
                if group > 0:
                    text = self._under_1000(group)
                    scale = self._scales[scale_index]
                    parts.append(f"{text} {scale}".strip())
                scale_index += 1
        except IndexError:
            raise ValueError("Number to large")

        return " ".join(reversed(parts))

    def _under_1000(self, number: int) -> str:
        hundreds, rest = divmod(number, 100)
        parts = []

        if hundreds > 0:
            parts.append(f"{self._ones[hundreds]} hundred")

        if rest > 0:
            if hundreds > 0:
                parts.append("and")
            parts.append(self._under_100(rest))

        return " ".join(parts)

    def _under_100(self, number: int) -> str:
        if number < 20:
            return self._ones[number]

        tens, unit = divmod(number, 10)
        if unit == 0:
            return self._tens[tens]

        return f"{self._tens[tens]} {self._ones[unit]}"


class NumberToWordsVI(NumberToWordsBase):
    """
    Number to words - Vietnamese

    Support:
    - Scale infinitely
    - Decimal number
    """

    _ones = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def convert(self, number: int | float) -> str:
        dec = Decimal(str(number))

        if dec == 0:
            return "không"

        sign = ""
        if dec < 0:
            sign = "âm "
            dec = abs(dec)

        integer_part = int(dec)
        fractional_part = dec - integer_part

        words = sign + self._convert_integer(integer_part)

        if fractional_part != 0:
            frac_digits = str(fractional_part).split(".")[1]
            frac_words = " ".join(self._ones[int(d)] for d in frac_digits)
            words += f" phẩy {frac_words}"

        return words

    def _convert_integer(self, number: int) -> str:
        parts = []
        index = 0

        while number > 0:
            number, group = divmod(number, 1000)
            if group > 0:
                text = self._under_1000(group)
                scale = self._scale_name(index)
                parts.append(f"{text} {scale}".strip())
            index += 1

        return " ".join(reversed(parts))

    def _scale_name(self, index: int) -> str:
        if index == 0:
            return ""

        base = ["", "nghìn", "triệu"]
        pos = index % 3
        level = index // 3

        scale = base[pos]
        if level > 0:
            scale = f"{scale} {'tỷ ' * level}".strip()

        return scale.strip()

    def _under_1000(self, number: int) -> str:
        hundreds, rest = divmod(number, 100)
        parts = []

        if hundreds > 0:
            parts.append(f"{self._ones[hundreds]} trăm")

        if rest > 0:
            if hundreds > 0 and rest < 10:
                parts.append("lẻ")
            parts.append(self._under_100(rest))

        return " ".join(parts)

    def _under_100(self, number: int) -> str:
        if number < 10:
            return self._ones[number]

        tens, unit = divmod(number, 10)

        if tens == 1:
            if unit == 0:
                return "mười"
            if unit == 5:
                return "mười lăm"
            return f"mười {self._ones[unit]}"

        result = f"{self._ones[tens]} mươi"

        if unit == 0:
            return result
        if unit == 1:
            return f"{result} mốt"
        if unit == 5:
            return f"{result} lăm"

        return f"{result} {self._ones[unit]}"


# Main
class NumberToWords:
    _languages: dict[str, NumberToWordsBase] = {
        "en": NumberToWordsEN,
        "vi": NumberToWordsVI,
    }

    def __init__(self, lang: str = "en"):
        self.set_language(lang)

    def set_language(self, lang: str) -> None:
        if lang not in self._languages:
            raise ValueError(f"Unsupported language: {lang}")
        # self._converter = self._languages[lang]()
        self._converter: NumberToWordsBase = self._languages.get(lang, NumberToWordsEN)()

    def convert(self, number: int) -> str:
        """
        Convert number to words

        Parameters
        ----------
        number : int
            Number to convert to

        Returns
        -------
        str
            Number in word form
        """
        return self._converter.convert(number)
