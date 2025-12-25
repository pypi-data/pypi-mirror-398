"""String manipulation utilities for text processing.

This module provides utility functions for common string operations including:
    - User input with timeout constraints
    - XML namespace extraction
    - String truncation for logging
    - Deterministic hash generation

Example:
    >>> from winiutils.src.data.structures.text.string import (
    ...     value_to_truncated_string,
    ...     get_reusable_hash,
    ... )
    >>> value_to_truncated_string("Hello, World!", max_length=10)
    'Hello,...'
    >>> get_reusable_hash("test")  # doctest: +ELLIPSIS
    '9f86d08...'
"""

import hashlib
import logging
import textwrap
from io import StringIO

from defusedxml import ElementTree as DefusedElementTree

from winiutils.src.iterating.concurrent.multiprocessing import (
    cancel_on_timeout,
)

logger = logging.getLogger(__name__)


def ask_for_input_with_timeout(prompt: str, timeout: int) -> str:
    """Request user input with a timeout constraint.

    Displays a prompt to the user and waits for input. If the user does not
    provide input within the specified timeout period, a TimeoutError is raised.

    This function uses multiprocessing internally to enforce the timeout,
    so it spawns a separate process for the input operation.

    Args:
        prompt: The text prompt to display to the user before waiting for input.
        timeout: Maximum time in seconds to wait for user input.

    Returns:
        The user's input as a stripped string.

    Raises:
        multiprocessing.TimeoutError: If the user doesn't provide input within
            the timeout period.

    Example:
        >>> # This example would block waiting for input
        >>> # response = ask_for_input_with_timeout("Enter name: ", timeout=30)
    """

    @cancel_on_timeout(timeout, "Input not given within the timeout")
    def give_input() -> str:
        return input(prompt)

    user_input: str = give_input()

    return user_input


def find_xml_namespaces(xml: str | StringIO) -> dict[str, str]:
    """Extract namespace declarations from XML content.

    Parses the XML content and extracts all namespace prefix-to-URI mappings,
    excluding the default (empty prefix) namespace. Uses defusedxml for safe
    XML parsing to prevent XML-based attacks.

    Args:
        xml: XML content as a string or StringIO object. If a string is
            provided, it will be wrapped in a StringIO internally.

    Returns:
        A dictionary mapping namespace prefixes to their URIs. The default
        namespace (empty prefix) is excluded from the result.

    Example:
        >>> xml_content = '''<?xml version="1.0"?>
        ... <root xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        ... </root>'''
        >>> find_xml_namespaces(xml_content)
        {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
    """
    if not isinstance(xml, StringIO):
        xml = StringIO(xml)
    # Extract the namespaces from the root tag
    namespaces_: dict[str, str] = {}
    iter_ns = DefusedElementTree.iterparse(xml, events=["start-ns"])
    for _, namespace_data in iter_ns:
        prefix, uri = namespace_data
        namespaces_[str(prefix)] = str(uri)

    namespaces_.pop("", None)

    return namespaces_


def value_to_truncated_string(value: object, max_length: int) -> str:
    """Convert any value to a string and truncate if it exceeds the maximum length.

    Useful for logging or displaying values where space is limited. The string
    is truncated at word boundaries when possible, with "..." appended to
    indicate truncation.

    Args:
        value: Any object to convert to a string representation.
        max_length: Maximum length of the resulting string, including the
            ellipsis placeholder if truncation occurs.

    Returns:
        The string representation of the value, truncated to max_length
        characters if necessary with "..." as the truncation indicator.

    Example:
        >>> value_to_truncated_string("Hello, World!", max_length=10)
        'Hello,...'
        >>> value_to_truncated_string([1, 2, 3], max_length=20)
        '[1, 2, 3]'
    """
    string = str(value)
    return textwrap.shorten(string, width=max_length, placeholder="...")


def get_reusable_hash(value: object) -> str:
    """Generate a deterministic SHA-256 hash for any object.

    Creates a consistent hash based on the string representation of the given
    value. Unlike Python's built-in ``hash()`` function, this hash is:
        - Deterministic across Python sessions
        - Consistent across different machines
        - Suitable for caching, deduplication, or identification

    Args:
        value: Any object to hash. The object's ``__str__`` method is used
            to generate the string representation for hashing.

    Returns:
        A 64-character hexadecimal string representation of the SHA-256 hash.

    Note:
        Two objects with the same string representation will produce the same
        hash, even if they are different types or have different internal state.

    Example:
        >>> get_reusable_hash("test")
        '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
        >>> get_reusable_hash({"key": "value"})  # doctest: +ELLIPSIS
        '...'
    """
    value_str = str(value)
    return hashlib.sha256(value_str.encode("utf-8")).hexdigest()
