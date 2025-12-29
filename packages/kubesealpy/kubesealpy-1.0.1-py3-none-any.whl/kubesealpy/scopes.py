"""Sealing scope definitions and label generation."""

from __future__ import annotations

from enum import Enum

from .constants import ANNOTATION_CLUSTER_WIDE, ANNOTATION_NAMESPACE_WIDE


class SealingScope(Enum):
    """
    Defines the scope for sealed secret encryption.

    The scope determines what label is used in RSA-OAEP encryption,
    which binds the encrypted data to specific namespace/name constraints.
    """

    STRICT = "strict"  # Default: bound to namespace + name
    NAMESPACE_WIDE = "namespace-wide"  # Bound to namespace only
    CLUSTER_WIDE = "cluster-wide"  # No binding, can be used anywhere


def build_label(
    scope: SealingScope,
    namespace: str | None = None,
    name: str | None = None,
) -> bytes:
    """
    Build the OAEP label for the given scope.

    Args:
        scope: The sealing scope
        namespace: Kubernetes namespace (required for STRICT and NAMESPACE_WIDE)
        name: Secret name (required for STRICT)

    Returns:
        bytes: The label to use for RSA-OAEP encryption

    Raises:
        ValueError: If required parameters are missing for the scope
    """
    if scope == SealingScope.CLUSTER_WIDE:
        return b""

    if namespace is None:
        raise ValueError(f"namespace is required for scope {scope.value}")

    if scope == SealingScope.NAMESPACE_WIDE:
        return namespace.encode("utf-8")

    # STRICT scope
    if name is None:
        raise ValueError(f"name is required for scope {scope.value}")

    return f"{namespace}/{name}".encode()


def scope_from_annotations(annotations: dict[str, str] | None) -> SealingScope:
    """
    Determine the sealing scope from Kubernetes annotations.

    Args:
        annotations: Dictionary of Kubernetes annotations

    Returns:
        SealingScope: The determined scope (cluster-wide takes precedence)
    """
    if annotations is None:
        return SealingScope.STRICT

    # Cluster-wide takes precedence
    if annotations.get(ANNOTATION_CLUSTER_WIDE, "").lower() == "true":
        return SealingScope.CLUSTER_WIDE

    if annotations.get(ANNOTATION_NAMESPACE_WIDE, "").lower() == "true":
        return SealingScope.NAMESPACE_WIDE

    return SealingScope.STRICT
