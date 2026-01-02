"""
Absfuyu: Data Extension
-----------------------
Extension for data type such as ``list``, ``str``, ``dict``, ...

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Features:
---------
- DictExt
- IntExt
- ListExt
- Text
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # Main
    "DictExt",
    "IntExt",
    "ListExt",
    "Text",
    # Support
    "DictAnalyzeResult",
    "DictBoolFalse",
    "DictBoolTrue",
    "ListNoDunder",
    "ListREPR",
    "Pow",
    "TextAnalyzeDictFormat",
]


# Library
# ---------------------------------------------------------------------------
from absfuyu.dxt.dictext import DictAnalyzeResult, DictExt
from absfuyu.dxt.dxt_support import DictBoolFalse, DictBoolTrue, ListNoDunder, ListREPR
from absfuyu.dxt.intext import IntExt, Pow
from absfuyu.dxt.listext import ListExt
from absfuyu.dxt.strext import Text, TextAnalyzeDictFormat
