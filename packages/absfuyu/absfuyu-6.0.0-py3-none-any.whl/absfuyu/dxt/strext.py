"""
Absfuyu: Data Extension
-----------------------
str extension

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["Text", "TextAnalyzeDictFormat"]


# Library
# ---------------------------------------------------------------------------
import random
from string import ascii_letters as _ascii_letters
from typing import NotRequired, Self, TypedDict

from absfuyu.core import GetClassMembersMixin, deprecated, versionadded, versionchanged
from absfuyu.util import set_min_max


# Support function
# ---------------------------------------------------------------------------
def _generate_string(
    charset: str | None = None,
    size: int = 8,
    times: int = 1,
    unique: bool = True,
) -> list[str]:
    """
    Generate a list of random string from character set
    (Random string generator)

    This is a lesser version of
    ``absfuyu.tools.generator.Generator.generate_string()``

    Parameters
    ----------
    charset : str, optional
        Custom character set, by default ``None``
        ([a-zA-Z] - string.ascii_letters)

    size : int, optional
            Length of each string in list, by default ``8``

    times : int, optional
        How many random string generated, by default ``1``

    unique : bool, optional
        Each generated text is unique, by default ``True``

    Returns
    -------
    list[str]
        List of random string generated
    """

    charset = _ascii_letters or charset

    try:
        char_lst = list(charset)  # type: ignore[arg-type]
    except Exception:
        char_lst = charset  # type: ignore[assignment]

    unique_string = []
    count = 0

    while count < times:
        gen_string = "".join(random.choice(char_lst) for _ in range(size))  # type: ignore
        if not unique:
            unique_string.append(gen_string)
            count += 1
        else:
            if gen_string not in unique_string:
                unique_string.append(gen_string)
                count += 1

    return unique_string


# Class
# ---------------------------------------------------------------------------
class TextAnalyzeDictFormat(TypedDict):
    """
    Dict format for ``Text.analyze()`` method

    Parameters
    ----------
    digit : int
        Number of digit characters

    uppercase : int
        Number of uppercase characters

    lowercase : int
        Number of lowercase characters

    other : int
        Number of other printable characters

    is_pangram : NotRequired[bool]
        Is a pangram (Not required)

    is_palindrome : NotRequired[bool]
        Is a palindrome (Not required)
    """

    digit: int
    uppercase: int
    lowercase: int
    other: int
    is_pangram: NotRequired[bool]
    is_palindrome: NotRequired[bool]


class Text(GetClassMembersMixin, str):
    """
    ``str`` extension

    >>> # For a list of new methods
    >>> Text.show_all_methods()
    """

    def divide(self, string_split_size: int = 60) -> list[str]:
        """
        Divide long string into smaller size

        Parameters
        ----------
        string_split_size : int
            Divide string every ``x`` character
            (Default: ``60``)

        Returns
        -------
        list[str]
            A list in which each item is a smaller
            string with the size of ``string_split_size``
            (need to be concaternate later)


        Example:
        --------
        >>> test = Text("This is an extremely long line of text!")
        >>> test.divide(string_split_size=20)
        ['This is an extremely', ' long line of text!']
        """
        temp = str(self)
        output = []
        while len(temp) != 0:
            output.append(temp[:string_split_size])
            temp = temp[string_split_size:]
        return output

    def divide_with_variable(
        self,
        split_size: int = 60,
        split_var_len: int = 12,
        custom_var_name: str | None = None,
    ) -> list[str]:
        """
        Divide long string into smaller size,
        then assign a random variable to splited
        string for later use

        Parameters
        ----------
        split_size : int
            Divide string every ``x`` character
            (Default: ``60``)

        split_var_len : int
            Length of variable name assigned to each item
            (Default: ``12``)

        custom_var_name : str
            Custom variable name when join string

        Returns
        -------
        list[str]
            A list in which each item is a smaller
            string with the size of ``split_size``
            and a way to concaternate them (when using ``print()``)


        Example:
        --------
        >>> test = Text("This is an extremely long line of text!")
        >>> test.divide_with_variable(split_size=20)
        [
            "qNTCnmkFPTJg='This is an extremely'",
            "vkmLBUykYYDG=' long line of text!'",
            'sBoSwEfoxBIH=qNTCnmkFPTJg+vkmLBUykYYDG',
            'sBoSwEfoxBIH'
        ]

        >>> test = Text("This is an extremely long line of text!")
        >>> test.divide_with_variable(split_size=20, custom_var_name="test")
        [
            "test1='This is an extremely'",
            "test2=' long line of text!'",
            'test=test1+test2',
            'test'
        ]
        """

        temp = self.divide(split_size)
        output = []

        # split variable
        splt_len = len(temp)

        if custom_var_name is None:
            splt_name = _generate_string(size=split_var_len, times=splt_len + 1)
            for i in range(splt_len):
                output.append(f"{splt_name[i]}='{temp[i]}'")
        else:
            for i in range(splt_len):
                output.append(f"{custom_var_name}{i + 1}='{temp[i]}'")

        # joined variable
        temp = []
        if custom_var_name is None:
            for i in range(splt_len):
                if i == 0:
                    temp.append(f"{splt_name[-1]}=")
                if i == splt_len - 1:
                    temp.append(f"{splt_name[i]}")
                else:
                    temp.append(f"{splt_name[i]}+")
        else:
            for i in range(splt_len):
                if i == 0:
                    temp.append(f"{custom_var_name}=")
                if i == splt_len - 1:
                    temp.append(f"{custom_var_name}{i + 1}")
                else:
                    temp.append(f"{custom_var_name}{i + 1}+")

        output.append("".join(temp))
        if custom_var_name is None:
            output.append(splt_name[-1])
        else:
            output.append(custom_var_name)

        return output

    @versionchanged("3.3.0", reason="Updated functionality")
    def analyze(self, full: bool = False) -> TextAnalyzeDictFormat:
        """
        String analyze (count number of type of character)

        Parameters
        ----------
        full : bool
            Full analyze when ``True``
            (Default: ``False``)

        Returns
        -------
        dict | TextAnalyzeDictFormat
            A dictionary contains number of digit character,
            uppercase character, lowercase character, and
            special character


        Example:
        --------
        >>> test = Text("Random T3xt!")
        >>> test.analyze()
        {'digit': 1, 'uppercase': 2, 'lowercase': 7, 'other': 2}
        """

        temp = self

        detail: TextAnalyzeDictFormat = {
            "digit": 0,
            "uppercase": 0,
            "lowercase": 0,
            "other": 0,
        }

        for x in temp:
            if ord(x) in range(48, 58):  # num
                detail["digit"] += 1
            elif ord(x) in range(65, 91):  # cap
                detail["uppercase"] += 1
            elif ord(x) in range(97, 123):  # low
                detail["lowercase"] += 1
            else:
                detail["other"] += 1

        if full:
            detail["is_palindrome"] = self.is_palindrome()
            detail["is_pangram"] = self.is_pangram()

        return detail

    def reverse(self) -> Self:
        """
        Reverse the string

        Returns
        -------
        Text
            Reversed string


        Example:
        --------
        >>> test = Text("Hello, World!")
        >>> test.reverse()
        '!dlroW ,olleH'
        """
        return self.__class__(self[::-1])

    @versionchanged("5.0.0", reason="Add ``custom_alphabet`` parameter")
    def is_pangram(self, custom_alphabet: set[str] | None = None) -> bool:
        """
        Check if string is a pangram

        A pangram is a unique sentence in which
        every letter of the alphabet is used at least once

        Parameters
        ----------
        custom_alphabet : set[str] | None, optional
            Custom alphabet to use
            (Default: ``None``)

        Returns
        -------
        bool
            | ``True`` if string is a pangram
            | ``False`` if string is not a pangram
        """
        text = self
        if custom_alphabet is None:
            alphabet = set("abcdefghijklmnopqrstuvwxyz")
        else:
            alphabet = custom_alphabet
        return not set(alphabet) - set(text.lower())

    def is_palindrome(self) -> bool:
        """
        Check if string is a palindrome

            A palindrome is a word, verse, or sentence
            or a number that reads the same backward or forward

        Returns
        -------
        bool
            | ``True`` if string is a palindrome
            | ``False`` if string is not a palindrome
        """
        text = self
        # Use string slicing [start:end:step]
        return text == text[::-1]

    def to_hex(self, raw: bool = False) -> str:
        r"""
        Convert string to hex form

        Parameters
        ----------
        raw : bool
            | ``False``: hex string in the form of ``\x`` (default)
            | ``True``: normal hex string

        Returns
        -------
        str
            Hexed string


        Example:
        --------
        >>> test = Text("Hello, World!")
        >>> test.to_hex()
        '\\x48\\x65\\x6c\\x6c\\x6f\\x2c\\x20\\x57\\x6f\\x72\\x6c\\x64\\x21'
        """
        text = self

        byte_str = text.encode("utf-8")
        # hex_str = byte_str.hex()

        if raw:
            return byte_str.hex()

        temp = byte_str.hex("x")
        return "\\x" + temp.replace("x", "\\x")

    def random_capslock(self, probability: int = 50) -> Self:
        """
        Randomly capslock letter in string

        Parameters
        ----------
        probability : int
            Probability in range [0, 100]
            (Default: ``50``)

        Returns
        -------
        Text
            Random capslocked text


        Example:
        --------
        >>> test = Text("This is an extremely long line of text!")
        >>> test.random_capslock()
        'tHis iS An ExtREmELY loNg liNE oF tExT!'
        """
        probability = int(set_min_max(probability))
        text = self.lower()

        random_caps = (
            x.upper() if random.randint(1, 100) <= probability else x for x in text
        )
        return self.__class__("".join(random_caps))

    @deprecated(
        "5.2.0",
        reason="str already has swapcase() method, will be removed in version 5.3.0",
    )
    @versionchanged("5.0.0", reason="Use ``str.swapcase()``")
    def reverse_capslock(self) -> Self:
        """
        Reverse capslock in string

        Returns
        -------
        Text
            Reversed capslock ``Text``


        Example:
        --------
        >>> test = Text("Foo")
        >>> test.reverse_capslock()
        'fOO'
        """
        return self.__class__(self.swapcase())

    def to_list(self) -> list[str]:
        """
        Convert into list

        Returns
        -------
        list[str]
            List of string


        Example:
        --------
        >>> test = Text("test")
        >>> test.to_list()
        ['t', 'e', 's', 't']
        """
        return list(self)

    @deprecated("5.0.0", reason="Unused, will be removed in version 5.3.0")
    def to_listext(self) -> None:
        """Deprecated, will be removed soon"""
        raise NotImplementedError("Deprecated, will be removed soon")

    @versionadded("3.3.0")
    def count_pattern(self, pattern: str, ignore_capslock: bool = False) -> int:
        """
        Returns how many times ``pattern`` appears in text

        Parameters
        ----------
        pattern : str
            Pattern to count

        ignore_capslock : bool
            Ignore the pattern uppercase or lowercase
            (Default: ``False`` - Exact match)

        Returns
        -------
        int
            How many times pattern appeared


        Example:
        --------
        >>> Text("test").count_pattern("t")
        2
        """
        if len(pattern) > len(self):
            raise ValueError(f"len(<pattern>) must not larger than {len(self)}")

        temp = str(self)
        if ignore_capslock:
            pattern = pattern.lower()
            temp = temp.lower()

        out = [
            1
            for i in range(len(temp) - len(pattern) + 1)
            if temp[i : i + len(pattern)] == pattern
        ]
        return sum(out)

    @versionadded("3.3.0")
    def hapax(self, strict: bool = False) -> list[str]:
        """
        A hapax legomenon (often abbreviated to hapax)
        is a word which occurs only once in either
        the written record of a language, the works of
        an author, or in a single text.

        This function returns a list of hapaxes (if any)
        (Lettercase is ignored)

        Parameters
        ----------
        strict : bool
            Remove all special characters before checking for hapax
            (Default: ``False``)

        Returns
        -------
        list[str]
            A list of hapaxes


        Example:
        --------
        >>> test = Text("A a. a, b c c= C| d d")
        >>> test.hapax()
        ['a', 'a.', 'a,', 'b', 'c', 'c=', 'c|']

        >>> test.hapax(strict=True)
        ['b']
        """
        word_list: list[str] = self.lower().split()
        if strict:
            remove_characters: list[str] = list(r"\"'.,:;|()[]{}\/!@#$%^&*-_=+?<>`~")
            temp = str(self)
            for x in remove_characters:
                temp = temp.replace(x, "")
            word_list = temp.lower().split()

        hapaxes = filter(lambda x: word_list.count(x) == 1, word_list)
        return list(hapaxes)

    @versionadded("5.0.0")
    def shorten(self, shorten_size: int = 60) -> str:
        """
        Shorten long text

        Parameters
        ----------
        shorten_size : int, optional
            How many characters per line.
            Minimum is ``1``, by default ``60``

        Returns
        -------
        str
            Shortened text


        Example:
        --------
        >>> test = Text("a" * 200)
        >>> test.shorten()
        (
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaaaaaaaaaaaaaaa'
        )
        """
        shorten_text_list: list[str] = self.divide(
            string_split_size=max(1, shorten_size)
        )
        shorten_text_list = [repr(x) for x in shorten_text_list]
        out = "(\n" + "\n".join(shorten_text_list) + "\n)"
        return out
