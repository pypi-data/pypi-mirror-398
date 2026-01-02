"""
Absfuyu: Beautiful
------------------
A decorator that makes output more beautiful

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "BeautifulOutput",
    "print",
]


# Library
# ---------------------------------------------------------------------------
import time
import tracemalloc
from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, NamedTuple, ParamSpec, TypeVar

BEAUTIFUL_MODE = False

try:
    from rich.align import Align
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:
        cmd = "python -m pip install -U absfuyu[beautiful]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[beautiful] package")  # noqa: B904
else:
    BEAUTIFUL_MODE = True

# Setup
# ---------------------------------------------------------------------------
# rich's console.print wrapper
console = Console(color_system="auto", tab_size=4)
print = console.print


# Type
# ---------------------------------------------------------------------------
P = ParamSpec("P")  # Parameter type
R = TypeVar("R")  # Return type - Can be anything
T = TypeVar("T", bound=type)  # Type type - Can be any subtype of `type`


# Class
# ---------------------------------------------------------------------------
class PerformanceOutput(NamedTuple):
    runtime: float
    current_memory: int
    peak_memory: int

    def to_text(self) -> str:
        """
        Beautify the result and ready to print
        """
        out = (
            f"Memory usage:      {self.current_memory / 10**6:,.6f} MB\n"
            f"Peak memory usage: {self.peak_memory / 10**6:,.6f} MB\n"
            f"Time elapsed:      {self.runtime:,.6f} s"
        )
        return out


# TODO: header and footer layout to 1,2,3 instead of true false
class BeautifulOutput:
    """A decorator that makes output more beautiful"""

    def __init__(
        self,
        layout: Literal[1, 2, 3, 4, 5, 6] = 1,
        include_header: bool = True,
        include_footer: bool = True,
        alternate_footer: bool = False,
    ) -> None:
        """
        Show function's signature and measure memory usage

        Parameters
        ----------
        layout : Literal[1, 2, 3, 4, 5, 6], optional
            Layout to show, by default ``1``

        include_header : bool, optional
            Include header with function's signature, by default ``True``

        include_footer : bool, optional
            Include footer, by default ``True``

        alternate_footer : bool, optional
            Alternative style of footer, by default ``False``


        Usage
        -----
        Use this as a decorator (``@BeautifulOutput(<parameters>)``)
        """
        self.layout = layout
        self.include_header = include_header
        self.include_footer = include_footer
        self.alternate_footer = alternate_footer

        # Data
        self._obj_name = ""
        self._signature = ""
        self._result: Any | None = None
        self._performance: PerformanceOutput | None = None

        # Setting
        self._header_footer_style = "white on blue"
        self._alignment = "center"

    def __call__(self, obj: Callable[P, R]) -> Callable[P, Group]:
        # Class wrapper
        if isinstance(obj, type):
            raise NotImplementedError("Classes are not supported")

        # Function wrapper
        @wraps(obj)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Group:
            """
            Wrapper function that executes the original function.
            """
            # Get all parameters inputed
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            self._signature = ", ".join(args_repr + kwargs_repr)
            self._obj_name = obj.__name__

            # Performance check
            tracemalloc.start()  # Start memory measure
            start_time = time.perf_counter()  # Start time measure

            self._result = obj(*args, **kwargs)  # Function run

            finish_time = time.perf_counter()  # Get finished time
            _cur, _peak = tracemalloc.get_traced_memory()  # Get memory stats
            tracemalloc.stop()  # End memory measure

            self._performance = PerformanceOutput(
                runtime=finish_time - start_time, current_memory=_cur, peak_memory=_peak
            )

            return self._get_layout(layout=self.layout)

        return wrapper

    # Signature
    def _func_signature(self) -> str:
        """Function's signature"""
        return f"{self._obj_name}({self._signature})"

    # Layout
    def _make_header(self) -> Table:
        header_table = Table.grid(expand=True)
        header_table.add_row(
            Panel(
                Align(f"[b]{self._func_signature()}", align=self._alignment),
                style=self._header_footer_style,
            )
        )
        return header_table

    def _make_line(self) -> Table:
        line = Table.grid(expand=True)
        line.add_row(Text("", style=self._header_footer_style))
        return line

    def _make_footer(self) -> Table:
        if self.alternate_footer:
            return self._make_line()

        footer_table = Table.grid(expand=True)
        footer_table.add_row(
            Panel(
                Align("[b]BeautifulOutput by absfuyu", align=self._alignment),
                style=self._header_footer_style,
            )
        )
        return footer_table

    def _make_result_panel(self) -> Panel:
        result_txt = Text(
            str(self._result),
            overflow="fold",
            no_wrap=False,
            tab_size=2,
        )
        result_panel = Panel(
            Align(result_txt, align=self._alignment),
            title="[bold]Result[/]",
            border_style="green",
            highlight=True,
        )
        return result_panel

    def _make_performance_panel(self) -> Panel:
        if self._performance is not None:
            performance_panel = Panel(
                Align(self._performance.to_text(), align=self._alignment),
                title="[bold]Performance[/]",
                border_style="red",
                highlight=True,
                # height=result_panel.height,
            )
            return performance_panel
        else:
            return Panel("None", title="[bold]Performance[/]")

    def _make_output(self) -> Table:
        out_table = Table.grid(expand=True)
        out_table.add_column(ratio=3)  # result
        out_table.add_column(ratio=2)  # performance

        out_table.add_row(
            self._make_result_panel(),
            self._make_performance_panel(),
        )
        return out_table

    def _get_layout(self, layout: int) -> Group:
        header = self._make_header() if self.include_header else Text()
        footer = self._make_footer() if self.include_footer else Text()
        layouts = {
            1: Group(header, self._make_output(), footer),
            2: Group(header, self._make_result_panel(), self._make_performance_panel()),
            3: Group(header, self._make_result_panel(), footer),
            4: Group(self._make_result_panel(), self._make_performance_panel()),
            5: Group(self._make_output()),
            6: Group(
                header,
                self._make_result_panel(),
                self._make_performance_panel(),
                footer,
            ),
        }
        return layouts.get(layout, layouts[1])
