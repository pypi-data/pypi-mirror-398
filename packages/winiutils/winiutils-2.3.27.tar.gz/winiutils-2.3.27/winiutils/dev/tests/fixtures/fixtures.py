"""Fixtures for testing.

This module provides custom fixtures for pytest that can be pluued into tests
across the entire test suite.
All fixtures defined under the fixtures package are auto plugged in automatically
by pyrig via the pytest_plugins mechanism.
"""

from collections.abc import Callable, Iterator

import keyring
import pytest


@pytest.fixture
def keyring_cleanup() -> Iterator[Callable[[str, str], None]]:
    """Factory fixture to clean up keyring entries after test.

    Usage:
        def test_something(keyring_cleanup):
            keyring_cleanup("service_name", "username")
            # ... test code that creates keyring entries ...
    """
    entries: list[tuple[str, str]] = []

    def register(service_name: str, username: str) -> None:
        entries.append((service_name, username))

    yield register

    for service_name, username in entries:
        keyring.delete_password(service_name, username)
