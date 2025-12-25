"""Concurrent processing utilities for parallel execution.

This module provides core functions for concurrent processing using both
multiprocessing and multithreading approaches. It includes utilities for
handling timeouts, managing process pools, and organizing parallel execution
of functions.

The main entry point is ``concurrent_loop()``, which provides a unified
interface for both threading and multiprocessing execution.

Example:
    >>> from winiutils.src.iterating.concurrent.concurrent import concurrent_loop
    >>> def square(x):
    ...     return x * x
    >>> results = concurrent_loop(
    ...     threading=True,
    ...     process_function=square,
    ...     process_args=[[1], [2], [3]],
    ...     process_args_len=3,
    ... )
    >>> results
    [1, 4, 9]
"""

import multiprocessing
import os
import threading
from collections.abc import Callable, Generator, Iterable
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from tqdm import tqdm

from winiutils.src.iterating.iterate import get_len_with_default

if TYPE_CHECKING:
    from multiprocessing.pool import Pool

import logging

logger = logging.getLogger(__name__)


def get_order_and_func_result(
    func_order_args: tuple[Any, ...],
) -> tuple[int, Any]:
    """Execute a function and return its result with order index.

    Helper function used with ``imap_unordered`` to execute a function with
    arguments unpacking while preserving the original order of results.

    Args:
        func_order_args: Tuple containing:
            - The function to be executed
            - The order index (int)
            - The arguments for the function (unpacked)

    Returns:
        A tuple of (order_index, result) where order_index is the original
        position and result is the function's return value.
    """
    function, order, *args = func_order_args
    return order, function(*args)


def generate_process_args(
    *,
    process_function: Callable[..., Any],
    process_args: Iterable[Iterable[Any]],
    process_args_static: Iterable[Any] | None = None,
    deepcopy_static_args: Iterable[Any] | None = None,
) -> Generator[tuple[Any, ...], None, None]:
    """Prepare arguments for multiprocessing or multithreading execution.

    Converts input arguments into a format suitable for parallel processing,
    organizing them for efficient unpacking during execution.

    The function performs the following transformations:
        1. Prepends the process function and order index to each argument tuple
        2. Appends static arguments to each call
        3. Deep-copies specified arguments for each call (for mutable objects)

    Args:
        process_function: The function to be executed in parallel.
        process_args: Iterable of argument lists for each parallel call.
            Each inner iterable contains the arguments for one function call.
        process_args_static: Optional constant arguments to append to each
            call. These are shared across all calls without copying.
        deepcopy_static_args: Optional arguments that should be deep-copied
            for each process. Use this for mutable objects that should not
            be shared between processes.

    Yields:
        Tuples formatted as: (process_function, order_index, *args,
        *static_args, *deepcopied_args)

    Example:
        >>> def add(a, b, c):
        ...     return a + b + c
        >>> args = generate_process_args(
        ...     process_function=add,
        ...     process_args=[[1], [2]],
        ...     process_args_static=[10],
        ... )
        >>> list(args)
        [(add, 0, 1, 10), (add, 1, 2, 10)]
    """
    process_args_static = (
        () if process_args_static is None else tuple(process_args_static)
    )
    deepcopy_static_args = (
        () if deepcopy_static_args is None else tuple(deepcopy_static_args)
    )
    for order, process_arg in enumerate(process_args):
        yield (
            process_function,
            order,
            *process_arg,
            *process_args_static,
            *(
                deepcopy(deepcopy_static_arg)
                for deepcopy_static_arg in deepcopy_static_args
            ),
        )


def get_multiprocess_results_with_tqdm(
    results: Iterable[Any],
    process_func: Callable[..., Any],
    process_args_len: int,
    *,
    threads: bool,
) -> list[Any]:
    """Collect parallel execution results with progress tracking.

    Processes results from parallel execution with a tqdm progress bar and
    ensures they are returned in the original submission order.

    Args:
        results: Iterable of (order_index, result) tuples from parallel
            execution.
        process_func: The function that was executed in parallel. Used for
            the progress bar description.
        process_args_len: Total number of items being processed. Used for
            the progress bar total.
        threads: Whether threading (True) or multiprocessing (False) was
            used. Affects the progress bar description.

    Returns:
        List of results from parallel execution, sorted by original
        submission order.
    """
    results = tqdm(
        results,
        total=process_args_len,
        desc=f"Multi{'threading' if threads else 'processing'} {process_func}",
        unit=f" {'threads' if threads else 'processes'}",
    )
    results_list = list(results)
    # results list is a tuple of (order, result),
    # so we need to sort it by order to get the original order
    results_list = sorted(results_list, key=lambda x: x[0])
    # now extract the results from the tuple
    return [result[1] for result in results_list]


