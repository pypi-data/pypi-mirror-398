"""
Absufyu: API
------------
Fetch data stuff

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "APIRequest",
    "ping_windows",
]


# Library
# ---------------------------------------------------------------------------
import json
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

from absfuyu.core.baseclass import BaseClass
from absfuyu.core.docstring import versionadded, versionchanged
from absfuyu.logger import logger

try:
    import requests
except ImportError:
    raise ImportError("Please install requests package")


# Function
# ---------------------------------------------------------------------------
class PingResult(NamedTuple):
    """
    Ping result

    Parameters
    ----------
    host : str
        Host name/IP

    result : str
        Ping result in ms
    """

    host: str
    result: str


@versionchanged("3.4.0", reason="Updated functionality")
@versionadded("2.5.0")
def ping_windows(host: list[str], ping_count: int = 3) -> list[PingResult]:
    """
    Ping web

    Parameters
    ----------
    host : list[str]
        List of host to ping

    ping_count : int
        Number of time to ping to take average
        (Default: ``3``)

    Returns
    -------
    list
        List of host with pinged value


    Example:
    --------
    >>> ping_windows(["1.1.1.1", "google.com"])
    ['1.1.1.1 : xxms', 'google.com : xxms']
    """
    out: list[PingResult] = []

    for ip in host:
        output = subprocess.run(
            f"ping {ip.strip()} -n {ping_count}",
            encoding="utf-8",
            capture_output=True,
            text=True,
        )
        logger.debug(output)

        data: str = "".join(output.stdout)
        res = re.findall(r"Average = (.*)", data)
        if res:
            out.append(PingResult(ip, res[0]))
        else:
            out.append(PingResult(ip, "FAILED"))

    return out


# Class
# ---------------------------------------------------------------------------
class APIRequest(BaseClass):
    """
    API data with cache feature

    Parameters
    ----------
    api_url : str
        API link

    encoding : str | None, optional
        Data encoding, by default ``"utf-8"``
    """

    def __init__(
        self,
        api_url: str,
        *,
        encoding: str | None = "utf-8",
    ) -> None:
        """
        Create APIRequest instance

        Parameters
        ----------
        api_url : str
            API link

        encoding : str | None, optional
            Data encoding, by default ``"utf-8"``
        """

        self.url = api_url
        self.encoding = encoding

    def fetch_data(self, *, update: bool = False, json_cache: str | Path):
        """
        Fetch data from an API then cache it for later use

        Parameters
        ----------
        update :
            Refresh the cache when ``True``
            (Default: ``False``)

        json_cache : Path | str
            Name of the cache

        Returns
        -------
        Any
           Data

        None
            No data fetched/unable to fetch data
        """
        if update:
            json_data = None
        else:
            try:
                with open(json_cache, "r", encoding=self.encoding) as file:
                    json_data = json.load(file)
                    logger.debug("Fetched data from local cache!")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.debug(f"No local cache found... ({e})")
                json_data = None

        if json_data is None:
            logger.debug("Fetching new json data... (Creating local cache)")
            try:
                json_data = requests.get(self.url).json()
                with open(json_cache, "w", encoding=self.encoding) as file:
                    json.dump(json_data, file, indent=2)
            except FileNotFoundError as e:
                logger.error(f"Can't create cache due to Path error - {e}")

        return json_data

    def fetch_data_only(self) -> requests.Response:
        """
        Fetch data without cache

        Returns
        -------
        Response
            ``requests.Response``
        """
        return requests.get(self.url)
