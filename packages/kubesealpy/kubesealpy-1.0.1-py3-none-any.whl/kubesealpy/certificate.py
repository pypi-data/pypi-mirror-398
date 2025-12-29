"""
Certificate loading, parsing, and validation.

Supports loading from files, URLs, and Kubernetes cluster endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from .constants import (
    CERT_ENDPOINT_PATH,
    DEFAULT_CONTROLLER_NAME,
    DEFAULT_CONTROLLER_NAMESPACE,
)
from .exceptions import (
    CertificateError,
    CertificateExpiredError,
    CertificateNotYetValidError,
    PrivateKeyError,
)


def load_certificate_from_pem(pem_data: str | bytes) -> x509.Certificate:
    """
    Parse a PEM-encoded X.509 certificate.

    Args:
        pem_data: PEM-encoded certificate data

    Returns:
        x509.Certificate: The parsed certificate

    Raises:
        CertificateError: If parsing fails
    """
    if isinstance(pem_data, str):
        pem_data = pem_data.encode("utf-8")

    try:
        return x509.load_pem_x509_certificate(pem_data)
    except Exception as e:
        raise CertificateError(f"Failed to parse certificate: {e}") from e


def extract_public_key(certificate: x509.Certificate) -> RSAPublicKey:
    """
    Extract the RSA public key from a certificate.

    Args:
        certificate: X.509 certificate

    Returns:
        RSAPublicKey: The extracted public key

    Raises:
        CertificateError: If the key is not RSA
    """
    public_key = certificate.public_key()

    if not isinstance(public_key, RSAPublicKey):
        raise CertificateError(f"Expected RSA public key, got {type(public_key).__name__}")

    return public_key


def validate_certificate(
    certificate: x509.Certificate,
    check_expiry: bool = True,
    reference_time: datetime | None = None,
) -> None:
    """
    Validate a certificate's validity period.

    Args:
        certificate: Certificate to validate
        check_expiry: Whether to check expiration
        reference_time: Time to check against (defaults to now)

    Raises:
        CertificateExpiredError: If certificate has expired
        CertificateNotYetValidError: If certificate is not yet valid
    """
    if not check_expiry:
        return

    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    # Ensure reference_time is timezone-aware
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    not_before = certificate.not_valid_before_utc
    not_after = certificate.not_valid_after_utc

    if reference_time < not_before:
        raise CertificateNotYetValidError(f"Certificate not valid until {not_before.isoformat()}")

    if reference_time > not_after:
        raise CertificateExpiredError(f"Certificate expired on {not_after.isoformat()}")


def load_certificate_from_file(
    path: str | Path,
    validate: bool = True,
) -> tuple[x509.Certificate, RSAPublicKey]:
    """
    Load a certificate from a local file.

    Args:
        path: Path to PEM file
        validate: Whether to validate expiry

    Returns:
        Tuple of (certificate, public_key)

    Raises:
        CertificateError: If loading fails
    """
    path = Path(path)

    if not path.exists():
        raise CertificateError(f"Certificate file not found: {path}")

    try:
        pem_data = path.read_bytes()
    except OSError as e:
        raise CertificateError(f"Failed to read certificate file: {e}") from e

    cert = load_certificate_from_pem(pem_data)

    if validate:
        validate_certificate(cert)

    public_key = extract_public_key(cert)

    return cert, public_key


async def load_certificate_from_url(
    url: str,
    validate: bool = True,
    timeout: float = 30.0,
    verify_ssl: bool = True,
) -> tuple[x509.Certificate, RSAPublicKey]:
    """
    Fetch a certificate from an HTTP(S) URL.

    Args:
        url: URL to fetch certificate from
        validate: Whether to validate expiry
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Tuple of (certificate, public_key)

    Raises:
        CertificateError: If fetching or parsing fails
    """
    try:
        async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            pem_data = response.content
    except httpx.HTTPError as e:
        raise CertificateError(f"Failed to fetch certificate from {url}: {e}") from e

    cert = load_certificate_from_pem(pem_data)

    if validate:
        validate_certificate(cert)

    public_key = extract_public_key(cert)

    return cert, public_key


def load_certificate_from_url_sync(
    url: str,
    validate: bool = True,
    timeout: float = 30.0,
    verify_ssl: bool = True,
) -> tuple[x509.Certificate, RSAPublicKey]:
    """
    Synchronous version of load_certificate_from_url.

    Args:
        url: URL to fetch certificate from
        validate: Whether to validate expiry
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Tuple of (certificate, public_key)

    Raises:
        CertificateError: If fetching or parsing fails
    """
    try:
        with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            pem_data = response.content
    except httpx.HTTPError as e:
        raise CertificateError(f"Failed to fetch certificate from {url}: {e}") from e

    cert = load_certificate_from_pem(pem_data)

    if validate:
        validate_certificate(cert)

    public_key = extract_public_key(cert)

    return cert, public_key


def load_certificate_from_cluster(
    controller_name: str = DEFAULT_CONTROLLER_NAME,
    controller_namespace: str = DEFAULT_CONTROLLER_NAMESPACE,
    validate: bool = True,
) -> tuple[x509.Certificate, RSAPublicKey]:
    """
    Fetch a certificate from a Kubernetes cluster's sealed-secrets controller.

    Uses the Kubernetes Python client to access the controller's certificate endpoint.

    Args:
        controller_name: Name of the sealed-secrets controller service
        controller_namespace: Namespace of the controller
        validate: Whether to validate expiry

    Returns:
        Tuple of (certificate, public_key)

    Raises:
        CertificateError: If fetching or parsing fails
    """
    try:
        from kubernetes import client, config
    except ImportError as e:
        raise CertificateError(
            "kubernetes package is required for cluster certificate fetching. "
            "Install it with: pip install kubernetes"
        ) from e

    try:
        # Try in-cluster config first, then fall back to kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        v1 = client.CoreV1Api()

        # Use the service proxy to access the certificate endpoint
        pem_data = v1.connect_get_namespaced_service_proxy_with_path(
            name=controller_name,
            namespace=controller_namespace,
            path=CERT_ENDPOINT_PATH.lstrip("/"),
        )

        if isinstance(pem_data, str):
            pem_data = pem_data.encode("utf-8")

    except Exception as e:
        raise CertificateError(
            f"Failed to fetch certificate from cluster "
            f"({controller_namespace}/{controller_name}): {e}"
        ) from e

    cert = load_certificate_from_pem(pem_data)

    if validate:
        validate_certificate(cert)

    public_key = extract_public_key(cert)

    return cert, public_key


def load_private_key_from_pem(
    pem_data: str | bytes,
    password: bytes | None = None,
) -> RSAPrivateKey:
    """
    Load an RSA private key from PEM data.

    Args:
        pem_data: PEM-encoded private key
        password: Optional password for encrypted keys

    Returns:
        RSAPrivateKey: The loaded private key

    Raises:
        PrivateKeyError: If loading fails
    """
    if isinstance(pem_data, str):
        pem_data = pem_data.encode("utf-8")

    try:
        private_key = serialization.load_pem_private_key(pem_data, password=password)
    except Exception as e:
        raise PrivateKeyError(f"Failed to load private key: {e}") from e

    if not isinstance(private_key, RSAPrivateKey):
        raise PrivateKeyError(f"Expected RSA private key, got {type(private_key).__name__}")

    return private_key


def load_private_key_from_file(
    path: str | Path,
    password: bytes | None = None,
) -> RSAPrivateKey:
    """
    Load an RSA private key from a PEM file.

    Args:
        path: Path to PEM file
        password: Optional password for encrypted keys

    Returns:
        RSAPrivateKey: The loaded private key

    Raises:
        PrivateKeyError: If loading fails
    """
    path = Path(path)

    if not path.exists():
        raise PrivateKeyError(f"Private key file not found: {path}")

    try:
        pem_data = path.read_bytes()
    except OSError as e:
        raise PrivateKeyError(f"Failed to read private key file: {e}") from e

    return load_private_key_from_pem(pem_data, password)


def load_private_keys_from_directory(
    directory: str | Path,
    password: bytes | None = None,
    pattern: str = "*.pem",
) -> list[RSAPrivateKey]:
    """
    Load all RSA private keys from a directory.

    Args:
        directory: Directory to scan
        password: Optional password for encrypted keys
        pattern: Glob pattern for key files

    Returns:
        List of loaded private keys
    """
    directory = Path(directory)
    keys: list[RSAPrivateKey] = []

    for key_file in directory.glob(pattern):
        try:
            key = load_private_key_from_file(key_file, password)
            keys.append(key)
        except PrivateKeyError:
            # Skip files that aren't valid private keys
            continue

    return keys
