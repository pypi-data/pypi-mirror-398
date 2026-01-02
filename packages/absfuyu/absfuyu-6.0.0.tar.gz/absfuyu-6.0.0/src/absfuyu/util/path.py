"""
Absfuyu: Path
-------------
Path related

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)

Feature:
--------
- Directory
- SaveFileAs
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Main
    "DirectoryBase",
    "Directory",
    "ProjectDirInit",
    "SaveFileAs",
    # Mixin
    "DirectoryInfoMixin",
    "DirectoryBasicOperationMixin",
    "DirectoryArchiverMixin",
    "DirectoryOrganizerMixin",
    "DirectoryTreeMixin",
    "DirectorySelectMixin",
    # Support
    "FileOrFolderWithModificationTime",
    "DirectoryInfo",
]


# Library
# ---------------------------------------------------------------------------
import os
import re
import shutil
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, ClassVar, Literal, NamedTuple

from absfuyu.core.baseclass import BaseClass
from absfuyu.core.decorator import add_subclass_methods_decorator
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.logger import logger

# Template
# ---------------------------------------------------------------------------
ORGANIZE_TEMPLATE: dict[str, list[str]] = {
    "Code": [
        ".ps1",
        ".py",
        ".rs",
        ".js",
        ".c",
        ".h",
        ".cpp",
        ".cs",
        ".r",
        ".cmd",
        ".bat",
        ".lua",
    ],
    "Comic": [".cbz", ".cbr", ".cb7", ".cbt", ".cba"],
    "Compressed": [
        ".7z",
        ".zip",
        ".rar",
        ".apk",
        ".cab",
        ".tar",
        ".tgz",
        ".txz",
        ".bz2",
        ".gz",
        ".lz",
        ".lz4",
        ".lzma",
        ".xz",
        ".zipx",
        ".zst",
    ],
    "Documents": [".docx", ".doc", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt"],
    "Ebook": [
        ".epub",
        ".mobi",
        ".prc",
        ".lrf",
        ".lrx",
        ".pdb",
        ".azw",
        ".azw3",
        ".kf8",
        ".kfx",
        ".opf",
    ],
    "Music": [".mp3", ".flac", ".wav", ".m4a", ".wma", ".aac", ".alac", ".aiff"],
    "OS": [".iso", ".dmg", ".wim"],
    "Pictures": [
        ".jpg",
        ".jpeg",
        ".png",
        ".apng",
        ".avif",
        ".bmp",
        ".gif",
        ".jfif",
        ".pjpeg",
        ".pjp",
        ".svg",
        ".ico",
        ".cur",
        ".tif",
        ".tiff",
        ".webp",
    ],
    "Programs": [".exe", ".msi"],
    "Video": [
        ".3g2",
        ".3gp",
        ".avi",
        ".flv",
        ".m2ts",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".mpeg",
        ".mpv",
        ".mts",
        ".ts",
        ".vob",
        ".webm",
    ],
    "Raw pictures": [
        ".3fr",
        ".ari",
        ".arw",
        ".bay",
        ".braw",
        ".crw",
        ".cr2",
        ".cr3",
        ".cap",
        ".data",
        ".dcs",
        ".dcr",
        ".dng",
        ".drf",
        ".eip",
        ".erf",
        ".fff",
        ".gpr",
        ".iiq",
        ".k25",
        ".kdc",
        ".mdc",
        ".mef",
        ".mos",
        ".mrw",
        ".nef",
        ".nrw",
        ".obm",
        ".orf",
        ".pef",
        ".ptx",
        ".pxn",
        ".r3d",
        ".raf",
        ".raw",
        ".rwl",
        ".rw2",
        ".rwz",
        ".sr2",
        ".srf",
        ".srw",
        ".tif",
        ".x3f",
    ],
}


# Support Class
# ---------------------------------------------------------------------------
@versionadded("3.3.0")
class FileOrFolderWithModificationTime(NamedTuple):
    """
    File or Folder with modification time

    :param path: Original path
    :param modification_time: Modification time
    """

    path: Path
    modification_time: datetime


@deprecated(
    "5.1.0", reason="Support for ``DirectoryInfoMixin`` which is also deprecated"
)
@versionadded("3.3.0")
class DirectoryInfo(NamedTuple):
    """
    Information of a directory
    """

    creation_time: datetime
    modification_time: datetime


# Class - Directory
# ---------------------------------------------------------------------------
@add_subclass_methods_decorator
class DirectoryBase(BaseClass):
    """
    Directory - Base

    Parameters
    ----------
    source_path : str | Path
        Source folder

    create_if_not_exist : bool
        Create directory when not exist,
        by default ``False``
    """

    # Custom attribute
    _METHOD_INCLUDE: ClassVar[bool] = True  # Include in DIR_METHODS
    SUBCLASS_METHODS: ClassVar[dict[str, list[str]]] = {}

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        source_path : str | Path
            Source folder

        create_if_not_exist : bool
            Create directory when not exist,
            by default ``False``
        """
        self.source_path = Path(source_path)
        if not self.source_path.exists():
            if create_if_not_exist:
                self.source_path.mkdir(exist_ok=True, parents=True)
            else:
                raise FileNotFoundError("Directory not existed")