def find_max_pools(
    *,
    threads: bool,
    process_args_len: int | None = None,
) -> int:
    """Determine optimal number of workers for parallel execution.

    Calculates the maximum number of worker processes or threads based on
    system resources, currently active tasks, and the number of items to
    process.

    Args:
        threads: Whether to use threading (True) or multiprocessing (False).
            Threading allows up to 4x CPU count, while multiprocessing is
            limited to CPU count.
        process_args_len: Number of items to process in parallel. If
            provided, the result will not exceed this value.

    Returns:
        Maximum number of worker processes or threads to use. Always at
        least 1.

    Note:
        For threading, the maximum is ``cpu_count * 4`` minus active threads.
        For multiprocessing, the maximum is ``cpu_count`` minus active
        child processes.
    """
    # use tee to find length of process_args
    cpu_count = os.cpu_count() or 1
    if threads:
        active_tasks = threading.active_count()
        max_tasks = cpu_count * 4
    else:
        active_tasks = len(multiprocessing.active_children())
        max_tasks = cpu_count

    available_tasks = max_tasks - active_tasks
    max_pools = (
        min(available_tasks, process_args_len) if process_args_len else available_tasks
    )
    max_pools = max(max_pools, 1)

    logger.info(
        "Multi%s with max_pools: %s",
        "threading" if threads else "processing",
        max_pools,
    )

    return max_pools


def concurrent_loop(  # noqa: PLR0913
    *,
    threading: bool,
    process_function: Callable[..., Any],
    process_args: Iterable[Iterable[Any]],
    process_args_static: Iterable[Any] | None = None,
    deepcopy_static_args: Iterable[Any] | None = None,
    process_args_len: int = 1,
) -> list[Any]:
    """Execute a function concurrently with multiple argument sets.

    Core function that provides a unified interface for both multiprocessing
    and multithreading execution. This is the internal implementation used
    by ``multiprocess_loop()`` and ``multithread_loop()``.

    Args:
        threading: Whether to use threading (True) or multiprocessing
            (False). Use threading for I/O-bound tasks and multiprocessing
            for CPU-bound tasks.
        process_function: The function to execute concurrently. Must be
            pickle-able for multiprocessing.
        process_args: Iterable of argument lists for each parallel call.
            Each inner iterable contains the arguments for one function
            call.
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
        This function is not meant to be used directly. Use
        ``multiprocess_loop()`` for CPU-bound tasks or ``multithread_loop()``
        for I/O-bound tasks instead.
    """
    from winiutils.src.iterating.concurrent.multiprocessing import (  # noqa: PLC0415  # avoid circular import
        get_spwan_pool,
    )
    from winiutils.src.iterating.concurrent.multithreading import (  # noqa: PLC0415  # avoid circular import
        imap_unordered,
    )

    process_args_len = get_len_with_default(process_args, process_args_len)
    process_args = generate_process_args(
        process_function=process_function,
        process_args=process_args,
        process_args_static=process_args_static,
        deepcopy_static_args=deepcopy_static_args,
    )
    max_workers = find_max_pools(threads=threading, process_args_len=process_args_len)
    pool_executor = (
        ThreadPoolExecutor(max_workers=max_workers)
        if threading
        else get_spwan_pool(processes=max_workers)
    )
    with pool_executor as pool:
        map_func: Callable[[Callable[..., Any], Iterable[Any]], Any]

        if process_args_len == 1:
            map_func = map
        elif threading:
            pool = cast("ThreadPoolExecutor", pool)
            map_func = partial(imap_unordered, pool)
        else:
            pool = cast("Pool", pool)
            map_func = pool.imap_unordered

        results = map_func(get_order_and_func_result, process_args)

        return get_multiprocess_results_with_tqdm(
            results=results,
            process_func=process_function,
            process_args_len=process_args_len,
            threads=threading,
        )
