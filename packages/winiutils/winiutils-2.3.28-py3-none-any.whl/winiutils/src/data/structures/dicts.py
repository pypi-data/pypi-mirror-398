"""Dictionary manipulation utilities.

This module provides utility functions for common dictionary operations
such as reversing key-value pairs.

Example:
    >>> from winiutils.src.data.structures.dicts import reverse_dict
    >>> original = {"a": 1, "b": 2}
    >>> reverse_dict(original)
    {1: 'a', 2: 'b'}
"""

from typing import Any


def reverse_dict(d: dict[Any, Any]) -> dict[Any, Any]:
    """Reverse the keys and values of a dictionary.

    Creates a new dictionary where the original values become keys and
    the original keys become values.

    Args:
        d: The dictionary to reverse. Values must be hashable to serve
            as keys in the resulting dictionary.

    Returns:
        A new dictionary with keys and values swapped from the original.

    Raises:
        TypeError: If any value in the input dictionary is not hashable.

    Warning:
        If the original dictionary contains duplicate values, only the last
        key-value pair for each value will be preserved in the result.

    Example:
        >>> reverse_dict({"name": "alice", "role": "admin"})
        {'alice': 'name', 'admin': 'role'}
    """
    return {v: k for k, v in d.items()}
