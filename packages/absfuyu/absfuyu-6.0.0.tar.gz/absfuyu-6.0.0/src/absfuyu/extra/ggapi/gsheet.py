"""
Absfuyu: Google related
-----------------------
Google Sheet

Version: 6.0.0
Date updated: 28/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["GoogleSheet"]


# Library
# ---------------------------------------------------------------------------
from typing import Any

from absfuyu.extra.ggapi.gdrive import GoogleDriveClient


# Class
# ---------------------------------------------------------------------------
class GoogleSheet(GoogleDriveClient):
    # Sheets — READ (NO DOWNLOAD)
    # ------------------------------------------------------------------
    def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str = "Sheet1",
        header: bool = True,
    ) -> list[list[Any]]:
        """
        Read Google Sheet directly.
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
        if values and header:
            return values[1:]

        return values

    # Sheets — APPEND
    # ------------------------------------------------------------------
    def append_rows(
        self,
        spreadsheet_id: str,
        range_: str,
        rows: list[list],
    ) -> None:
        """
        Append rows to Google Sheet.
        """
        self.sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()

    # Sheets — UPDATE
    # ------------------------------------------------------------------
    def update_range(
        self,
        spreadsheet_id: str,
        range_: str,
        values: list[list],
    ) -> None:
        """
        Update an existing cell range.
        """
        self.sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()
