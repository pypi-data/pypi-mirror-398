"""
Absfuyu: Logger
---------------
Custom Logger Module

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # logger
    "logger",
    "AbsfuyuLogger",
    "compress_for_log",
    # log level
    "LogLevel",
    # Mixin
    "LoggerMixin",
    "AbsfuyuLoggerMixin",
]


# Library
# ---------------------------------------------------------------------------
import atexit
import datetime
import json
import logging
import math
import sys
from collections import Counter
from collections.abc import Callable
from logging.handlers import (
    QueueHandler,
    QueueListener,
    RotatingFileHandler,
    TimedRotatingFileHandler,
)
from pathlib import Path
from queue import Queue
from typing import Any, ClassVar, Self, override


# Setup
# ---------------------------------------------------------------------------
class LogLevel:
    """
    Python's ``logging`` module log level wrapper
    """

    NOTSET: int = logging.NOTSET
    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR
    CRITICAL: int = logging.CRITICAL

_LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


# Create a custom logger
# Temp logger - delete later
logger = logging.getLogger(__name__)


# Functions
# ---------------------------------------------------------------------------
def _compress_list_for_print(iterable: list, max_visible: int | None = 5) -> str:
    """
    Compress the list to be more log-readable

    iterable: list
    max_visible: Maximum items can be printed on screen (Minimum: 3)
    """

    if max_visible is None or max_visible <= 2:
        max_visible = 5

    if len(iterable) <= max_visible:
        return str(iterable)
    else:
        # logger.debug(f"Max vis: {max_visible}")
        if max_visible % 2 == 0:
            cut_idx_1 = math.floor(max_visible / 2) - 1
            cut_idx_2 = math.floor(max_visible / 2)
        else:
            cut_idx_1 = cut_idx_2 = math.floor(max_visible / 2)

        # logger.debug(f"Cut pos: {(cut_idx_1, cut_idx_2)}")
        # temp = [iterable[:cut_idx_1], ["..."], iterable[len(iterable)-cut_idx_2:]]
        # out = list(chain.from_iterable(temp))
        # out = [*iterable[:cut_idx_1], "...", *iterable[len(iterable)-cut_idx_2:]] # Version 2
        out = f"{str(iterable[:cut_idx_1])[:-1]}, ..., {str(iterable[len(iterable) - cut_idx_2 :])[1:]}"  # Version 3
        # logger.debug(out)
        return f"{out} [Len: {len(iterable)}]"


def _compress_string_for_print(text: str, max_visible: int | None = 120) -> str:
    """
    Compress the string to be more log-readable

    text: str
    max_visible: Maximum text can be printed on screen (Minimum: 5)
    """

    if max_visible is None or max_visible <= 5:
        max_visible = 120

    text = text.replace("\n", " ")  # Remove new line
    # logger.debug(text)

    if len(text) <= max_visible:
        return str(text)
    else:
        cut_idx = math.floor((max_visible - 3) / 2)
        temp = f"{text[:cut_idx]}...{text[len(text) - cut_idx :]}"
        return f"{temp} [Len: {len(text)}]"


def compress_for_log(object_: Any, max_visible: int | None = None) -> str:
    """
    Compress the object to be more log-readable

    :param object_: Object
    :param max_visible: Maximum objects can be printed on screen
    :returns: Compressed log output
    :rtype: str
    """

    if isinstance(object_, list):
        return _compress_list_for_print(object_, max_visible)

    elif isinstance(object_, (set, tuple)):
        return _compress_list_for_print(list(object_), max_visible)

    elif isinstance(object_, dict):
        temp = [{k: v} for k, v in object_.items()]
        return _compress_list_for_print(temp, max_visible)

    elif isinstance(object_, str):
        return _compress_string_for_print(object_, max_visible)

    else:
        try:
            return _compress_string_for_print(str(object_), max_visible)
        except Exception:
            return object_  # type: ignore


# Unused Class
# ---------------------------------------------------------------------------
class __CustomLogger:
    """
    DO NOT USE

    Custom logger [Incompleted, Remove soon]

    Create a custom logger

    *Useable but maybe unstable*
    """

    def __init__(
        self,
        name: str,
        cwd: str | Path = ".",
        log_format: str | None = None,
        *,
        save_log_file: bool = False,
        separated_error_file: bool = False,
        timed_log: bool = False,
        date_log_format: str | None = None,
        error_log_size: int = 1_000_000,  # 1 MB
    ) -> None:
        """
        :param name: Custom logger name
        :param cwd: Current working directory
        :param log_format: Log format
        :param save_log_file: Save logs to log file (default: False)
        :param separated_error_file: Save error logs into a separated file (Default: False)
        :param timed_log: Split log file every day. Requirement: `save_log_file = True` (Default: False)
        :param date_log_format: Date format in log
        :param error_log_size: Error log file max size (Default: 1 MB)
        """
        self._cwd = Path(cwd)
        self.log_folder = self._cwd.joinpath("logs")
        self.log_folder.mkdir(exist_ok=True, parents=True)  # Does not throw exception when folder existed
        self.name = name
        self.log_file = self.log_folder.joinpath(f"{name}.log")

        # Create a custom logger
        try:
            self.logger = logging.getLogger(self.name)
        except Exception:
            try:
                self.logger = logging.getLogger(__name__)
            except Exception:
                self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        if date_log_format is None:
            _date_format = "%Y-%m-%d %H:%M:%S"
        else:
            _date_format = date_log_format

        ## Console log handler
        if log_format is None:
            # Time|LogType|Function|LineNumber|Message
            _log_format = "%(asctime)s [%(levelname)5s] %(funcName)s:%(lineno)3d: %(message)s"
        else:
            _log_format = log_format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Minimum log level
        _console_log_format = _log_format  # Create formatters and add it to handlers
        _console_formatter = logging.Formatter(_console_log_format, datefmt=_date_format)
        console_handler.setFormatter(_console_formatter)
        self._console_handler = console_handler
        self.logger.addHandler(self._console_handler)  # Add handlers to the logger

        ## Log file handler
        if save_log_file:
            if log_format is None:
                # Time|LogType|FileName|Function|LineNumber|Message
                _log_format = "%(asctime)s [%(levelname)5s] %(filename)s:%(funcName)s:%(lineno)3d: %(message)s"
            else:
                _log_format = log_format
            file_handler = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            _file_log_format = _log_format
            _file_formatter = logging.Formatter(_file_log_format, datefmt=_date_format)
            file_handler.setFormatter(_file_formatter)
            self._file_handler = file_handler
            self.logger.addHandler(self._file_handler)

            if timed_log:
                ## Time handler (split log every day)
                time_handler = TimedRotatingFileHandler(
                    self.log_folder.joinpath(f"{self.name}_timed.log"),
                    when="midnight",
                    interval=1,
                    encoding="utf-8",
                )
                time_handler.setLevel(logging.DEBUG)
                time_handler.setFormatter(_file_formatter)
                self._time_handler = time_handler
                self.logger.addHandler(self._time_handler)
                # |   Value  |    Type of interval   |
                # |:--------:|:---------------------:|
                # |     S    |        Seconds        |
                # |     M    |        Minutes        |
                # |     H    |         Hours         |
                # |     D    |          Days         |
                # |     W    |  Week day (0=Monday)  |
                # | midnight | Roll over at midnight |

        ## Error and above log handler
        if separated_error_file:
            if log_format is None:
                # Time|LogType|FileName|Function|LineNumber|Message
                _log_format = "%(asctime)s [%(levelname)5s] %(filename)s:%(funcName)s:%(lineno)3d: %(message)s"
            else:
                _log_format = log_format
            error_handler = RotatingFileHandler(
                self.log_folder.joinpath(f"{self.name}_error.log"),
                maxBytes=error_log_size,
                backupCount=1,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(_log_format)  # type: ignore
            self._error_handler = error_handler
            self.logger.addHandler(self._error_handler)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def _add_logging_level(level_name: str, level_num: int, method_name: str | None = None):
        """
        Comprehensively adds a new logging level to the `logging` module and the
        currently configured logging class.

        `level_name` becomes an attribute of the `logging` module with the value
        `level_num`. `method_name` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present
        """
        # Original code: https://stackoverflow.com/a/35804945/1691778
        if not method_name:
            method_name = level_name.lower()

        if hasattr(logging, level_name):
            raise AttributeError(f"{level_name} already defined in logging module")
        if hasattr(logging, method_name):
            raise AttributeError(f"{method_name} already defined in logging module")
        if hasattr(logging.getLoggerClass(), method_name):
            raise AttributeError(f"{method_name} already defined in logger class")

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730, especially
        # http://stackoverflow.com/a/13638084/2988730
        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, **kwargs)

        def logToRoot(message, *args, **kwargs):
            logging.log(level_num, message, *args, **kwargs)

        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging.getLoggerClass(), method_name, logForLevel)
        setattr(logging, method_name, logToRoot)

    def add_log_level(self, level_name: str, level_num: int):
        __class__._add_logging_level(level_name, level_num)  # type: ignore
        if level_num < logging.DEBUG:
            self._console_handler.setLevel(level_num)
            self.logger.setLevel(level_num)


# Class
# ---------------------------------------------------------------------------
class _BasicJsonFormatter(logging.Formatter):
    """
    .json LogRecord

    *deprecated*
    """

    @override
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S"),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
        }
        return json.dumps(data)


class LoggingJSONFormatter(logging.Formatter):
    """
    JSONify log record to ``.jsonl`` file
    """

    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: (msg_val if (msg_val := always_fields.pop(val, None)) is not None else getattr(record, val))
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        # Get data from LogRecord
        # for key, val in record.__dict__.items():
        #     if key not in _LOG_RECORD_BUILTIN_ATTRS:
        #         message[key] = val
        for x in _LOG_RECORD_BUILTIN_ATTRS:
            v = getattr(record, x, None)
            if x not in message and v is not None:
                message[x] = v

        return message


class LogLevelUpperFilter(logging.Filter):
    """
    Filter ``LogRecord`` that <= ``filter_level``, by default: ``logging.WARNING``
    """

    def __init__(self, name: str = "", filter_level: int | str = LogLevel.WARNING) -> None:
        """
        Log level upper filter

        Parameters
        ----------
        name : str, optional
            Name of the filter, by default ``""``

        filter_level : int | str, optional
            Log level to to filter, by default ``logging.WARNING``

        Raises
        ------
        ValueError
            When type of ``filter_level`` is not ``<str>`` or ``<int>``
        """
        super().__init__(name)

        if isinstance(filter_level, str):
            log_level = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            new_filter_level = log_level.get(filter_level.strip().upper())
            self._filter_level = new_filter_level if new_filter_level is not None else logging.WARNING
        elif isinstance(filter_level, int):
            self._filter_level = filter_level
        else:
            raise ValueError("filter_level must type <str> or <int>")

    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= self._filter_level


class AbsfuyuLogger(logging.Logger):
    """
    Custom ``logging.Logger`` with prebuilt add handler method, and queue logging enabler

    Available handlers:
    - Stream
    - File
    - Rotating file
    - Timed file
    - Json

    Note:
    - Add format for formater with: ``add_log_format(...)``
    - Enable queue with: ``enable_queue``
    - Properties: ``available_log_format_style``, ``handlers_name_list``
    """

    _LOG_FORMAT: ClassVar[dict[str, str]] = {
        # Time|LogType|Function|LineNumber|Message
        "console": "%(asctime)s [%(levelname)8s] %(funcName)s:%(lineno)3d: %(message)s",
        # Time|LogType|FileName|Function|LineNumber|Message
        "file": "%(asctime)s [%(levelname)s] %(filename)s:%(module)s:%(funcName)s:%(lineno)3d: %(message)s",
    }

    def __init__(
        self,
        name: str,
        level: int = LogLevel.NOTSET,
        *,
        date_format: str | None = None,
        date_format_file: str | None = None,
    ) -> None:
        """
        Initialize the logger with a name and an optional level.
        (Custom version)

        Parameters
        ----------
        name : str
            Name of the logger

        level : int, optional
            Log level, by default ``logging.NOTSET``

        date_format : str | None, optional
            | Date format in log handler, by default ``None``
            | If ``date_format`` is not specified, ``"%Y-%m-%d %H:%M:%S"`` is used

        date_format_file : str | None, optional
            | Date format in log file handler, by default ``None``
            | If ``date_format`` is not specified, ``"%Y-%m-%dT%H:%M:%S%z"`` is used
        """
        super().__init__(name, level)

        # Extra
        self._cl_date_fmt = "%Y-%m-%d %H:%M:%S" if date_format is None else date_format
        self._cl_date_fmt_file = "%Y-%m-%dT%H:%M:%S%z" if date_format_file is None else date_format_file

    # Class method
    # --------------------------------
    @classmethod
    def default_config(cls, name: str, level: int = LogLevel.WARNING, /) -> Self:
        """
        Default configuration for this custom logger
        - 1 debug stream handler
        - 1 info-warning stream handler
        - 1 error-critical stream handler

        Parameters
        ----------
        name : str
            Name of the logger

        level : int, optional
            Log level, by default ``logging.NOTSET``

        Returns
        -------
        Self
            Custom logger
        """
        logger = cls(name=name, level=level)

        # Debug handler
        logger.add_stream_handler(
            name="handler_stream_debug",
            level=LogLevel.DEBUG,
            stream=sys.stdout,
            upper_bound_level=LogLevel.DEBUG,
        )

        # Info-Warning handler
        logger.add_stream_handler(
            name="handler_stream_normal",
            level=LogLevel.INFO,
            stream=sys.stdout,
            upper_bound_level=LogLevel.WARNING,
        )

        # Error-Critical handler
        logger.add_stream_handler(name="handler_stream_error", level=LogLevel.ERROR, stream=sys.stderr)
        return logger

    # Formater
    # --------------------------------
    @classmethod
    def add_log_format(cls, name: str, format: str) -> None:
        """
        Add a log format to use in ``logging.Formater`` for ``logging.Handler``

        Parameters
        ----------
        name : str
            Name of the format

        format : str
            Format string
        """
        cls._LOG_FORMAT[name] = format

    @property
    def available_log_format_style(self) -> list[str]:
        """
        Available log format style for ``logging.Formatter``
        """
        return list(self._LOG_FORMAT.keys())

    def _get_log_format(self, format_name: str, /) -> str:
        default = "%(asctime)s [%(levelname)5s] %(funcName)s:%(lineno)3d: %(message)s"
        return self._LOG_FORMAT.get(format_name, default)

    # Handlers
    # --------------------------------
    def _handle_log_handler(
        self,
        handler: logging.Handler,
        name: str | None,
        format_name: str,
        level: int,
        upper_bound_level: int | None = None,
        overwrite_date_format: str | None = None,
    ) -> logging.Handler:
        """
        Handle handler configuration

        Parameters
        ----------
        handler : logging.Handler
            Handler to config

        name : str | None
            Name of the handler

        format_name : str
            | LogFormater to use
            | Default options: ``console``, ``file``

        level : int
            Log level

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level

        overwrite_date_format : str | None, optional
            Overwrite the date format for formater, by default ``None``

        Returns
        -------
        logging.Handler
            Handler
        """

        # Set name
        if name is not None:
            handler.set_name(name)

        # Set level
        handler.setLevel(level)

        # Filter
        dt_fmt = self._cl_date_fmt
        if isinstance(
            handler,
            (RotatingFileHandler, TimedRotatingFileHandler, logging.FileHandler),
        ):
            dt_fmt = self._cl_date_fmt_file
        if overwrite_date_format is not None:
            dt_fmt = overwrite_date_format
        fmt = logging.Formatter(self._get_log_format(format_name), datefmt=dt_fmt)
        handler.setFormatter(fmt)

        # Upperbound
        if upper_bound_level is not None:
            log_filter = LogLevelUpperFilter(filter_level=upper_bound_level)
            handler.addFilter(log_filter)

        return handler

    @property
    def handlers_name_list(self) -> Counter:
        """
        List of handlers available in the logger

        Returns
        -------
        Counter
            List of handlers
        """
        # out = {}
        # for x in self.handlers:
        #     out.setdefault(x.name, 0)
        #     out[x.name] += 1
        # return out
        return Counter(x.name for x in self.handlers)

    def add_stream_handler(
        self,
        name: str | None = None,
        format_name: str = "console",
        level: int = LogLevel.NOTSET,
        *,
        stream: Any | None = None,
        upper_bound_level: int | None = None,
        overwrite_date_format: str | None = None,
    ) -> None:
        """
        Add stream handler for logger

        Parameters
        ----------
        name : str | None, optional
            Name of the handler, by default ``None``

        format_name : str, optional
            | LogFormater to use, by default ``"console"``
            | Default options: ``console``, ``file``

        level : int, optional
            Log level, by default ``logging.NOTSET``

        stream : Any | None, optional
            | Stream to use, by default ``None``
            | If ``stream`` is not specified, ``sys.stderr`` is used.
            | Options: ``sys.stdout``, ``sys.stderr``, ...

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level

        overwrite_date_format : str | None, optional
            Overwrite the date format for formater, by default ``None``
        """
        st = sys.stderr if stream is None else stream
        handler = logging.StreamHandler(st)
        handler = self._handle_log_handler(
            handler=handler,
            name=name,
            format_name=format_name,
            level=level,
            upper_bound_level=upper_bound_level,
            overwrite_date_format=overwrite_date_format,
        )
        self.addHandler(handler)

    def add_file_handler(
        self,
        file_path: str | Path,
        name: str | None = None,
        format_name: str = "file",
        level: int = LogLevel.ERROR,
        *,
        upper_bound_level: int | None = None,
        overwrite_date_format: str | None = None,
    ) -> None:
        """
        Add file handler for logger

        Parameters
        ----------
        file_path : str | Path
            Path to log file

        name : str | None, optional
            Name of the handler, by default ``None``

        format_name : str, optional
            | LogFormater to use, by default ``"file"``
            | Default options: ``console``, ``file``

        level : int, optional
            Log level, by default ``logging.ERROR``

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level

        overwrite_date_format : str | None, optional
            Overwrite the date format for formater, by default ``None``
        """
        path = Path(file_path)
        handler = logging.FileHandler(str(path.resolve()), mode="a", encoding="utf-8")
        handler = self._handle_log_handler(
            handler=handler,
            name=name,
            format_name=format_name,
            level=level,
            upper_bound_level=upper_bound_level,
            overwrite_date_format=overwrite_date_format,
        )
        self.addHandler(handler)

    def add_rotating_file_handler(
        self,
        file_path: str | Path,
        name: str | None = None,
        format_name: str = "file",
        level: int = LogLevel.DEBUG,
        *,
        max_bytes: int = 5_000_000,
        backup_count: int = 5,
        upper_bound_level: int | None = None,
        overwrite_date_format: str | None = None,
    ) -> None:
        """
        Add rotating file handler for logger

        Parameters
        ----------
        file_path : str | Path
            Path to log file

        name : str | None, optional
            Name of the handler, by default ``None``

        format_name : str, optional
            | LogFormater to use, by default ``"file"``
            | Default options: ``console``, ``file``

        level : int, optional
            Log level, by default ``logging.DEBUG``

        max_bytes : int, optional
            | Max byte to rollover, by default ``0``
            | If ``max_bytes`` is zero, rollover never occurs.
            | Set to ``1_000_000`` for 1 MB

        backup_count : int, optional
            Number of backup file, by default ``0``

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level

        overwrite_date_format : str | None, optional
            Overwrite the date format for formater, by default ``None``
        """
        path = Path(file_path)
        handler = RotatingFileHandler(
            str(path.resolve()),
            mode="a",
            encoding="utf-8",
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        handler = self._handle_log_handler(
            handler=handler,
            name=name,
            format_name=format_name,
            level=level,
            upper_bound_level=upper_bound_level,
            overwrite_date_format=overwrite_date_format,
        )
        self.addHandler(handler)

    def add_timed_rotating_file_handler(
        self,
        file_path: str | Path,
        name: str | None = None,
        format_name: str = "file",
        level: int = LogLevel.DEBUG,
        *,
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 5,
        upper_bound_level: int | None = None,
        overwrite_date_format: str | None = None,
    ) -> None:
        """
        Add timed rotating file handler for logger

        Parameters
        ----------
        file_path : str | Path
            Path to log file

        name : str | None, optional
            Name of the handler, by default ``None``

        format_name : str, optional
            | LogFormater to use, by default ``"file"``
            | Default options: ``console``, ``file``

        level : int, optional
            Log level, by default ``logging.DEBUG``

        when : Literal["S", "M", "H", "D", "midnight", "W"] | str, optional
            When to rollover, by default ``"midnight"``
            - S - Seconds
            - M - Minutes
            - H - Hours
            - D - Days
            - midnight - roll over at midnight
            - W{0-6} - roll over on a certain day; 0 - Monday

        interval : int, optional
            Interval, by default ``1``

        backup_count : int, optional
            Number of backup file, by default ``0``

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level

        overwrite_date_format : str | None, optional
            Overwrite the date format for formater, by default ``None``
        """
        path = Path(file_path)
        handler = TimedRotatingFileHandler(
            str(path.resolve()),
            encoding="utf-8",
            when=when,
            interval=interval,
            backupCount=backup_count,
        )
        handler = self._handle_log_handler(
            handler=handler,
            name=name,
            format_name=format_name,
            level=level,
            upper_bound_level=upper_bound_level,
            overwrite_date_format=overwrite_date_format,
        )
        self.addHandler(handler)

    def add_json_file_handler(
        self,
        file_path: str | Path,
        name: str | None = None,
        level: int = LogLevel.ERROR,
        *,
        max_bytes: int = 0,
        backup_count: int = 0,
        upper_bound_level: int | None = None,
    ) -> None:
        """
        Add ``.jsonl`` file log handler for logger

        Parameters
        ----------
        file_path : str | Path
            Path to ``.jsonl`` log file

        name : str | None, optional
            Name of the handler, by default ``None``

        level : int, optional
            Log level, by default ``logging.ERROR``

        max_bytes : int, optional
            | Max byte to rollover, by default ``0``
            | If ``max_bytes`` is zero, rollover never occurs.
            | Set to ``1_000_000`` for 1 MB

        backup_count : int, optional
            Number of backup file, by default ``0``

        upper_bound_level : int | None, optional
            | Log level to cut off, by default ``None``
            | Eg: ``upper_bound_level=logging.ERROR`` to show logs upto ERROR level
        """
        path = Path(file_path)
        handler = RotatingFileHandler(
            str(path.resolve()),
            mode="a",
            encoding="utf-8",
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        handler.setLevel(level)
        if name is not None:
            handler.set_name(name)
        handler.setFormatter(LoggingJSONFormatter())
        if upper_bound_level is not None:
            log_filter = LogLevelUpperFilter(filter_level=upper_bound_level)
            handler.addFilter(log_filter)
        self.addHandler(handler)

    def enable_queue(self, listener_handlers: list[logging.Handler] | None = None) -> None:
        """
        Convert logger to async queue mode.

        Parameters
        ----------
        listener_handlers : list[logging.Handler] | None, optional
            | List of handlers the listener should write to, by default ``None``
            | If ``listener_handlers`` is not specified, all handlers are used.
        """

        # Get all available handlers
        if listener_handlers is None:
            listener_handlers = [h for h in self.handlers]

        self._queue = Queue()

        # Make listener
        self._listener = QueueListener(self._queue, *listener_handlers, respect_handler_level=True)

        # Replace existing handlers with Queue handler in self.handlers
        self._queue_handler = QueueHandler(self._queue)
        self._queue_handler.listener = self._listener
        self.remove_all_hanlders()
        self.addHandler(self._queue_handler)  # self.handlers = [self._queue_handler]

        # Log listener
        # self._listener.start()
        # atexit.register(self._listener.stop)  # Register to stop listening when exit
        self._queue_handler.listener.start()
        atexit.register(self._queue_handler.listener.stop)

    def remove_all_hanlders(self) -> None:
        """
        Remove all handlers for this logger
        """
        for x in self.handlers[:]:
            x.close()
            self.removeHandler(x)

    def remove_hander_by_name(self, handler_name: str | None, /) -> None:
        """
        Remove an existing handler by its name

        Parameters
        ----------
        handler_name : str | None
            Name of the handler
        """
        for x in self.handlers[:]:
            if x.name == handler_name:
                x.close()
                self.removeHandler(x)

    # Test
    # --------------------------------
    def test_logger(self) -> None:
        """
        Test the logger by logging message in every log level
        """
        # test = ["debug", "info", "warning", "error", "exception", "critical"]
        # for x in test:
        #     log_func = getattr(self, x)
        #     log_func(f"This is {'an'if x.startswith('e')else 'a'} {x} message")

        self.debug("This is a debug message")
        self.info("This is a info message")
        self.warning("This is a warning message")
        self.error("This is an error message")
        # self.exception("This is an exception message")
        self.critical("This is a critical message")


# Mixin
# ---------------------------------------------------------------------------
class LoggerMixin[LoggerLike: logging.Logger]:
    """
    Mixin providing a lazily-initialized logger.

    Attributes
    ----------
    CUSTOM_LOGGER : Callable[[str], LoggerLike] | None, optional
        Optional factory for creating a custom logger.

    LOGGER_NAME : str | None, optional
        Override default logger name.


    Example:
    --------
    >>> class Test(LoggerMixin[logging.Logger]):
    >>>     pass

    >>> class Test2(LoggerMixin[AbsfuyuLogger]):
    >>>     CUSTOM_LOGGER = AbsfuyuLogger
    >>>     LOGGER_NAME = "App"
    >>>     pass
    """

    CUSTOM_LOGGER: Callable[[str], LoggerLike] | None = None
    LOGGER_NAME: str | None = None

    # def __init__(self) -> None:
    #     self._logger: LoggerLike

    @property
    def logger(self) -> LoggerLike:
        if not hasattr(self, "_logger"):
            logger_name = self.__class__.__name__ if self.LOGGER_NAME is None else self.LOGGER_NAME
            if self.CUSTOM_LOGGER is None:
                self._logger = logging.getLogger(logger_name)
            else:
                self._logger = self.CUSTOM_LOGGER(logger_name)
        return self._logger


class AbsfuyuLoggerMixin(LoggerMixin[AbsfuyuLogger]):
    CUSTOM_LOGGER = AbsfuyuLogger


class _AbsfuyuLoggerLib(AbsfuyuLoggerMixin):
    """Logger for this library"""

    CUSTOM_LOGGER = AbsfuyuLogger.default_config
    LOGGER_NAME = "absfuyu"