class DirectoryInfoMixin(DirectoryBase):
    """
    Directory - Info

    - Quick info
    """

    @deprecated("5.1.0", reason="Not efficient")
    @versionadded("3.3.0")
    def quick_info(self) -> DirectoryInfo:
        """
        Quick information about this Directory

        Returns
        -------
        DirectoryInfo
            DirectoryInfo
        """
        source_stat: os.stat_result = self.source_path.stat()
        out = DirectoryInfo(
            creation_time=datetime.fromtimestamp(source_stat.st_ctime),
            modification_time=datetime.fromtimestamp(source_stat.st_mtime),
        )
        return out


class DirectoryBasicOperationMixin(DirectoryBase):
    """
    Directory - Basic operation

    - Rename
    - Copy
    - Move
    - Delete
    """

    # Rename
    def rename(self, new_name: str) -> None:
        """
        Rename directory

        Parameters
        ----------
        new_name : str
            Name only (not the entire path)
        """
        try:
            logger.debug(f"Renaming to {new_name}...")
            self.source_path.rename(self.source_path.with_name(new_name))
            logger.debug(f"Renaming to {new_name}...DONE")
        except Exception as e:
            logger.error(e)
        # return self.source_path

    # Copy
    def copy(self, dst: Path) -> None:
        """
        Copy entire directory

        Parameters
        ----------
        dst : Path
            Destination
        """
        logger.debug(f"Copying to {dst}...")
        try:
            try:
                shutil.copytree(self.source_path, Path(dst), dirs_exist_ok=True)
            except Exception:
                shutil.copytree(self.source_path, Path(dst))
            logger.debug(f"Copying to {dst}...DONE")
        except Exception as e:
            logger.error(e)

    # Move
    def move(self, dst: Path, content_only: bool = False) -> None:
        """
        Move entire directory

        Parameters
        ----------
        dst : Path
            Destination

        content_only : bool
            Only move content inside the folder (Default: ``False``; Move entire folder)
        """
        try:
            logger.debug(f"Moving to {dst}...")
            if content_only:
                for x in self.source_path.iterdir():
                    shutil.move(x, Path(dst))
            else:
                shutil.move(self.source_path, Path(dst))
            logger.debug(f"Moving to {dst}...DONE")

        except OSError as e:  # File already exists
            logger.error(e)
            logger.debug("Overwriting file...")
            if content_only:
                for x in self.source_path.iterdir():
                    shutil.move(x, Path(dst).joinpath(x.name))
            else:
                shutil.move(self.source_path, Path(dst))
            logger.debug("Overwriting file...DONE")

    # Delete folder
    def _mtime_folder(self) -> list[FileOrFolderWithModificationTime]:
        """
        Get modification time of file/folder (first level only)
        """
        return [
            FileOrFolderWithModificationTime(
                path, datetime.fromtimestamp(path.stat().st_mtime)
            )
            for path in self.source_path.glob("*")
        ]

    @staticmethod
    def _delete_files(list_of_files: list[Path]) -> None:
        """
        Delete files/folders
        """
        for x in list_of_files:
            x = Path(x).absolute()
            logger.debug(f"Removing {x}...")
            try:
                if x.is_dir():
                    shutil.rmtree(x)
                else:
                    x.unlink()
                logger.debug(f"Removing {x}...SUCCEED")
            except Exception:
                logger.error(f"Removing {x}...FAILED")

    @staticmethod
    def _date_filter(
        value: FileOrFolderWithModificationTime,
        period: Literal["Y", "M", "D"] = "Y",
    ) -> bool:
        """
        Filter out file with current Year|Month|Day
        """
        data = {
            "Y": value.modification_time.year,
            "M": value.modification_time.month,
            "D": value.modification_time.day,
        }
        now = datetime.now()
        ntime = {"Y": now.year, "M": now.month, "D": now.day}
        return data[period] != ntime[period]

    def delete(
        self,
        entire: bool = False,
        *,
        based_on_time: bool = False,
        keep: Literal["Y", "M", "D"] = "Y",
    ) -> None:
        """
        Deletes everything

        Parameters
        ----------
        entire : bool
            | ``True``: Deletes the folder itself
            | ``False``: Deletes content inside only
            | (Default: ``False``)

        based_on_time : bool
            | ``True``: Deletes everything except ``keep`` period
            | ``False``: Works normal
            | (Default: ``False``)

        keep : Literal["Y", "M", "D"]
            Delete all file except current ``Year`` | ``Month`` | ``Day``
        """
        try:
            logger.info(f"Removing {self.source_path}...")

            if entire:
                shutil.rmtree(self.source_path)
            else:
                if based_on_time:
                    filter_func = partial(self._date_filter, period=keep)
                    # self._delete_files([x[0] for x in filter(filter_func, self._mtime_folder())])
                    self._delete_files(
                        [x.path for x in filter(filter_func, self._mtime_folder())]
                    )
                else:
                    self._delete_files(
                        map(lambda x: x.path, self._mtime_folder())  # type: ignore
                    )

            logger.info(f"Removing {self.source_path}...SUCCEED")
        except Exception as e:
            logger.error(f"Removing {self.source_path}...FAILED\n{e}")


