"""Constants and defaults for kubesealpy."""

from typing import Final

# Encryption parameters
AES_KEY_SIZE: Final[int] = 32  # 256 bits
AES_NONCE: Final[bytes] = b"\x00" * 12  # 96-bit zero nonce (single-use key)
RSA_KEY_SIZE: Final[int] = 4096

# SealedSecret API
SEALED_SECRETS_API_VERSION: Final[str] = "bitnami.com/v1alpha1"
SEALED_SECRETS_KIND: Final[str] = "SealedSecret"

# Scope annotations
ANNOTATION_CLUSTER_WIDE: Final[str] = "sealedsecrets.bitnami.com/cluster-wide"
ANNOTATION_NAMESPACE_WIDE: Final[str] = "sealedsecrets.bitnami.com/namespace-wide"

# Certificate endpoints
DEFAULT_CONTROLLER_NAMESPACE: Final[str] = "kube-system"
DEFAULT_CONTROLLER_NAME: Final[str] = "sealed-secrets-controller"
CERT_ENDPOINT_PATH: Final[str] = "/v1/cert.pem"
