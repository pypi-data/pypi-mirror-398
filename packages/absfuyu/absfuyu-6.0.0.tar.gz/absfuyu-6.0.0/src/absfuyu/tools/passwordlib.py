"""
Absfuyu: Passwordlib
--------------------
Password library

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["PasswordGenerator", "PasswordHash", "TOTP"]


# Library
# ---------------------------------------------------------------------------
import hashlib
import os
import random
import re
from typing import ClassVar, Literal, NamedTuple
from urllib.parse import quote, urlencode

from absfuyu.core.baseclass import BaseClass
from absfuyu.core.docstring import deprecated, versionadded
from absfuyu.dxt import DictExt, Text
from absfuyu.logger import logger
from absfuyu.pkg_data import DataList, DataLoader
from absfuyu.tools.generator import Charset, Generator


# Function
# ---------------------------------------------------------------------------
@deprecated("5.0.0")
@versionadded("4.2.0")
def _password_check(password: str) -> bool:
    """
    Verify the strength of ``password``.
    A password is considered strong if:

    - 8 characters length or more
    - 1 digit or more
    - 1 symbol or more
    - 1 uppercase letter or more
    - 1 lowercase letter or more

    :param password: Password want to be checked
    :type password: str
    :rtype: bool
    """

    # calculating the length
    length_error = len(password) < 8

    # searching for digits
    digit_error = re.search(r"\d", password) is None

    # searching for uppercase
    uppercase_error = re.search(r"[A-Z]", password) is None

    # searching for lowercase
    lowercase_error = re.search(r"[a-z]", password) is None

    # searching for symbols
    symbols = re.compile(r"[ !#$%&'()*+,-./[\\\]^_`{|}~" + r'"]')
    symbol_error = symbols.search(password) is None

    detail = {
        "length_error": length_error,
        "digit_error": digit_error,
        "uppercase_error": uppercase_error,
        "lowercase_error": lowercase_error,
        "symbol_error": symbol_error,
    }
    logger.debug(f"Password error summary: {detail}")

    return not any(
        [
            length_error,
            digit_error,
            uppercase_error,
            lowercase_error,
            symbol_error,
        ]
    )


# Class
# ---------------------------------------------------------------------------
class PasswordHash(NamedTuple):
    """
    Password hash

    Parameters
    ----------
    salt : bytes
        Salt

    key : bytes
        Key
    """

    salt: bytes
    key: bytes


@versionadded("4.2.0")
class PasswordGenerator(BaseClass):
    """Password Generator"""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    @staticmethod
    def password_hash(password: str) -> PasswordHash:
        """
        Generate hash for password.

        Parameters
        ----------
        password : str
            Password string

        Returns
        -------
        PasswordHash
            Password hash contains salt and key
        """
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=100000,
        )
        out = PasswordHash(salt, key)
        return out

    @staticmethod
    def password_check(password: str) -> dict:
        """
        Check password's characteristic.

        Parameters
        ----------
        password : str
            Password string

        Returns
        -------
        dict
            Password's characteristic.
        """
        data = Text(password).analyze()
        data = DictExt(data).apply(lambda x: True if x > 0 else False)  # type: ignore
        data.__setitem__("length", len(password))
        return dict(data)

    # Password generator
    @staticmethod
    def generate_password(
        length: int = 8,
        include_uppercase: bool = True,
        include_number: bool = True,
        include_special: bool = True,
    ) -> str:
        r"""
        Generate a random password.

        Parameters
        ----------
        length : int
            | Length of the password.
            | Minimum value: ``8``
            | (Default: ``8``)

        include_uppercase : bool
            Include uppercase character in the password, by default ``True``

        include_number : bool
            Include digit character in the password, by default ``True``

        include_special : bool
            Include special character in the password, by default ``True``

        Returns
        -------
        str
            Generated password


        Example:
        --------
        >>> Password.generate_password()
        [T&b@mq2
        """
        charset = Charset.LOWERCASE
        check = 0

        if include_uppercase:
            charset += Charset.UPPERCASE
            check += 1

        if include_number:
            charset += Charset.DIGIT
            check += 1

        if include_special:
            charset += r"[!#$%&'()*+,-./]^_`{|}~\""
            check += 1

        while True:
            pwd = Generator.generate_string(
                charset=charset,
                size=max(length, 8),  # type: ignore
                times=1,
                string_type_if_1=True,
            )

            analyze = Text(pwd).analyze()  # Count each type of char

            s = sum([1 for x in analyze.values() if x > 0])  # type: ignore
            if s > check:  # Break loop if each type of char has atleast 1
                break
        return pwd  # type: ignore

    @staticmethod
    def generate_passphrase(
        num_of_blocks: int = 5,
        block_divider: str | None = None,
        first_letter_cap: bool = True,
        include_number: bool = True,
        *,
        custom_word_list: list[str] | None = None,
    ) -> str:
        """
        Generate a random passphrase

        Parameters
        ----------
        num_of_blocks : int
            Number of word used, by default ``5``

        block_divider : str
            Character symbol that between each word, by default ``"-"``

        first_letter_cap : bool
            Capitalize first character of each word, by default ``True``

        include_number : bool
            Add number to the end of each word, by default ``True``

        custom_word_list : list[str] | None
            Custom word list for passphrase generation, by default uses a list of 360K+ words

        Returns
        -------
        str
            Generated passphrase


        Example:
        --------
        >>> print(Password().generate_passphrase())
        Myomectomies7-Sully4-Torpedomen7-Netful2-Begaud8
        """
        words: list[str] = (
            DataLoader(DataList.PASSWORDLIB).load().decode().split(",")
            if not custom_word_list
            else custom_word_list
        )

        if block_divider is None:
            block_divider = "-"

        dat = [random.choice(words) for _ in range(num_of_blocks)]

        if first_letter_cap:
            dat = list(map(lambda x: x.title(), dat))

        if include_number:
            idx = random.choice(range(num_of_blocks))
            dat[idx] += str(random.choice(range(10)))

        return block_divider.join(dat)


@versionadded("5.0.0")
class TOTP(BaseClass):
    """
    A class to represent a Time-based One-Time Password (TOTP) generator.

    Parameters
    ----------
    secret : str
        The shared secret key used to generate the TOTP.

    name : str, optional
        | The name associated with the TOTP.
        | If not provided, by default ``"None"``.

    issuer : str, optional
        The issuer of the TOTP.

    algorithm : Literal["SHA1", "SHA256", "SHA512"], optional
        | The hashing algorithm used to generate the TOTP.
        | Must be one of ``"SHA1"``, ``"SHA256"``, or ``"SHA512"``.
        | By default ``"SHA1"``.

    digit : int, optional
        | The number of digits in the generated TOTP.
        | Must be greater than 0.
        | By default ``6``.

    period : int, optional
        | The time step in seconds for TOTP generation.
        | Must be greater than 0.
        | by default ``30``.
    """

    URL_SCHEME: ClassVar[str] = "otpauth://totp/"

    def __init__(
        self,
        secret: str,
        name: str | None = None,
        issuer: str | None = None,
        algorithm: Literal["SHA1", "SHA256", "SHA512"] = "SHA1",
        digit: int = 6,
        period: int = 30,
    ) -> None:
        """
        Initializes a TOTP instance.

        Parameters
        ----------
        secret : str
            The shared secret key used to generate the TOTP.

        name : str, optional
            | The name associated with the TOTP.
            | If not provided, by default ``"None"``.

        issuer : str, optional
            The issuer of the TOTP.

        algorithm : Literal["SHA1", "SHA256", "SHA512"], optional
            | The hashing algorithm used to generate the TOTP.
            | Must be one of ``"SHA1"``, ``"SHA256"``, or ``"SHA512"``.
            | By default ``"SHA1"``.

        digit : int, optional
            | The number of digits in the generated TOTP.
            | Must be greater than 0.
            | By default ``6``.

        period : int, optional
            | The time step in seconds for TOTP generation.
            | Must be greater than 0.
            | by default ``30``.
        """
        self.secret = secret.upper()
        self.name = name if name else "None"
        self.issuer = issuer
        self.algorithm = algorithm.upper()
        self.digit = max(digit, 1)  # digit must be larger than 0
        self.period = max(period, 1)  # period must be larger than 0

    def to_url(self) -> str:
        """
        Generates a URL for the TOTP in the otpauth format.

        The URL format is as follows:
            ``otpauth://totp/<name>?secret=<secret>&issuer=<issuer>&algorithm=<algorithm>&digit=<digit>&period=<period>``

        Returns
        -------
        str
            A URL representing the TOTP in otpauth format.
        """
        params = {
            "secret": self.secret,
            "issuer": self.issuer,
            "algorithm": self.algorithm,
            "digit": self.digit,
            "period": self.period,
        }
        # Filter out None values from the params dictionary
        filtered_params = {k: v for k, v in params.items() if v is not None}
        # filtered_params = {k: v for k, v in self.__dict__.items() if v is not None}

        name = quote(self.name)
        tail = urlencode(filtered_params, quote_via=quote)
        return f"{self.URL_SCHEME}{name}?{tail}"