class DirectoryArchiverMixin(DirectoryBase):
    """
    Directory - Archiver/Compress

    - Compress
    - Decompress
    - Register extra zip format <staticmethod>
    """

    @versionchanged("5.1.0", reason="Update funcionality (new parameter)")
    def compress(
        self,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        delete_after_compress: bool = False,
        move_inside: bool = True,
    ) -> Path | None:
        """
        Compress the directory (Default: Create ``.zip`` file)

        Parameters
        ----------
        format : Literal["zip", "tar", "gztar", "bztar", "xztar"], optional
            By default ``"zip"``
            - ``zip``: ZIP file (if the ``zlib`` module is available).
            - ``tar``: Uncompressed tar file. Uses POSIX.1-2001 pax format for new archives.
            - ``gztar``: gzip'ed tar-file (if the ``zlib`` module is available).
            - ``bztar``: bzip2'ed tar-file (if the ``bz2`` module is available).
            - ``xztar``: xz'ed tar-file (if the ``lzma`` module is available).

        delete_after_compress : bool, optional
            Delete directory after compress, by default ``False``

        move_inside : bool, optional
            Move the commpressed file inside the directory,
            by default ``True``

        Returns
        -------
        Path
            Compressed path

        None
            When fail to compress
        """
        logger.debug(f"Zipping {self.source_path}...")
        try:
            # Zip
            # zip_name = self.source_path.parent.joinpath(self.source_path.name).__str__()
            # shutil.make_archive(zip_name, format=format, root_dir=self.source_path)
            zip_path = shutil.make_archive(
                self.source_path.__str__(), format=format, root_dir=self.source_path
            )
            logger.debug(f"Zipping {self.source_path}...DONE")
            logger.debug(f"Path: {zip_path}")

            # Del
            if delete_after_compress:
                move_inside = False
                shutil.rmtree(self.source_path)

            # Move
            if move_inside:
                zf = Path(zip_path)
                _move_path = self.source_path.joinpath(zf.name)
                if _move_path.exists():
                    _move_path.unlink(missing_ok=True)
                _move = zf.rename(_move_path)
                return _move

            return Path(zip_path)
        except (FileExistsError, OSError) as e:
            logger.error(f"Zipping {self.source_path}...FAILED\n{e}")
            return None

    @staticmethod
    @versionadded("5.1.0")
    def register_extra_zip_format() -> None:
        """This register extra extension for zipfile"""
        extra_extension = [".zip", ".cbz"]
        shutil.unregister_unpack_format("zip")
        shutil.register_unpack_format(
            "zip",
            extra_extension,
            shutil._unpack_zipfile,  # type: ignore
            description="ZIP file",
        )

    @versionadded("5.1.0")
    def decompress(
        self,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] | None = None,
        delete_after_done: bool = False,
    ) -> None:
        """
        Decompress compressed file in directory (first level only)

        Parameters
        ----------
        format : Literal["zip", "tar", "gztar", "bztar", "xztar"] | None, optional
            By default ``None``
            - ``zip``: ZIP file (if the ``zlib`` module is available).
            - ``tar``: Uncompressed tar file. Uses POSIX.1-2001 pax format for new archives.
            - ``gztar``: gzip'ed tar-file (if the ``zlib`` module is available).
            - ``bztar``: bzip2'ed tar-file (if the ``bz2`` module is available).
            - ``xztar``: xz'ed tar-file (if the ``lzma`` module is available).

        delete_after_done : bool, optional
            Delete compressed file when extracted, by default ``False``
        """
        # Register extra extension
        self.register_extra_zip_format()

        # Decompress first level only
        for path in self.source_path.glob("*"):
            try:
                shutil.unpack_archive(
                    path, path.parent.joinpath(path.stem), format=format
                )
                if delete_after_done and path.is_file():
                    path.unlink(missing_ok=True)
            except OSError:
                continue


