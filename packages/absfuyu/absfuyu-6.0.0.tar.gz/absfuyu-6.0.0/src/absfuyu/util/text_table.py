"""
Absufyu: Utilities
------------------
Text table

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["BoxStyle", "OneColumnTableMaker"]


# Library
# ---------------------------------------------------------------------------
import os
from collections.abc import Sequence
from textwrap import TextWrapper
from typing import Literal

from absfuyu.core import BaseClass

# Style
# ---------------------------------------------------------------------------
BoxStyle = Literal[
    "normal",
    "bold",
    "dashed",
    "double",
    "rounded",
    "drounded",
    "diamond",
    "dbold",
    "dashed3",
    "dashed4",
]


class BoxDrawingCharacterBase:
    """
    Box drawing characters - Base/Normal characters

    Characters reference: https://en.wikipedia.org/wiki/Box-drawing_characters
    """

    UPPER_LEFT_CORNER = "\u250c"
    UPPER_RIGHT_CORNER = "\u2510"
    HORIZONTAL = "\u2500"
    VERTICAL = "\u2502"
    LOWER_LEFT_CORNER = "\u2514"
    LOWER_RIGHT_CORNER = "\u2518"
    VERTICAL_RIGHT = "\u251c"
    VERTICAL_LEFT = "\u2524"
    CROSS = "\u253c"
    HORIZONTAL_UP = "\u2534"
    HORIZONTAL_DOWN = "\u252c"


class BoxDrawingCharacterNormal(BoxDrawingCharacterBase):
    """Normal"""

    pass


class BoxDrawingCharacterDashed(BoxDrawingCharacterNormal):
    """Dashed"""

    HORIZONTAL = "\u254c"
    VERTICAL = "\u254e"


class BoxDrawingCharacterDashed3(BoxDrawingCharacterNormal):
    """Triple dashed"""

    HORIZONTAL = "\u2504"
    VERTICAL = "\u2506"


class BoxDrawingCharacterDashed4(BoxDrawingCharacterNormal):
    """Quadruple dashed"""

    HORIZONTAL = "\u2508"
    VERTICAL = "\u250a"


class BoxDrawingCharacterRounded(BoxDrawingCharacterNormal):
    """Rounded"""

    UPPER_LEFT_CORNER = "\u256d"
    UPPER_RIGHT_CORNER = "\u256e"
    LOWER_LEFT_CORNER = "\u2570"
    LOWER_RIGHT_CORNER = "\u256f"


class BoxDrawingCharacterDiamond(BoxDrawingCharacterNormal):
    """Diamond"""

    UPPER_LEFT_CORNER = "\u2571"
    UPPER_RIGHT_CORNER = "\u2572"
    LOWER_LEFT_CORNER = "\u2572"
    LOWER_RIGHT_CORNER = "\u2571"


class BoxDrawingCharacterDashedRound(
    BoxDrawingCharacterDashed, BoxDrawingCharacterRounded
):
    """Dashed rounded"""

    pass


class BoxDrawingCharacterBold(BoxDrawingCharacterBase):
    """Bold"""

    UPPER_LEFT_CORNER = "\u250f"
    UPPER_RIGHT_CORNER = "\u2513"
    HORIZONTAL = "\u2501"
    VERTICAL = "\u2503"
    LOWER_LEFT_CORNER = "\u2517"
    LOWER_RIGHT_CORNER = "\u251b"
    VERTICAL_RIGHT = "\u2523"
    VERTICAL_LEFT = "\u252b"
    CROSS = "\u254b"
    HORIZONTAL_UP = "\u253b"
    HORIZONTAL_DOWN = "\u2533"


class BoxDrawingCharacterDashedBold(BoxDrawingCharacterBold):
    """Dashed bold"""

    HORIZONTAL = "\u254d"
    VERTICAL = "\u254f"


class BoxDrawingCharacterDouble(BoxDrawingCharacterBase):
    """Double"""

    UPPER_LEFT_CORNER = "\u2554"
    UPPER_RIGHT_CORNER = "\u2557"
    HORIZONTAL = "\u2550"
    VERTICAL = "\u2551"
    LOWER_LEFT_CORNER = "\u255a"
    LOWER_RIGHT_CORNER = "\u255d"
    VERTICAL_RIGHT = "\u2560"
    VERTICAL_LEFT = "\u2563"
    CROSS = "\u256c"
    HORIZONTAL_UP = "\u2569"
    HORIZONTAL_DOWN = "\u2566"


def get_box_drawing_character(
    style: BoxStyle | str = "normal",
) -> type[BoxDrawingCharacterBase]:
    """
    Choose style for Box drawing characters.

    Parameters
    ----------
    style : BoxStyle | str, optional
        Style for the table, by default ``"normal"``.
        Available style:
        - normal
        - bold
        - dashed
        - double
        - rounded
        - drounded: Dashed and rounded
        - diamond
        - dbold: Bold dashed
        - dashed3: Triple dash
        - dashed4: Quadruple dash

    Returns
    -------
    BoxDrawingCharacter
        Box drawing characters in specified style.
    """

    match style.lower().strip():
        case "normal":
            return BoxDrawingCharacterNormal
        case "bold":
            return BoxDrawingCharacterBold
        case "dashed":
            return BoxDrawingCharacterDashed
        case "dashed3":
            return BoxDrawingCharacterDashed3
        case "dashed4":
            return BoxDrawingCharacterDashed4
        case "double":
            return BoxDrawingCharacterDouble
        case "rounded":
            return BoxDrawingCharacterRounded
        case "drounded":
            return BoxDrawingCharacterDashedRound
        case "diamond":
            return BoxDrawingCharacterDiamond
        case "dbold":
            return BoxDrawingCharacterDashedBold
        case _:
            return BoxDrawingCharacterNormal


# Class
# ---------------------------------------------------------------------------
class OneColumnTableMaker(BaseClass):
    """
    Table Maker instance

    Parameters
    ----------
    ncols : int | None, optional
        Length of the table (include content). Must be >= 5.
        Set to ``None`` to use maximum length,
        defaults to ``88`` when failed to use ``os.get_terminal_size()``.
        By default ``None``

    BoxStyle : Literal["normal", "bold", "dashed", "double"], optional
        Style for the table, by default ``"normal"``
    """

    __slots__ = ("ncols", "_title", "_paragraphs", "_table_char", "_text_wrapper")

    def __init__(self, ncols: int | None = None, style: BoxStyle = "normal") -> None:
        """
        Table Maker instance

        Parameters
        ----------
        ncols : int | None, optional
            Length of the table (include content). Must be >= 5.
            Set to ``None`` to use maximum length,
            defaults to ``88`` when failed to use ``os.get_terminal_size()``.
            By default ``None``

        style : BoxStyle, optional
            Style for the table, by default ``"normal"``
        """

        # Text length
        if ncols is None:
            try:
                self.ncols = os.get_terminal_size().columns
            except OSError:
                self.ncols = 88
        else:
            self.ncols = max(5, ncols)

        # Title & paragraph
        self._title = ""
        self._paragraphs: list[Sequence[str]] = []

        # Style
        self._table_char = get_box_drawing_character(style=style)

        # Text wrapper
        self._text_wrapper = TextWrapper(
            width=self.ncols - 4,
            initial_indent="",
            subsequent_indent="",
            tabsize=4,
            break_long_words=True,
        )

    def add_title(self, title: str) -> None:
        """
        Add title to Table

        Parameters
        ----------
        title : str
            Title to add.
            When ``len(title) > ncols``: title will not show
        """
        max_padding_length = self.ncols - 2
        if max_padding_length < (len(title) + 2) or len(title) < 1:
            _title = ""
        else:
            _title = f" {title} "

        line = (
            f"{self._table_char.UPPER_LEFT_CORNER}"
            f"{_title.center(max_padding_length, self._table_char.HORIZONTAL)}"
            f"{self._table_char.UPPER_RIGHT_CORNER}"
        )
        self._title = line

    def add_paragraph(self, paragraph: Sequence[str]) -> None:
        """
        Add paragraph into Table

        Parameters
        ----------
        paragraph : Sequence[str]
            An iterable of str
        """
        if isinstance(paragraph, str):
            self._paragraphs.append([paragraph])
        else:
            self._paragraphs.append(paragraph)

    def _make_line(self, option: Literal[0, 1, 2]) -> str:
        options = (
            (self._table_char.UPPER_LEFT_CORNER, self._table_char.UPPER_RIGHT_CORNER),
            (self._table_char.VERTICAL_RIGHT, self._table_char.VERTICAL_LEFT),
            (self._table_char.LOWER_LEFT_CORNER, self._table_char.LOWER_RIGHT_CORNER),
        )
        max_line_length = self.ncols - 2
        line = (
            f"{options[option][0]}"
            f"{''.ljust(max_line_length, self._table_char.HORIZONTAL)}"
            f"{options[option][1]}"
        )
        return line

    def _make_table(self) -> list[str] | None:
        # Check if empty
        if len(self._paragraphs) < 1:
            return None
        if len(self._paragraphs[0]) < 1:
            return None

        # Make table
        max_content_length = self.ncols - 4
        paragraph_length = len(self._paragraphs)

        # Line prep
        _first_line = self._make_line(0)
        _sep_line = self._make_line(1)
        _last_line = self._make_line(2)

        # Table
        table: list[str] = [_first_line] if self._title == "" else [self._title]
        for i, paragraph in enumerate(self._paragraphs, start=1):
            for line in paragraph:
                splitted_line = self._text_wrapper.wrap(line) if len(line) > 0 else [""]
                mod_lines: list[str] = [
                    f"{self._table_char.VERTICAL} "
                    f"{line.ljust(max_content_length, ' ')}"
                    f" {self._table_char.VERTICAL}"
                    for line in splitted_line
                ]
                table.extend(mod_lines)

            if i != paragraph_length:
                table.append(_sep_line)
            else:
                table.append(_last_line)
        return table

    def make_table(self) -> str:
        table = self._make_table()
        if table is None:
            return ""
        return "\n".join(table)


# W.I.P
# ---------------------------------------------------------------------------
class _BoxDrawingCharacterFactory:
    _TRANSLATE: dict[str, str] = {
        "n": "normal",
        "d": "dashed",
        "b": "bold",
        "r": "rounded",
        "x": "double",
    }

    UPPER_LEFT_CORNER: list[tuple[str, str]] = [
        ("\u250c", "n,d"),
        ("\u256d", "r"),
        ("\u250f", "b"),
        ("\u2554", "x"),
    ]
    UPPER_RIGHT_CORNER: list[tuple[str, str]] = [
        ("\u2510", "n,d"),
        ("\u256e", "r"),
        ("\u2513", "b"),
        ("\u2557", "x"),
    ]
    HORIZONTAL: list[tuple[str, str]] = [
        ("\u2500", "n,r"),
        ("\u254c", "d"),
        ("\u2501", "b"),
        ("\u2550", "x"),
    ]
    VERTICAL: list[tuple[str, str]] = [
        ("\u2502", "n,r"),
        ("\u254e", "d"),
        ("\u2503", "b"),
        ("\u2551", "x"),
    ]
    LOWER_LEFT_CORNER: list[tuple[str, str]] = [
        ("\u2514", "n,d"),
        ("\u2570", "r"),
        ("\u2517", "b"),
        ("\u255a", "x"),
    ]
    LOWER_RIGHT_CORNER: list[tuple[str, str]] = [
        ("\u2518", "n,d"),
        ("\u256f", "r"),
        ("\u251b", "b"),
        ("\u255d", "x"),
    ]
    VERTICAL_RIGHT: list[tuple[str, str]] = [
        ("\u251c", "n,d,r"),
        ("\u2523", "b"),
        ("\u2560", "x"),
    ]
    VERTICAL_LEFT: list[tuple[str, str]] = [
        ("\u2524", "n,d,r"),
        ("\u252b", "b"),
        ("\u2563", "x"),
    ]
    CROSS: list[tuple[str, str]] = [
        ("\u253c", "n,d,r"),
        ("\u254b", "b"),
        ("\u256c", "x"),
    ]
    HORIZONTAL_UP: list[tuple[str, str]] = [
        ("\u2534", "n,d,r"),
        ("\u253b", "b"),
        ("\u2569", "x"),
    ]
    HORIZONTAL_DOWN: list[tuple[str, str]] = [
        ("\u252c", "n,d,r"),
        ("\u2533", "b"),
        ("\u2566", "x"),
    ]

    _FIELDS: tuple[str, ...] = (
        "UPPER_LEFT_CORNER",
        "UPPER_RIGHT_CORNER",
        "HORIZONTAL",
        "VERTICAL",
        "LOWER_LEFT_CORNER",
        "LOWER_RIGHT_CORNER",
        "VERTICAL_RIGHT",
        "VERTICAL_LEFT",
        "CROSS",
        "HORIZONTAL_UP",
        "HORIZONTAL_DOWN",
    )

    def __init__(self, style: str | None = None):
        self.style = style

    @classmethod
    def _make_style(cls) -> dict[str, dict[str, str]]:
        """
        Creates a style dictionary based on the class attributes.

        Returns
        -------
        dict[str, dict[str, str]]
            A dictionary mapping group names to style configurations.
        """

        # Initialize an empty style dictionary
        style: dict[str, dict[str, str]] = {}

        # Create a dictionary mapping field names to themselves
        field_map = {field: "" for field in cls._FIELDS}

        # Initialize style entries for each translation key
        for x in cls._TRANSLATE.keys():
            style[x] = field_map

        # Extract character data from class fields
        char_data: list[tuple[str, list[tuple[str, str]]]] = [
            (field, getattr(cls, field)) for field in cls._FIELDS
        ]

        # Populate the style dictionary with character mappings
        for name, chars in char_data:
            for char, groups in chars:
                for group in map(str.strip, groups.split(",")):
                    style[group][name] = char

        return style
