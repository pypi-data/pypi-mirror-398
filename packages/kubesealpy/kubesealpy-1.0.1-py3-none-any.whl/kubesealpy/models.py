"""
Pydantic models for Kubernetes Secret and SealedSecret resources.
"""

from __future__ import annotations

import base64

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .constants import SEALED_SECRETS_API_VERSION, SEALED_SECRETS_KIND


class ObjectMeta(BaseModel):
    """Kubernetes ObjectMeta."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    namespace: str | None = None
    labels: dict[str, str] | None = None
    annotations: dict[str, str] | None = None


class SecretTemplateSpec(BaseModel):
    """Template for the generated Secret."""

    model_config = ConfigDict(populate_by_name=True)

    type: str | None = Field(default="Opaque")
    immutable: bool | None = None
    metadata: ObjectMeta | None = None
    data: dict[str, str] | None = None  # For templated values


class Secret(BaseModel):
    """Kubernetes Secret resource."""

    model_config = ConfigDict(populate_by_name=True)

    api_version: str = Field(default="v1", alias="apiVersion")
    kind: str = Field(default="Secret")
    metadata: ObjectMeta
    type: str = Field(default="Opaque")
    data: dict[str, str] | None = None  # Base64-encoded values
    string_data: dict[str, str] | None = Field(default=None, alias="stringData")

    def get_data_decoded(self) -> dict[str, bytes]:
        """Get secret data with base64 values decoded."""
        result: dict[str, bytes] = {}

        if self.data:
            for key, value in self.data.items():
                result[key] = base64.b64decode(value)

        if self.string_data:
            for key, value in self.string_data.items():
                result[key] = value.encode("utf-8")

        return result

    @classmethod
    def from_string_data(
        cls,
        name: str,
        namespace: str,
        data: dict[str, str],
        secret_type: str = "Opaque",
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
    ) -> Secret:
        """Create a Secret from string data (will be base64 encoded)."""
        return cls(
            metadata=ObjectMeta(
                name=name,
                namespace=namespace,
                labels=labels,
                annotations=annotations,
            ),
            type=secret_type,
            stringData=data,
        )

    def to_yaml(self) -> str:
        """Serialize to YAML format."""
        return yaml.dump(
            self.model_dump(by_alias=True, exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Secret:
        """Parse from YAML content."""
        data = yaml.safe_load(yaml_content)
        return cls.model_validate(data)


class SealedSecretSpec(BaseModel):
    """Spec for a SealedSecret."""

    model_config = ConfigDict(populate_by_name=True)

    encrypted_data: dict[str, str] = Field(alias="encryptedData")
    template: SecretTemplateSpec | None = None


class SealedSecret(BaseModel):
    """Bitnami SealedSecret CRD."""

    model_config = ConfigDict(populate_by_name=True)

    api_version: str = Field(default=SEALED_SECRETS_API_VERSION, alias="apiVersion")
    kind: str = Field(default=SEALED_SECRETS_KIND)
    metadata: ObjectMeta
    spec: SealedSecretSpec

    def to_yaml(self) -> str:
        """Serialize to YAML format."""
        return yaml.dump(
            self.model_dump(by_alias=True, exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> SealedSecret:
        """Parse from YAML content."""
        data = yaml.safe_load(yaml_content)
        return cls.model_validate(data)

    def get_encrypted_data(self) -> dict[str, bytes]:
        """Get encrypted data with base64 decoded."""
        return {key: base64.b64decode(value) for key, value in self.spec.encrypted_data.items()}
