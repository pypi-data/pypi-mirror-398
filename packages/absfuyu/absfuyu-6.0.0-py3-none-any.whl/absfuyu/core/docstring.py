"""
Absfuyu: Core
-------------
Sphinx docstring decorator

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    "SphinxDocstring",
    "SphinxDocstringMode",
    "versionadded",
    "versionchanged",
    "deprecated",
]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from enum import Enum
from functools import partial, wraps
from string import Template
from typing import ClassVar, ParamSpec, TypeVar, overload

# Type
# ---------------------------------------------------------------------------
_P = ParamSpec("_P")  # Parameter type
_R = TypeVar("_R")  # Return type - Can be anything
_T = TypeVar("_T", bound=type)  # Type type - Can be any subtype of `type`

_SPHINX_DOCS_TEMPLATE = Template("$line_break*$mode in version $version$reason*")


# Class
# ---------------------------------------------------------------------------
class SphinxDocstringMode(Enum):
    """
    Enum representing the mode of the version change
    (added, changed, or deprecated)
    """

    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    PENDING_REMOVE = "Pending to remove"


class SphinxDocstring:
    """
    A class-based decorator to add a 'Version added',
    'Version changed', or 'Deprecated' note to a function's docstring,
    formatted for Sphinx documentation.

    Parameters
    ----------
    version : str
        The version in which the function was added, changed, or deprecated.

    reason : str | None, optional
        An optional reason or description for the change
        or deprecation, by default ``None``

    mode : SphinxDocstringMode, optional
        Specifies whether the function was 'added', 'changed', or 'deprecated',
        by default SphinxDocstringMode.ADDED


    Usage
    -----
    Use this as a decorator (``@SphinxDocstring(<parameters>)``)
    """

    _LINEBREAK: ClassVar[str] = "\n\n"  # Use ClassVar for constant

    def __init__(
        self,
        version: str,
        reason: str | None = None,
        mode: SphinxDocstringMode = SphinxDocstringMode.ADDED,
    ) -> None:
        """
        Initializes the SphinxDocstring decorator.

        Parameters
        ----------
        version : str
            The version in which the function was added, changed, or deprecated.

        reason : str | None, optional
            An optional reason or description for the change
            or deprecation, by default ``None``

        mode : SphinxDocstringMode, optional
            Specifies whether the function was 'added', 'changed', or 'deprecated',
            by default SphinxDocstringMode.ADDED

        Usage
        -----
        Use this as a decorator (``@SphinxDocstring(<parameters>)``)
        """
        self.version = version
        self.reason = reason
        self.mode = mode

    @overload  # Class overload
    def __call__(self, obj: _T) -> _T: ...

    @overload  # Function overload
    def __call__(self, obj: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(self, obj: _T | Callable[_P, _R]) -> _T | Callable[_P, _R]:
        """
        Decorator for class and callable
        """

        # Class wrapper
        if isinstance(obj, type):  # if inspect.isclass(obj):
            return self._update_doc(obj)

        # Function wrapper
        @wraps(obj)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return obj(*args, **kwargs)

        return self._update_doc(wrapper)

    def _calculate_white_space(self, docs: str | None) -> int:
        """
        Calculates the number of leading white spaces
        in __doc__ of original function
        """

        res = 0
        if docs is None:
            return res

        try:
            # Replace tabs with space and split line
            lines = docs.expandtabs(4).splitlines()
        except UnicodeError:
            return res
        else:
            # Get indentation of each line and unique it
            indent_set = {len(line) - len(line.lstrip()) for line in lines[1:]}
            # Drop 0
            res_list = sorted([x for x in indent_set if x > 0])

        if res_list:
            return res_list[0]
        return res

    def _generate_version_note(self, num_of_white_spaces: int) -> str:
        """
        Generates the version note string based on the mode
        """
        reason_str = f": {self.reason}" if self.reason else ""
        # return f"{self._LINEBREAK}*{self.mode.value} in version {self.version}{reason_str}*"
        return _SPHINX_DOCS_TEMPLATE.substitute(
            line_break=self._LINEBREAK + " " * num_of_white_spaces,
            mode=self.mode.value,
            version=self.version,
            reason=reason_str,
        )

    @overload
    def _update_doc(self, obj: _T) -> _T: ...
    @overload
    def _update_doc(self, obj: Callable[_P, _R]) -> Callable[_P, _R]: ...
    def _update_doc(self, obj: _T | Callable[_P, _R]) -> _T | Callable[_P, _R]:
        """Update docstring for an object"""
        obj.__doc__ = (obj.__doc__ or "") + self._generate_version_note(
            num_of_white_spaces=self._calculate_white_space(obj.__doc__)
        )
        return obj


# Partial
# ---------------------------------------------------------------------------
versionadded = partial(SphinxDocstring, mode=SphinxDocstringMode.ADDED)
versionchanged = partial(SphinxDocstring, mode=SphinxDocstringMode.CHANGED)
deprecated = partial(SphinxDocstring, mode=SphinxDocstringMode.DEPRECATED)
pendingremove = partial(SphinxDocstring, mode=SphinxDocstringMode.PENDING_REMOVE)
