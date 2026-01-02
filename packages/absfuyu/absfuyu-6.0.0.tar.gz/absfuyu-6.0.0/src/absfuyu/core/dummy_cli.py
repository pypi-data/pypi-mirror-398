"""
Absfuyu: Core
-------------
Dummy cli

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["cli"]


# Library
# ---------------------------------------------------------------------------
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from absfuyu import __title__, __version__


# Function
# ---------------------------------------------------------------------------
def get_parser(
    name: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
    *,
    version: str = "",
    add_help: bool = True,
    add_logging: bool = True,
) -> ArgumentParser:
    arg_parser = ArgumentParser(
        prog=name,
        description=description,
        epilog=epilog,
        add_help=add_help,
        formatter_class=ArgumentDefaultsHelpFormatter,
        # allow_abbrev=False, # Disable long options recognize
        # exit_on_error=True
    )
    arg_parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version}"
    )
    if add_logging:
        _ll_val = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        arg_parser.add_argument(
            "--log-level",
            metavar="LOG_LEVEL",
            dest="log_level",
            choices=_ll_val,
            default="INFO",
            help=f"Log level: {_ll_val}",
        )
    return arg_parser


def cli() -> None:
    desc = "This is a dummy cli, install <click> and <colorama> package to use this feature"
    arg_parser = get_parser(
        name=__title__,
        description=desc,
        version=__version__,
        add_logging=False,
    )
    args = arg_parser.parse_args(args=None if sys.argv[1:] else ["--help"])  # noqa
