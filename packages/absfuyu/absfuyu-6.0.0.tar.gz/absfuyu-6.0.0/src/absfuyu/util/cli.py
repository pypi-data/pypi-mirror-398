"""
Absfuyu: CLI
------------
Custom Argument Parser

Version: 6.0.0
Date updated: 25/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["FuyuArgumentParser"]


# Library
# ---------------------------------------------------------------------------
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections.abc import Callable
from typing import Any


# Class
# ---------------------------------------------------------------------------
class FuyuArgumentParser(ArgumentParser):
    """
    Usage:
    ------
    >>> import sys
    >>> args = FuyuArgumentParser()
    >>> args.start()
    """

    def __init__(
        self,
        prog: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        version: str = "0.0.1",
        formatter_class: Any = ArgumentDefaultsHelpFormatter,
        prefix_chars: str = "-",
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
    ) -> None:
        # Desc
        if description is None:
            description = f"Absfuyu CLI {version}"

        # Default
        self._default_args = ["--help"]

        # Super
        super().__init__(
            prog=prog,
            description=description,
            epilog=epilog,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler,
            add_help=add_help,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
        )

        # Add version
        self.add_argument("-v", "--version", action="version", version=f"%(prog)s {version}")

        # Add log level
        _ll_val = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.add_argument(
            "-ll",
            "--log-level",
            metavar="LOG_LEVEL",
            dest="log_level",
            choices=_ll_val,
            default="ERROR",
            help=f"Log level: {', '.join(_ll_val)}",
        )

    def _fuyu_set_log_level(self, log_level: str = "ERROR") -> None:
        log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        logging.basicConfig(
            level=log_levels[log_level],
            format="[%(asctime)s] [%(module)s] [%(name)s] [%(funcName)s] [%(levelname)-s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def start(self, default: Callable[[], Any] | None = None):
        """
        Quick start for argument parser

        Parameters
        ----------
        default : Callable[[], Any] | None, optional
            | Default callable to run, by default ``None``
            | Shows help on default behavior (default=None)

        Returns
        -------
        Namespace
            Namespace
        """
        if default is None:
            args = self.parse_args(args=None if sys.argv[1:] else self._default_args)
        else:
            args = self.parse_args(args=None if sys.argv[1:] else default())
        self._fuyu_set_log_level(getattr(args, "log_level", "ERROR"))
        return args
