"""
Absfuyu: Google related
-----------------------
Google Online license from sheet

Version: 6.0.0
Date updated: 28/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["GGSheetOnlineLicenseSystem"]


# Library
# ---------------------------------------------------------------------------
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Self, cast

from absfuyu.core.baseclass import BaseClass
from absfuyu.extra.ggapi.gsheet import GoogleSheet
from absfuyu.tools.sw import HWIDgen, get_system_info

# Var
# ---------------------------------------------------------------------------
type GoogleSheetClient = GoogleSheet


@dataclass(frozen=True)
class LicenseEntry:
    id: int
    hwid: str
    name: str
    os: str
    date: int | datetime
    active: bool

    def to_row(self) -> list:
        return [self.id, self.hwid, self.name, self.os, self.date, self.active]


# Class
# ---------------------------------------------------------------------------
class GGSheetOnlineLicenseSystem(BaseClass):
    def __init__(self, google_client: GoogleSheetClient, sheet_id: str, sheet_name: str = "Sheet1") -> None:
        """
        Google sheet online license system instance

        Parameters
        ----------
        google_client : GoogleSheetClient
            Google sheet client

        sheet_id : str
            Sheet ID

        sheet_name : str, optional
            Sheet name, by default ``"Sheet1"``
        """
        self.client = google_client
        self._sheet_id = sheet_id
        self._sheet_name = sheet_name

        # Variable
        self._df: list[LicenseEntry] | None = None
        try:
            self._load()
        except Exception:
            pass

    # Property
    @cached_property
    def hwid(self) -> str:
        return HWIDgen.generate()

    # Support
    def _load(self) -> None:
        df = cast(list[list[Any]], self.client.read_sheet(spreadsheet_id=self._sheet_id, sheet_name=self._sheet_name))
        data = [LicenseEntry(*x) for x in df]
        self._df = data

    def _gather_system_info(self) -> list[str]:
        self._sysif = get_system_info()
        return [self.hwid, self._sysif.system_name, self._sysif.os_type]

    def _make_device_entry(self) -> list:
        df = self._df
        row = [int(df[-1].id) + 1]
        row.extend(self._gather_system_info())
        row.extend([datetime.now().strftime("%d/%m/%Y"), False])
        return row

    def _get_device_online(self):
        """Get ID of device in sheet, create entry if None"""
        df = self._df

        for x in df:
            if x.hwid == self.hwid:
                return x.id

        has_updated = False  # safe guard
        if not has_updated:
            new_entry = self._make_device_entry()
            self.client.append_rows(self._sheet_id, self._sheet_name, [new_entry])
            has_updated = True
        self._load()
        return new_entry[0]

    # Main
    def license_check(self) -> None:
        """Check if activated in sheet"""
        df = self._df
        id = self._get_device_online()

        try:
            for x in df:
                if x.id == id:
                    active_status = x.active
            if not active_status:
                raise SystemExit("Not activated")
            return None
        except Exception:
            raise SystemExit("Not activated")

    # Classmethod
    @classmethod
    def from_service_account(
        cls, service_account_data: str | Path | dict[str, str], sheet_id: str, sheet_name: str = "Sheet1"
    ) -> Self:
        """
        Google sheet online license system instance

        Parameters
        ----------
        service_account_data : str | Path | dict[str, str]
            Path to ``service_account.json`` file or .json loaded data

        sheet_id : str
            Sheet ID

        sheet_name : str, optional
            Sheet name, by default ``"Sheet1"``
        """
        client = GoogleSheet(service_account_data)
        return cls(client, sheet_id, sheet_name)
