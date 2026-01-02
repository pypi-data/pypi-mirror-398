"""
Absfuyu: Core
-------------
Dummy functions when other libraries are unvailable

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    "tqdm",
    "unidecode",
    "dummy_function",
]


# Library
# ---------------------------------------------------------------------------
from importlib import import_module

# Wrapper
# ---------------------------------------------------------------------------
# tqdm wrapper
try:
    _tqdm = import_module("tqdm")
    tqdm = getattr(_tqdm, "tqdm")  # noqa
except (ImportError, AttributeError):

    def tqdm(iterable, *args, **kwargs):
        """
        Dummy tqdm function,
        install package ``tqdm`` to fully use this feature
        """
        return iterable


# unidecode wrapper
try:
    _unidecode = import_module("unidecode")
    unidecode = getattr(_unidecode, "unidecode")  # noqa
except (ImportError, AttributeError):

    def unidecode(*args, **kwargs):
        """
        Dummy unidecode function,
        install package ``unidecode`` to fully use this feature
        """
        return args[0]


# dummy
def dummy_function(*args, **kwargs):
    """This is a dummy function"""
    if args:
        return args[0]
    if kwargs:
        return kwargs[list(kwargs)[0]]
    return None