class DirectoryOrganizerMixin(DirectoryBase):
    """
    Directory - File organizer

    - Organize
    """

    @versionadded("5.3.0")
    def organize(self, dirtemplate: dict[str, list[str]] | None = None) -> None:
        """
        Organize a directory.

        Parameters
        ----------
        dirtemplate : dict[str, Collection[str]] | None, optional
            | Template to move file to, by default ``None``.
            | Example: {"Documents": [".txt", ".pdf", ...]}
        """
        if dirtemplate is None:
            template = ORGANIZE_TEMPLATE
        else:
            template = dirtemplate

        other_dir = self.source_path.joinpath("Others")
        other_dir.mkdir(parents=True, exist_ok=True)

        for path in self.source_path.iterdir():
            if path.is_dir():
                continue

            for dir_name, suffixes in template.items():
                if path.suffix.lower() in suffixes:
                    move_path = self.source_path.joinpath(dir_name)
                    move_path.mkdir(parents=True, exist_ok=True)
                    path.rename(move_path.joinpath(path.name))
                    break
            else:
                path.rename(other_dir.joinpath(path.name))


class DirectoryTreeMixin(DirectoryBase):
    # Directory structure
    def _list_dir(self, *ignore: str) -> list[Path]:
        """
        List all directories and files

        Parameters
        ----------
        ignore : str
            List of pattern to ignore. Example: "__pycache__", ".pyc"
        """
        logger.debug(f"Base folder: {self.source_path.name}")

        list_of_path = self.source_path.glob("**/*")

        # No ignore rules
        if len(ignore) == 0:  # No ignore pattern
            return [path.relative_to(self.source_path) for path in list_of_path]

        # With ignore rules
        # ignore_pattern = "|".join(ignore)
        ignore_pattern = re.compile("|".join(ignore))
        logger.debug(f"Ignore pattern: {ignore_pattern}")
        return [
            path.relative_to(self.source_path)
            for path in list_of_path
            if re.search(ignore_pattern, path.name) is None
        ]

    @staticmethod
    @versionadded("3.3.0")
    def _split_dir(list_of_path: list[Path]) -> list[list[str]]:
        """
        Split pathname by ``os.sep``

        Parameters
        ----------
        list_of_path : list[Path]
            List of Path

        Returns
        -------
        list[list[str]]
            List of splitted dir


        Example:
        --------
        >>> test = [Path(test_root / test_not_root), ...]
        >>> Directory._split_dir(test)
        [[test_root, test_not_root], [...]...]
        """

        return sorted([str(path).split(os.sep) for path in list_of_path])

    def _separate_dir_and_files(
        self,
        list_of_path: list[Path],
        *,
        tab_symbol: str | None = None,
        sub_dir_symbol: str | None = None,
    ) -> list[str]:
        """
        Separate dir and file and transform into folder structure

        Parameters
        ----------
        list_of_path : list[Path]
            List of paths

        tab_symbol : str | None
            Tab symbol
            (Default: ``"\\t"``)

        sub_dir_symbol : str | None
            Sub-directory symbol
            (Default: ``"|-- "``)

        Returns
        -------
        list[str]
            Folder structure ready to print
        """
        # Check for tab and sub-dir symbol
        if tab_symbol is None:
            tab_symbol = "\t"
        if sub_dir_symbol is None:
            sub_dir_symbol = "|-- "

        temp: list[list[str]] = self._split_dir(list_of_path)

        return [  # Returns n-tab space with sub-dir-symbol for the last item in x
            f"{tab_symbol * (len(x) - 1)}{sub_dir_symbol}{x[-1]}" for x in temp
        ]

    def list_structure(self, *ignore: str) -> str:
        """
        List folder structure

        Parameters
        ----------
        ignore : str
            Tuple contains patterns to ignore

        Returns
        -------
        str
            Directory structure


        Example (For typical python library):
        -------------------------------------
        >>> test = Directory(<source path>)
        >>> test.list_structure(
                "__pycache__",
                ".pyc",
                "__init__",
                "__main__",
            )
        ...
        """
        temp: list[Path] = self._list_dir(*ignore)
        out: list[str] = self._separate_dir_and_files(temp)
        return "\n".join(out)  # Join the list

    def list_structure_pkg(self) -> str:
        """
        List folder structure of a typical python package

        Returns
        -------
        str
            Directory structure
        """
        return self.list_structure("__pycache__", ".pyc")


