"""
Main Unsealer class for decrypting SealedSecrets.

This is the primary public API for decrypting sealed secrets.
Note: Unsealing typically happens on the cluster side (controller),
but this is useful for testing and offline operations.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from .certificate import load_private_key_from_file, load_private_keys_from_directory
from .crypto import decrypt_with_any_key
from .models import ObjectMeta, SealedSecret, Secret
from .scopes import SealingScope, build_label, scope_from_annotations


class Unsealer:
    """
    Unseals Kubernetes SealedSecrets.

    Example usage:

        # With a single private key
        unsealer = Unsealer.from_private_key_file("/path/to/key.pem")

        # Or with multiple keys (for rotation)
        unsealer = Unsealer.from_private_keys_directory("/path/to/keys/")

        # Unseal
        secret = unsealer.unseal(sealed_secret)
    """

    def __init__(self, private_keys: list[RSAPrivateKey]):
        """
        Initialize the Unsealer with private keys.

        Args:
            private_keys: List of RSA private keys (tries each in order)
        """
        if not private_keys:
            raise ValueError("At least one private key is required")
        self._private_keys = private_keys

    @classmethod
    def from_private_key(cls, private_key: RSAPrivateKey) -> Unsealer:
        """
        Create an Unsealer from a single private key.

        Args:
            private_key: RSA private key

        Returns:
            Configured Unsealer instance
        """
        return cls([private_key])

    @classmethod
    def from_private_key_file(
        cls,
        path: str | Path,
        password: bytes | None = None,
    ) -> Unsealer:
        """
        Create an Unsealer from a PEM private key file.

        Args:
            path: Path to the private key file
            password: Optional password for encrypted keys

        Returns:
            Configured Unsealer instance
        """
        key = load_private_key_from_file(path, password)
        return cls([key])

    @classmethod
    def from_private_keys_directory(
        cls,
        directory: str | Path,
        password: bytes | None = None,
        pattern: str = "*.pem",
    ) -> Unsealer:
        """
        Create an Unsealer from all private keys in a directory.

        Args:
            directory: Directory containing private key files
            password: Optional password for encrypted keys
            pattern: Glob pattern for key files

        Returns:
            Configured Unsealer instance
        """
        keys = load_private_keys_from_directory(directory, password, pattern)
        return cls(keys)

    @property
    def key_count(self) -> int:
        """Number of private keys available."""
        return len(self._private_keys)

    def unseal_value(
        self,
        encrypted_value: bytes,
        namespace: str | None = None,
        name: str | None = None,
        scope: SealingScope = SealingScope.STRICT,
    ) -> bytes:
        """
        Unseal a single encrypted value.

        Args:
            encrypted_value: The encrypted value (raw bytes, not base64)
            namespace: Kubernetes namespace
            name: Secret name
            scope: Sealing scope

        Returns:
            bytes: The decrypted value
        """
        label = build_label(scope, namespace, name)
        return decrypt_with_any_key(encrypted_value, self._private_keys, label)

    def unseal(
        self,
        sealed_secret: SealedSecret,
        scope: SealingScope | None = None,
    ) -> Secret:
        """
        Unseal a SealedSecret to a Secret.

        Args:
            sealed_secret: The SealedSecret to decrypt
            scope: Override scope detection from annotations

        Returns:
            Secret: The decrypted Kubernetes Secret
        """
        # Determine scope from annotations if not provided
        if scope is None:
            scope = scope_from_annotations(sealed_secret.metadata.annotations)

        name = sealed_secret.metadata.name
        namespace = sealed_secret.metadata.namespace

        # Build label for decryption
        label = build_label(scope, namespace, name)

        # Decrypt each value
        decrypted_data: dict[str, str] = {}
        for key, encrypted_b64 in sealed_secret.spec.encrypted_data.items():
            encrypted = base64.b64decode(encrypted_b64)
            plaintext = decrypt_with_any_key(encrypted, self._private_keys, label)
            # Store as base64 for the Secret
            decrypted_data[key] = base64.b64encode(plaintext).decode("ascii")

        # Get template metadata if available
        template = sealed_secret.spec.template
        secret_type = "Opaque"
        labels = None
        annotations = None

        if template:
            secret_type = template.type or "Opaque"
            if template.metadata:
                labels = template.metadata.labels
                annotations = template.metadata.annotations

        return Secret(
            metadata=ObjectMeta(
                name=name,
                namespace=namespace,
                labels=labels,
                annotations=annotations,
            ),
            type=secret_type,
            data=decrypted_data,
        )
