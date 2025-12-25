"""Multiprocessing utilities for CPU-bound parallel execution.

This module provides functions for parallel processing using Python's
multiprocessing module. It includes utilities for handling timeouts,
managing process pools, and organizing parallel execution of CPU-bound
functions.

Use multiprocessing for CPU-bound tasks that benefit from true parallelism
by bypassing Python's Global Interpreter Lock (GIL).

Example:
    >>> from winiutils.src.iterating.concurrent.multiprocessing import (
    ...     multiprocess_loop,
    ... )
    >>> def square(x):
    ...     return x * x
    >>> results = multiprocess_loop(
    ...     process_function=square,
    ...     process_args=[[1], [2], [3]],
    ...     process_args_len=3,
    ... )
    >>> results
    [1, 4, 9]
"""

import logging
import multiprocessing
from collections.abc import Callable, Iterable
from functools import wraps
from multiprocessing.pool import Pool
from typing import Any

from winiutils.src.iterating.concurrent.concurrent import concurrent_loop

logger = logging.getLogger(__name__)


def get_spwan_pool(*args: Any, **kwargs: Any) -> Pool:
    """Create a multiprocessing pool with the spawn context.

    Uses the 'spawn' start method which creates a fresh Python interpreter
    process. This is safer than 'fork' as it avoids issues with inherited
    file descriptors and locks.

    Args:
        *args: Positional arguments passed to ``Pool`` constructor.
        **kwargs: Keyword arguments passed to ``Pool`` constructor.

    Returns:
        A multiprocessing Pool configured with the spawn context.

    Example:
        >>> pool = get_spwan_pool(processes=4)
        >>> with pool:
        ...     results = pool.map(square, [1, 2, 3])
    """
    return multiprocessing.get_context("spawn").Pool(*args, **kwargs)


def cancel_on_timeout(seconds: float, message: str) -> Callable[..., Any]:
    """Create a decorator that cancels function execution on timeout.

    Creates a wrapper that executes the decorated function in a separate
    process and terminates it if execution time exceeds the specified
    timeout.

    Args:
        seconds: Maximum execution time in seconds before timeout.
        message: Error message to include in the warning log when timeout
            occurs.

    Returns:
        A decorator function that wraps the target function with timeout
        functionality.

    Raises:
        multiprocessing.TimeoutError: When function execution exceeds the
            timeout.

    Warning:
        Only works with functions that are pickle-able. This means it may
        not work as a decorator on methods or closures. Instead, use it as
        a wrapper function::

            my_func = cancel_on_timeout(
                seconds=2,
                message="Test timeout",
            )(my_func)

    Example:
        >>> def slow_function():
        ...     import time
        ...     time.sleep(10)
        ...     return "done"
        >>> timed_func = cancel_on_timeout(
        ...     seconds=1,
        ...     message="Function took too long",
        ... )(slow_function)
        >>> timed_func()  # Raises TimeoutError after 1 second
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            spawn_pool = get_spwan_pool(processes=1)
            with spawn_pool as pool:
                async_result = pool.apply_async(func, args, kwargs)
                try:
                    return async_result.get(timeout=seconds)
                except multiprocessing.TimeoutError:
                    logger.warning(
                        "%s -> Execution exceeded %s seconds: %s",
                        func,
                        seconds,
                        message,
                    )
                    raise
                finally:
                    pool.terminate()  # Ensure the worker process is killed
                    pool.join()  # Wait for cleanup

        return wrapper

    return decorator


def multiprocess_loop(
    process_function: Callable[..., Any],
    process_args: Iterable[Iterable[Any]],
    process_args_static: Iterable[Any] | None = None,
    deepcopy_static_args: Iterable[Any] | None = None,
    process_args_len: int = 1,
) -> list[Any]:
    """Execute a function in parallel using multiprocessing Pool.

    Executes the given function with the provided arguments in parallel
    using multiprocessing Pool, which is suitable for CPU-bound tasks.

    Args:
        process_function: The function to execute in parallel. Must be
            pickle-able.
        process_args: Iterable of argument lists for each parallel call.
            Each inner iterable contains the arguments for one function
            call. Example: ``[(1, 2), (3, 4), (5, 6)]``
        process_args_static: Optional constant arguments to append to each
            call. These are shared across all calls without copying.
            Defaults to None.
        deepcopy_static_args: Optional arguments that should be deep-copied
            for each process. Use this for mutable objects that should not
            be shared between processes. Defaults to None.
        process_args_len: Length of ``process_args``. Used for progress bar
            and worker pool sizing. Defaults to 1.

    Returns:
        List of results from the function executions, in the original
        submission order.

    Note:
        - Use multiprocessing for CPU-bound tasks as it bypasses Python's
          GIL by creating separate processes.
        - Multiprocessing is not safe for mutable objects; use
          ``deepcopy_static_args`` for mutable data.
        - If ConnectionErrors occur during debugging, try reducing the
          number of processes.
        - All functions and arguments must be pickle-able.

    Example:
        >>> def add(a, b, c):
        ...     return a + b + c
        >>> results = multiprocess_loop(
        ...     process_function=add,
        ...     process_args=[[1, 2], [3, 4]],
        ...     process_args_static=[10],
        ...     process_args_len=2,
        ... )
        >>> results
        [13, 17]
    """
    return concurrent_loop(
        threading=False,
        process_function=process_function,
        process_args=process_args,
        process_args_static=process_args_static,
        deepcopy_static_args=deepcopy_static_args,
        process_args_len=process_args_len,
    )
