"""
Absfuyu: XML
------------
XML Tool [W.I.P]

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["XML2Dict"]


# Library
# ---------------------------------------------------------------------------
from pathlib import Path
from typing import Any, Self

from absfuyu.core.baseclass import GetClassMembersMixin

XML_MODE = False

try:
    import xmltodict
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[full]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[full] package")  # noqa: B904
else:
    XML_MODE = True


# Class
# ---------------------------------------------------------------------------
class XML2Dict(GetClassMembersMixin):
    """
    Automatically convert .xml file to dict


    Usage
    -----
    >>> XML2Dict(<path>)
    >>> XML2Dict.parsed_data
    """

    def __init__(self, text: str) -> None:
        """
        Automatically convert .xml file to dict

        Parameters
        ----------
        text : str
            ``.xml`` format text
        """
        self._text = text

        self.parsed_data: dict[str, Any] = self._parse_xml()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def _parse_xml(self) -> dict[str, Any]:
        """Convert xml to dict"""
        return xmltodict.parse(self._text, encoding="utf-8")  # type: ignore

    @classmethod
    def from_path(cls, xml_path: str | Path) -> Self:
        """
        Convert from .xml file path

        Parameters
        ----------
        xml_path : str | Path
            Path to .xml file

        Returns
        -------
        Self
            xml to dict
        """
        with Path(xml_path).open("r", encoding="utf-8") as f:
            dat = "\n".join(f.readlines())
        return cls(dat)
