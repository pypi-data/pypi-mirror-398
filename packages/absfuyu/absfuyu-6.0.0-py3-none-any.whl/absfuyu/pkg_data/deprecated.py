"""
Absfuyu: Package data
---------------------
Deprecated (but might have some use)

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import zlib
from ast import literal_eval
from importlib.resources import files, read_binary
from pathlib import Path

from absfuyu.core import BaseClass
from absfuyu.logger import logger

# External Data
# ---------------------------------------------------------------------------
# These are sources of data
_EXTERNAL_DATA = {
    "chemistry.json": "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json",
    "tarot.json": "https://raw.githubusercontent.com/dariusk/corpora/master/data/divination/tarot_interpretations.json",
    "word_list.json": "https://raw.githubusercontent.com/dwyl/english-words/master/words_dictionary.json",
    # "countries.json": "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/refs/heads/master/json/countries.json",
}


# Deprecated
# ---------------------------------------------------------------------------
DATA_PATH = files("absfuyu.pkg_data")


class _DatMaker(BaseClass):
    """
    Package data ``.dat`` maker/loader

    *Deprecated since version 5.0.0*
    """

    def __init__(self, data_name: str) -> None:
        self.name = data_name

    def _make_dat(self, data: str, name: str | Path):
        """
        :param data: string data
        :param name: name and location of the data
        """
        compressed_data = zlib.compress(str(data).encode(), zlib.Z_BEST_COMPRESSION)
        with open(name, "wb") as file:
            file.write(compressed_data)

    def load_dat_data(self, evaluate: bool = False):
        """
        Load ``.dat`` data from package resource

        :param evaluate: use ``ast.literal_eval()`` to evaluate string data
        :type evaluate: bool
        :returns: Loaded data
        :rtype: Any
        """
        compressed_data = read_binary("absfuyu.pkg_data", self.name)
        data = zlib.decompress(compressed_data).decode()
        # return data
        return literal_eval(data) if evaluate else data

    def update_data(self, new_data: str):
        """
        Update existing data

        :param new_data: Data to be updated
        """
        self._make_dat(data=new_data, name=DATA_PATH.joinpath(self.name))  # type:ignore
        logger.debug("Data updated")


class _ManagePkgData(BaseClass):
    """
    Manage this package data

    *Deprecated since version 5.0.0*
    """

    def __init__(self, pkg_data_loc: str | Path) -> None:
        """
        pkg_data_loc: Package data location
        """
        self.data_loc = Path(pkg_data_loc)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.data_loc.name})"

    def get_data_list(self, *, pattern: str = "*") -> list[Path]:
        """Get a list of data available"""
        excludes = [
            x for x in self.data_loc.glob("*.[pP][yY]")
        ]  # exclude python scripts
        return [
            x for x in self.data_loc.glob(pattern) if x not in excludes and x.is_file()
        ]

    @property
    def data_list(self) -> list[str]:
        """List of available data"""
        return [x.name for x in self.get_data_list()]

    def download_all_data(self):
        """
        Download all external data
        """

        logger.debug("Downloading data...")
        try:
            from absfuyu.util.api import APIRequest

            for data_name, data_link in _EXTERNAL_DATA.items():
                logger.debug(f"Downloading {data_name}...")
                data = APIRequest(data_link, encoding="utf-8")
                data.fetch_data(
                    update=True,
                    json_cache=DATA_PATH.joinpath(data_name),  # type: ignore
                )
                logger.debug(f"Downloading {data_name}...DONE")
            logger.debug("Downloading data...DONE")
        except Exception:
            logger.debug("Downloading data...FAILED")

    def clear_data(self) -> None:
        """Clear data in data list"""
        for x in self.get_data_list():
            x.unlink()
