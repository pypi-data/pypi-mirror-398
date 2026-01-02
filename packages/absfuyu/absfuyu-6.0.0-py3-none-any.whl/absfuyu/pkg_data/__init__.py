"""
Absfuyu: Package data
---------------------
Load package data

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "Pickler",
    "BasicLZMAOperation",
    "DataLoader",
    # "DataList",  # Disable due to Sphinx show real path, still importable
]


# Library
# ---------------------------------------------------------------------------
import lzma
import pickle
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any

from absfuyu.core import BaseClass, versionadded


# Class
# ---------------------------------------------------------------------------
class DataList(Enum):
    CHEMISTRY = files("absfuyu.pkg_data").joinpath("chemistry.pkl")
    TAROT = files("absfuyu.pkg_data").joinpath("tarot.pkl")
    PASSWORDLIB = files("absfuyu.pkg_data").joinpath("passwordlib_lzma.pkl")


class Pickler(BaseClass):
    """
    A utility class for saving and loading data using the pickle format.

    This class provides static methods for serializing Python objects to a file
    using the ``pickle`` module and deserializing them back from a file.
    It simplifies the process of saving and loading data to and from pickle files.
    """

    @staticmethod
    def save(location: Path, data: Any) -> None:
        """
        Serializes and saves the given data to a file using the pickle format.

        Parameters
        ----------
        location : Path
            The path to the file where the data will be saved.

        data : Any
            The Python object to be serialized and saved.
        """
        with open(Path(location), "wb") as file:
            pickle.dump(data, file)

    @staticmethod
    def load(location: Path):
        """
        Loads and deserializes data from a file that is in pickle format.

        Parameters
        ----------
        location : Path
            The path to the pickle file to load.

        Returns
        -------
        Any
            The deserialized Python object loaded from the file.
        """
        with open(Path(location), "rb") as file:
            data = pickle.load(file)
        return data


@versionadded("5.0.0")
class BasicLZMAOperation(BaseClass):
    """
    A class for basic LZMA compression and decompression operations,
    integrated with pickle for saving and loading compressed data.

    This class provides static methods to compress data using LZMA,
    save the compressed data to a pickle file, load compressed data
    from a pickle file, and decompress LZMA-compressed data.
    """

    @staticmethod
    def save_to_pickle(location: Path, data: bytes) -> None:
        """
        Compresses the given byte data using LZMA and saves the compressed
        data to a file using pickle serialization.

        Parameters
        ----------
        location : Path
            The path to the file where the compressed data will be saved.

        data : bytes
            The byte data to be compressed and saved.


        Example:
        --------
        >>> data = b"This is some example data to compress."
        >>> BasicLZMAOperation.save_to_pickle(Path("compressed_data.pkl"), data)
        """
        compressed_data = lzma.compress(data)
        Pickler.save(location=location, data=compressed_data)

    @staticmethod
    def load(data: Any) -> bytes:
        """
        Decompresses LZMA-compressed data.

        Parameters
        ----------
        data : Any
            The LZMA-compressed data to be decompressed.

        Returns
        -------
        bytes
            The decompressed data.
        """
        return lzma.decompress(data)

    @staticmethod
    def load_from_pickle(location: Path) -> bytes:
        """
        Loads LZMA-compressed data from a pickle file, decompresses it.

        Parameters
        ----------
        location : Path
            The path to the pickle file containing the LZMA-compressed data.

        Returns
        -------
        bytes
            The decompressed data.
        """
        compressed_data = Pickler.load(location=location)
        return lzma.decompress(compressed_data)


@versionadded("5.0.0")
class DataLoader(BaseClass):
    """A class to load package data"""

    def __init__(self, data: DataList) -> None:
        """
        Initializes the DataLoader with a DataList object.

        Parameters
        ----------
        data : DataList
            A ``DataList`` object containing information about the data file to be loaded.
            It is expected to have a ``'value'`` attribute representing the file path.
        """
        self.data = data

    def load(self):
        """
        Loads data from the specified file, handling different file formats automatically.

        Returns
        -------
        Any
            The loaded data from the file.
        """
        try:
            data_name: str = self.data.value.stem  # type: ignore
        except Exception:
            data_name: str = self.data.value.name.split(".")[0]  # type: ignore

        if data_name.endswith("lzma"):
            return BasicLZMAOperation.load_from_pickle(self.data.value)  # type: ignore
        return Pickler.load(self.data.value)  # type: ignore
