"""Mixin utilities for class composition and behavior extension.

This module provides mixin classes that facilitate class composition through
the mixin pattern. It includes utilities for automatic method logging with
performance tracking.

These utilities help create robust class hierarchies with built-in logging
capabilities without requiring explicit decorator usage.

Example:
    >>> from winiutils.src.oop.mixins.mixin import ABCLoggingMixin
    >>> class MyService(ABCLoggingMixin):
    ...     def process(self, data):
    ...         return data.upper()
    >>> service = MyService()
    >>> service.process("hello")  # Logs method call automatically
    'HELLO'
"""

import logging

from winiutils.src.oop.mixins.meta import ABCLoggingMeta

logger = logging.getLogger(__name__)


class ABCLoggingMixin(metaclass=ABCLoggingMeta):
    """Mixin class that provides automatic method logging.

    This mixin can be used as a base class for any class that needs
    automatic method logging with performance tracking. All non-magic
    methods will be automatically wrapped with logging functionality.

    The logging includes:
        - Method name and class name
        - Arguments passed to the method (truncated)
        - Execution time
        - Return value (truncated)

    Inheriting from this class is equivalent to using ``ABCLoggingMeta``
    as the metaclass, but provides a cleaner inheritance syntax.

    Example:
        >>> class DataProcessor(ABCLoggingMixin):
        ...     def transform(self, data):
        ...         return [x * 2 for x in data]
        >>> processor = DataProcessor()
        >>> processor.transform([1, 2, 3])
        [2, 4, 6]
        # Logs: "DataProcessor - Calling transform with ..."
        # Logs: "DataProcessor - transform finished with 0.001 seconds -> ..."

    Note:
        - Magic methods (``__init__``, ``__str__``, etc.) are not logged.
        - Logging is rate-limited to once per second per method.
        - This class can be combined with abstract methods since it uses
          ``ABCLoggingMeta`` which extends ``ABCMeta``.
    """
