---
sidebar_label: config
title: synapse_sdk.utils.storage.config
---

Storage configuration models using Pydantic v2.

## LocalStorageConfig Objects

```python
class LocalStorageConfig(BaseModel)
```

Configuration for local filesystem storage.

**Attributes**:

- `location` - Base directory path for storage operations.

## S3StorageConfig Objects

```python
class S3StorageConfig(BaseModel)
```

Configuration for S3-compatible storage (AWS S3, MinIO).

**Attributes**:

- `bucket_name` - S3 bucket name.
- `access_key` - AWS access key ID.
- `secret_key` - AWS secret access key.
- `region_name` - AWS region (default: us-east-1).
- `endpoint_url` - Custom endpoint for S3-compatible services (MinIO).

## GCSStorageConfig Objects

```python
class GCSStorageConfig(BaseModel)
```

Configuration for Google Cloud Storage.

**Attributes**:

- `bucket_name` - GCS bucket name.
- `credentials` - Path to service account JSON or credentials dict.
- `project` - GCP project ID (optional, inferred from credentials).

## SFTPStorageConfig Objects

```python
class SFTPStorageConfig(BaseModel)
```

Configuration for SFTP storage.

**Attributes**:

- `host` - SFTP server hostname.
- `username` - SSH username.
- `password` - SSH password (for password auth).
- `private_key` - Path to private key file (for key auth).
- `private_key_passphrase` - Passphrase for encrypted private key.
- `port` - SSH port (default: 22).
- `root_path` - Base path on remote server.

## HTTPStorageConfig Objects

```python
class HTTPStorageConfig(BaseModel)
```

Configuration for HTTP storage.

**Attributes**:

- `base_url` - Base URL of the HTTP file server.
- `timeout` - Request timeout in seconds.
- `headers` - Optional headers to include in requests.

## StorageConfig Objects

```python
class StorageConfig(BaseModel)
```

Top-level storage configuration model.

**Attributes**:

- `provider` - Storage provider type.
- `configuration` - Provider-specific configuration.
  

**Example**:

  >>> config = StorageConfig(
  ...     provider='s3',
  ...     configuration=\{
  ...         'bucket_name': 'my-bucket',
  ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
  ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
  ...     \}
  ... )

#### get\_typed\_config

```python
def get_typed_config() -> ProviderConfig
```

Get configuration as the appropriate typed model.

**Returns**:

  Typed configuration model based on provider.
  

**Raises**:

- `ValueError` - If provider is unknown.

