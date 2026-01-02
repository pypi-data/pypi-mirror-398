"""
Absfuyu: GUI
------------
Custom tkinter GUI

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["CustomTkinterApp"]


# Library
# ---------------------------------------------------------------------------
import tkinter as tk

from absfuyu.pkg_data.logo import AbsfuyuLogo


# Class
# ---------------------------------------------------------------------------
class CustomTkinterApp(tk.Tk):

    def __init__(self, title: str | None = None, size: tuple[int, int] | None = None) -> None:
        """
        Custom Tkinter GUI

        Parameters
        ----------
        title : str | None, optional
            Title of the app, by default None

        size : tuple[int, int] | None, optional
            Size of the app (width, height), by default None
        """
        super().__init__()

        # Set custom icon
        self.iconphoto(True, tk.PhotoImage(data=AbsfuyuLogo.SHORT))

        # Title
        self.title(title)

        # Set size
        self._absfuyu_set_width_height(size)

    # @versionadded("5.10.0")
    def _absfuyu_set_width_height(self, size: tuple[int, int] | None = None) -> None:
        """
        Set width and height for the app.

        Parameters
        ----------
        size : tuple[int, int] | None, optional
            Size of the app (width, height), by default ``None``
            (420 x 250)
        """
        # Set GUI appears in center
        if size is None:
            _width = 420
            _height = 250
        else:
            _width, _height = size

        _width_screen = self.winfo_screenwidth()
        _width_screen_offset = 0.0052  # x offset mutiplier
        _x_offset = int(_width_screen * _width_screen_offset)

        _height_screen = self.winfo_screenheight()
        _height_screen_offset = 0.0926  # y offset mutiplier
        _y_offset = int(_height_screen * _height_screen_offset)

        if _width > _width_screen:
            _width = int(_width_screen * (1 - 0.001))
            # _x_offset = 0

        if _height > (_height_screen - _y_offset):
            _height = int(_height_screen * (1 - 0.001))
            _y_offset = 0

        _x = (_width_screen / 2) - (_width / 2) - _x_offset
        _y = (_height_screen / 2) - (_height / 2) - _y_offset

        self.geometry(f"{_width}x{_height}+{int(_x)}+{int(_y)}")


if __name__ == "__main__":
    app = CustomTkinterApp("absfuyu")
    app.mainloop()
