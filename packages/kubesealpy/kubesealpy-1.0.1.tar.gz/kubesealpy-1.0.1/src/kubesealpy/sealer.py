"""
Main Sealer class for creating SealedSecrets.

This is the primary public API for encrypting Kubernetes secrets.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from .certificate import (
    extract_public_key,
    load_certificate_from_cluster,
    load_certificate_from_file,
    load_certificate_from_pem,
    load_certificate_from_url_sync,
    validate_certificate,
)
from .constants import (
    ANNOTATION_CLUSTER_WIDE,
    ANNOTATION_NAMESPACE_WIDE,
    DEFAULT_CONTROLLER_NAME,
    DEFAULT_CONTROLLER_NAMESPACE,
)
from .crypto import encrypt
from .models import ObjectMeta, SealedSecret, SealedSecretSpec, Secret, SecretTemplateSpec
from .scopes import SealingScope, build_label


class Sealer:
    """
    Seals Kubernetes secrets using kubeseal-compatible encryption.

    Example usage:

        # From a certificate file
        sealer = Sealer.from_certificate_file("/path/to/cert.pem")

        # Seal a secret
        sealed = sealer.seal(
            name="my-secret",
            namespace="default",
            data={"password": b"supersecret"},
        )

        # Output as YAML
        print(sealed.to_yaml())
    """

    def __init__(
        self,
        public_key: RSAPublicKey,
        certificate: x509.Certificate | None = None,
    ):
        """
        Initialize the Sealer with a public key.

        Args:
            public_key: RSA public key for encryption
            certificate: Optional certificate (for metadata)
        """
        self._public_key = public_key
        self._certificate = certificate

    @classmethod
    def from_certificate_file(
        cls,
        path: str | Path,
        validate: bool = True,
    ) -> Sealer:
        """
        Create a Sealer from a PEM certificate file.

        Args:
            path: Path to the certificate file
            validate: Whether to validate certificate expiry

        Returns:
            Configured Sealer instance
        """
        cert, public_key = load_certificate_from_file(path, validate)
        return cls(public_key, cert)

    @classmethod
    def from_certificate_url(
        cls,
        url: str,
        validate: bool = True,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ) -> Sealer:
        """
        Create a Sealer by fetching a certificate from a URL.

        Args:
            url: URL to fetch the certificate from
            validate: Whether to validate certificate expiry
            timeout: Request timeout
            verify_ssl: Whether to verify SSL

        Returns:
            Configured Sealer instance
        """
        cert, public_key = load_certificate_from_url_sync(url, validate, timeout, verify_ssl)
        return cls(public_key, cert)

    @classmethod
    def from_certificate_pem(
        cls,
        pem_data: str | bytes,
        validate: bool = True,
    ) -> Sealer:
        """
        Create a Sealer from PEM certificate data.

        Args:
            pem_data: PEM-encoded certificate
            validate: Whether to validate certificate expiry

        Returns:
            Configured Sealer instance
        """
        cert = load_certificate_from_pem(pem_data)
        if validate:
            validate_certificate(cert)
        public_key = extract_public_key(cert)
        return cls(public_key, cert)

    @classmethod
    def from_cluster(
        cls,
        controller_name: str = DEFAULT_CONTROLLER_NAME,
        controller_namespace: str = DEFAULT_CONTROLLER_NAMESPACE,
        validate: bool = True,
    ) -> Sealer:
        """
        Create a Sealer by fetching the certificate from a Kubernetes cluster.

        Args:
            controller_name: Name of the sealed-secrets controller service
            controller_namespace: Namespace of the controller
            validate: Whether to validate certificate expiry

        Returns:
            Configured Sealer instance
        """
        cert, public_key = load_certificate_from_cluster(
            controller_name, controller_namespace, validate
        )
        return cls(public_key, cert)

    @property
    def public_key(self) -> RSAPublicKey:
        """The RSA public key used for encryption."""
        return self._public_key

    @property
    def certificate(self) -> x509.Certificate | None:
        """The X.509 certificate, if available."""
        return self._certificate

    def seal_value(
        self,
        value: bytes,
        namespace: str | None = None,
        name: str | None = None,
        scope: SealingScope = SealingScope.STRICT,
    ) -> bytes:
        """
        Seal a single value.

        Args:
            value: The plaintext value to encrypt
            namespace: Kubernetes namespace
            name: Secret name
            scope: Sealing scope

        Returns:
            bytes: The encrypted value
        """
        label = build_label(scope, namespace, name)
        return encrypt(value, self._public_key, label)

    def seal(
        self,
        name: str,
        namespace: str,
        data: dict[str, bytes],
        scope: SealingScope = SealingScope.STRICT,
        secret_type: str = "Opaque",
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
    ) -> SealedSecret:
        """
        Seal a Kubernetes secret.

        Args:
            name: Secret name
            namespace: Kubernetes namespace
            data: Dictionary of secret key-value pairs (raw bytes)
            scope: Sealing scope
            secret_type: Kubernetes secret type
            labels: Optional labels for the secret
            annotations: Optional annotations for the secret

        Returns:
            SealedSecret: The sealed secret resource
        """
        # Build scope-specific label
        label = build_label(scope, namespace, name)

        # Encrypt each value
        encrypted_data: dict[str, str] = {}
        for key, value in data.items():
            encrypted = encrypt(value, self._public_key, label)
            encrypted_data[key] = base64.b64encode(encrypted).decode("ascii")

        # Build annotations with scope
        result_annotations = dict(annotations) if annotations else {}
        if scope == SealingScope.CLUSTER_WIDE:
            result_annotations[ANNOTATION_CLUSTER_WIDE] = "true"
        elif scope == SealingScope.NAMESPACE_WIDE:
            result_annotations[ANNOTATION_NAMESPACE_WIDE] = "true"

        # Build template
        template = SecretTemplateSpec(
            type=secret_type,
            metadata=ObjectMeta(
                name=name,
                namespace=namespace,
                labels=labels,
                annotations=annotations,  # Original annotations on the resulting Secret
            ),
        )

        return SealedSecret(
            metadata=ObjectMeta(
                name=name,
                namespace=namespace,
                annotations=result_annotations if result_annotations else None,
            ),
            spec=SealedSecretSpec(
                encryptedData=encrypted_data,
                template=template,
            ),
        )

    def seal_secret(
        self,
        secret: Secret,
        scope: SealingScope = SealingScope.STRICT,
    ) -> SealedSecret:
        """
        Seal an existing Kubernetes Secret object.

        Args:
            secret: The Secret to seal
            scope: Sealing scope

        Returns:
            SealedSecret: The sealed secret resource
        """
        if secret.metadata.namespace is None:
            raise ValueError("Secret must have a namespace")

        data = secret.get_data_decoded()

        return self.seal(
            name=secret.metadata.name,
            namespace=secret.metadata.namespace,
            data=data,
            scope=scope,
            secret_type=secret.type,
            labels=secret.metadata.labels,
            annotations=secret.metadata.annotations,
        )
