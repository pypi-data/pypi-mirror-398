"""
Absufyu: Software
-----------------
Software, pyinstaller related stuff

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Function
    "get_system_info",
    "get_pyinstaller_exe_dir",
    "get_pyinstaller_resource_path",
    "PyinstallerHelper",
    "HWIDgen",
    "LicenseKeySystem",
    "BasicSoftwareProtection",
    # Support
    "SystemInfo",
    "LicenseKey",
    "PyinstallerHiddenImportPreset",
]


# Library
# ---------------------------------------------------------------------------
import base64
import hashlib
import hmac
import json
import os
import platform
import socket
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal, NamedTuple, TypedDict

from absfuyu.core.baseclass import BaseClass
from absfuyu.core.docstring import versionadded, versionchanged
from absfuyu.dxt import Text
from absfuyu.tools.converter import Base64EncodeDecode
from absfuyu.util import stop_after_day


# MARK: System Info
# ---------------------------------------------------------------------------
class SystemInfo(NamedTuple):
    """System info"""

    os_type: str | Literal["Windows", "Linux", "Darwin"]
    os_kernel: str
    os_arch: str
    system_name: str


def get_system_info() -> SystemInfo:
    """
    Returns the current operating system info.

    The function attempts to retrieve the computer name using `platform.node()`.
    If that fails or returns an empty string, it falls back to environment variables
    or `socket.gethostname()` as a last resort, depending on the OS.

    Returns
    -------
    SystemInfo
        A tuple containing:
        - OS name (e.g., 'Windows', 'Linux', 'Darwin')
        - OS kernel (version)
        - OS arch
        - Computer name (hostname)
    """
    os_name = platform.system()

    # Get computer name
    try:
        computer_name = platform.node()
        if not computer_name:
            raise ValueError("Empty name")
    except ValueError:
        if os_name == "Windows":
            computer_name = os.environ.get("COMPUTERNAME", "Unknown")
        else:
            computer_name = os.environ.get("HOSTNAME", socket.gethostname())

    # Return
    return SystemInfo(
        os_name, platform.version(), platform.machine().lower(), computer_name
    )


# MARK: Pyinstaller
# ---------------------------------------------------------------------------
@versionchanged("5.6.1", "Fixed behavior")
def get_pyinstaller_exe_dir() -> Path:
    """
    Returns the directory where the current script or executable resides.

    This function is useful for locating resources relative to the running script or
    bundled executable (e.g., when using PyInstaller). It checks if the script is
    running in a "frozen" state (as an executable), and returns the appropriate
    directory accordingly.

    Returns
    -------
    Path
        A `pathlib.Path` object representing the directory containing the
        executable or the current script file.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(sys.argv[0]).resolve().parent


