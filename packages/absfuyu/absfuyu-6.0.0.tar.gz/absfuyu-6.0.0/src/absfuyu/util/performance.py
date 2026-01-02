"""
Absfuyu: Performance
--------------------
Performance Check

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Feature:
--------
- measure_performance
- function_debug
- retry
- var_check
- Checker
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Wrapper
    "function_debug",
    "function_benchmark",
    "measure_performance",
    "retry",
    # Class
    "Checker",
]


# Library
# ---------------------------------------------------------------------------
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from inspect import getsource
from typing import Any, Literal, ParamSpec, TypeVar, overload

from absfuyu.core import deprecated, versionadded, versionchanged

# Type
# ---------------------------------------------------------------------------
P = ParamSpec("P")  # Parameter type
R = TypeVar("R")  # Return type


# Support
# ---------------------------------------------------------------------------
@dataclass
class BenchmarkResult:
    """
    Use ``format(BenchmarkResult(...), "seconds")`` to view result in seconds.
    """

    min_: float
    max_: float
    avg: float

    def __format__(self, format_spec: str) -> str:
        clsname = self.__class__.__name__
        if format_spec.lower().strip().startswith("seconds"):
            fields = [f"{x}={getattr(self, x):,.6f}s" for x in self._get_fields()]
            return f"{clsname}({', '.join(fields)})"
        return repr(self)

    @classmethod
    def _get_fields(cls) -> tuple[str, ...]:
        return tuple(cls.__dataclass_fields__)


# Function
# ---------------------------------------------------------------------------
@versionchanged("3.2.0", reason="Updated functionality")
def measure_performance(f: Callable[P, R]) -> Callable[P, R]:
    r"""
    Measure performance of a function

    Parameters
    ----------
    f : Callable [P, R]
        Function to measure

    Returns
    -------
    Callable
        A decorated function


    Usage
    -----
    Use this as a decorator (``@measure_performance``)

    Example:
    --------
    >>> @measure_performance
    >>> def test():
    ...     return 1 + 1
    >>> test()
        --------------------------------------
        Function: test
        Memory usage:		 0.000000 MB
        Peak memory usage:	 0.000000 MB
        Time elapsed (seconds):	 0.000002
        --------------------------------------

    """

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Performance check
        tracemalloc.start()  # Start memory measure
        start_time = time.perf_counter()  # Start time measure
        output = f(*args, **kwargs)  # Run function and save result into a variable
        current, peak = tracemalloc.get_traced_memory()  # Get memory stats
        finish_time = time.perf_counter()  # Get finished time
        tracemalloc.stop()  # End memory measure

        # Print output
        print(
            f"{'-' * 38}\n"
            f"Function: {f.__name__}\n"
            f"Memory usage:\t\t {current / 10**6:,.6f} MB\n"
            f"Peak memory usage:\t {peak / 10**6:,.6f} MB\n"
            f"Time elapsed (seconds):\t {finish_time - start_time:,.6f}\n"
            f"{'-' * 38}"
        )

        # Return
        return output

    return wrapper


@overload
def function_benchmark(func: Callable[P, R], /) -> Callable[P, R]: ...
@overload
def function_benchmark(*, n: int = 1) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
@overload
def function_benchmark(
    *, n: int = 1, result_only: Literal[False] = False
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
@overload
def function_benchmark(
    *, n: int = 1, result_only: Literal[True] = ...
) -> Callable[[Callable[P, R]], Callable[P, BenchmarkResult]]: ...


@versionadded("5.2.0")
def function_benchmark(
    func: Callable[P, R] | None = None, /, *, n: int = 1, result_only: bool = False
):
    """
    This run function for ``n`` times and calculate min, max, average runtime.

    Parameters
    ----------
    func : Callable[P, R] | None, optional
        Callable with parameter **P and returns R, by default ``None``

    n : int, optional
        Run how many times, by default ``1``

    result_only : bool, optional
        Returns BenchmarkResult instead of ``func`` result, by default ``False``


    Usage
    -----
    Use this as a decorator (``@function_benchmark``)

    Example:
    --------
    >>> @function_benchmark
    >>> def test():
    ...     return 1 + 1
    >>> test()
    BenchmarkResult(min_=0.000000s, max_=0.000000s, avg=0.000000s)
    2

    >>> @function_benchmark(n=1)
    >>> def test():
    ...     return 1 + 1
    >>> test()
    BenchmarkResult(min_=0.000000s, max_=0.000000s, avg=0.000000s)
    2
    """

    times = max(n, 1)

    def decorator(f: Callable[P, R]) -> Callable[P, R | BenchmarkResult]:
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | BenchmarkResult:
            output = f(*args, **kwargs)  # Run function and save result into a variable

            def _run() -> float:
                # Performance check
                start_time = time.perf_counter()  # Start time measure
                f(*args, **kwargs)
                finish_time = time.perf_counter()  # Get finished time
                return finish_time - start_time

            # run = (_run() for _ in range(times))
            run = [_run() for _ in range(times)]
            try:
                avg_runtime = sum(run) / len(run)
            except ZeroDivisionError:
                avg_runtime = min(run)
            result = BenchmarkResult(min(run), max(run), avg_runtime)

            if result_only:
                return result

            print(format(result, "seconds"))

            return output

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


@versionadded("3.2.0")
def function_debug(f: Callable[P, R]) -> Callable[P, R]:
    """
    Print the function signature and return value

    Parameters
    ----------
    func : Callable
        Function to debug

    Returns
    -------
    Callable
        A decorated function


    Usage
    -----
    Use this as a decorator (``@function_debug``)

    Example:
    --------
    >>> @function_debug
    >>> def test(a: int, b: int):
    ...     return a + b
    >>> test(6, 8)
    Calling test(6, 8)
    test() returned 14
    """

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Get all parameters inputed
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)

        # Output
        print(f"Calling {f.__name__}({signature})")
        # logger.debug(f"Calling {func.__name__}({signature})")
        value = f(*args, **kwargs)
        print(f"{f.__name__}() returned {repr(value)}")
        # logger.debug(f"{func.__name__}() returned {repr(value)}")
        return value

    return wrapper


@versionadded("3.2.0")
def retry(retries: int, delay: float = 1):
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    Parameters
    ----------
    retries : int
        The max amount of retries you want for the function call

    delay : int
        The delay (in seconds) between each function retry

    Returns
    -------
    Callable
        A decorated function


    Usage
    -----
    Use this as a decorator (``@retry``)

    Example:
    --------
    >>> @retry(retries=3, delay=1)
    >>> def test() -> None:
    ...     time.sleep(1)
    ...     raise Exception("Function error")
    >>> test()
    Running (1): test()
    Error: Exception('Function error') -> Retrying...
    Running (2): test()
    Error: Exception('Function error') -> Retrying...
    Running (3): test()
    Error: Exception('Function error').
    "test()" failed after 3 retries.
    """

    # Condition
    if retries < 1 or delay <= 0:
        raise ValueError("retries must be >= 1, delay must be >= 0")

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            for i in range(1, retries + 1):
                try:
                    print(f"Running ({i}): {f.__name__}()")
                    return f(*args, **kwargs)
                except Exception as e:
                    # Break out of the loop if the max amount of retries is exceeded
                    if i == retries:
                        print(f"Error: {repr(e)}.")
                        print(f'"{f.__name__}()" failed after {retries} retries.')
                        break
                    else:
                        print(f"Error: {repr(e)} -> Retrying...")
                        time.sleep(
                            delay
                        )  # Add a delay before running the next iteration

        return wrapper

    return decorator


