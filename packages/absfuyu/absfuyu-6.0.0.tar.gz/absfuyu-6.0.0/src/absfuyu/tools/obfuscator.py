"""
Absfuyu: Obfuscator
-------------------
Obfuscate code

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Obfuscator", "StrShifter"]


# Library
# ---------------------------------------------------------------------------
import base64
import codecs
import random
import zlib
from collections import deque
from string import Template
from typing import ClassVar

from absfuyu.core.baseclass import BaseClass, GetClassMembersMixin
from absfuyu.core.docstring import versionadded
from absfuyu.dxt import Text
from absfuyu.logger import logger
from absfuyu.tools.generator import Charset, Generator


# Class
# ---------------------------------------------------------------------------
@versionadded("5.0.0")
class StrShifter(BaseClass):
    """
    Shift characters in a string by a specified number of positions.

    Parameters
    ----------
    str_to_shift : str
        The string whose characters will be shifted.

    shift_by : int, optional
        The number of positions to shift the characters, by default ``5``.
    """

    __slots__ = ("_str_to_shift", "shift_by")

    def __init__(self, str_to_shift: str, shift_by: int = 5) -> None:
        """
        Initialize the StrShifter with the string to shift and the shift amount.

        Parameters
        ----------
        str_to_shift : str
            The string whose characters will be shifted.

        shift_by : int, optional
            The number of positions to shift the characters, by default ``5``.
        """
        if not isinstance(str_to_shift, str):
            raise TypeError("Value must be an instance of str")
        self._str_to_shift = str_to_shift
        self.shift_by = shift_by

    def _make_convert_table(self) -> dict[str, str]:
        """
        Create a translation table for shifting characters.

        Returns
        -------
        dict[str, str]
            A dictionary mapping each character to its shifted counterpart.
        """
        data = self._str_to_shift  # Make a copy

        unique_char_sorted = deque(sorted(list(set(data))))
        translate = unique_char_sorted.copy()
        translate.rotate(self.shift_by)
        convert_table = dict(zip(unique_char_sorted, translate))

        return convert_table

    def _use_convert_table(self, convert_table: dict[str, str]) -> str:
        """
        Convert the original string using the provided conversion table.

        Parameters
        ----------
        convert_table : dict[str, str]
            The conversion table mapping original characters to shifted characters.

        Returns
        -------
        str
            The transformed string after applying the conversion table.
        """
        return "".join([convert_table[char] for char in list(self._str_to_shift)])

    def shift(self) -> str:
        """
        Shift the characters in the string and return the new string.

        Returns
        -------
        str
            The resulting string after shifting.
        """
        return self._use_convert_table(self._make_convert_table())


class Obfuscator(GetClassMembersMixin):
    """
    Obfuscate code

    Parameters
    ----------
    code : str
        Code text

    base64_only : bool, optional
        - ``True``: encode in base64 form only
        - ``False``: base64, compress, rot13 (default)

    split_every : int, optional
        Split the long line of code every ``x`` character.
        Minimum is ``1``, by default ``60``

    variable_length : int, optional
        Length of variable name (when data string split).
        Minimum is ``7``, by default ``12``

    fake_data : bool, optional
        Generate additional meaningless data, by default ``False``
    """

    # Var
    LIB_BASE64_ONLY: ClassVar[list[str]] = ["base64"]
    LIB_FULL: ClassVar[list[str]] = ["base64", "codecs", "zlib"]

    # Template
    SINGLE_LINE_TEMPLATE: ClassVar[Template] = Template(
        "exec(bytes.fromhex('$one_line_code').decode('utf-8'))"
    )
    PRE_HEX_B64_TEMPLATE: ClassVar[Template] = Template(
        "eval(compile(base64.b64decode($encoded_string),$type_var,$execute))"
    )
    PRE_HEX_FULL_TEMPLATE: ClassVar[Template] = Template(
        "eval(compile(base64.b64decode(zlib.decompress(base64.b64decode(codecs."
        "encode($encoded_string,$codec_to_decode).encode()))),$type_var,$execute))"
    )

    def __init__(
        self,
        code: str,
        *,
        base64_only: bool = False,
        split_every: int = 60,
        variable_length: int = 12,
        fake_data: bool = False,
    ) -> None:
        """
        Obfuscator

        Parameters
        ----------
        code : str
            Code text

        base64_only : bool, optional
            - ``True``: encode in base64 form only
            - ``False``: base64, compress, rot13 (default)

        split_every : int, optional
            Split the long line of code every ``x`` character.
            Minimum is ``1``, by default ``60``

        variable_length : int, optional
            Length of variable name (when data string split).
            Minimum is ``7``, by default ``12``

        fake_data : bool, optional
            Generate additional meaningless data, by default ``False``
        """
        self.base_code = code
        self.base64_only = base64_only
        self.split_every_length = max(1, split_every)
        self.variable_length = max(7, variable_length)
        self.fake_data = fake_data

        # Setting
        self._library_import_variable_length = self.variable_length - 1
        self._splited_variable_length = self.variable_length
        self._decode_variable_length = self.variable_length + 3

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        repr_out_dict = {
            "base_code": "...",
            "base64_only": self.base64_only,
            "split_every_length": self.split_every_length,
            "variable_length": self.variable_length,
            "fake_data": self.fake_data,
        }
        repr_out = ", ".join([f"{k}={repr(v)}" for k, v in repr_out_dict.items()])
        return f"{self.__class__.__name__}({repr_out})"

    def to_single_line(self) -> str:
        """
        Convert multiple lines of code into one line

        Returns
        -------
        str
            Converted code.
        """
        newcode = self.base_code.encode("utf-8").hex()
        output = self.SINGLE_LINE_TEMPLATE.substitute(one_line_code=newcode)
        return output

    # Obfuscate original code
    def _obfuscate(self) -> str:
        """
        Convert multiple lines of code through multiple transformation
        (base64 -> compress -> base64 -> caesar (13))
        """
        code = self.base_code  # Make a copy
        logger.debug("Encoding...")

        b64_encode = base64.b64encode(code.encode())
        if self.base64_only:
            output = b64_encode.decode()
        else:
            compressed_data = zlib.compress(b64_encode)
            logger.debug(
                f"Compressed data: {str(compressed_data)} | Len: {len(str(compressed_data))}"
            )
            b64_encode_2 = base64.b64encode(compressed_data).decode()
            logger.debug(f"Base64 encode 2: {b64_encode_2} | Len: {len(b64_encode_2)}")
            caesar_data = codecs.encode(b64_encode_2, "rot_13")
            output = caesar_data

        logger.debug(f"Output: {output}")
        logger.debug("Code encoded.")
        return output

    @staticmethod
    def _convert_to_base64_decode(text: str, raw: bool = False) -> str:
        """
        Convert text into base64 and then return a code that decode that base64 code

        Parameters
        ----------
        text : str
            Code that need to convert

        raw : bool
            Return hex form only, by default ``False``
        """
        b64_encode_codec = base64.b64encode(text.encode()).decode()
        b64_decode_codec = f"base64.b64decode('{b64_encode_codec}'.encode()).decode()"
        hex = Text(b64_decode_codec).to_hex()
        out = f"eval('{hex}')"
        if raw:
            return hex
        return out

    # Generate output (decode obfuscated code)
    def _make_output_lib(self) -> list[str]:
        """Obfuscate the `import <lib>`"""
        output = []

        # Make import lib
        library_list = self.LIB_BASE64_ONLY if self.base64_only else self.LIB_FULL
        imports = [f"import {lib}" for lib in library_list]
        logger.debug(f"Lib: {imports}")

        # Convert to hex
        lib_hex = Text("\n".join(imports)).to_hex()
        output.append(f"exec('{lib_hex}')")
        logger.debug(f"Current output (import library): {output}")

        return output

    def _make_prep_for_decode_var(self) -> tuple[list[str], list[str]]:
        """
        ``<var> = "rot_13"``
        ``<var> = "<string>"``
        ``<var> = "exec"``

        Returns
        -------
        tuple[list[str], list[str]]
            - tuple[0]: output
            - tuple[1]: decode var name
        """
        output = []

        # Make variables for "rot_13", "<string>", "exec"
        dc_name_lst: list[str] = Generator.generate_string(
            charset=Charset.ALPHABET,
            size=self._decode_variable_length,
            times=3,
            unique=True,
        )

        # Assign and convert to hex
        encode_codec = "rot_13"  # full
        if not self.base64_only:  # full
            hex_0 = self._convert_to_base64_decode(encode_codec)
            output.append(f"{dc_name_lst[0]}={hex_0}")

        for i, x in enumerate(["<string>", "exec"], start=1):
            # hex_str = Text(x).to_hex()
            hex_str = self._convert_to_base64_decode(x)
            output.append(f"{dc_name_lst[i]}={hex_str}")
        logger.debug(f"Current output (decode variables): {output}")

        return output, dc_name_lst

    def _make_fake_output(self, input_size: int) -> list[str]:
        """Fake data"""
        output = []

        f1 = Generator.generate_string(
            charset=Charset.DEFAULT,
            size=input_size,
            times=1,
            string_type_if_1=True,
        )  # Generate fake data with len of original data
        f2 = Text(f1).divide_with_variable(
            self.split_every_length, self._splited_variable_length
        )
        output.extend(f2[:-1])

        # Random data
        bait_lst = Generator.generate_string(
            charset=Charset.ALPHABET, size=self._splited_variable_length, times=25
        )
        for x in bait_lst:
            output.append(
                f"{x}='{Generator.generate_string(charset=Charset.DEFAULT, size=self.split_every_length, times=1, string_type_if_1=True)}'"
            )

        random_eval_text = str(random.randint(1, 100))
        for _ in range(random.randint(10, 50)):
            random_eval_text += f"+{random.randint(1, 100)}"
        random_eval_text_final = Text(random_eval_text).to_hex()
        output.append(f"eval('{random_eval_text_final}')")

        return output

    def _make_obfuscate_output(self) -> list[str]:
        """
        Convert multiple lines of code through multiple transformation
        (base64 -> compress -> base64 -> caesar (13))

        Then return a list (obfuscated code) that can
        be print or export into .txt file
        """
        # Obfuscated code
        input_str = Text(self._obfuscate())

        # Generate output
        output = []

        # Import library
        output.extend(self._make_output_lib())

        # Append divided long text list
        input_list = input_str.divide_with_variable(
            split_size=self.split_every_length,
            split_var_len=self._splited_variable_length,
        )
        encoded_str = input_list[-1]  # Main var name that will later be used
        output.extend(input_list[:-1])  # Append list minus the last element
        logger.debug(f"Current output (encoded code): {output}")

        # Decode: encoded_str
        dc_out, dc_name_lst = self._make_prep_for_decode_var()
        output.extend(dc_out)

        if self.base64_only:  # b64
            pre_hex = self.PRE_HEX_B64_TEMPLATE.substitute(
                encoded_string=encoded_str,
                type_var=dc_name_lst[1],
                execute=dc_name_lst[2],
            )
        else:  # full
            pre_hex = self.PRE_HEX_FULL_TEMPLATE.substitute(
                encoded_string=encoded_str,
                codec_to_decode=dc_name_lst[0],
                type_var=dc_name_lst[1],
                execute=dc_name_lst[2],
            )

        t_hex = Text(pre_hex).to_hex()
        output.append(f"exec('{t_hex}')")
        logger.debug(f"Current output (decode code): {output}")

        # Fake data
        if self.fake_data:
            output.extend(self._make_fake_output(len(input_str)))

        logger.debug("Code obfuscated.")
        return output

    def obfuscate(self) -> str:
        """
        Obfuscate code

        Returns
        -------
        str
            Obfuscated code
        """
        return "\n".join(self._make_obfuscate_output())
