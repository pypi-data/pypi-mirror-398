"""
Absfuyu: Content
----------------
Handle .txt file

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Usage:
------
>>> from absfuyu.general.content import ContentLoader
"""

# TODO: rewrite this

# Module level
# ---------------------------------------------------------------------------
__all__ = ["ContentLoader", "Content", "LoadedContent"]


# Library
# ---------------------------------------------------------------------------
import json
import random
import re
from collections import Counter
from itertools import chain
from pathlib import Path
from typing import Self

from absfuyu.core import BaseClass, GetClassMembersMixin, unidecode
from absfuyu.logger import logger


# Class
# ---------------------------------------------------------------------------
class Content(BaseClass):
    """
    Contain data

    Data format: list[str, list[str]]
        where: ``str: data``; ``list[str]: data tags``
    """

    def __init__(self, data: list) -> None:
        self.data: str = str(data[0])
        self.tag: list = data[1]
        # logger.debug(self.__dict__)

    def __str__(self) -> str:
        # return f"{self.data} | {self.tag}"
        return str(self.data)

    def unidecoded(self) -> Self:
        """
        Convert data through ``unidecode`` package

        Returns
        -------
        Content
            ``unidecoded`` Content
        """
        return self.__class__([unidecode(self.data), list(map(unidecode, self.tag))])

    def to_text(self) -> str:
        """
        Convert back into text

        Returns
        -------
        str
            Text
        """
        # hard code
        tags = ",".join(self.tag)
        return f"{self.data}|{tags}"

    def short_form(self, separator: str = ",") -> str:
        """
        Short form show only first item when separated by ``separator``

        Parameters
        ----------
        separator : str
            Default: ``","``

        Returns
        -------
        str
            Short form
        """
        if not separator.startswith(","):
            logger.debug(f"Separated symbol: {separator}")
        return self.data.split(separator)[0]

    def handle_address(
        self, address_separator: str = ",", *, first_item_not_address: bool = True
    ) -> Self:
        """
        Handle ``self.data`` as address and then update the address into ``self.tag``

        Parameters
        ----------
        address_separator : str
            | Split the address by which character
            | (Default: ``","``)

        first_item_not_address : bool
            Set to ``False`` when ``<splited data>[0]`` is not part of an address

        Returns
        -------
        Content
            Handled Content


        Example:
        --------
        >>> test = "Shop A, 22 ABC Street, DEF District, GHI City"
        >>> # After handle_address()
        ["Shop A", "22 ABC Street", "DEF District", "GHI City"]

        >>> # After handle_address(first_item_not_address = False)
        ["22 ABC Street", "DEF District", "GHI City"]
        """
        if first_item_not_address:
            temp = self.data.split(address_separator)
        else:
            logger.debug(
                f"First item ({self.data.split(address_separator)[0]}) is not part of an address"
            )
            temp = self.data.split(address_separator)[1:]

        new_tag = [x.strip().lower() for x in temp]
        logger.debug(f"Current tags: {self.tag}")
        logger.debug(f"New tags: {new_tag}")
        self.tag = list(set(self.tag + new_tag))
        logger.debug(f"Final tags: {self.tag} Len: {len(self.tag)}")

        return self.__class__([self.data, self.tag])


