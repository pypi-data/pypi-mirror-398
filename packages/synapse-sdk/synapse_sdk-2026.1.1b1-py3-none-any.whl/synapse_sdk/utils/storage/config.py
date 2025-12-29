"""Storage configuration models using Pydantic v2."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class LocalStorageConfig(BaseModel):
    """Configuration for local filesystem storage.

    Attributes:
        location: Base directory path for storage operations.
    """

    location: str = Field(..., description='Base directory path')

    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        if not v:
            raise ValueError('location cannot be empty')
        return v


class S3StorageConfig(BaseModel):
    """Configuration for S3-compatible storage (AWS S3, MinIO).

    Attributes:
        bucket_name: S3 bucket name.
        access_key: AWS access key ID.
        secret_key: AWS secret access key.
        region_name: AWS region (default: us-east-1).
        endpoint_url: Custom endpoint for S3-compatible services (MinIO).
    """

    bucket_name: str
    access_key: str
    secret_key: str
    region_name: str = 'us-east-1'
    endpoint_url: str | None = None


class GCSStorageConfig(BaseModel):
    """Configuration for Google Cloud Storage.

    Attributes:
        bucket_name: GCS bucket name.
        credentials: Path to service account JSON or credentials dict.
        project: GCP project ID (optional, inferred from credentials).
    """

    bucket_name: str
    credentials: str | dict[str, Any]
    project: str | None = None


class SFTPStorageConfig(BaseModel):
    """Configuration for SFTP storage.

    Attributes:
        host: SFTP server hostname.
        username: SSH username.
        password: SSH password (for password auth).
        private_key: Path to private key file (for key auth).
        private_key_passphrase: Passphrase for encrypted private key.
        port: SSH port (default: 22).
        root_path: Base path on remote server.
    """

    host: str
    username: str
    password: str | None = None
    private_key: str | None = None
    private_key_passphrase: str | None = None
    port: int = 22
    root_path: str = '/'

    @model_validator(mode='after')
    def validate_auth(self) -> SFTPStorageConfig:
        if not self.password and not self.private_key:
            raise ValueError('Either password or private_key must be provided')
        return self


class HTTPStorageConfig(BaseModel):
    """Configuration for HTTP storage.

    Attributes:
        base_url: Base URL of the HTTP file server.
        timeout: Request timeout in seconds.
        headers: Optional headers to include in requests.
    """

    base_url: str
    timeout: int = 30
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        # Ensure trailing slash
        return v if v.endswith('/') else f'{v}/'


# Type alias for all provider configurations
ProviderConfig = LocalStorageConfig | S3StorageConfig | GCSStorageConfig | SFTPStorageConfig | HTTPStorageConfig

# Provider type literals
ProviderType = Literal[
    'local',
    'file_system',  # alias for local (backward compat)
    's3',
    'amazon_s3',  # alias for s3
    'minio',  # alias for s3
    'gcs',
    'gs',  # alias for gcs
    'gcp',  # alias for gcs
    'sftp',
    'http',
    'https',  # alias for http
]


class StorageConfig(BaseModel):
    """Top-level storage configuration model.

    Attributes:
        provider: Storage provider type.
        configuration: Provider-specific configuration.

    Example:
        >>> config = StorageConfig(
        ...     provider='s3',
        ...     configuration={
        ...         'bucket_name': 'my-bucket',
        ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
        ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        ...     }
        ... )
    """

    provider: ProviderType
    configuration: dict[str, Any]

    def get_typed_config(self) -> ProviderConfig:
        """Get configuration as the appropriate typed model.

        Returns:
            Typed configuration model based on provider.

        Raises:
            ValueError: If provider is unknown.
        """
        config_map: dict[str, type[BaseModel]] = {
            'local': LocalStorageConfig,
            'file_system': LocalStorageConfig,
            's3': S3StorageConfig,
            'amazon_s3': S3StorageConfig,
            'minio': S3StorageConfig,
            'gcs': GCSStorageConfig,
            'gs': GCSStorageConfig,
            'gcp': GCSStorageConfig,
            'sftp': SFTPStorageConfig,
            'http': HTTPStorageConfig,
            'https': HTTPStorageConfig,
        }

        config_cls = config_map.get(self.provider)
        if not config_cls:
            raise ValueError(f'Unknown provider: {self.provider}')

        return config_cls.model_validate(self.configuration)


__all__ = [
    'StorageConfig',
    'LocalStorageConfig',
    'S3StorageConfig',
    'GCSStorageConfig',
    'SFTPStorageConfig',
    'HTTPStorageConfig',
    'ProviderConfig',
    'ProviderType',
]
