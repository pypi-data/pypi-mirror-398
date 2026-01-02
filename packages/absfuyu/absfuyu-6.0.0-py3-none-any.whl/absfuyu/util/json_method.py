"""
Absfuyu: Json Method
--------------------
``.json`` file handling

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["JsonFile"]


# Library
# ---------------------------------------------------------------------------
import json
from pathlib import Path

from absfuyu.core import BaseClass


# Class
# ---------------------------------------------------------------------------
class JsonFile(BaseClass):
    """
    ``.json`` file handling

    Parameters
    ----------
    json_file_location : str | Path
        .json file location

    encoding : str | None, optional
        Data encoding, by default ``"utf-8"``

    indent : int | str | None, optional
        Indentation when export to json file, by default ``4``

    sort_keys : bool, optional
        Sort the keys before export to json file, by default ``True``
    """

    def __init__(
        self,
        json_file_location: str | Path,
        *,
        encoding: str | None = "utf-8",
        indent: int | str | None = 4,
        sort_keys: bool = True,
    ) -> None:
        """
        ``.json`` file handling

        Parameters
        ----------
        json_file_location : str | Path
            .json file location

        encoding : str | None, optional
            Data encoding, by default ``"utf-8"``

        indent : int | str | None, optional
            Indentation when export to json file, by default ``4``

        sort_keys : bool, optional
            Sort the keys before export to json file, by default ``True``
        """

        self.json_file_location = Path(json_file_location)
        self.encoding = encoding
        self.indent = indent
        self.sort_keys = sort_keys
        self.data: dict = {}

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.json_file_location.name})"

    def load_json(self) -> dict:
        """
        Load ``.json`` file

        Returns
        -------
        dict
            ``.json`` data
        """
        with open(self.json_file_location, "r", encoding=self.encoding) as file:
            self.data = json.load(file)
        return self.data

    def save_json(self) -> None:
        """Save ``.json`` file"""
        json_data = json.dumps(self.data, indent=self.indent, sort_keys=self.sort_keys)
        with open(self.json_file_location, "w", encoding=self.encoding) as file:
            file.writelines(json_data)

    def update_data(self, data: dict) -> None:
        """
        Update ``.json`` data without save

        Parameters
        ----------
        data : dict
            ``.json`` data
        """
        self.data = data