def get_pyinstaller_resource_path(relative_path: str) -> Path:
    r"""
    Get the absolute path to a resource file, compatible with both development
    environments and PyInstaller-packaged executables.

    When running from a PyInstaller bundle, this function resolves the path relative
    to the temporary ``_MEIPASS`` folder. During normal execution, it resolves the path
    relative to the current script's directory.

    Parameters
    ----------
    relative_path : str
        Relative path to the resource file or directory.

    Returns
    -------
    Path
        A `pathlib.Path` object pointing to the absolute location of the resource.


    Example:
    --------
    >>> get_pyinstaller_resource_path("assets/logo.png")
    <path>\assets\logo.png
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller temp folder
        base_path = Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path


class PyinstallerHiddenImportPreset:
    """
    pyinstaller hidden import preset (library preset)

    Example:
    --------
    >>> PyinstallerHelper(...).add_hidden_import(*PyinstallerHiddenImportPreset.ABSFUYU)
    """

    ABSFUYU = ["absfuyu"]
    DF = ["pandas", "numpy", "openpyxl", "xlsxwriter"]  # DataFrame
    VISUAL = ["rich", "tqdm"]


@versionadded("5.11.0")
class PyinstallerHelper(BaseClass):
    """pyinstaller helper"""

    def __init__(
        self,
        path_to_file: str | Path,
        relative_to_cwd: bool = True,
        console: bool = True,
        onefile: bool = False,
        noconfirm: bool = False,
    ) -> None:
        """
        pyinstaller cmd helper

        Parameters
        ----------
        path_to_file : str | Path
            Path to .py file to make .exe

        relative_to_cwd : bool, optional
            Is the file relative to cwd, by default True

        console : bool, optional
            Include console, by default True

        onefile : bool, optional
            Convert into one file, by default False

        noconfirm : bool, optional
            No confirmation, by default False
        """
        self.source_path = Path(path_to_file)
        self.relative_to_cwd = relative_to_cwd
        self.console = console
        self.onefile = onefile
        self.noconfirm = noconfirm

        if self.relative_to_cwd:
            # rel = self.source_path.relative_to(Path.cwd())
            # self._base_cmd = ["pyinstaller", f"'.\\{Path('.').joinpath(rel)}'"]
            self._base_cmd = ["pyinstaller", f"'.\\{self.source_path.relative_to(Path.cwd())}'"]
        else:
            self._base_cmd = ["pyinstaller", f"'{self.source_path.resolve()}'"]

        self._hidden_import = []
        self._icon = ""

    def add_hidden_import(self, *library: str) -> None:
        """
        Add hidden import (library)
        """
        if len(self._hidden_import) < 1:
            self._hidden_import = list(library)
        else:
            self._hidden_import.extend(list(library))

    def add_icon(self, path_to_icon: str | Path, *, relative_to_cwd: bool | None = None) -> None:
        """
        Add icon to .exe

        Parameters
        ----------
        path_to_icon : str | Path
            Path to icon file

        relative_to_cwd : bool | None, optional
            Use boolean value to overwrite relative_to_cwd option of the main engine, by default None
        """
        p = Path(path_to_icon)
        use_relative = self.relative_to_cwd if relative_to_cwd is None else relative_to_cwd

        # --icon=favicon.ico
        if use_relative:
            rel = p.relative_to(Path.cwd())
            # ensure it always shows with ./ prefix
            # self._icon = f"'{Path('.').joinpath(rel)}'"
            self._icon = f"--icon='.\\{rel}'"
        else:
            self._icon = f"--icon='{p.resolve()}'"

    def export_cmd(self) -> str:
        """
        Export pyinstaller cmd

        Returns
        -------
        str
            pyinstaller command
        """
        cmd = self._base_cmd

        # Hidden import
        if len(self._hidden_import) > 0:
            dat = (f"--hidden-import={x}" for x in list(set(self._hidden_import)))
            cmd.append(" ".join(dat))

        # Console
        if not self.console:
            cmd.append("--noconsole")

        # One file
        if self.onefile:
            cmd.append("--onefile")

        # No confirm
        if self.noconfirm:
            cmd.append("--noconfirm")

        # Icon
        if len(self._icon) > 0:
            cmd.append(self._icon)

        return " ".join(cmd)


# MARK: Key System
# ---------------------------------------------------------------------------
class HWIDgen(BaseClass):
    """
    Generate Hardware ID (HWID)


    Example:
    --------
    >>> HWIDgen.generate()
    """

    def __init__(self) -> None:
        pass

    @classmethod
    def generate(cls) -> str:
        """Generate HWID for current system"""
        os_type = platform.system().lower()
        if os_type == "windows":
            return cls._get_windows_hwid()
        elif os_type == "linux":
            return cls._get_linux_hwid()
        else:
            return cls._get_hwid_mac()

    @staticmethod
    def _get_hwid_mac() -> str:
        """HWID: MAC address"""
        mac = uuid.getnode()  # 48-bit MAC address
        mac_str = ":".join(("%012X" % mac)[i : i + 2] for i in range(0, 12, 2))
        hwid = hashlib.sha256(mac_str.encode()).hexdigest()
        return hwid

    @staticmethod
    def _get_windows_hwid() -> str:
        try:
            # Get BIOS serial number
            bios = (
                subprocess.check_output("wmic bios get serialnumber", shell=True)
                .decode()
                .split("\n")[1]
                .strip()
            )

            # Get Motherboard serial
            board = (
                subprocess.check_output("wmic baseboard get serialnumber", shell=True)
                .decode()
                .split("\n")[1]
                .strip()
            )

            # Get Disk serial
            disk = (
                subprocess.check_output("wmic diskdrive get serialnumber", shell=True)
                .decode()
                .split("\n")[1]
                .strip()
            )

            raw = bios + board + disk
            hwid = hashlib.sha256(raw.encode()).hexdigest()
            return hwid
        except Exception as e:
            return f"Error getting HWID: {e}"

    @staticmethod
    def _get_linux_hwid() -> str:
        try:
            disk_info = subprocess.check_output(
                "udevadm info --query=all --name=/dev/sda", shell=True
            ).decode()
            serial = ""
            for line in disk_info.splitlines():
                if "ID_SERIAL_SHORT" in line:
                    serial = line.split("=")[1]
                    break

            mac = uuid.getnode()
            mac_str = ":".join(("%012X" % mac)[i : i + 2] for i in range(0, 12, 2))

            raw = serial + mac_str
            hwid = hashlib.sha256(raw.encode()).hexdigest()
            return hwid
        except Exception as e:
            return f"Error getting HWID: {e}"


class LicenseKey(TypedDict):
    name: str
    expiry: str
    signature: str


class LicenseKeySystem(BaseClass):
    def __init__(self, name: str, expiry: str, secret_key: str) -> None:
        """
        License Key implementation

        Parameters
        ----------
        name : str
            Name of license holder

        expiry : str
            Expiry date (in yyyy-mm-dd format)

        secret_key : str
            Secret key to make license key
        """
        self._name = name
        self._expiry = expiry
        self._secret = secret_key.encode("utf-8")

    # Make key
    def make_key(self, *, hwid_overwrite: str | None = None) -> str:
        """
        Make a license key in these following steps:
        1. Generate HWID
        2. Combine name, expiry, HWID -> sign it
        3. Base64-encode the signature
        4. Store name, expiry, signature in JSON -> Base64 -> Hex
        5. Divide by 30 chars per line
        6. Wrap in BEGIN/END KEY

        Parameters
        ----------
        hwid_overwrite : str | None, optional
            Overwrite the HWID, by default None

        Returns
        -------
        str
            License key
        """
        # Prepare
        hwid = (
            HWIDgen.generate() if hwid_overwrite is None else hwid_overwrite
        )  # Get HWID
        msg_data = f"{self._name}|{self._expiry}|{hwid}"  # Make msg
        signature = hmac.new(self._secret, msg_data.encode(), hashlib.sha256).digest()
        encoded_sig = base64.urlsafe_b64encode(signature).decode()

        # Key format
        key: LicenseKey = {
            "name": self._name,
            "expiry": self._expiry,
            "signature": encoded_sig,
        }
        # This convert to .json -> Base64 -> Hex
        encoded_key = Text(Base64EncodeDecode.encode(json.dumps(key))).to_hex(raw=True)
        output_key = (
            "BEGIN KEY".center(30, "=")
            + "\n"
            + "\n".join(Text(encoded_key).divide(30))
            + "\n"
            + "END KEY".center(30, "=")
        )
        return output_key

    # Check key
    @staticmethod
    def _parse_license_key(license_key: str) -> LicenseKey:
        """
        Parse a formatted license key

        Parameters
        ----------
        license_key : str
            License key

        Returns
        -------
        LicenseKey
            Parsed license key
        """
        try:
            lines = license_key.strip().split("\n")[1:-1]  # Remove BEGIN/END KEY lines
            raw_hex = "".join(lines)
            decoded_json = Base64EncodeDecode.decode(
                bytes.fromhex(raw_hex).decode("utf-8")
            )
            return json.loads(decoded_json)
        except Exception as e:
            raise ValueError("Invalid license key format") from e

    @classmethod
    def verify_license(
        cls,
        license_key: str,
        secret_key: str | None = None,
        hwid_overwrite: str | None = None,
    ) -> bool:
        """
        Verify a license key

        Parameters
        ----------
        license_key : str
            License key

        secret_key : str | None, optional
            Secret key, by default None

        hwid_overwrite : str | None, optional
            HWID, by default None

        Returns
        -------
        bool
            _description_
        """

        # Prep
        secret = "" if secret_key is None else secret_key
        hwid = HWIDgen.generate() if hwid_overwrite is None else hwid_overwrite
        parsed_license_key = cls._parse_license_key(license_key)

        try:
            msg_data = (
                f"{parsed_license_key['name']}|{parsed_license_key['expiry']}|{hwid}"
            )

            expected_sig = hmac.new(
                secret.encode("utf-8"), msg_data.encode(), hashlib.sha256
            ).digest()
            expected_encoded_sig = base64.urlsafe_b64encode(expected_sig).decode()

            return parsed_license_key["signature"] == expected_encoded_sig
        except Exception:
            return False


# MARK: Software
# ---------------------------------------------------------------------------
class BasicSoftwareProtection(BaseClass):
    """
    Basic software protection

    This check valid license before run any app. Recommended to put at start of the code

    Usage:
    ------
    >>> t = BasicSoftwareProtection(get_pyinstaller_exe_dir())
    >>> t.add_secret("Test Key")
    >>> t.check_valid_license()
    """

    def __init__(
        self,
        cwd: str | Path,
        name: str | None = None,
        version: str | None = None,
        author: str | None = None,
        author_email: str | None = None,
    ) -> None:
        """
        Basic software protection.

        Parameters
        ----------
        cwd : str | Path
            Current working directory

        name : str | None, optional
            Name of the software, by default None

        version : str | None, optional
            Version of the software, by default None

        author : str | None, optional
            Author of the software, by default None

        author_email : str | None, optional
            Author's email of the software, by default None
        """
        self._cwd = Path(cwd)
        self._author = "" if author is None else author
        self._author_email = "" if author_email is None else author_email
        self._software_name = "" if name is None else name
        self._software_version = "" if version is None else version
        self._secret = ""

    # Metadata
    @property
    def cwd(self) -> Path:
        """Current working directory"""
        return self._cwd

    @property
    def software_name(self) -> str:
        """Name of the software"""
        return self._software_name

    @software_name.setter
    def software_name(self, value: str) -> None:
        # Logic to validate name
        self._software_name = value

    @property
    def author(self) -> str:
        """Author of the software"""
        return self._author

    @property
    def version(self) -> str:
        """Version of the software"""
        return self._software_version

    # Protection
    def add_secret(self, secret: str) -> None:
        """
        Add secret

        Parameters
        ----------
        secret : str
            secret
        """
        self._secret = secret

    def check_valid_license(self, generate_helper: bool = True) -> None:
        """
        Check for valid license
        (``.zlic`` file in the same directory as the script that runs this code)

        Parameters
        ----------
        generate_helper : bool, optional
            Generate a helper file (``license.helper``),
            which can be used to make license key,
            by default ``True``

        Raises
        ------
        SystemExit
            License file not found!

        SystemExit
            Invalid license key format!

        SystemExit
            Invalid license!
        """
        try:
            # Get license file
            license_file = list(self._cwd.glob("*.zlic"))[0]
            with license_file.open() as f:
                # Load data
                data = "".join(f.readlines())
        except IndexError:
            if generate_helper:
                self.generate_license_helper()
            raise SystemExit("License file not found!")
        except ValueError:
            raise SystemExit("Invalid license key format!")
        else:
            # Verify license
            if LicenseKeySystem.verify_license(data, secret_key=self._secret):
                parsed_date = datetime.strptime(
                    LicenseKeySystem._parse_license_key(data)["expiry"], "%Y-%m-%d"
                )
                stop_after_day(
                    parsed_date.year,
                    parsed_date.month,
                    parsed_date.day,
                    custom_msg="License expired!",
                )
            else:  # Invalid license
                raise SystemExit("Invalid license!")

    @versionadded("5.9.0")
    def check_valid_license_gui(
        self, title: str = "WARNING", message: str = "INVALID LICENSE!", generate_helper: bool = True
    ) -> None:
        """
        Check for valid license
        (``.zlic`` file in the same directory as the script that runs this code)
        but will pop up a GUI when invalid license.

        Parameters
        ----------
        title : str, optional
            Title of the GUI, by default "WARNING"

        message : str, optional
            Message in the GUI, by default "INVALID LICENSE!"

        generate_helper : bool, optional
            Generate a helper file (``license.helper``),
            which can be used to make license key,
            by default ``True``

        Raises
        ------
        SystemExit
            Invalid license
        """
        try:
            self.check_valid_license(generate_helper=generate_helper)
        except SystemExit:
            from tkinter import messagebox

            messagebox.showwarning(title, message, icon="error")
            raise SystemExit("Invalid license")

    # Make key
    def _make_key(self, name: str, expiry: str, secret: str) -> None:
        """
        Generate license key in the same directory as the script that runs this code.

        Parameters
        ----------
        name : str
            Name of license's holder

        expiry : str
            Expiry date in format "yyyy-mm-dd"

        secret : str
            Secret string
        """
        path = self._cwd.joinpath("license.zlic")
        engine = LicenseKeySystem(name, expiry, secret)
        with path.open("w", encoding="utf-8") as f:
            f.write(engine.make_key())

    def generate_license_helper(self) -> None:
        """Gather HWID and make it into a file"""
        path = self._cwd.joinpath("license.helper")
        with path.open("w", encoding="utf-8") as f:
            f.write(HWIDgen.generate())