class LoadedContent(list[Content], GetClassMembersMixin):
    """
    Contain list of ``Content``
    """

    def __str__(self) -> str:
        # return f"{self.__class__.__name__} - Total: {len(self)}"
        return f"{self.__class__.__name__}({[x.data for x in self]})"

    def __repr__(self) -> str:
        return self.__str__()

    def apply(self, func) -> Self:
        """
        Apply function to each entry

        :param func: Callable function
        :type func: Callable
        :rtype: LoadedContent
        """
        return self.__class__(func(x.data) for x in self)

    @classmethod
    def load_from_json(cls, file: Path) -> Self:
        """
        Use this method to load data from ``.json`` file from ``to_json()`` method

        Parameters
        ----------
        file : Path
            Path to ``.json`` file

        Returns
        -------
        LoadedContent
            Loaded content from ``.json`` file
        """
        with open(file) as json_file:
            parsed_json: dict = json.load(json_file)
        out = [Content(list(x.values())) for x in parsed_json]
        return cls(out)

    @property
    def tags(self) -> list:
        """A list contains all available tag"""
        temp = chain.from_iterable([x.tag for x in self])
        out = list(set(temp))
        logger.debug(f"Found {len(out)} {'tags' if len(out) > 1 else 'tag'}")
        return sorted(out)

    def tag_count(self) -> Counter:
        """
        Count number of tags

        :rtype: Counter
        """
        temp = chain.from_iterable([x.tag for x in self])
        logger.debug(temp)
        return Counter(temp)

    def filter(self, tag: str) -> Self:
        """
        Filter out entry with ``tag``

        :param tag: Tag to filter
        :type tag: str
        :rtype: LoadedContent
        """
        tag = tag.strip().lower()
        logger.debug(f"Tag: {tag}")
        if tag not in self.tags:
            # tag = random.choice(self.tags)
            # logger.debug(f"Tag not exist, changing to a random tag... {tag}")
            logger.warning(f'"{tag}" tag does not exist')
            _avail_tag = ", ".join(list(dict(self.tag_count().most_common(5)).keys()))
            raise ValueError(
                f"Available tags: {_avail_tag},..."
                f"\nMore tag at: `{self.__class__.__name__}.tags`"
            )
        return self.__class__([x for x in self if tag in x.tag])

    def find(self, keyword: str) -> Self:
        """
        Return all entries that include ``keyword``

        :param keyword: Keyword to find
        :type keyword: str
        :rtype: LoadedContent
        """
        temp = self.__class__(
            [x for x in self if x.data.lower().find(keyword.lower()) >= 0]
        )
        if temp:
            logger.debug(f"Found {len(temp)} {'entries' if len(temp) > 1 else 'entry'}")
        else:
            logger.debug("No result")
        return temp

    def short_form(self, separator: str = ",") -> list[str]:
        """
        Shows only first item when separated by ``separator`` of ``Content.data``

        Parameters
        ----------
        separator : str
            Default: ``","``

        Returns
        -------
        list[str]
            Short form
        """
        return [x.short_form(separator) for x in self]

    def pick_one(self, tag: str | None = None) -> Content:
        """
        Pick a random entry

        Parameters
        ----------
        tag : str | None
            Pick a random entry with ``tag``
            (Default: None)

        Returns
        -------
        Content
            Random entry
        """
        if tag:
            temp = self.filter(tag)
            logger.debug(f"Tag: {tag}")
            return random.choice(temp)
        return random.choice(self)

    def handle_address(
        self, address_separator: str = ",", *, first_item_not_address: bool = True
    ) -> Self:
        """
        Execute ``Content.handle_address()`` on every ``self.data`` of ``Content``

        Parameters
        ----------
        address_separator : str
            | Split the address by which character
            | (Default: ``","``)

        first_item_not_address : bool
            Set to ``False`` when ``<splited data>[0]`` is not part of an address

        Returns
        -------
        LoadedContent
            Handled Content


        Example:
        --------
        >>> test = "Shop A, 22 ABC Street, DEF District, GHI City"
        >>> # After handle_address()
        ["Shop A", "22 ABC Street", "DEF District", "GHI City"]

        >>> # After handle_address(first_item_not_address = False)
        ["22 ABC Street", "DEF District", "GHI City"]
        """
        return self.__class__(
            [
                x.handle_address(
                    address_separator=address_separator,
                    first_item_not_address=first_item_not_address,
                )
                for x in self
            ]
        )

    def to_json(self, no_accent: bool = False) -> str:
        """
        Convert data into ``.json`` file

        Parameters
        ----------
        no_accent : bool
            | when ``True``: convert the data through ``unidecode`` package
            | (Default: ``False``)

        Returns
        -------
        str
            Data
        """
        if no_accent:
            out = [x.unidecoded().__dict__ for x in self]
        else:
            out = [x.__dict__ for x in self]
        logger.debug(out)
        return json.dumps(out, indent=2)

    def to_text(self, no_accent: bool = False) -> str:
        """
        Convert data into ``.txt`` file

        Parameters
        ----------
        no_accent : bool
            | when ``True``: convert the data through ``unidecode`` package
            | (Default: ``False``)

        Returns
        -------
        str
            Data
        """
        if no_accent:
            out = [x.unidecoded().to_text() for x in self]
        else:
            out = [x.to_text() for x in self]
        logger.debug(out)
        return "\n".join(out)