@versionadded("5.6.0")
class DirectorySelectMixin(DirectoryBase):
    """
    Directory - File select

    - Select all
    """

    def select_all(self, *file_type: str, recursive: bool = False) -> list[Path]:
        """
        Select all files

        Parameters
        ----------
        file_type : str
            File suffix to select

        recursive : bool, optional
            Include sub directories, by default ``False``

        Returns
        -------
        list[Path]
            Selected file paths
        """
        pattern = "**/*" if recursive else "*"
        paths = [
            x
            for x in self.source_path.glob(pattern)
            if x.is_file() and x.suffix.lower() in map(lambda x: x.lower(), file_type)
        ]
        return paths


class Directory(
    DirectoryTreeMixin,
    DirectoryOrganizerMixin,
    DirectoryArchiverMixin,
    DirectoryBasicOperationMixin,
    DirectorySelectMixin,
    DirectoryInfoMixin,
):
    """
    Some shortcuts for directory

    Parameters
    ----------
    source_path : str | Path
        Source folder

    create_if_not_exist : bool
        Create directory when not exist,
        by default ``False``


    Example:
    --------
    >>> # For a list of method
    >>> Directory.SUBCLASS_METHODS
    """

    pass


# Class - ProjectDirInit
# ---------------------------------------------------------------------------
class FileContent(NamedTuple):
    path: Path
    content: str


