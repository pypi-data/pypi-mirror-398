"""
Absfuyu: Inspector
------------------
Inspector

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Inspector", "inspect_all"]


# Library
# ---------------------------------------------------------------------------
import inspect as _inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from textwrap import TextWrapper
from textwrap import shorten as text_shorten
from typing import Any, Literal, Protocol, get_overloads, overload

from absfuyu.core.baseclass import (
    AutoREPRMixin,
    BaseDataclass,
    ClassMembers,
    ClassMembersResult,
    GetClassMembersMixin,
)
from absfuyu.dxt.listext import ListExt
from absfuyu.typings import P, R
from absfuyu.util.text_table import BoxStyle, OneColumnTableMaker


# TODO: rewrite with each class for docs, method, property, attr, param, title
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class BaseDCInspect(BaseDataclass):
    def _make_repr(self) -> str | None:
        fields = self._get_fields()
        if 0 < len(fields) < 2:
            return repr(getattr(self, fields[0]))
        return None

    def _long_list_terminal_size(
        self, long_list: list[str], width: int = 80, /
    ) -> list[str]:
        ll = ListExt(long_list).wrap_to_column(width, margin=4, transpose=True)
        return list(ll)


@dataclass
class _TitleSignature:
    """
    Inspector:
    Object's title and signature
    """

    title: str
    signature: list[str]

    def make_output(self):
        pass


@dataclass
class _Docstring(BaseDCInspect):
    """
    Inspector:
    Object's docstring
    """

    docs: str

    def __repr__(self) -> str:
        r = self._make_repr()
        if r is not None:
            return r
        return super().__repr__()

    def _get_first_paragraph(self) -> str:
        # Get docs and get first paragraph
        doc_lines = []
        for line in self.docs.splitlines():
            if len(line) < 1:
                break
            doc_lines.append(line.strip())
        return " ".join(doc_lines)

    def make_output(self) -> list[str]:
        if len(self._get_first_paragraph()) > 0:
            return ["Docstring:", self._get_first_paragraph()]
        return [""]


@dataclass
class _MRO(BaseDCInspect):
    """
    Inspector:
    Object's MRO, bases
    """

    mro: tuple[type, ...]

    def __repr__(self) -> str:
        r = self._make_repr()
        if r is not None:
            return r
        return super().__repr__()

    def _make_output(self) -> list[str]:
        out = [
            f"- {i:02}. {x.__module__}.{x.__name__}"
            for i, x in enumerate(self.mro[1:], start=1)
        ]
        # ListExt.wrap_to_column
        return out

    def make_output(self, *, width: int = 80) -> list[str]:
        out = self._make_output()
        if len(out) > 0:
            out_ = self._long_list_terminal_size(out, width)
            return ["", f"Bases (Len: {len(out)}):", *out_]
        return [""]


@dataclass
class _Member(BaseDCInspect):
    """
    Inspector:
    Object's member
    """

    member: ClassMembers

    def __repr__(self) -> str:
        r = self._make_repr()
        if r is not None:
            return r
        return super().__repr__()

    def make_output(
        self,
        *,
        width: int = 80,
        obj,
        include_method: bool = True,
        include_property: bool = True,
    ) -> list[str]:
        mems = self.member.pack().sort()
        body: list[str] = []

        if include_method:
            ml = [text_shorten(f"- {x}", width - 4) for x in mems.methods]
            if len(ml) > 0:
                head = ["", f"Methods (Len: {len(ml)}):"]
                head.extend(self._long_list_terminal_size(ml, width))
                body.extend(head)

        if include_property:
            pl = [
                text_shorten(f"- {x} = {getattr(obj, x, None)}", width - 4)
                for x in mems.properties
            ]
            if len(pl) > 0:
                head = ["", f"Properties (Len: {len(pl)}):"]
                head.extend(self._long_list_terminal_size(pl, width))
                body.extend(head)

        if len(body) > 0:
            return body
        return [""]


class InspectComponents(Protocol):
    """Supports make_output() -> list[str]"""

    @overload
    def make_output(self) -> list[str]: ...
    @overload
    def make_output(self, *, width: int = ...) -> list[str]: ...
    def make_output(self, *args, **kwargs) -> list[str]: ...


# Class
# ---------------------------------------------------------------------------
class Inspector(AutoREPRMixin):
    """
    Inspect an object.
    By default shows object's docstring and attribute (if any).

    Parameters
    ----------
    obj : Any
        Object to inspect

    line_length: int | None
        Number of cols in inspect output (Split line every line_length).
        Set to ``None`` to use ``os.get_terminal_size()``, by default ``None``

    include_docs : bool, optional
        Include docstring, by default ``True``

    include_mro : bool, optional
        Include class bases (__mro__), by default ``False``

    include_method : bool, optional
        Include object's methods (if any), by default ``False``

    include_property : bool, optional
        Include object's properties (if any), by default ``False``

    include_attribute : bool, optional
        Include object's attributes (if any), by default ``True``

    include_private : bool, optional
        Include object's private attributes, by default ``False``

    include_all : bool, optional
        Include all infomation availble, by default ``False``

    max_textwrap_lines : int, optional
        Maximum lines for the output's header (class, signature, repr).
        Must be >= 1, by default ``8``

    style : BoxStyle, optional
        Style for the table, by default ``"normal"``


    Example:
    --------
    >>> print(Inspector(<object>, **kwargs))
    """

    @overload
    def __init__(self, obj: Any) -> None: ...

    @overload
    def __init__(self, obj: Any, *, include_all: Literal[True] = ...) -> None: ...

    @overload
    def __init__(
        self,
        obj: Any,
        *,
        line_length: int | None = None,
        include_docs: bool = True,
        include_mro: bool = False,
        include_method: bool = False,
        include_property: bool = False,
        include_attribute: bool = True,
        include_private: bool = False,
        max_textwrap_lines: int = 8,
        style: BoxStyle = "normal",
    ) -> None: ...

    def __init__(
        self,
        obj: Any,
        *,
        # Line length
        line_length: int | None = None,
        line_length_offset: int = 0,  # line_length += line_length_offset (when line_length=None)
        max_textwrap_lines: int = 8,
        # Include
        include_docs: bool = True,
        include_mro: bool = False,
        include_method: bool = False,
        include_property: bool = False,
        include_attribute: bool = True,
        include_dunder: bool = False,
        include_private: bool = False,
        include_all: bool = False,
        # Style
        style: BoxStyle = "normal",
    ) -> None:
        """
        Inspect an object.
        By default shows object's docstring and attribute (if any).

        Parameters
        ----------
        obj : Any
            Object to inspect

        line_length: int | None
            Number of cols in inspect output (Split line every line_length).
            Set to ``None`` to use ``os.get_terminal_size()``, by default ``None``

        include_docs : bool, optional
            Include docstring, by default ``True``

        include_mro : bool, optional
            Include class bases (__mro__), by default ``False``

        include_method : bool, optional
            Include object's methods (if any), by default ``False``

        include_property : bool, optional
            Include object's properties (if any), by default ``False``

        include_attribute : bool, optional
            Include object's attributes (if any), by default ``True``

        include_private : bool, optional
            Include object's private attributes, by default ``False``

        include_all : bool, optional
            Include all infomation availble, by default ``False``

        max_textwrap_lines : int, optional
            Maximum lines for the output's header (class, signature, repr).
            Must be >= 1, by default ``8``

        style : BoxStyle | Literal["normal", "bold", "dashed", "double", "rounded", ...], optional
            Style for the table, by default ``"normal"``


        Example:
        --------
        >>> print(Inspector(<object>, **kwargs))
        """
        self.obj = obj
        self.include_docs = include_docs
        self.include_mro = include_mro
        self.include_method = include_method
        self.include_property = include_property
        self.include_attribute = include_attribute
        self.include_private = include_private
        self.include_dunder = include_dunder
        self._style = style

        if include_all:
            self.include_docs = True
            self.include_mro = True
            self.include_method = True
            self.include_property = True
            self.include_attribute = True
            self.include_private = True

        # Setup line length
        if line_length is None:
            try:
                self._linelength = os.get_terminal_size().columns + line_length_offset
            except OSError:
                self._linelength = 88
        elif isinstance(line_length, (int, float)):
            self._linelength = max(int(line_length), 9)
        else:
            raise ValueError("Use different line_length")

        # Textwrap
        self._text_wrapper = TextWrapper(
            width=self._linelength - 4,
            initial_indent="",
            subsequent_indent="",
            tabsize=4,
            break_long_words=True,
            max_lines=max(max_textwrap_lines, 1),
        )

        # Output
        self._inspect_output = self._make_output()

    def __str__(self) -> str:
        return self._inspect_output.make_table()

    # 00. Support
    # -----------------------------------------------------------
    # @deprecated
    def _long_list_terminal_size(self, long_list: list) -> list:
        ll = ListExt(long_list).wrap_to_column(
            self._linelength, margin=4, transpose=True
        )
        return list(ll)

    # 01. Signature
    # -----------------------------------------------------------
    def _make_title(self) -> str:
        title_str = (
            str(self.obj)
            if (
                _inspect.isclass(self.obj)
                or callable(self.obj)
                or _inspect.ismodule(self.obj)
            )
            else str(type(self.obj))
        )
        return title_str

    def _get_signature_prefix(self) -> str:
        # signature prefix
        if _inspect.isclass(self.obj):
            return "class"
        elif _inspect.iscoroutinefunction(self.obj):
            return "async def"
        elif _inspect.isfunction(self.obj):
            return "def"
        return ""

    # @deprecated
    def get_parameters(self) -> list[str] | None:
        try:
            sig = _inspect.signature(self.obj)
        except (ValueError, AttributeError, TypeError):
            return None
        return [str(x) for x in sig.parameters.values()]

    def _get_func_signature(self, func: Callable[P, R]) -> list[str]:
        overloads = list(get_overloads(func))
        if len(overloads) < 1:
            return [
                f"{self._get_signature_prefix()} {func.__name__}{_inspect.signature(func)}"
            ]
        return [
            f"{self._get_signature_prefix()} {x.__name__}{_inspect.signature(x)}"
            for x in overloads
        ]

    # @deprecated
    def _make_signature(self) -> list[str]:
        try:
            # if isinstance(self.obj, Callable):
            if _inspect.isfunction(self.obj):
                funcs = [
                    self._text_wrapper.wrap(x)
                    for x in self._get_func_signature(self.obj)
                ]
                return ListExt(funcs).flatten()
            return self._text_wrapper.wrap(
                f"{self._get_signature_prefix()} {self.obj.__name__}{_inspect.signature(self.obj)}"
            )
        #    not class, func | not type   | is module
        except (ValueError, AttributeError, TypeError):
            return self._text_wrapper.wrap(repr(self.obj))

    @property
    def obj_signature(self) -> _TitleSignature:
        """Object's title and signature"""
        title: str = self._make_title()
        sig: list[str] = []
        try:
            if _inspect.isfunction(self.obj):
                sig.extend(self._get_func_signature(self.obj))
            sig.append(
                f"{self._get_signature_prefix()} {self.obj.__name__}{_inspect.signature(self.obj)}"
            )
        #    not class, func | not type   | is module
        except (ValueError, AttributeError, TypeError):
            sig.append(repr(self.obj))

        return _TitleSignature(title=title, signature=sig)

    # 02. Docstring
    # -----------------------------------------------------------
    @property
    def obj_docs(self) -> _Docstring:
        """Object's docstring"""
        docs: str | None = _inspect.getdoc(self.obj)

        if docs is None:
            return _Docstring("")
        return _Docstring(docs=docs)

    # @deprecated
    def _get_docs(self) -> str:
        docs: str | None = _inspect.getdoc(self.obj)

        if docs is None:
            return ""

        # Get docs and get first paragraph
        # doc_lines: list[str] = [x.strip() for x in docs.splitlines()]
        doc_lines = []
        for line in docs.splitlines():
            if len(line) < 1:
                break
            doc_lines.append(line.strip())

        return text_shorten(" ".join(doc_lines), width=self._linelength - 4, tabsize=4)

    # 03. MRO/Bases
    # -----------------------------------------------------------
    @property
    def obj_mro(self) -> _MRO:
        """Object's MRO, bases"""
        if isinstance(self.obj, type):
            return _MRO(mro=self.obj.__mro__[::-1])
        return _MRO(mro=type(self.obj).__mro__[::-1])

    @property
    def obj_bases(self) -> _MRO:
        """Object's MRO, bases"""
        return self.obj_mro

    # @deprecated
    def _get_mro(self) -> tuple[type, ...]:
        """Get MRO in reverse and subtract <class 'object'>"""
        if isinstance(self.obj, type):
            return self.obj.__mro__[::-1][1:]
        return type(self.obj).__mro__[::-1][1:]

    # @deprecated
    def _make_mro_data(self) -> list[str]:
        mro = [
            f"- {i:02}. {x.__module__}.{x.__name__}"
            for i, x in enumerate(self._get_mro(), start=1)
        ]
        mod_chunk = self._long_list_terminal_size(mro)

        # return [text_shorten(x, self._linelength - 4) for x in mod_chunk]
        return mod_chunk

    # 04. Class's members
    # -----------------------------------------------------------
    def _get_obj_member(self) -> ClassMembersResult:
        # if _inspect.isclass(self.obj) or inspect.ismodule(self.obj):
        if _inspect.isclass(self.obj):
            tmpcls = type(
                "tmpcls",
                (
                    self.obj,
                    GetClassMembersMixin,
                ),
                {},
            )
        else:
            tmpcls = type(
                "tmpcls",
                (
                    type(self.obj),
                    GetClassMembersMixin,
                ),
                {},
            )
        med_prop = tmpcls._get_members(  # type: ignore
            dunder=False, private=self.include_private
        )

        try:
            # If self.obj is a subclass of GetClassMembersMixin
            _mro = getattr(
                self.obj, "__mro__", getattr(type(self.obj), "__mro__", None)
            )
            if GetClassMembersMixin in _mro:  # type: ignore
                return med_prop  # type: ignore
        except AttributeError:  # Not a class
            pass
        med_prop.__delitem__(GetClassMembersMixin.__name__)
        return med_prop  # type: ignore

    @property
    def obj_member(self) -> _Member:
        """Object's members"""
        try:
            mem = self._get_obj_member()
            return _Member(mem.flatten_value())
        except (TypeError, AttributeError):
            return _Member(ClassMembers())

    # @deprecated
    def _get_method_property(self) -> ClassMembersResult:
        return self._get_obj_member()

    # Attribute
    @staticmethod
    def _is_real_attribute(obj: Any) -> bool:
        """
        Not method, classmethod, staticmethod, property
        """
        if callable(obj):
            return False
        if isinstance(obj, staticmethod):
            return False
        if isinstance(obj, classmethod):
            return False
        if isinstance(obj, property):
            return False
        return True

    def _get_attributes(self) -> list[tuple[str, Any]]:
        # Get attributes
        cls_dict = getattr(self.obj, "__dict__", None)
        cls_slots = getattr(self.obj, "__slots__", None)
        out = []

        # Check if __dict__ exist and len(__dict__) > 0
        if cls_dict is not None and len(cls_dict) > 0:
            if self.include_private:
                out = [
                    (k, v)
                    for k, v in self.obj.__dict__.items()
                    if self._is_real_attribute(v)
                ]
            else:
                out = [
                    (k, v)
                    for k, v in self.obj.__dict__.items()
                    if not k.startswith("_") and self._is_real_attribute(v)
                ]

        # Check if __slots__ exist and len(__slots__) > 0
        elif cls_slots is not None and len(cls_slots) > 0:
            if self.include_private:
                out = [
                    (x, getattr(self.obj, x))
                    for x in self.obj.__slots__  # type: ignore
                    if self._is_real_attribute(getattr(self.obj, x))
                ]
            else:
                out = [
                    (x, getattr(self.obj, x))
                    for x in self.obj.__slots__  # type: ignore
                    if not x.startswith("_")
                    and self._is_real_attribute(getattr(self.obj, x))
                ]

        return out

    def _handle_attributes_for_output(
        self, attr_list: list[tuple[str, Any]]
    ) -> list[str]:
        return [
            text_shorten(f"- {x[0]} = {x[1]}", self._linelength - 4) for x in attr_list
        ]

    # Output
    # -----------------------------------------------------------
    # @deprecated
    def _make_output(self) -> OneColumnTableMaker:
        table = OneColumnTableMaker(self._linelength, style=self._style)  # type: ignore
        body: list[str] = []

        # Signature
        title = self._make_title()
        table.add_title(title)
        sig = self._make_signature()
        if table._title == "":  # Title too long
            _title = [title]
            _title.extend(sig)
            table.add_paragraph(_title)
        else:
            table.add_paragraph(sig)

        # Docstring
        docs = self._get_docs()
        if len(docs) > 0 and self.include_docs:
            body.extend(["Docstring:", docs])

        # Class bases
        clsbases = self._make_mro_data()
        if len(clsbases) > 0 and self.include_mro:
            body.extend(["", f"Bases (Len: {len(self._get_mro())}):"])
            body.extend(clsbases)

        # Method & Property
        try:
            method_n_properties = (
                self._get_method_property().flatten_value().pack().sort()
            )
            if self.include_method:
                ml = [
                    text_shorten(f"- {x}", self._linelength - 4)
                    for x in method_n_properties.methods
                ]
                if len(ml) > 0:
                    head = ["", f"Methods (Len: {len(ml)}):"]
                    head.extend(self._long_list_terminal_size(ml))
                    body.extend(head)
            if self.include_property:
                pl = [
                    text_shorten(
                        f"- {x} = {getattr(self.obj, x, None)}", self._linelength - 4
                    )
                    for x in method_n_properties.properties
                ]
                if len(pl) > 0:
                    head = ["", f"Properties (Len: {len(pl)}):"]
                    head.extend(pl)
                    body.extend(head)
        except (TypeError, AttributeError):
            pass

        # Attribute
        attrs = self._get_attributes()
        if len(attrs) > 0 and self.include_attribute:
            body.extend(["", f"Attributes (Len: {len(attrs)}):"])
            body.extend(self._handle_attributes_for_output(attr_list=attrs))

        # Add to table
        table.add_paragraph(body)

        return table

    def _make_output_2(self) -> OneColumnTableMaker:
        # Prep
        # components: list[InspectComponents] = [
        #     self.obj_signature,
        #     self.obj_docs,
        #     self.obj_mro,
        #     self.obj_member,
        # ]
        table = OneColumnTableMaker(self._linelength, style=self._style)  # type: ignore
        body: list[str] = []

        # Signature
        title = self.obj_signature.title
        table.add_title(title)
        if table._title == "":  # Title too long
            _title = [title]
            _title.extend(self.obj_signature.signature)
            table.add_paragraph(_title)
        else:
            table.add_paragraph(self.obj_signature.signature)

        # Docstring
        if self.include_docs:
            body.extend(self.obj_docs.make_output())

        # Class bases
        if self.include_mro:
            body.extend(self.obj_mro.make_output(width=self._linelength))

        # Method & Property
        body.extend(
            self.obj_member.make_output(
                width=self._linelength,
                obj=self.obj,
                include_method=self.include_method,
                include_property=self.include_property,
            )
        )

        # Attribute
        attrs = self._get_attributes()
        if len(attrs) > 0 and self.include_attribute:
            body.extend(["", f"Attributes (Len: {len(attrs)}):"])
            body.extend(self._handle_attributes_for_output(attr_list=attrs))

        # Add to table
        table.add_paragraph(body)

        return table


# Partial
# ---------------------------------------------------------------------------
inspect_all = partial(Inspector, line_length=None, include_all=True)  # type: ignore
