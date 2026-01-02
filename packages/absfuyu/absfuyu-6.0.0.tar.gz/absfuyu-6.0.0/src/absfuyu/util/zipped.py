"""
Absfuyu: Zipped
---------------
Zipping stuff
(deprecated, use absfuyu.util.path.Directory)

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Zipper"]


# Library
# ---------------------------------------------------------------------------
import shutil
import zipfile
from pathlib import Path

from absfuyu.core import BaseClass, deprecated, versionadded
from absfuyu.logger import logger


# Class
# ---------------------------------------------------------------------------
@deprecated("5.1.0", reason="Use ``absfuyu.util.path.Directory`` instead")
class Zipper(BaseClass):
    """Zip file or folder"""

    def __init__(self, path_to_zip: str | Path, name: str | None = None) -> None:
        """
        path_to_zip: source location
        name: zipped file name
        """
        self.source_path = Path(path_to_zip)
        if name is None:
            self.name = self.source_path.name + ".zip"
        else:
            self.name = name
        self.destination = self.source_path.parent.joinpath(self.name)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def zip_stuff(self, delete_after_zip: bool = False) -> None:
        """
        Zip file/folder

        :param delete_after_zip: Delete source after zip (Default: ``False``)
        :type delete_after_zip: bool
        """

        # Zip
        logger.debug("Zipping...")
        if self.source_path.is_dir():  # zip entire folder
            try:
                with zipfile.ZipFile(self.destination, "w", zipfile.ZIP_DEFLATED) as f:
                    for file in self.source_path.rglob("*"):
                        f.write(file, file.relative_to(self.source_path))
            except Exception:
                logger.error("Zip failed!")
                # shutil.make_archive(zip_file, format="zip", root_dir=zip_path) # Method 2
        else:  # zip a file
            # Implement later
            pass

        # Delete folder
        if delete_after_zip:
            try:
                logger.debug("Deleting unused folder...")
                shutil.rmtree(self.source_path)
                logger.debug("Files deleted")
            except OSError as e:
                logger.error(f"Error: {e.filename} - {e.strerror}.")

    @versionadded("4.0.0")
    def unzip(self):
        """
        Unzip every archive files in directory
        """
        _valid = [".zip", ".cbz"]
        for x in self.source_path.glob("*"):
            if x.suffix.lower() in _valid:
                logger.debug(f"Unzipping {x.name}...")
                if x.suffix.lower() == ".cbz":
                    temp = x.rename(x.with_suffix(".zip"))
                    shutil.unpack_archive(temp, temp.parent.joinpath(temp.stem))
                else:
                    shutil.unpack_archive(x, x.parent.joinpath(x.stem))