@versionadded("6.0.0")
class ProjectDirInit(DirectoryBase):
    """
    Project directory init, normally to setup project

    Available variables:
    - _folders
    - _files
    """

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
        *,
        auto_generate: bool = False,
    ) -> None:
        """
        Project directory

        Parameters
        ----------
        source_path : str | Path
            Source folder

        create_if_not_exist : bool
            Create directory when not exist, by default ``False``

        auto_generate : bool, optional
            Auto generate folders and file in ``self._folders``
            and ``self._files`` when using add method, by default ``False``
        """

        super().__init__(source_path, create_if_not_exist)

        # This variable store sub folder/file paths
        self.auto_generate = auto_generate
        self._folders: dict[str, Path] = {}
        self._files: dict[str, FileContent] = {}

    # Add
    # -----------------------------------------
    def add_folder(self, folder_name_only: str, /) -> None:
        """
        Add a subfolder relative to ``self.source_path``

        Parameters
        ----------
        folder_name_only : str
            Folder name
        """
        self._folders[folder_name_only] = self.source_path.joinpath(folder_name_only)
        if self.auto_generate:
            self._make_folder()

    def add_file(self, file_name_only: str, content: str | None = None) -> None:
        """
        Add a file relative to ``self.source_path``

        Parameters
        ----------
        file_name_only : str
            File name

        content : str | None, optional
            Content of the file, by default ``None``
        """
        c = "" if content is None else content
        self._files[file_name_only] = FileContent(self.source_path.joinpath(file_name_only), c)
        if self.auto_generate:
            self._make_file()

    # Generate
    # -----------------------------------------
    def _make_folder(self) -> None:
        """
        Generate folders in ``self._folders``
        """
        if len(self._folders) < 1:
            return None

        for _, v in self._folders.items():
            if not v.exists():
                v.mkdir(parents=True, exist_ok=True)

    def _make_file(self) -> None:
        """
        Generate files in ``self._files``
        """
        if len(self._files) < 1:
            return None

        for _, v in self._files.items():
            if not v.path.exists():
                with v.path.open("w", encoding="utf-8") as f:
                    f.write(v.content)

    def generate_project(self) -> None:
        """
        Generate folders and file in ``self._folders`` and ``self._files``
        """
        self._make_folder()
        self._make_file()

    # Clean
    # -----------------------------------------
    def clean_up(self) -> None:
        """Delete files in ``self._folders``"""
        # Del folders
        for x in self._folders.values():
            shutil.rmtree(x.absolute(), ignore_errors=False)


# Class - SaveFileAs
# ---------------------------------------------------------------------------
class SaveFileAs:
    """
    File as multiple file type
    """

    def __init__(self, data: Any, *, encoding: str | None = "utf-8") -> None:
        """
        :param encoding: Default: utf-8
        """
        self.data = data
        self.encoding = encoding

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __repr__(self) -> str:
        return self.__str__()

    def to_txt(self, path: str | Path) -> None:
        """
        Save as ``.txt`` file

        Parameters
        ----------
        path : Path
            Save location
        """
        with open(path, "w", encoding=self.encoding) as file:
            file.writelines(self.data)

    # def to_pickle(self, path: Union[str, Path]) -> None:
    #     """
    #     Save as .pickle file

    #     :param path: Save location
    #     """
    #     from absfuyu.util.pkl import Pickler
    #     Pickler.save(path, self.data)

    # def to_json(self, path: Union[str, Path]) -> None:
    #     """
    #     Save as .json file

    #     :param path: Save location
    #     """
    #     from absfuyu.util.json_method import JsonFile
    #     temp = JsonFile(path, sort_keys=False)
    #     temp.save_json()
