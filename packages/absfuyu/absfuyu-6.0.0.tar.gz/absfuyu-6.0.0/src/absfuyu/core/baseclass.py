"""
Absfuyu: Core
-------------
Bases for other features

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # Color
    "CLITextColor",
    # Support
    "ClassMembers",
    "ClassMembersResult",
    # Mixins
    "GetClassMembersMixin",
    "AutoREPRMixin",
    "AddFormatMixin",
    # Class
    "BaseClass",
    "BaseDataclass",
    # Metaclass
    "PositiveInitArgsMeta",
]

# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, Self


# Color
# ---------------------------------------------------------------------------
class CLITextColor:
    """Color code for text in terminal"""

    WHITE = "\x1b[37m"
    BLACK = "\x1b[30m"
    BLUE = "\x1b[34m"
    GRAY = "\x1b[90m"
    GREEN = "\x1b[32m"
    RED = "\x1b[91m"
    DARK_RED = "\x1b[31m"
    MAGENTA = "\x1b[35m"
    YELLOW = "\x1b[33m"
    RESET = "\x1b[39m"


# Dataclass
# ---------------------------------------------------------------------------
# @versionadded("5.5.0")
@dataclass
class BaseDataclass:
    """
    Base dataclass.

    Contains util methods:
    - _get_fields
    - to_dict
    """

    @classmethod
    def _get_fields(cls) -> tuple[str, ...]:
        """
        Get dataclass's fields.

        Returns
        -------
        tuple[str, ...]
            Dataclass's fields.
        """
        _fields = getattr(cls, "__dataclass_fields__", ())
        return tuple(_fields)

    # @versionadded("5.11.0")
    def to_dict(self):
        """
        Convert dataclass into dict

        Returns
        -------
        dict
            Dataclass converted into dict
        """
        fields = self._get_fields()
        output = {}
        for field in fields:
            output.__setitem__(field, self.__getattribute__(field))
        return output


# Support
# ---------------------------------------------------------------------------
# @versionadded("5.5.0")
@dataclass
class ClassMembers(BaseDataclass):
    """
    Contains lists of methods, classmethods, staticmethods,
    properties, and attributes of a class.

    Parameters
    ----------
    methods : list[str], optional
        List contains method names of a class.
        By default inits an empty list.

    classmethods : list[str], optional
        List contains classmethod names of a class.
        By default inits an empty list.

    staticmethods : list[str], optional
        List contains staticmethod names of a class.
        By default inits an empty list.

    properties : list[str], optional
        List contains property names of a class.
        By default inits an empty list.

    attributes : list[str], optional
        List contains attributes of a class instance.
        By default inits an empty list.

    classattributes : list[str], optional
        List contains attributes of a class.
        By default inits an empty list.


    Available formats
    -----------------
    Alternative format to use with: ``format(<obj>, <format_spec>)``
    - ``s``/``short`` (This hides attributes with empty value)
    """

    methods: list[str] = field(default_factory=list)
    classmethods: list[str] = field(default_factory=list)
    staticmethods: list[str] = field(default_factory=list)
    properties: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    classattributes: list[str] = field(default_factory=list)

    def __format__(self, format_spec: str) -> str:
        """
        Available format:
        - ``s``/``short`` (This hides attributes with empty value)

        Parameters
        ----------
        format_spec : str
            Format spec

        Returns
        -------
        str
            Alternative text representation of this class.
        """

        fmt = format_spec.lower().strip()
        cls_name = self.__class__.__name__

        if fmt == "short" or fmt == "s":
            out = []
            sep = ", "
            for x in self._get_fields():
                if len(getattr(self, x)) > 0:
                    out.append(f"{x}={repr(getattr(self, x))}")
            return f"{cls_name}({sep.join(out)})"

        return self.__repr__()

    def is_empty(self) -> bool:
        """
        Checks if all fields are empty.


        Example:
        --------
        >>> ClassMembers().is_empty()
        True

        >>> ClassMembers(["a"]).is_empty()
        False
        """

        # return all(len(getattr(self, x)) == 0 for x in self._get_fields())
        for x in self._get_fields():
            if len(getattr(self, x)) > 0:
                return False
        return True

    def pack(
        self,
        include_method: bool = True,
        include_classmethod: bool = True,
        classmethod_indicator: str = "<cls>",
        include_staticmethod: bool = True,
        staticmethod_indicator: str = "<stc>",
        include_attribute: bool = True,
        include_classattribute: bool = True,
        classattribute_indicator: str = "<cls>",
    ) -> Self:
        """
        Combines the following into one list:
        - methods, classmethods, and staticmethods
        - attributes and class attributes

        Parameters
        ----------
        include_method : bool, optional
            Whether to include methods in the output, by default ``True``

        include_classmethod : bool, optional
            Whether to include classmethods in the output, by default ``True``

        classmethod_indicator : str, optional
            A string used to mark classmethod in the output. This string is appended
            to the name of each classmethod to visually differentiate it from regular
            instance methods, by default ``"<cls>"``

        include_staticmethod : bool, optional
            Whether to include staticmethods in the output, by default ``True``

        staticmethod_indicator : str, optional
            A string used to mark staticmethod in the output. This string is appended
            to the name of each staticmethod to visually differentiate it from regular
            instance methods, by default ``"<stc>"``

        include_attribute : bool, optional
            Whether to include attributes in the output, by default ``True``

        include_classattribute : bool, optional
            Whether to include class attributes in the output, by default ``True``

        classattribute_indicator : str, optional
            A string used to mark class attribute in the output. This string is appended
            to the name of each class attribute to visually differentiate it from regular
            instance attributes, by default ``"<cls>"``

        Returns
        -------
        Self
            ClassMembers (combined methods)


        Example:
        --------
        >>> ClassMembers(["a"], ["b"], ["c"], ["d"], ["e"], ["f"]).pack().__format__("short")
        ClassMembers(methods=['a', 'b <cls>', 'c <stc>'], properties=['d'], attributes=['e', 'f <cls>'])
        """

        new_methods_list: list[str] = []

        # Method
        if include_method:
            new_methods_list.extend(self.methods)

        # Classmethod
        if include_classmethod:
            new_methods_list.extend(
                [f"{x} {classmethod_indicator}".strip() for x in self.classmethods]
            )

        # Staticmethod
        if include_staticmethod:
            new_methods_list.extend(
                [f"{x} {staticmethod_indicator}".strip() for x in self.staticmethods]
            )

        new_attributes_list: list[str] = []

        # Attribute
        if include_attribute:
            new_attributes_list.extend(self.attributes)

        # Class attribute
        if include_classattribute:
            new_attributes_list.extend(
                [
                    f"{x} {classattribute_indicator}".strip()
                    for x in self.classattributes
                ]
            )

        # return self.__class__(new_methods_list, [], [], self.properties, [])
        return self.__class__(
            methods=new_methods_list,
            properties=self.properties,
            attributes=new_attributes_list,
        )

    def sort(self, reverse: bool = False) -> Self:
        """
        Sorts every element in each method list.

        Parameters
        ----------
        reverse : bool, optional
            Descending order, by default ``False``

        Returns
        -------
        Self
            Self with sorted values.


        Example:
        --------
        >>> ClassMembers(["b", "a"], ["d", "c"], ["f", "e"]).sort().__format__("short")
        ClassMembers(methods=['a', 'b'], classmethods=['c', 'd'], staticmethods=['e', 'f'])

        >>> ClassMembers(["b", "a"], ["d", "c"], ["f", "e"]).pack().sort().__format__("short")
        ClassMembers(methods=['a', 'b', 'c <cls>', 'd <cls>', 'e <stc>', 'f <stc>'])
        """

        sorted_vals: list[list[str]] = [
            sorted(getattr(self, field), reverse=reverse)
            for field in self._get_fields()
        ]

        return self.__class__(*sorted_vals)


# @versionadded("5.5.0")
class ClassMembersResult(dict[str, ClassMembers]):
    """
    All members of a class and its parent classes.
    """

    _LINELENGTH: ClassVar[int] = 88

    def __format__(self, format_spec: str) -> str:
        """
        Available format:
        - ``s``/``short`` (This hides attributes with empty value)

        Parameters
        ----------
        format_spec : str
            Format spec

        Returns
        -------
        str
            Alternative text representation of this class.
        """

        fmt = format_spec.lower().strip()

        if fmt == "short" or fmt == "s":
            # out = {}
            # for name, member in self.items():
            #     out[name] = format(member, fmt)
            # return repr(out)
            out = []
            sep = ", "
            for idx, (name, member) in enumerate(self.items()):
                mem = format(member, fmt)
                base = f"{repr(name)}: {mem}"

                # if idx == 0:
                #     out.append("{" + base)
                # elif idx + 1 == len(self.items()):
                #     out.append(base + "}")
                # else:
                #     out.append(base)
                out.append(
                    ("{" if idx == 0 else "")
                    + base
                    + ("}" if idx + 1 == len(self.items()) else "")
                )

            return sep.join(out)

        return self.__repr__()

    def _merge_value(
        self,
        value_name: Literal[
            "methods",
            "classmethods",
            "staticmethods",
            "properties",
            "attributes",
            "classattributes",
        ],
    ) -> list[str]:
        """
        Merge all specified values from the dictionary.

        Parameters
        ----------
        value_name : Literal["methods", "classmethods", "staticmethods", "properties", "attributes", "classattributes"]
            The type of value to merge.

        Returns
        -------
        list[str]
            A list of merged values.
        """

        merged = []
        for _, member in self.items():
            if value_name in member._get_fields():
                merged.extend(getattr(member, value_name))
        return merged

    def flatten_value(self, sort: bool = True) -> ClassMembers:
        """
        Merge all attributes of ``dict``'s values into one ``ClassMembers``.

        Parameters
        ----------
        sort : bool
            Sort value in ascending order after flatten, by default ``True``

        Returns
        -------
        ClassMembers
            Flattened value.


        Example:
        --------
        >>> test = ClassMembersResult(
        ...     ABC=ClassMembers(["a"], ["b"], ["c"], ["d"], ["y"], ["x"]),
        ...     DEF=ClassMembers(["e"], ["f"], ["g"], ["h"], ["w"], ["z"]),
        ... )
        >>> test.flatten_value()
        ClassMembers(
            methods=["a", "e"],
            classmethods=["b", "f"],
            staticmethods=["c", "g"],
            properties=["d", "h"],
            attributes=["w", "y"],
            classattributes=["x", "z"],
        )
        """

        res: list[list[str]] = []
        # for x in [
        #     "methods",
        #     "classmethods",
        #     "staticmethods",
        #     "properties",
        #     "attributes",
        #     "classattributes",
        # ]:
        for x in ClassMembers._get_fields():
            res.append(self._merge_value(x))  # type: ignore
        return ClassMembers(*res).sort() if sort else ClassMembers(*res)

    def pack_value(
        self,
        include_method: bool = True,
        include_classmethod: bool = True,
        classmethod_indicator: str = "<classmethod>",
        include_staticmethod: bool = True,
        staticmethod_indicator: str = "<staticmethod>",
        include_attribute: bool = True,
        include_classattribute: bool = True,
        classattribute_indicator: str = "<cls>",
    ) -> Self:
        """
        Join members into one list for each value.

        Parameters
        ----------
        include_method : bool, optional
            Whether to include method in the output, by default ``True``

        include_classmethod : bool, optional
            Whether to include classmethod in the output, by default ``True``

        classmethod_indicator : str, optional
            A string used to mark classmethod in the output. This string is appended
            to the name of each classmethod to visually differentiate it from regular
            instance methods, by default ``"<classmethod>"``

        include_staticmethod : bool, optional
            Whether to include staticmethod in the output, by default ``True``

        staticmethod_indicator : str, optional
            A string used to mark staticmethod in the output. This string is appended
            to the name of each staticmethod to visually differentiate it from regular
            instance methods, by default ``"<staticmethod>"``

        include_attribute : bool, optional
            Whether to include attributes in the output, by default ``True``

        include_classattribute : bool, optional
            Whether to include class attributes in the output, by default ``True``

        classattribute_indicator : str, optional
            A string used to mark class attribute in the output. This string is appended
            to the name of each class attribute to visually differentiate it from regular
            instance attributes, by default ``"<cls>"``

        Returns
        -------
        Self
            ClassMembersResult with packed value.


        Example:
        --------
        >>> test = ClassMembersResult(
        ...     ABC=ClassMembers(["a"], ["b"], ["c"], ["d"], ["y"], ["x"]),
        ...     DEF=ClassMembers(["e"], ["f"], ["g"], ["h"], ["w"], ["z"]),
        ... )
        >>> test.pack_value()
        {
            "ABC": ClassMembers(
                methods=["a", "b <classmethod>", "c <staticmethod>"],
                classmethods=[],
                staticmethods=[],
                properties=["d"],
                attributes=["y", "x <cls>"],
                classattributes=[],
            ),
            "DEF": ClassMembers(
                methods=["e", "f <classmethod>", "g <staticmethod>"],
                classmethods=[],
                staticmethods=[],
                properties=["h"],
                attributes=["w", "z <cls>"],
                classattributes=[],
            ),
        }
        """

        for class_name, members in self.items():
            self[class_name] = members.pack(
                include_method=include_method,
                include_classmethod=include_classmethod,
                classmethod_indicator=classmethod_indicator,
                include_staticmethod=include_staticmethod,
                staticmethod_indicator=staticmethod_indicator,
                include_attribute=include_attribute,
                include_classattribute=include_classattribute,
                classattribute_indicator=classattribute_indicator,
            )
        return self

    def prioritize_value(
        self,
        value_name: Literal[
            "methods",
            "classmethods",
            "staticmethods",
            "properties",
            "attributes",
            "classattributes",
        ] = "methods",
    ) -> dict[str, list[str]]:
        """
        Prioritize which field of value to show.

        Parameters
        ----------
        value_name : Literal["methods", "classmethods", "staticmethods", "properties", "attributes", "classattributes"], optional
            The type of value to prioritize, by default ``"methods"``

        Returns
        -------
        dict[str, list[str]]
            A dictionary with prioritized values.


        Example:
        --------
        >>> test = ClassMembersResult(
        ...     ABC=ClassMembers(["a"], ["b"], ["c"], ["d"]),
        ...     DEF=ClassMembers(["e"], ["f"], ["g"], ["h"]),
        ... )
        >>> test.prioritize_value("methods")
        {'ABC': ['a'], 'DEF': ['e']}
        >>> test.prioritize_value("classmethods")
        {'ABC': ['b'], 'DEF': ['f']}
        >>> test.prioritize_value("staticmethods")
        {'ABC': ['c'], 'DEF': ['g']}
        >>> test.prioritize_value("properties")
        {'ABC': ['d'], 'DEF': ['h']}
        """

        result: dict[str, list[str]] = {}
        for name, member in self.items():
            result[name] = getattr(member, value_name, member.methods)
        return result

    def print_output(
        self,
        where_to_print: Literal["methods", "properties", "attributes"] = "methods",
        print_in_one_column: bool = False,
    ) -> None:
        """
        Beautifully print the result.

        *This method is deprecated.*

        Parameters
        ----------
        where_to_print : Literal["methods", "properties", "attributes"], optional
            Whether to print ``methods`` or ``properties``, by default ``"methods"``

        print_in_one_column : bool, optional
            Whether to print in one column, by default ``False``
        """

        print_func = print  # Can be extended with function parameter

        # Loop through each class base
        for order, (class_base, member) in enumerate(self.items(), start=1):
            methods: list[str] = getattr(member, where_to_print, member.methods)
            mlen = len(methods)  # How many methods in that class
            if mlen == 0:
                continue
            print_func(f"{order:02}. <{class_base}> | len: {mlen:02}")

            # Modify methods list
            max_method_name_len = max([len(x) for x in methods])
            if mlen % 2 == 0:
                p1, p2 = methods[: int(mlen / 2)], methods[int(mlen / 2) :]
            else:
                p1, p2 = methods[: int(mlen / 2) + 1], methods[int(mlen / 2) + 1 :]
                p2.append("")
            new_methods = list(zip(p1, p2))

            # print
            if print_in_one_column:
                # This print 1 method in one line
                for name in methods:
                    print(f"    - {name.ljust(max_method_name_len)}")
            else:
                # This print 2 methods in 1 line
                for x1, x2 in new_methods:
                    if x2 == "":
                        print_func(f"    - {x1.ljust(max_method_name_len)}")
                    else:
                        print_func(
                            f"    - {x1.ljust(max_method_name_len)}    - {x2.ljust(max_method_name_len)}"
                        )

            print_func("".ljust(self._LINELENGTH, "-"))


# Mixins
# ---------------------------------------------------------------------------
class GetClassMembersMixin:
    """
    Show all methods of the class and its parent class minus ``object`` class

    *This class is meant to be used with other class*


    Example:
    --------
    >>> class TestClass(GetClassMembersMixin):
    ...     def method1(self): ...
    >>> TestClass._get_members(dunder=False)
    {
        'GetClassMembersMixin': ClassMembers(
            methods=[],
            classmethods=['_get_members', ..., 'show_all_methods', 'show_all_properties'],
            staticmethods=[],
            properties=[],
            attributes=[],
            classattributes=[]
        ),
        'TestClass': ClassMembers(
            methods=['method1'],
            classmethods=[],
            staticmethods=[],
            properties=[],
            attributes=[],
            classattributes=[]
        )
    }
    """

    # @versionadded("5.5.0")
    @classmethod
    def _get_members(
        cls,
        dunder: bool = True,
        underscore: bool = True,
        private: bool = True,
    ) -> ClassMembersResult:
        """
        Class method to get all methods, properties, and attributes
        of the class and its parent classes.

        Parameters
        ----------
        dunder : bool, optional
            Whether to include attribute with ``__`` (dunder)
            in the output, by default ``True``

        underscore : bool, optional
            Whether to include attribute starts with ``_``
            in the output (will also skip dunder), by default ``True``

        private : bool, optional
            Whether to include private attribute
            (``_<__class__.__name__>__<attribute>``)
            in the output, by default ``True``

        Returns
        -------
        ClassMembersResult
            A dictionary where keys are class names
            and values are tuples of method names and properties.
        """

        # MRO in reverse order
        classes = cls.__mro__[::-1]
        result: dict[str, ClassMembers] = {}

        # For each class base in classes
        for base in classes:
            methods: list[str] = []
            classmethods: list[str] = []
            staticmethods: list[str] = []
            properties: list[str] = []
            classattributes: list[str] = []

            # Dict items of base
            for name, attr in base.__dict__.items():
                # Skip dunder
                if name.startswith("__") and not dunder:
                    continue

                # Skip private attribute
                if base.__name__ in name and not private:
                    continue

                # Skip underscore
                if (
                    name.startswith("_")
                    and not underscore
                    and base.__name__ not in name
                ):
                    continue

                # Methods
                if callable(attr):
                    if isinstance(attr, staticmethod):
                        staticmethods.append(name)
                    else:
                        methods.append(name)
                elif isinstance(attr, classmethod):
                    classmethods.append(name)

                # Property
                elif isinstance(attr, property):
                    properties.append(name)

                # Class attribute
                else:
                    classattributes.append(name)

                # Save to result
                result[base.__name__] = ClassMembers(
                    methods=methods,
                    classmethods=classmethods,
                    staticmethods=staticmethods,
                    properties=properties,
                    classattributes=classattributes,
                ).sort()

        return ClassMembersResult(result)

    # @versionadded("5.5.0")
    def _get_attributes(
        self,
        underscore: bool = True,
        private: bool = True,
    ) -> list[str]:
        """
        Get all attributes of the class instance.

        Parameters
        ----------
        underscore : bool, optional
            Whether to include attribute starts with ``_``
            in the output, by default ``True``

        private : bool, optional
            Whether to include private attribute
            (``_<__class__.__name__>__<attribute>``)
            in the output, by default ``True``

        Returns
        -------
        list[str]
            A list contains attributes.
        """

        # Default output
        out: list[str] = []

        # Get attributes
        cls_dict: dict[str, Any] | None = getattr(self, "__dict__", None)
        cls_slots: tuple[str, ...] | None = getattr(self, "__slots__", None)
        cls_name: str = self.__class__.__name__

        def _is_valid(item_name: str) -> bool:
            if not item_name.startswith("_"):
                return True
            if cls_name in item_name and private:
                return True
            if underscore and cls_name not in item_name:
                return True
            return False

        # Check if __dict__ exist and len(__dict__) > 0
        if cls_dict is not None and len(cls_dict) > 0:
            # out = [x for x in self.__dict__ if _is_valid(x)]
            out.extend(list(cls_dict))

        # Check if __slots__ exist and len(__slots__) > 0
        if cls_slots is not None and len(cls_slots) > 0:
            # Convert __<attribute> to _<self.__class__.__name__>__<attribute>
            _slot = [f"_{cls_name}{x}" if x.startswith("__") else x for x in cls_slots]
            out.extend(_slot)

        return [x for x in out if _is_valid(x)]

    # @versionadded("5.5.0")
    def get_members(
        self,
        dunder: bool = False,
        underscore: bool = True,
        private: bool = True,
    ) -> ClassMembersResult:
        """
        Get all members of a class instance.

        Parameters
        ----------
        dunder : bool, optional
            Whether to include attribute with ``__`` (dunder)
            in the output, by default ``False``

        underscore : bool, optional
            Whether to include attribute starts with ``_``
            in the output (will also skip dunder), by default ``True``

        private : bool, optional
            Whether to include private attribute
            (``_<__class__.__name__>__<attribute>``)
            in the output, by default ``True``

        Returns
        -------
        ClassMembersResult
            All member of a class instance.
        """
        mems = self._get_members(dunder=dunder, underscore=underscore, private=private)
        attrs = self._get_attributes(underscore=underscore, private=private)
        mems[self.__class__.__name__].attributes = attrs
        return mems

    @classmethod
    def show_all_methods(
        cls,
        print_result: bool = False,
        include_classmethod: bool = True,
        classmethod_indicator: str = "<classmethod>",
        include_staticmethod: bool = True,
        staticmethod_indicator: str = "<staticmethod>",
        include_private_method: bool = False,
    ) -> dict[str, list[str]]:
        """
        Class method to display all methods of the class and its parent classes,
        including the class in which they are defined in alphabetical order.

        Parameters
        ----------
        print_result : bool, optional
            Beautifully print the output, by default ``False``

        include_classmethod : bool, optional
            Whether to include classmethod in the output, by default ``True``

        classmethod_indicator : str, optional
            A string used to mark classmethod in the output. This string is appended
            to the name of each classmethod to visually differentiate it from regular
            instance methods, by default ``"<classmethod>"``

        include_staticmethod : bool, optional
            Whether to include staticmethod in the output, by default ``True``

        staticmethod_indicator : str, optional
            A string used to mark staticmethod in the output. This string is appended
            to the name of each staticmethod to visually differentiate it from regular
            instance methods, by default ``"<staticmethod>"``

        include_private_method : bool, optional
            Whether to include private method in the output, by default ``False``

        Returns
        -------
        dict[str, list[str]]
            A dictionary where keys are class names and values are lists of method names.
        """

        result = cls._get_members(
            dunder=False, private=include_private_method
        ).pack_value(
            include_classmethod=include_classmethod,
            classmethod_indicator=classmethod_indicator,
            include_staticmethod=include_staticmethod,
            staticmethod_indicator=staticmethod_indicator,
        )

        if print_result:
            result.print_output("methods")

        return result.prioritize_value("methods")

    @classmethod
    def show_all_properties(cls, print_result: bool = False) -> dict[str, list[str]]:
        """
        Class method to display all properties of the class and its parent classes,
        including the class in which they are defined in alphabetical order.

        Parameters
        ----------
        print_result : bool, optional
            Beautifully print the output, by default ``False``

        Returns
        -------
        dict[str, list[str]]
            A dictionary where keys are class names and values are lists of property names.
        """

        # result = cls.get_methods_and_properties().prioritize_value("properties")
        result = ClassMembersResult(
            {
                cls.__name__: ClassMembers(
                    properties=cls._get_members(dunder=False)
                    .flatten_value()
                    .properties,
                )
            }
        )

        if print_result:
            result.print_output("properties")

        return result.prioritize_value("properties")


class AutoREPRMixin:
    """
    Generate ``repr()`` output as ``<class(param1=any, param2=any, ...)>``

    *This class is meant to be used with other class*


    Example:
    --------
    >>> class Test(AutoREPRMixin):
    ...     def __init__(self, param):
    ...         self.param = param
    >>> print(repr(Test(1)))
    Test(param=1)
    """

    def __repr__(self) -> str:
        """
        Generate a string representation of the instance's attributes.

        This function retrieves attributes from either the ``__dict__`` or
        ``__slots__`` of the instance, excluding private attributes (those
        starting with an underscore). The attributes are returned as a
        formatted string, with each attribute represented as ``"key=value"``.

        Convert ``self.__dict__`` from ``{"a": "b"}`` to ``a=repr(b)``
        or ``self.__slots__`` from ``("a",)`` to ``a=repr(self.a)``
        (excluding private attributes)
        """
        # Default output
        out = []
        sep = ", "  # Separator

        # Get attributes
        cls_dict = getattr(self, "__dict__", None)
        cls_slots = getattr(self, "__slots__", None)

        # Check if __dict__ exist and len(__dict__) > 0
        if cls_dict is not None and len(cls_dict) > 0:
            out = [
                f"{k}={repr(v)}"
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            ]

        # Check if __slots__ exist and len(__slots__) > 0
        elif cls_slots is not None and len(cls_slots) > 0:
            out = [
                f"{x}={repr(getattr(self, x))}"
                for x in self.__slots__  # type: ignore
                if not x.startswith("_")
            ]

        # Return out
        return f"{self.__class__.__name__}({sep.join(out)})"


class AddFormatMixin:
    """
    This mixin that allows classes to define and register custom format
    specifications for use with Python's built-in :func:`format` function
    and f-string formatting.

    This mixin extends the standard ``__format__`` mechanism by letting you
    attach named formatting presets at runtime. Each format spec is simply a
    callable that receives the object instance and returns a formatted string.

    Attribute ``_format_specs`` is used and must not be overwritten in any
    circumstances.
    """

    def __init__(self) -> None:
        self._format_specs: dict[str, Callable[[Self], str]] = {}

    def __format__(self, format_spec: str) -> str:
        """
        Format the object using a registered format specification.

        Parameters
        ----------
        format_spec : str
            The name of a previously registered format spec. If empty or not
            found, the object's ``__str__`` representation is returned.

        Returns
        -------
        str
            The formatted string according to the given format spec.


        Usage
        -----
        >>> print(f"{<object>:<format_spec>}")
        >>> print(<object>.__format__(<format_spec>))
        >>> print(format(<object>, <format_spec>))
        """

        func = self._format_specs.get(format_spec, None)

        if func is None:
            return self.__str__()
        else:
            return func(self)

    def add_format_spec(self, name: str, format_func: Callable[[Self], str]) -> None:
        """
        Register a custom format specification.

        Parameters
        ----------
        name : str
            The format specifier string to register.

        format_func : Callable[[Self], str]
            A function that receives the object instance and returns a formatted string.
        """
        if getattr(self, "_format_specs", None) is None:
            self._format_specs: dict[str, Callable[[Self], str]] = {}
        self._format_specs[name] = format_func

    @property
    def available_format_spec(self) -> list[str]:
        """
        List all registered format specification names.

        Returns
        -------
        list[str]
            A list containing the names of all format specs that have been
            registered via :meth:`add_format_spec`. If no format specs exist,
            an empty list is returned.


        Notes
        -----
        - This is a convenience property to inspect which formatting presets
        are currently available for the object.
        - The list contains only the names (keys), not the formatting functions.
        """
        if getattr(self, "_format_specs", None) is None:
            return []
        return list(self._format_specs)


# Class
# ---------------------------------------------------------------------------
class BaseClass(GetClassMembersMixin, AutoREPRMixin):
    """Base class"""

    def __str__(self) -> str:
        return repr(self)


# Metaclass
# ---------------------------------------------------------------------------
class PositiveInitArgsMeta(type):
    """
    Make sure that every args in a class __init__ is positive

    Usage
    -----
    >>> class Test(metaclass=PositiveInitArgsMeta): pass
    """

    def __call__(cls, *args, **kwargs):
        # Check if all positional and keyword arguments are positive
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError(f"Argument {arg} must be positive")
        for key, value in kwargs.items():
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"Argument {key}={value} must be positive")

        # Call the original __init__ method
        return super().__call__(*args, **kwargs)
