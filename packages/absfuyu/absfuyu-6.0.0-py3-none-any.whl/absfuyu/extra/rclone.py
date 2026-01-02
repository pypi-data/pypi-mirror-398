"""
Absfuyu: Rclone decrypt
-----------------------
Rclone decryptor

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["RcloneEncryptDecrypt", "DirectoryRcloneDEMixin"]


# Library
# ---------------------------------------------------------------------------
import os
import shutil
from pathlib import Path
from typing import Literal, Self

from rclone import Crypt

from absfuyu.core.baseclass import AutoREPRMixin
from absfuyu.logger import LogLevel, logger
from absfuyu.util.path import DirectoryBase


# Class
# ---------------------------------------------------------------------------
class RcloneEncryptDecrypt(AutoREPRMixin):
    """
    Rclone Decrypt/Encrypt Module
    """

    def __init__(self, crypt: Crypt) -> None:
        """
        This will encrypt/decrypt with rclone style

        Parameters
        ----------
        crypt : Crypt
            ``rclone.Crypt`` object | Encrypt/Decrypt engine
        """
        self._crypt = crypt

    @classmethod
    def from_passwd_salt(cls, passwd: str, salt: str | None = None) -> Self:
        """
        Create Rclone Decrypt/Encrypt object from password and salt

        Parameters
        ----------
        passwd : str
            Custom password

        salt : str | None, optional
            Custom salt, by default None

        Returns
        -------
        Self
            Rclone Decrypt/Encrypt object
        """
        if salt is None:
            crypt: Crypt = Crypt(passwd=passwd)
        else:
            crypt: Crypt = Crypt(passwd=passwd, salt=salt)
        return cls(crypt)

    # Support
    @staticmethod
    def _directory_validator(path: Path) -> Path:
        """Validate if directory exists, then return the path"""
        path = Path(path)
        if not path.exists():
            raise ValueError("Path does not exist")
        return path

    def _modify_name(self, name_to_modify: str, mode: Literal["encrypt", "decrypt"]) -> str:
        if mode == "decrypt":
            return self._crypt.Name.standard_decrypt(name_to_modify)
        if mode == "encrypt":
            return self._crypt.Name.standard_encrypt(name_to_modify)

    def _decrypt_encrypt_operation(
        self,
        mode: Literal["encrypt", "decrypt"],
        root_dir: Path | str,  # type: ignore
        delete_when_complete: bool = False,
    ) -> None:
        """
        Base operation to decrypt, encrypt

        Parameters
        ----------
        mode : Literal["encrypt", "decrypt"]
            Encrypt or decrypt

        root_dir : Path | str
            Directory location

        delete_when_complete : bool
            Delete directory when completed, defaults to False
        """

        logger.info(f"Begin operation: {mode.title()}")
        root_dir = Path(root_dir)
        FILE_MODE = False

        # Make Base folder
        if root_dir.is_file():
            # Get name of parent dir and make name
            temp = self._modify_name(root_dir.parent.name, "encrypt" if mode == "decrypt" else "decrypt")
            # Create sub dir
            base_dir = root_dir.parent.joinpath(temp)
            base_dir.mkdir(exist_ok=True, parents=True)
            # Move file to that dir
            new_path = root_dir.rename(base_dir.joinpath(root_dir.name))
            root_dir = base_dir  # Make root dir
            FILE_MODE = True
        else:
            root_dir: Path = self._directory_validator(root_dir)
            base_name: str = self._modify_name(root_dir.name, mode=mode)
            base_dir: Path = root_dir.parent.joinpath(base_name)
            base_dir.mkdir(exist_ok=True, parents=True)

        _ljust: int = 17  # Logger ljust value

        # Decrypt / Encrypt
        for path in root_dir.glob("**/*"):
            rel_path: Path = path.relative_to(root_dir)
            rel_path_splited: list[str] = str(rel_path).split(os.sep)
            rel_path_modified: list[str] = [self._modify_name(x, mode=mode) for x in rel_path_splited]
            new_path: Path = base_dir.joinpath(*rel_path_modified)

            if path.is_dir():
                logger.debug(f"{mode.title()}ing Dir:".ljust(_ljust) + f"{path}")
                new_path.mkdir(exist_ok=True, parents=True)
                logger.debug(f"{mode.title()}ed Dir:".ljust(_ljust) + f"{new_path}")
            else:
                logger.debug(f"{mode.title()}ing File:".ljust(_ljust) + f"{path}")
                if mode == "decrypt":
                    self._crypt.File.file_decrypt(path, new_path)  # type: ignore
                if mode == "encrypt":
                    self._crypt.File.file_encrypt(path, new_path)  # type: ignore
                logger.debug(f"{mode.title()}ed File:".ljust(_ljust) + f"{new_path}")
        logger.info(f"Operation: {mode.title()} COMPLETED")

        # File mode
        if FILE_MODE:
            new_path.rename(root_dir.parent.joinpath(new_path.name))  # type: ignore
            shutil.rmtree(root_dir)

        # Delete when completed
        if delete_when_complete:
            logger.debug(f"Deleting {root_dir}")
            shutil.rmtree(root_dir)
            logger.debug(f"Deleting {root_dir}...DONE")

    # Decrypt/Encrypt
    def decrypt(self, root_dir: Path, delete_when_complete: bool = False) -> None:
        """
        Decrypt encrypted directory.

        This will decrypt the directory itself and
        create a decrypted directory next to the original

        Parameters
        ----------
        root_dir : Path
            Directory location

        delete_when_complete : bool, optional
            Delete directory when completed, by default False
        """
        self._decrypt_encrypt_operation(mode="decrypt", root_dir=root_dir, delete_when_complete=delete_when_complete)

    def encrypt(self, root_dir: Path, delete_when_complete: bool = False) -> None:
        """
        Encrypt entire directory.

        This will encrypt the directory itself and
        create an encrypted directory next to the original

        Parameters
        ----------
        root_dir : Path
            Directory location

        delete_when_complete : bool, optional
            Delete directory when completed, by default False
        """
        self._decrypt_encrypt_operation(mode="encrypt", root_dir=root_dir, delete_when_complete=delete_when_complete)


class DirectoryRcloneDEMixin(DirectoryBase):
    """
    Directory - Rclone encrypt/decrypt

    Extension for ``absfuyu.util.path.Directory``

    - Decrypt
    - Encrypt
    """

    def rclone_encrypt(self, passwd: str, salt: str | None = None, delete_when_complete: bool = False) -> None:
        """
        Encrypt entire directory.

        This will encrypt the directory itself and
        create an encrypted directory next to the original

        Parameters
        ----------
        passwd : str
            Custom password

        salt : str | None, optional
            Custom salt, by default None

        delete_when_complete : bool, optional
            Delete directory when completed, by default False
        """
        engine = RcloneEncryptDecrypt.from_passwd_salt(passwd=passwd, salt=salt)
        engine.encrypt(self.source_path, delete_when_complete=delete_when_complete)

    def rclone_decrypt(self, passwd: str, salt: str | None = None, delete_when_complete: bool = False) -> None:
        """
        Decrypt encrypted directory.

        This will decrypt the directory itself and
        create a decrypted directory next to the original

        Parameters
        ----------
        passwd : str
            Custom password

        salt : str | None, optional
            Custom salt, by default None

        delete_when_complete : bool, optional
            Delete directory when completed, by default False
        """
        engine = RcloneEncryptDecrypt.from_passwd_salt(passwd=passwd, salt=salt)
        engine.decrypt(self.source_path, delete_when_complete=delete_when_complete)


# Run
# -----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    logger.setLevel(LogLevel.DEBUG)