class ContentLoader(BaseClass):
    """
    This load data from ``.txt`` file

    Content format:
    ``<content><split_symbol><tags separated by <tag_separate_symbol>>``
    """

    def __init__(
        self,
        file_path: Path | str,
        characteristic_detect: bool = True,
        tag_dictionary: dict | None = None,
        *,
        comment_symbol: str = "#",
        split_symbol: str = "|",
        tag_separate_symbol: str = ",",
    ) -> None:
        """
        Parameters
        ----------
        file_path : str
            file location/file to load

        characteristic_detect : bool
            detect whether the content is long, short, or a question
            (default: ``True``)

        tag_dict : dict
            custom tag pattern
            format: ``{"keyword": "tag",...}``
            example: ``{"apple": "fruit", "orange": "fruit"}``

        comment_symbol : str
            symbol that `ContentLoader` will ignore
            (default: ``"#"``)

        split_symbol : str
            symbol that `ContentLoader` will split content and tags
            (default: ``"|"``)

        tag_separate_symbol : str
            symbol that `ContentLoader` will split between tags
            (default: ``","``)
        """
        # file
        self.file = Path(file_path)

        # characteristic detect
        self.characteristic_detect: bool = characteristic_detect

        # tag dictionary
        if tag_dictionary is None:
            # logger.debug("No tag patern available")
            self.tag_dictionary: dict = dict()
        else:
            logger.debug(
                f"Tag pattern available: "
                f"{len(tag_dictionary)} {'entries' if len(tag_dictionary) > 1 else 'entry'} "
                f"({len(set(tag_dictionary.values()))} unique "
                f"{'tags' if len(set(tag_dictionary.values())) > 1 else 'tag'})"
            )
            self.tag_dictionary = tag_dictionary

        # symbol stuff
        assert comment_symbol != split_symbol, (
            "comment_symbol and split_symbol should have different values"
        )
        assert tag_separate_symbol != split_symbol, (
            "tag_separate_symbol and split_symbol should have different values"
        )
        self.comment_symbol: str = comment_symbol
        self.split_symbol: str = split_symbol
        self.tag_separate_symbol: str = tag_separate_symbol

    def content_format(self) -> str:
        """
        Shows current content format

        Returns
        -------
        str
            Current content format


        Example:
        --------
        >>> ContentLoader(".").content_format()
        # This line will be ignored
        <content> | <tag1>, <tag2>
        """
        out = (
            f"{self.comment_symbol} This line will be ignored\n"
            f"<content> {self.split_symbol} "
            f"<tag1>{self.tag_separate_symbol} <tag2>, ..., <tag n>"
        )
        return out

    def load(self) -> list:
        """
        Load content from ``self.file``

        Returns
        -------
        list
            List of content
        """
        with open(self.file, "r", encoding="utf-8") as data:
            logger.debug("Loading data...")
            dat = []
            check = []

            for i, x in enumerate(data.readlines()):
                x = x.strip()
                if x.startswith(self.comment_symbol) or len(x) == 0:
                    continue  # skip comment and empty lines
                logger.debug(
                    f"### Loop {i + 1} #####################################################################"
                )

                temp = x.split(self.split_symbol)
                if len(temp) != 2:
                    logger.debug(f"Split len: {len(temp)}")
                    logger.warning(
                        f"The current entry is missing data or tag: {x[:20]}..."
                    )

                temp[0] = temp[0].strip()
                if temp[0].lower() not in check:
                    check.append(temp[0].lower())  # check for dupes

                    # tag
                    additional_tags = []
                    for k, v in self.tag_dictionary.items():
                        key = k.strip().lower()
                        val = temp[0].lower()
                        regex_pattern = f"[^a-zA-Z0-9]({key})[^a-zA-Z0-9]|^({key})[^a-zA-Z0-9]|[^a-zA-Z0-9]({key})$"
                        if re.search(regex_pattern, val) is not None or val.startswith(
                            key
                        ):
                            # regex has a bug (or idk if it's a bug or not) that
                            # doesn't recognise when there is only one word in the sentence
                            # therefore use `val.startswith(key)` to fix
                            additional_tags.append(v.strip().lower())

                    if self.characteristic_detect:
                        long_short = (120, 20)  # setting
                        if len(temp[0]) > long_short[0]:
                            additional_tags.append("long")
                        if len(temp[0]) < long_short[1]:
                            additional_tags.append("short")
                        if temp[0][-1].startswith("?"):
                            additional_tags.append("question")
                    if additional_tags:
                        logger.debug(f"Additional tags: {additional_tags}")

                    try:
                        tags = [
                            tag.strip() for tag in temp[1].strip().lower().split(",")
                        ]  # separate and strip tags
                        logger.debug(f"Tags: {tags}")
                    except Exception:
                        logger.warning("No tag found in the original string")
                        if additional_tags:
                            tags = additional_tags
                        else:
                            tags = ["unspecified"]
                            logger.debug('Assigned "unspecified" tag')

                    tags.extend(additional_tags)
                    final_tags = list(set(tags))
                    logger.debug(f"Final tags: {final_tags} Len: {len(final_tags)}")

                    dat.append([temp[0], final_tags])  # add everything
                else:
                    logger.debug(f"Found duplicates, {x} removed")

        return dat

    def load_content(self) -> LoadedContent:
        """
        Load data into a list of ``Content``

        Returns
        -------
        LoadedContent
            Loaded content
        """
        return LoadedContent(map(Content, self.load()))