# Class
# ---------------------------------------------------------------------------
@deprecated("5.1.0", reason="Use `absfuyu.tools.inspector` instead")
class Checker:
    """
    Check a variable

    Parameters
    ----------
    variable : Any
        Variable that needed to check


    Example:
    --------
    >>> test = "test"
    >>> Checker(test).check()
    {'name': None, 'value': 'test', 'class': <class 'str'>, 'id': ...}
    """

    def __init__(self, variable: Any) -> None:
        self.item_to_check = variable

    def __str__(self) -> str:
        return self.item_to_check.__str__()  # type: ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.item_to_check})"

    @property
    def name(self) -> Any | None:
        """``__name__`` of variable (if any)"""
        try:
            return self.item_to_check.__name__
        except Exception:
            return None

    @property
    def value(self) -> Any:
        """Value of the variable"""
        return self.item_to_check

    @property
    def docstring(self) -> str | None:
        """``__doc__`` of variable (if any)"""
        return self.item_to_check.__doc__  # type: ignore

    @property
    def class_(self) -> Any:
        """``class()`` of variable"""
        return type(self.item_to_check)

    @property
    def id_(self) -> int:
        """``id()`` of variable"""
        return id(self.item_to_check)

    @property
    def dir_(self) -> list[str]:
        """``dir()`` of variable"""
        # return self.item_to_check.__dir__()
        return [x for x in dir(self.item_to_check) if not x.startswith("__")]

    @property
    def source(self) -> str | None:
        """Source code of variable (if available)"""
        try:
            return getsource(self.item_to_check)
        except Exception:
            return None

    def check(self, full: bool = False) -> dict[str, Any]:
        """
        Check the variable

        Parameters
        ----------
        full : bool
            | ``True``: Shows full detail
            | ``False``: Hides ``dir``, ``docstring`` and source code
            | Default: ``False``

        Returns
        -------
        dict[str, Any]
            Check result
        """
        out = {
            "name": self.name,
            "value": self.value,
            "class": self.class_,
            "id": self.id_,
        }
        if full:
            out["dir"] = self.dir_
            out["docs"] = self.docstring
            out["source"] = self.source
        return out
