"""
Absfuyu: Google related
-----------------------
Google Drive downloader

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["GoogleDriveFile", "GoogleDriveClient"]


# Library
# ---------------------------------------------------------------------------
import io
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, cast

from absfuyu.core.baseclass import BaseClass

try:
    import requests
    from google.oauth2 import service_account
    from googleapiclient.discovery import Resource, build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[ggapi]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[ggapi] package")  # noqa: B904


# Class
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class DriveFileMeta:
    id: str
    name: str
    mime_type: str


class GoogleDriveClient(BaseClass):
    SCOPES: ClassVar = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    EXPORT_MIME_MAP: ClassVar = {
        "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "application/vnd.google-apps.document": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "application/vnd.google-apps.presentation": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
    }

    def __init__(self, service_account_data: str | Path | dict[str, str]) -> None:
        """
        Google drive instance

        Parameters
        ----------
        service_account_data : str | Path | dict[str, str]
            Path to ``service_account.json`` file or .json loaded data
        """
        if isinstance(service_account_data, str):
            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_data,
                scopes=self.SCOPES,
            )
        elif isinstance(service_account_data, Path):
            self.credentials = service_account.Credentials.from_service_account_file(
                str(service_account_data.resolve()),
                scopes=self.SCOPES,
            )
        else:
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_data,
                scopes=self.SCOPES,
            )

        self.drive = cast(Resource, build("drive", "v3", credentials=self.credentials))
        self.sheets = cast(Resource, build("sheets", "v4", credentials=self.credentials))

    # Metadata
    # -----------------------------
    def get_metadata(self, file_id: str) -> DriveFileMeta:
        data = self.drive.files().get(fileId=file_id, fields="id,name,mimeType").execute()
        return DriveFileMeta(
            id=data["id"],
            name=data["name"],
            mime_type=data["mimeType"],
        )

    # Download / Export
    # -----------------------------
    def download_bytes(self, file_id: str) -> bytes:
        request = self.drive.files().get_media(fileId=file_id)
        return self._download(request)

    def export_bytes(self, file_id: str, mime_type: str) -> bytes:
        request = self.drive.files().export_media(
            fileId=file_id,
            mimeType=mime_type,
        )
        return self._download(request)

    def _download(self, request) -> bytes:
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        return buf.read()


class GoogleDriveFile:
    """
    Google drive file to download


    Example:
    --------
    >>> client = GoogleDriveClient("service_account.json")
    >>> gfile = GoogleDriveFile(file_id=<id>, client=client)
    >>> gfile.download(<dir>)
    """

    PUBLIC_URL = "https://drive.google.com/uc?export=download"

    def __init__(
        self,
        file_id: str,
        *,
        client: GoogleDriveClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.file_id = file_id
        self.client = client
        self.timeout = timeout
        self.session = requests.Session()

    # Public API
    # -----------------------------
    def download(self, directory: str | Path = ".") -> Path:
        """
        Download file with auto-detected name and extension.
        Returns saved file path.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        if self.client:
            return self._download_private(directory)

        return self._download_public(directory)

    # Private (Service Account)
    # -----------------------------
    def _download_private(self, directory: Path) -> Path:
        meta = self.client.get_metadata(self.file_id)

        # Google Docs -> export
        if meta.mime_type in self.client.EXPORT_MIME_MAP:
            export_mime, ext = self.client.EXPORT_MIME_MAP[meta.mime_type]
            data = self.client.export_bytes(self.file_id, export_mime)
            filename = meta.name + ext
        else:
            data = self.client.download_bytes(self.file_id)
            ext = mimetypes.guess_extension(meta.mime_type) or ""
            filename = meta.name if Path(meta.name).suffix else meta.name + ext

        path = directory / filename
        path.write_bytes(data)
        return path

    # Public (no auth)
    # -----------------------------
    def _download_public(self, directory: Path) -> Path:
        response = self.session.get(
            self.PUBLIC_URL,
            params={"id": self.file_id},
            timeout=self.timeout,
        )

        # confirmation token
        for k, v in response.cookies.items():
            if k.startswith("download_warning"):
                response = self.session.get(
                    self.PUBLIC_URL,
                    params={"id": self.file_id, "confirm": v},
                    timeout=self.timeout,
                )
                break

        response.raise_for_status()

        # filename from header (if present)
        cd = response.headers.get("content-disposition", "")
        filename = "downloaded_file"

        if "filename=" in cd:
            filename = cd.split("filename=")[-1].strip('"')

        path = directory / filename
        path.write_bytes(response.content)
        return path
