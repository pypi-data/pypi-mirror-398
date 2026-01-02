"""
Absfuyu: Relative resolution
----------------------------
Relative resolution

Use with screen resolution getter like ``tkinter``, ``ctypes``, ``screeninfo`` is recommended

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["RelativeResoluton", "RelativeResolutonTranslater"]


# Library
# ---------------------------------------------------------------------------
from fractions import Fraction
from typing import Self, overload

from absfuyu.core.baseclass import BaseClass


# Class
# ---------------------------------------------------------------------------
class RelativeResoluton(BaseClass):
    def __init__(self, x: int, y: int) -> None:
        """
        Resolution

        Parameters
        ----------
        x : int
            Normally width

        y : int
            Normally height

        Raises
        ------
        ValueError
            When x or y < 1
        """
        if x < 1 or y < 1:
            raise ValueError("Resolution must be >= 1")

        self.x = x
        self.y = y

    @property
    def ratio(self) -> Fraction:
        """
        Ratio of the resolution
        """
        return Fraction(self.x, self.y)

    def scale_by(self, by: int | float | Fraction, /) -> Self:
        """
        Scale the resolution by an amount

        Parameters
        ----------
        by : int | float | Fraction
            Amount to scale

        Returns
        -------
        Self
            New scaled resolution
        """
        if isinstance(by, Fraction):
            x = int(self.x * by.numerator / by.denominator)
            y = int(self.y * by.numerator / by.denominator)
        else:
            x = int(self.x * by)
            y = int(self.y * by)
        return self.__class__(x, y)

    @overload
    def get_point_relative(self, x: int, y: int, /) -> tuple[Fraction, Fraction]: ...
    @overload
    def get_point_relative(self, x: int, y: int, /, *, strict: bool = True) -> tuple[Fraction, Fraction]: ...
    def get_point_relative(self, x: int, y: int, /, *, strict: bool = True) -> tuple[Fraction, Fraction]:
        """
        Get relative point from fixed point.

        Parameters
        ----------
        x : int
            Normally width

        y : int
            Normally height

        strict : bool, optional
            Convert ``x`` and ``y`` into type int first, by default ``True``

        Returns
        -------
        tuple[Fraction, Fraction]
            Relative point
        """
        if strict:
            x = int(x)
            y = int(y)
        x_rel = Fraction(x, self.x)
        y_rel = Fraction(y, self.y)
        return x_rel, y_rel

    def get_fixed_point(self, x_rel: Fraction, y_rel: Fraction, /) -> tuple[int, int]:
        """
        Get fixed point from relative point.

        Parameters
        ----------
        x_rel : Fraction
            Normally width

        y_rel : Fraction
            Normally height

        Returns
        -------
        tuple[int, int]
            Fixed point
        """
        x = int(self.x * x_rel.numerator / x_rel.denominator)
        y = int(self.y * y_rel.numerator / y_rel.denominator)
        return x, y


class RelativeResolutonTranslater(RelativeResoluton):
    """
    Relative resolution translater

    It is recommended to use with screen resolution getter like
    ``tkinter``, ``ctypes``, ``screeninfo``, ``pyautogui``


    Example:
    --------
    >>> import tkinter as tk
    >>> root = tk.Tk()
    >>> width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    >>> rr = RelativeResolutonTranslater(width, height)
    >>> rr.add_target_scale((1920, 1080))
    >>> rr.t(1280, 720)

    >>> import tkinter as tk
    >>> root = tk.Tk()
    >>> width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    >>> rr = RelativeResolutonTranslater(1920, 1080)
    >>> rr.add_target_scale((width, height))
    >>> rr.t(1280, 720)
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self._target_scale = Fraction(1, 1)

    @overload
    def add_target_scale(self, target: int | float, /) -> None: ...
    @overload
    def add_target_scale(self, target: Fraction, /) -> None: ...
    @overload
    def add_target_scale(self, target: tuple[int, int], /) -> None: ...
    def add_target_scale(self, target: tuple[int, int] | Fraction | int | float, /) -> None:
        """
        Add target scale to scale resolution to

        Parameters
        ----------
        target : tuple[int, int] | Fraction | int | float
            Target scale (tuple[int, int] for desire resolution)

        Raises
        ------
        NotImplementedError
            When ratio of new and old resolution is not equal
        """
        if isinstance(target, tuple):  # Resolution
            if self.ratio == Fraction(*target):  # Same ratio
                self._target_scale = Fraction(target[0] / self.x)
            else:
                raise NotImplementedError("Resolution's ratio conversion not supported")
        else:
            self._target_scale = Fraction(target)

    def translate_point(self, x: int, y: int, /) -> tuple[int, int]:
        """
        Translate point(x, y) to target_scale fixed point through relative point.

        Parameters
        ----------
        x : int
            Normally width

        y : int
            Normally height

        Returns
        -------
        tuple[int, int]
            Translated point
        """
        x_rel, y_rel = self.get_point_relative(x, y)
        fixed_point = self.scale_by(self._target_scale).get_fixed_point(x_rel, y_rel)
        return fixed_point

    def t(self, x: int, y: int, /) -> tuple[int, int]:
        """Wrapper for self.translate_point"""
        return self.translate_point(x, y)
