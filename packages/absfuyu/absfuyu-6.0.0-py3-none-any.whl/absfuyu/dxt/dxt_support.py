"""
Absfuyu: Data Extension
-----------------------
Support classes

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["DictBoolTrue", "DictBoolFalse"]


# Library
# ---------------------------------------------------------------------------
from typing import Any

from absfuyu.logger import _compress_list_for_print


# Dict Boolean Masking Repr
# ---------------------------------------------------------------------------
def _dict_bool(dict_object: dict, option: bool) -> dict | None:
    """
    Support function DictBool class
    """
    out = dict()
    for k, v in dict_object.items():
        if v == option:
            out[k] = v
    if out:
        return out
    else:
        return None


class DictBoolTrue(dict[Any, bool]):
    """Only show items when ``values == True`` in ``__repr__()``"""

    def __repr__(self) -> str:
        temp = self.copy()
        return _dict_bool(temp, True).__repr__()


class DictBoolFalse(dict[Any, bool]):
    """Only show items when ``values == False`` in ``__repr__()``"""

    def __repr__(self) -> str:
        temp = self.copy()
        return _dict_bool(temp, False).__repr__()


# ---------------------------------------------------------------------------
class ListREPR(list):
    """Show ``list`` in shorter form"""

    def __repr__(self) -> str:
        return _compress_list_for_print(self, 9)


class ListNoDunder(list[str]):
    """Use with ``object.__dir__()``"""

    def __repr__(self) -> str:
        out = [x for x in self if not x.startswith("__")]
        return out.__repr__()


# class DictNoDunder(dict):  # W.I.P
#     """Remove dunder methods in ``__repr__()`` of dict"""

#     def __repr__(self) -> str:
#             temp = self.copy()
#             out = dict()
#             for k, v in temp.items():
#                 if not str(k).startswith("__"):
#                     out.__setattr__(k, v)
#             return out.__repr__()
