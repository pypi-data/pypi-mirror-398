"""
Absfuyu: Google related
-----------------------
Google Online license from sheet (DataFrame version)

Version: 6.0.0
Date updated: 28/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["GGSheetOnlineLicenseSystemDF"]


# Library
# ---------------------------------------------------------------------------
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Self, override

import pandas as pd

from absfuyu.extra.ggapi.glicense import GGSheetOnlineLicenseSystem
from absfuyu.extra.ggapi.gsheet import GoogleSheet

# Var
# ---------------------------------------------------------------------------
AVAILABLE_COLUMNS = ["stt", "hwid", "pc_name", "os", "date", "active"]


class DF_COL(StrEnum):
    TT = "stt"
    HWID = "hwid"
    NAME = "pc_name"
    OS = "OS"
    DATE = "date"
    ACTIVE = "active"


# Class
# ---------------------------------------------------------------------------
class GoogleSheetDF(GoogleSheet):
    # Sheets — READ (NO DOWNLOAD)
    # ------------------------------------------------------------------
    def read_sheet_as_dataframe(
        self,
        spreadsheet_id: str,
        sheet_name: str = "Sheet1",
        header: bool = True,
    ) -> pd.DataFrame:
        """
        Read Google Sheet directly into DataFrame.
        """
        result = (
            self.sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name,
                valueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )

        values = result.get("values", [])
        if not values:
            return pd.DataFrame()

        if header:
            return pd.DataFrame(values[1:], columns=values[0])

        return pd.DataFrame(values)

    # Sheets — APPEND
    # ------------------------------------------------------------------
    def append_dataframe(
        self,
        spreadsheet_id: str,
        range_: str,
        df: pd.DataFrame,
    ) -> None:
        self.append_rows(
            spreadsheet_id,
            range_,
            df.astype(object).where(pd.notnull(df), "").values.tolist(),
        )


type GoogleSheetClient = GoogleSheetDF


class GGSheetOnlineLicenseSystemDF(GGSheetOnlineLicenseSystem):
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
        self._df: pd.DataFrame | None = None
        try:
            self._load()
        except Exception:
            pass

    # Support
    @override
    def _load(self) -> None:
        df = self.client.read_sheet_as_dataframe(spreadsheet_id=self._sheet_id, sheet_name=self._sheet_name)
        self._df = df

    @override
    def _make_device_entry(self) -> list:
        df = self._df
        row = [int(df[DF_COL.TT].max()) + 1]
        row.extend(self._gather_system_info())
        row.extend([datetime.now().strftime("%d/%m/%Y"), False])
        return row

    @override
    def _get_device_online(self):
        """Get ID of device in sheet, create entry if None"""
        df = self._df
        id = df[df[DF_COL.HWID] == self.hwid][DF_COL.TT]

        has_updated = False  # safe guard
        if id is None or id.empty:
            if not has_updated:
                new_entry = self._make_device_entry()
                self.client.append_rows(self._sheet_id, self._sheet_name, [new_entry])
                has_updated = True
            self._load()
            return new_entry[0]

        return id.to_list()[0]

    # Main
    @override
    def license_check(self) -> None:
        """Check if activated in sheet"""
        df = self._df
        id = self._get_device_online()

        try:
            active_status = df[df[DF_COL.TT] == id][DF_COL.ACTIVE].to_list()[0]
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
        client = GoogleSheetDF(service_account_data)
        return cls(client, sheet_id, sheet_name)
