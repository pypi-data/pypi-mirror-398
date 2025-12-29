"""
kubesealpy - Python library for Kubernetes Sealed Secrets.

Compatible with Bitnami's kubeseal/sealed-secrets project.
"""

from .exceptions import (
    CertificateError,
    CertificateExpiredError,
    DecryptionError,
    EncryptionError,
    KubesealPyError,
    NoMatchingKeyError,
    PrivateKeyError,
)
from .models import SealedSecret, Secret
from .scopes import SealingScope
from .sealer import Sealer
from .unsealer import Unsealer

__version__ = "0.1.0"

__all__ = [
    # Main API
    "Sealer",
    "Unsealer",
    "SealingScope",
    # Models
    "Secret",
    "SealedSecret",
    # Exceptions
    "KubesealPyError",
    "EncryptionError",
    "DecryptionError",
    "CertificateError",
    "CertificateExpiredError",
    "PrivateKeyError",
    "NoMatchingKeyError",
]
