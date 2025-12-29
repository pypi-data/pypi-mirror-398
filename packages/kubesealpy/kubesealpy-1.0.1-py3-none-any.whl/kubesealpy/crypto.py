"""
Low-level cryptographic operations for sealed secrets.

Implements hybrid encryption: RSA-OAEP (SHA-256) + AES-256-GCM
Compatible with Bitnami kubeseal format.
"""

import os
import struct

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .constants import AES_KEY_SIZE, AES_NONCE
from .exceptions import DecryptionError, EncryptionError, NoMatchingKeyError


def _create_oaep_padding(label: bytes) -> padding.OAEP:
    """
    Create OAEP padding with SHA-256 and the given label.

    Args:
        label: The label bytes for OAEP (scope-dependent)

    Returns:
        OAEP padding instance configured for kubeseal compatibility
    """
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=label if label else None,
    )


def encrypt(
    plaintext: bytes,
    public_key: RSAPublicKey,
    label: bytes = b"",
) -> bytes:
    """
    Encrypt data using hybrid RSA-OAEP + AES-GCM encryption.

    Output format: [2-byte length (big-endian)] | [RSA-encrypted session key] | [AES-GCM ciphertext]

    Args:
        plaintext: Data to encrypt
        public_key: RSA public key for encrypting the session key
        label: OAEP label for scope binding

    Returns:
        bytes: The encrypted payload in kubeseal format

    Raises:
        EncryptionError: If encryption fails
    """
    try:
        # Generate random 32-byte session key
        session_key = os.urandom(AES_KEY_SIZE)

        # Encrypt session key with RSA-OAEP
        oaep = _create_oaep_padding(label)
        encrypted_key = public_key.encrypt(session_key, oaep)

        # Encrypt plaintext with AES-GCM (zero nonce, single-use key)
        aesgcm = AESGCM(session_key)
        ciphertext = aesgcm.encrypt(AES_NONCE, plaintext, associated_data=None)

        # Build output: [2-byte length] | [encrypted key] | [ciphertext]
        length_bytes = struct.pack(">H", len(encrypted_key))

        return length_bytes + encrypted_key + ciphertext

    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt(
    ciphertext: bytes,
    private_key: RSAPrivateKey,
    label: bytes = b"",
) -> bytes:
    """
    Decrypt data encrypted with hybrid RSA-OAEP + AES-GCM.

    Input format: [2-byte length (big-endian)] | [RSA-encrypted session key] | [AES-GCM ciphertext]

    Args:
        ciphertext: The encrypted payload in kubeseal format
        private_key: RSA private key for decrypting the session key
        label: OAEP label for scope binding (must match encryption)

    Returns:
        bytes: The decrypted plaintext

    Raises:
        DecryptionError: If decryption fails (wrong key, wrong label, corrupted data)
    """
    try:
        if len(ciphertext) < 2:
            raise DecryptionError("Ciphertext too short: missing length header")

        # Extract encrypted key length
        key_length = struct.unpack(">H", ciphertext[:2])[0]

        if len(ciphertext) < 2 + key_length:
            raise DecryptionError("Ciphertext too short: incomplete encrypted key")

        # Split components
        encrypted_key = ciphertext[2 : 2 + key_length]
        aes_ciphertext = ciphertext[2 + key_length :]

        # Decrypt session key with RSA-OAEP
        oaep = _create_oaep_padding(label)
        session_key = private_key.decrypt(encrypted_key, oaep)

        # Decrypt data with AES-GCM
        aesgcm = AESGCM(session_key)
        plaintext = aesgcm.decrypt(AES_NONCE, aes_ciphertext, associated_data=None)

        return plaintext

    except DecryptionError:
        raise
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e


def decrypt_with_any_key(
    ciphertext: bytes,
    private_keys: list[RSAPrivateKey],
    label: bytes = b"",
) -> bytes:
    """
    Attempt decryption with multiple private keys.

    Useful for key rotation scenarios where multiple keys may be valid.

    Args:
        ciphertext: The encrypted payload
        private_keys: List of private keys to try
        label: OAEP label for scope binding

    Returns:
        bytes: The decrypted plaintext

    Raises:
        NoMatchingKeyError: If no key can decrypt the data
    """
    if not private_keys:
        raise NoMatchingKeyError("No private keys provided")

    errors: list[str] = []
    for key in private_keys:
        try:
            return decrypt(ciphertext, key, label)
        except DecryptionError as e:
            errors.append(str(e))

    raise NoMatchingKeyError(
        f"None of the {len(private_keys)} provided keys could decrypt the data. "
        f"Last error: {errors[-1]}"
    )
