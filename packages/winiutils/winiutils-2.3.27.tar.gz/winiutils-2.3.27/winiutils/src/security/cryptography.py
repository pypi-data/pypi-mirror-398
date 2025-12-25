"""Cryptography utilities for secure data handling.

This module provides utility functions for working with cryptography,
including encryption and decryption using AES-GCM (Galois/Counter Mode).
AES-GCM provides both confidentiality and authenticity guarantees.

Example:
    >>> from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    >>> from winiutils.src.security.cryptography import (
    ...     encrypt_with_aes_gcm,
    ...     decrypt_with_aes_gcm,
    ... )
    >>> key = AESGCM.generate_key(bit_length=256)
    >>> aes_gcm = AESGCM(key)
    >>> encrypted = encrypt_with_aes_gcm(aes_gcm, b"secret message")
    >>> decrypted = decrypt_with_aes_gcm(aes_gcm, encrypted)
    >>> decrypted
    b'secret message'
"""

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

IV_LEN = 12
"""int: Length of the initialization vector (IV) in bytes.

AES-GCM requires a 12-byte (96-bit) IV for optimal performance and security.
"""


def encrypt_with_aes_gcm(
    aes_gcm: AESGCM, data: bytes, aad: bytes | None = None
) -> bytes:
    """Encrypt data using AES-GCM with a random initialization vector.

    Encrypts the provided data using AES-GCM and prepends a randomly
    generated 12-byte IV to the ciphertext. The IV is required for
    decryption.

    Args:
        aes_gcm: An initialized AESGCM cipher instance.
        data: The plaintext data to encrypt.
        aad: Optional additional authenticated data. This data is not
            encrypted but is authenticated, meaning any tampering will
            be detected during decryption.

    Returns:
        The encrypted data with the IV prepended. Format: ``IV + ciphertext``.

    Example:
        >>> key = AESGCM.generate_key(bit_length=256)
        >>> aes_gcm = AESGCM(key)
        >>> encrypted = encrypt_with_aes_gcm(aes_gcm, b"hello world")
        >>> len(encrypted) > len(b"hello world")  # IV + ciphertext + tag
        True

    Note:
        A new random IV is generated for each encryption call. Never reuse
        an IV with the same key.
    """
    iv = os.urandom(IV_LEN)
    encrypted = aes_gcm.encrypt(iv, data, aad)
    return iv + encrypted


def decrypt_with_aes_gcm(
    aes_gcm: AESGCM, data: bytes, aad: bytes | None = None
) -> bytes:
    """Decrypt data that was encrypted with AES-GCM.

    Extracts the IV from the beginning of the encrypted data and uses it
    to decrypt the ciphertext. Also verifies the authentication tag to
    ensure data integrity.

    Args:
        aes_gcm: An initialized AESGCM cipher instance with the same key
            used for encryption.
        data: The encrypted data with IV prepended (as returned by
            ``encrypt_with_aes_gcm``).
        aad: Optional additional authenticated data. Must match the AAD
            used during encryption, or decryption will fail.

    Returns:
        The decrypted plaintext data.

    Raises:
        cryptography.exceptions.InvalidTag: If the authentication tag is
            invalid, indicating the data was tampered with or the wrong
            key/AAD was used.

    Example:
        >>> key = AESGCM.generate_key(bit_length=256)
        >>> aes_gcm = AESGCM(key)
        >>> encrypted = encrypt_with_aes_gcm(aes_gcm, b"secret")
        >>> decrypt_with_aes_gcm(aes_gcm, encrypted)
        b'secret'
    """
    iv, encrypted = data[:IV_LEN], data[IV_LEN:]
    return aes_gcm.decrypt(iv, encrypted, aad)
