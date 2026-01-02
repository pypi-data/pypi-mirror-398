"""
ABSFUYU CLI
-----------
Color

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["COLOR"]


# Library
# ---------------------------------------------------------------------------
try:
    import colorama
except ImportError:  # Check for `colorama`
    colorama = None

# Color
# ---------------------------------------------------------------------------
if colorama is None:
    COLOR = {
        "green": "",
        "GREEN": "",
        "blue": "",
        "BLUE": "",
        "red": "",
        "RED": "",
        "yellow": "",
        "YELLOW": "",
        "reset": "",
    }
else:
    COLOR = {
        "green": colorama.Fore.LIGHTGREEN_EX,
        "GREEN": colorama.Fore.GREEN,
        "blue": colorama.Fore.LIGHTCYAN_EX,
        "BLUE": colorama.Fore.CYAN,
        "red": colorama.Fore.LIGHTRED_EX,
        "RED": colorama.Fore.RED,
        "yellow": colorama.Fore.LIGHTYELLOW_EX,
        "YELLOW": colorama.Fore.YELLOW,
        "reset": colorama.Fore.RESET,
    }
