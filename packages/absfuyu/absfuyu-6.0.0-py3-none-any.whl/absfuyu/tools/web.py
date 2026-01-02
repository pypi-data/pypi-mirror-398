"""
Absfuyu: Web
------------
Web, ``request``, ``BeautifulSoup`` stuff

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""


# Function
# ---------------------------------------------------------------------------
def soup_link(link: str):
    """
    ``BeautifulSoup`` the link

    Parameters
    ----------
    link : str
        Link to BeautifulSoup

    Returns
    -------
    BeautifulSoup
        ``BeautifulSoup`` instance
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        page = requests.get(link)
        soup = BeautifulSoup(page.content, "html.parser")
        return soup

    except ImportError:
        raise ImportError("Please install bs4, requests package")

    except Exception:
        raise SystemExit("Something wrong")  # noqa: B904


def gen_random_commit_msg() -> str:
    """
    Generate random commit message

    Returns
    -------
    str
        Random commit message
    """
    out = soup_link("https://whatthecommit.com/").get_text()[34:-20]
    return out  # type: ignore
