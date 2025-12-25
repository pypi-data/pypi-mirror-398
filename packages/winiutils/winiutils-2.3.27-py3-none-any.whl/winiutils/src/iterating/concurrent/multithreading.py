"""Multithreading utilities for I/O-bound parallel execution.

This module provides functions for parallel processing using thread pools.
It includes utilities for handling thread pools, managing futures, and
organizing parallel execution of I/O-bound tasks.

Use multithreading for I/O-bound tasks such as network requests, file
operations, or database queries where threads spend most of their time
waiting for external resources.

Example:
    >>> from winiutils.src.iterating.concurrent.multithreading import (
    ...     multithread_loop,
    ... )
    >>> def fetch_url(url):
    ...     import requests
    ...     return requests.get(url).status_code
    >>> results = multithread_loop(
    ...     process_function=fetch_url,
    ...     process_args=[["https://example.com"], ["https://google.com"]],
    ...     process_args_len=2,
    ... )
"""

from collections.abc import Callable, Generator, Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any

from winiutils.src.iterating.concurrent.concurrent import concurrent_loop


def get_future_results_as_completed(
    futures: Iterable[Future[Any]],
) -> Generator[Any, None, None]:
    """Yield future results as they complete.

    Yields results from futures in the order they complete, not in the
    order they were submitted. This allows processing results as soon as
    they're available.

    Args:
        futures: Iterable of Future objects to get results from.

    Yields:
        The result of each completed future.

    Example:
        >>> with ThreadPoolExecutor() as executor:
        ...     futures = [executor.submit(square, i) for i in range(3)]
        ...     for result in get_future_results_as_completed(futures):
        ...         print(result)
    """
    for future in as_completed(futures):
        yield future.result()


def multithread_loop(
    process_function: Callable[..., Any],
    process_args: Iterable[Iterable[Any]],
    process_args_static: Iterable[Any] | None = None,
    process_args_len: int = 1,
) -> list[Any]:
    """Execute a function in parallel using ThreadPoolExecutor.

    Executes the given function with the provided arguments in parallel
    using ThreadPoolExecutor, which is suitable for I/O-bound tasks.

    Args:
        process_function: The function to execute in parallel.
        process_args: Iterable of argument lists for each parallel call.
            Each inner iterable contains the arguments for one function
            call. Example: ``[["url1"], ["url2"], ["url3"]]``
        process_args_static: Optional constant arguments to append to each
            call. These are shared across all calls. Defaults to None.
        process_args_len: Length of ``process_args``. Used for progress bar
            and worker pool sizing. Defaults to 1.

    Returns:
        List of results from the function executions, in the original
        submission order.

    Note:
        Use ThreadPoolExecutor for I/O-bound tasks (network requests, file
        I/O, database queries). For CPU-bound tasks, use
        ``multiprocess_loop()`` instead.

    Example:
        >>> def download(url, timeout):
        ...     import requests
        ...     return requests.get(url, timeout=timeout).text
        >>> results = multithread_loop(
        ...     process_function=download,
        ...     process_args=[["https://example.com"], ["https://google.com"]],
        ...     process_args_static=[30],  # 30 second timeout for all
        ...     process_args_len=2,
        ... )
    """
    return concurrent_loop(
        threading=True,
        process_function=process_function,
        process_args=process_args,
        process_args_static=process_args_static,
        process_args_len=process_args_len,
    )


def imap_unordered(
    executor: ThreadPoolExecutor,
    func: Callable[..., Any],
    iterable: Iterable[Any],
) -> Generator[Any, None, None]:
    """Apply a function to each item in an iterable in parallel.

    Similar to ``multiprocessing.Pool.imap_unordered()``, this function
    submits all items to the executor and yields results as they complete.

    Args:
        executor: ThreadPoolExecutor to use for parallel execution.
        func: Function to apply to each item in the iterable.
        iterable: Iterable of items to apply the function to.

    Yields:
        Results of applying the function to each item, in completion order
        (not submission order).

    Example:
        >>> with ThreadPoolExecutor(max_workers=4) as executor:
        ...     for result in imap_unordered(executor, square, [1, 2, 3]):
        ...         print(result)
    """
    results = [executor.submit(func, item) for item in iterable]
    yield from get_future_results_as_completed(results)
