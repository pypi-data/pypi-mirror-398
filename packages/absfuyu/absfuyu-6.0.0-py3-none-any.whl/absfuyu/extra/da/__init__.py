"""
Absfuyu: Data Analysis
----------------------
Data Analyst

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "MatplotlibFormatString",
    "DADF",
    # Function
    "custom_pandas_settings",
    "reset_custom_pandas_settings",
]


# Library
# ---------------------------------------------------------------------------
DA_MODE = False

try:
    import numpy as np
    import openpyxl
    import pandas as pd
    import xlsxwriter
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[full]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[full] package")  # noqa: B904
else:
    DA_MODE = True

from absfuyu.extra.da.dadf import DADF
from absfuyu.extra.da.mplt import MatplotlibFormatString


# Function
# ---------------------------------------------------------------------------
def custom_pandas_settings(*, show_all_rows: bool = False) -> None:
    """
    Custom pandas settings. Currently only show all cols/rows

    Parameters
    ----------
    show_all_rows : bool, optional
        Show all rows, by default False
    """
    # Shows all columns
    pd.set_option("display.max_columns", None)  # type: ignore

    if show_all_rows:
        # (optional) also show all rows if needed
        pd.set_option("display.max_rows", None)  # type: ignore


def reset_custom_pandas_settings() -> None:
    """
    Reset custom pandas settings
    """
    settings = ["display.max_columns", "display.max_rows"]
    for x in settings:
        pd.reset_option(x)  # type: ignore
