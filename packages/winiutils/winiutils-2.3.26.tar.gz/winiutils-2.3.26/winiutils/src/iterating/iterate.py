"""Iterating utilities for handling iterables.

This module provides utility functions for working with iterables,
including getting the length of an iterable with a default value.
These utilities help with iterable operations and manipulations.
"""

from collections.abc import Iterable
from typing import Any


def get_len_with_default(iterable: Iterable[Any], default: int | None = None) -> int:
    """Get the length of an iterable, falling back to a default value.

    Attempts to get the length of an iterable using ``len()``. If the
    iterable doesn't support ``len()`` (e.g., generators), returns the
    provided default value instead.

    Args:
        iterable: The iterable to get the length of.
        default: Default value to return if the iterable doesn't support
            ``len()``. If None and the iterable doesn't support ``len()``,
            a TypeError is raised.

    Returns:
        The length of the iterable, or the default value if the iterable
        doesn't support ``len()``.

    Raises:
        TypeError: If the iterable doesn't support ``len()`` and no default
            value is provided.

    Example:
        >>> get_len_with_default([1, 2, 3])
        3
        >>> get_len_with_default((x for x in range(10)), default=10)
        10
    """
    try:
        return len(iterable)  # type: ignore[arg-type]
    except TypeError as e:
        if default is None:
            msg = "Can't get length of iterable and no default value provided"
            raise TypeError(msg) from e
        return default
