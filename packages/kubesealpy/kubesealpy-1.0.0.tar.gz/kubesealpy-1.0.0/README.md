# kubesealpy

A Python library for sealing and unsealing Kubernetes secrets, compatible with [Bitnami's Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets).

## Features

- **Native Python implementation** - No dependency on the `kubeseal` CLI
- **Full compatibility** - Uses the same hybrid encryption (RSA-OAEP + AES-256-GCM) as kubeseal
- **Multiple certificate sources** - Load from files, URLs, or directly from a Kubernetes cluster
- **All sealing scopes** - Supports strict, namespace-wide, and cluster-wide scopes
- **Multi-key decryption** - Try multiple private keys for key rotation scenarios
- **Type-safe** - Full type hints and Pydantic models
- **CLI** - New CLI coming in 2006

## Installation

```bash
pip install kubesealpy
```


For development:
```bash
pip install kubesealpy[dev]
```

## Quick Start

### Sealing a Secret

```python
from kubesealpy import Sealer, SealingScope

# Create a sealer from a certificate file
sealer = Sealer.from_certificate_file("/path/to/cert.pem")

# Seal a secret
sealed = sealer.seal(
    name="my-secret",
    namespace="default",
    data={
        "username": b"admin",
        "password": b"supersecret",
    },
)

# Output as YAML (ready to apply to Kubernetes)
print(sealed.to_yaml())
```

Output:
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: my-secret
  namespace: default
spec:
  encryptedData:
    username: AgBz...
    password: AgCx...
  template:
    metadata:
      name: my-secret
      namespace: default
    type: Opaque
```

### Sealing from a Kubernetes Cluster

```python
from kubesealpy import Sealer, SealingScope

# Fetch the certificate directly from your cluster's sealed-secrets controller
sealer = Sealer.from_cluster(
    controller_name="my-sealed-secrets",
    controller_namespace="sealed-secrets",
)

# Seal a secret
sealed = sealer.seal(
    name="my-secret",
    namespace="default",
    data={"api-key": b"secret-api-key"},
)

print(sealed.to_yaml())
```

### Unsealing a Secret

```python
from kubesealpy import Unsealer, SealedSecret

# Create an unsealer from a private key
unsealer = Unsealer.from_private_key_file("/path/to/private-key.pem")

# Load and unseal
sealed = SealedSecret.from_yaml(open("sealed-secret.yaml").read())
secret = unsealer.unseal(sealed)

# Access the decrypted data
import base64
password = base64.b64decode(secret.data["password"])
print(password.decode())  # "supersecret"
```

## Certificate Sources

### From a File

```python
sealer = Sealer.from_certificate_file("/path/to/cert.pem")
```

### From a URL

```python
sealer = Sealer.from_certificate_url("https://example.com/cert.pem")
```

### From a Kubernetes Cluster

```python
# Uses your current kubeconfig context
sealer = Sealer.from_cluster()

# Or specify the controller location
sealer = Sealer.from_cluster(
    controller_name="sealed-secrets-controller",
    controller_namespace="kube-system",
)
```

### From PEM Data

```python
pem_data = open("cert.pem").read()
sealer = Sealer.from_certificate_pem(pem_data)
```

## Sealing Scopes

Sealed Secrets supports three scoping modes that determine where a secret can be unsealed:

### Strict (Default)

The secret is bound to both its name and namespace. It cannot be decrypted if either changes.

```python
sealed = sealer.seal(
    name="my-secret",
    namespace="production",
    data={"key": b"value"},
    scope=SealingScope.STRICT,
)
```

### Namespace-wide

The secret is bound only to its namespace. The name can change.

```python
sealed = sealer.seal(
    name="my-secret",
    namespace="production",
    data={"key": b"value"},
    scope=SealingScope.NAMESPACE_WIDE,
)
```

### Cluster-wide

The secret can be decrypted in any namespace with any name.

```python
sealed = sealer.seal(
    name="my-secret",
    namespace="production",
    data={"key": b"value"},
    scope=SealingScope.CLUSTER_WIDE,
)
```

## Working with Existing Secrets

You can seal an existing Kubernetes Secret object:

```python
from kubesealpy import Secret, Sealer

# Create a Secret object
secret = Secret.from_string_data(
    name="my-secret",
    namespace="default",
    data={
        "username": "admin",
        "password": "secret123",
    },
    secret_type="Opaque",
    labels={"app": "myapp"},
)

# Seal it
sealer = Sealer.from_certificate_file("cert.pem")
sealed = sealer.seal_secret(secret)
```

## Multi-Key Decryption

For key rotation scenarios, you can provide multiple private keys:

```python
# From a directory of key files
unsealer = Unsealer.from_private_keys_directory("/path/to/keys/")

# The unsealer will try each key until one works
secret = unsealer.unseal(sealed_secret)
```

## API Reference

### Sealer

| Method | Description |
|--------|-------------|
| `Sealer(public_key)` | Create from an RSA public key |
| `Sealer.from_certificate_file(path)` | Create from a PEM certificate file |
| `Sealer.from_certificate_url(url)` | Create by fetching a certificate from a URL |
| `Sealer.from_certificate_pem(data)` | Create from PEM certificate data |
| `Sealer.from_cluster()` | Create by fetching from a Kubernetes cluster |
| `seal(name, namespace, data, scope)` | Seal a secret |
| `seal_secret(secret, scope)` | Seal an existing Secret object |
| `seal_value(value, namespace, name, scope)` | Seal a single value |

### Unsealer

| Method | Description |
|--------|-------------|
| `Unsealer(private_keys)` | Create from a list of RSA private keys |
| `Unsealer.from_private_key(key)` | Create from a single private key |
| `Unsealer.from_private_key_file(path)` | Create from a PEM private key file |
| `Unsealer.from_private_keys_directory(dir)` | Create from all keys in a directory |
| `unseal(sealed_secret)` | Unseal a SealedSecret |
| `unseal_value(value, namespace, name, scope)` | Unseal a single value |

### Models

| Class | Description |
|-------|-------------|
| `Secret` | Kubernetes Secret resource |
| `SealedSecret` | Bitnami SealedSecret CRD |
| `SealingScope` | Enum: `STRICT`, `NAMESPACE_WIDE`, `CLUSTER_WIDE` |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `KubesealPyError` | Base exception for all kubesealpy errors |
| `EncryptionError` | Encryption operation failed |
| `DecryptionError` | Decryption operation failed |
| `CertificateError` | Certificate operation failed |
| `CertificateExpiredError` | Certificate has expired |
| `PrivateKeyError` | Private key operation failed |
| `NoMatchingKeyError` | No private key could decrypt the data |




## Development

```bash
# Clone the repository
git clone https://gitlab.com/nighthawk-oss/kubesealpy
cd kubesealpy

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=kubesealpy --cov-report=term-missing

# Type checking
mypy src/kubesealpy

# Linting
ruff check src/kubesealpy
```

## How It Works

kubesealpy implements the same hybrid encryption scheme as kubeseal:

1. **Session Key Generation**: A random 32-byte AES key is generated
2. **RSA Encryption**: The session key is encrypted using RSA-OAEP with SHA-256
3. **AES Encryption**: The secret data is encrypted using AES-256-GCM with the session key
4. **Label Binding**: A cryptographic label (based on scope) is included in RSA-OAEP to bind the ciphertext to specific namespace/name

The output format is:
```
[2-byte key length (big-endian)] | [RSA-encrypted session key] | [AES-GCM ciphertext]
```

## License

MIT License

## Related Projects

- [Bitnami Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) - The original project
- [kubeseal](https://github.com/bitnami-labs/sealed-secrets#kubeseal) - Official CLI tool

## Author
Brandon Handeland < pypi at unbuffered dot net >