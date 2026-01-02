"""
Absfuyu: Data Analysis
----------------------
Matplotlib Helper

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["MatplotlibFormatString", "_PLTFormatString"]

# Library
# ---------------------------------------------------------------------------
import random
from collections.abc import Sequence
from itertools import product
from typing import ClassVar, Self

from absfuyu.core.baseclass import AutoREPRMixin, BaseClass


# Class
# ---------------------------------------------------------------------------
class _PLTFormatString(AutoREPRMixin):
    """
    Matplotlib format string

    Available format:
    - ``<marker><line><color>``
    - ``<color><marker><line>``
    """

    __slots__ = (
        "marker",
        "line_style",
        "color",
        "_marker_fullname",
        "_line_style_fullname",
        "_color_fullname",
    )

    def __init__(
        self,
        marker: str,
        line_style: str,
        color: str,
        *,
        marker_fullname: str | None = None,
        line_style_fullname: str | None = None,
        color_fullname: str | None = None,
    ) -> None:
        """
        Matplotlib format string

        Parameters
        ----------
        marker : str
            Maker

        line_style : str
            Line style

        color : str
            Color

        marker_fullname : str | None, optional
            Maker fullname, by default ``None``

        line_style_fullname : str | None, optional
            Line style fullname, by default ``None``

        color_fullname : str | None, optional
            Color fullname, by default ``None``
        """

        self.marker = marker
        self.line_style = line_style
        self.color = color

        self._marker_fullname = marker_fullname
        self._line_style_fullname = line_style_fullname
        self._color_fullname = color_fullname

    def __str__(self) -> str:
        return self.fstr

    def __format__(self, format_spec: str) -> str:
        if format_spec.lower() == "full":
            if (
                self._marker_fullname is None
                or self._line_style_fullname is None
                or self._color_fullname is None
            ):
                return self.__str__()
            clsname = self.__class__.__name__
            return (
                f"{clsname}(marker={repr(self._marker_fullname)}"
                f", line_style={repr(self._line_style_fullname)}"
                f", color={repr(self._color_fullname)})"
            )
        return super().__format__(format_spec)

    @property
    def fstr(self) -> str:
        """Format string"""
        return f"{self.marker}{self.line_style}{self.color}"

    @property
    def alternate(self) -> str:
        """Alternative version of format string"""
        return f"{self.color}{self.marker}{self.line_style}"

    @classmethod
    def _make(cls, iterable: Sequence[str]) -> Self:
        if len(iterable) not in (3, 6):
            raise ValueError("iterable must have a length of 3 or 6")
        try:  # Len 6
            return cls(
                marker=iterable[0],
                line_style=iterable[1],
                color=iterable[2],
                marker_fullname=iterable[3],
                line_style_fullname=iterable[4],
                color_fullname=iterable[5],
            )
        except IndexError:  # Len 3
            return cls(iterable[0], iterable[1], iterable[2])


class MatplotlibFormatString(BaseClass):
    """
    Matplotlib format string

    Available format:
    - ``<marker><line><color>``
    - ``<color><marker><line>``
    """

    MARKER_DATA: ClassVar[dict[str, str]] = {
        ".": "point marker",
        ",": "pixel marker",
        "o": "circle marker",
        "v": "triangle_down marker",
        "^": "triangle_up marker",
        "<": "triangle_left marker",
        ">": "triangle_right marker",
        "1": "tri_down marker",
        "2": "tri_up marker",
        "3": "tri_left marker",
        "4": "tri_right marker",
        "8": "octagon marker",
        "s": "square marker",
        "p": "pentagon marker",
        "P": "plus (filled) marker",
        "*": "star marker",
        "h": "hexagon1 marker",
        "H": "hexagon2 marker",
        "+": "plus marker",
        "x": "x marker",
        "X": "x (filled) marker",
        "D": "diamond marker",
        "d": "thin_diamond marker",
        "|": "vline marker",
        "_": "hline marker",
    }
    LINE_STYLE_DATA: ClassVar[dict[str, str]] = {
        "-": "solid line style",
        "--": "dashed line style",
        "-.": "dash-dot line style",
        ":": "dotted line style",
    }
    COLOR_DATA: ClassVar[dict[str, str]] = {
        "b": "blue",
        "g": "green",
        "r": "red",
        "c": "cyan",
        "m": "magenta",
        "y": "yellow",
        "k": "black",
        "w": "white",
    }

    @classmethod
    def all_format_string(cls) -> list[_PLTFormatString]:
        # This return full list without full name
        # return [
        #     _PLTFormatString._make(x)
        #     for x in product(cls.MARKER_DATA, cls.LINE_STYLE_DATA, cls.COLOR_DATA)
        # ]

        # This return full list with full name
        def convert(
            x: tuple[tuple[str, str], tuple[str, str], tuple[str, str]],
        ) -> tuple[str, str, str, str, str, str]:
            return (x[0][0], x[1][0], x[2][0], x[0][1], x[1][1], x[2][1])

        return [
            _PLTFormatString._make(convert(x))
            for x in product(
                cls.MARKER_DATA.items(),
                cls.LINE_STYLE_DATA.items(),
                cls.COLOR_DATA.items(),
            )
        ]

    @classmethod
    def get_random(cls) -> _PLTFormatString:
        """
        Get a random format string

        Returns
        -------
        str
            Random format string
        """
        random_fmtstr = random.choice(cls.all_format_string())
        return random_fmtstr
