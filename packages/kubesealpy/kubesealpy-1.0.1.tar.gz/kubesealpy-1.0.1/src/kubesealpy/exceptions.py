"""Custom exceptions for kubesealpy."""


class KubesealPyError(Exception):
    """Base exception for all kubesealpy errors."""

    pass


class EncryptionError(KubesealPyError):
    """Raised when encryption fails."""

    pass


class DecryptionError(KubesealPyError):
    """Raised when decryption fails."""

    pass


class CertificateError(KubesealPyError):
    """Raised when certificate operations fail."""

    pass


class CertificateExpiredError(CertificateError):
    """Raised when the certificate has expired."""

    pass


class CertificateNotYetValidError(CertificateError):
    """Raised when the certificate is not yet valid."""

    pass


class InvalidSealedSecretError(KubesealPyError):
    """Raised when a SealedSecret is malformed."""

    pass


class PrivateKeyError(KubesealPyError):
    """Raised when private key operations fail."""

    pass


class NoMatchingKeyError(DecryptionError):
    """Raised when no private key can decrypt the data."""

    pass
