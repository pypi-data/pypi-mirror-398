"""
Absfuyu: Audio
--------------
Audio convert, lossless checker

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["StatusCode", "ResultStatus"]

# Library
# ---------------------------------------------------------------------------
from enum import StrEnum
from pathlib import Path

# Class Enum, Result
# ---------------------------------------------------------------------------
try:
    from rich import print

    class StatusCode(StrEnum):
        OK = "[bold green]OK[/]"
        SKIP = "[bold yellow]SKIP[/]"
        ERROR = "[bold red]ERROR[/]"
        LOSSLESS = "[bold green]LOSSLESS[/]"
        NOT_LOSSLESS = "[bold red]NOT LOSSLESS[/]"
        HIRES = "[bold blue]HIRES[/]"

except ImportError:

    class StatusCode(StrEnum):
        OK = "OK"
        SKIP = "SKIP"
        ERROR = "ERROR"
        LOSSLESS = "LOSSLESS"
        NOT_LOSSLESS = "NOT LOSSLESS"
        HIRES = "HIRES"


class ResultStatus:
    """
    Result status
    """

    def __init__(self, status: StatusCode, path: Path) -> None:
        self.status = status
        self.path = path

    def __repr__(self) -> str:
        return f"{self.status} : {self.path.name}"

    def print(self) -> None:
        """Print repr (for rich package)"""
        print(self.status, ": ", self.path.name)
