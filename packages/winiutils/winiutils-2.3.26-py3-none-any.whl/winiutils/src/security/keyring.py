"""Keyring utilities for secure storage and retrieval of secrets.

This module provides utility functions for working with the OS keyring,
including getting and creating cryptographic keys. Keys are stored
securely in the system's credential manager (e.g., macOS Keychain,
Windows Credential Manager, or Linux Secret Service).

When running in GitHub Actions, a plaintext keyring is used instead
since the system keyring is not available.

Example:
    >>> from winiutils.src.security.keyring import get_or_create_fernet
    >>> fernet, key_bytes = get_or_create_fernet("my_app", "encryption_key")
    >>> encrypted = fernet.encrypt(b"secret data")
    >>> fernet.decrypt(encrypted)
    b'secret data'
"""

from base64 import b64decode, b64encode
from collections.abc import Callable

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pyrig.src.git.git import running_in_github_actions

if running_in_github_actions():
    from keyrings.alt.file import PlaintextKeyring  # type: ignore[import-untyped]

    keyring.set_keyring(PlaintextKeyring())


def get_or_create_fernet(service_name: str, username: str) -> tuple[Fernet, bytes]:
    """Get or create a Fernet symmetric encryption key from the keyring.

    Retrieves an existing Fernet key from the system keyring, or generates
    a new one if it doesn't exist. The key is stored in the keyring for
    future use.

    Args:
        service_name: The service name to use for keyring storage. This
            identifies your application.
        username: The username/key identifier within the service.

    Returns:
        A tuple of (Fernet instance, raw key bytes). The Fernet instance
        can be used directly for encryption/decryption.

    Example:
        >>> fernet, key = get_or_create_fernet("my_app", "main_key")
        >>> encrypted = fernet.encrypt(b"hello")
        >>> fernet.decrypt(encrypted)
        b'hello'
    """
    return get_or_create_key(
        service_name, username, Fernet, lambda: Fernet.generate_key()
    )


def get_or_create_aes_gcm(service_name: str, username: str) -> tuple[AESGCM, bytes]:
    """Get or create an AES-GCM encryption key from the keyring.

    Retrieves an existing AES-GCM key from the system keyring, or generates
    a new 256-bit key if it doesn't exist. The key is stored in the keyring
    for future use.

    Args:
        service_name: The service name to use for keyring storage. This
            identifies your application.
        username: The username/key identifier within the service.

    Returns:
        A tuple of (AESGCM instance, raw key bytes). The AESGCM instance
        can be used with ``encrypt_with_aes_gcm`` and ``decrypt_with_aes_gcm``.

    Example:
        >>> aes_gcm, key = get_or_create_aes_gcm("my_app", "aes_key")
        >>> from winiutils.src.security.cryptography import encrypt_with_aes_gcm
        >>> encrypted = encrypt_with_aes_gcm(aes_gcm, b"secret")
    """
    return get_or_create_key(
        service_name, username, AESGCM, lambda: AESGCM.generate_key(bit_length=256)
    )


def get_or_create_key[T](
    service_name: str,
    username: str,
    key_class: Callable[[bytes], T],
    generate_key_func: Callable[..., bytes],
) -> tuple[T, bytes]:
    """Get or create a cryptographic key from the keyring.

    Generic function that retrieves an existing key from the system keyring,
    or generates a new one using the provided generator function if it
    doesn't exist.

    Args:
        service_name: The service name to use for keyring storage.
        username: The username/key identifier within the service.
        key_class: A callable that takes raw key bytes and returns a cipher
            instance (e.g., ``Fernet``, ``AESGCM``).
        generate_key_func: A callable that generates new raw key bytes.

    Returns:
        A tuple of (cipher instance, raw key bytes).

    Note:
        Keys are stored in the keyring as base64-encoded strings. The
        service name is modified to include the key class name to allow
        storing different key types for the same service/username.

    Example:
        >>> from cryptography.fernet import Fernet
        >>> cipher, key = get_or_create_key(
        ...     "my_app",
        ...     "custom_key",
        ...     Fernet,
        ...     Fernet.generate_key,
        ... )
    """
    key = get_key_as_str(service_name, username, key_class)
    if key is None:
        binary_key = generate_key_func()
        key = b64encode(binary_key).decode("ascii")
        modified_service_name = make_service_name(service_name, key_class)
        keyring.set_password(modified_service_name, username, key)

    binary_key = b64decode(key)
    return key_class(binary_key), binary_key


def get_key_as_str[T](
    service_name: str, username: str, key_class: Callable[[bytes], T]
) -> str | None:
    """Retrieve a key from the keyring as a base64-encoded string.

    Args:
        service_name: The service name used for keyring storage.
        username: The username/key identifier within the service.
        key_class: The key class used to modify the service name.

    Returns:
        The base64-encoded key string, or None if the key doesn't exist.
    """
    service_name = make_service_name(service_name, key_class)
    return keyring.get_password(service_name, username)


def make_service_name[T](service_name: str, key_class: Callable[[bytes], T]) -> str:
    """Create a unique service name by combining service name and key class.

    This allows storing different key types (Fernet, AESGCM, etc.) for the
    same service and username combination.

    Args:
        service_name: The base service name.
        key_class: The key class whose name will be appended.

    Returns:
        A modified service name in the format ``{service_name}_{class_name}``.

    Example:
        >>> make_service_name("my_app", Fernet)
        'my_app_Fernet'
    """
    return f"{service_name}_{key_class.__name__}"  # ty:ignore[unresolved-attribute]
