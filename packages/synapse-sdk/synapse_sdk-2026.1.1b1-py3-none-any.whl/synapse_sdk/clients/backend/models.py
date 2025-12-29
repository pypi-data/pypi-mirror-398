"""Backend client models and enums.

This module defines Pydantic v2 models for backend API entities.
All models use modern Python type syntax (PEP 585, PEP 604).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StorageCategory(StrEnum):
    """Storage category classification."""

    INTERNAL = 'internal'
    EXTERNAL = 'external'


class StorageProvider(StrEnum):
    """Supported storage providers."""

    AMAZON_S3 = 'amazon_s3'
    AZURE = 'azure'
    DIGITAL_OCEAN = 'digital_ocean'
    FILE_SYSTEM = 'file_system'
    FTP = 'ftp'
    SFTP = 'sftp'
    MINIO = 'minio'
    GCP = 'gcp'


class JobStatus(StrEnum):
    """Job execution status."""

    PENDING = 'pending'
    RUNNING = 'running'
    STOPPED = 'stopped'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class Storage(BaseModel):
    """Storage configuration from backend API."""

    model_config = ConfigDict(extra='ignore')

    id: int
    name: str
    category: StorageCategory
    provider: StorageProvider
    configuration: dict[str, Any]
    is_default: bool = False


class UpdateJobRequest(BaseModel):
    """Request model for updating job status and data.

    All fields are optional - only include fields to update.
    """

    model_config = ConfigDict(extra='forbid')

    status: JobStatus | None = None
    progress_record: dict[str, Any] | None = None
    metrics_record: dict[str, Any] | None = None
    console_logs: dict[str, Any] | list[dict[str, Any]] | None = None
    result: dict[str, Any] | list[Any] | None = None


class ChunkedUploadResponse(BaseModel):
    """Response from chunked upload endpoint."""

    model_config = ConfigDict(extra='ignore')

    id: int
    url: str
    offset: int
    filename: str | None = None


class ChunkedUploadFinalizeResponse(BaseModel):
    """Response after finalizing a chunked upload."""

    model_config = ConfigDict(extra='ignore')

    id: int
    file: str
    checksum: str
    size: int


class DataFileResponse(BaseModel):
    """Response from data file creation."""

    model_config = ConfigDict(extra='ignore')

    id: int
    file: str
    checksum: str
    size: int
    created_at: str | None = None
    updated_at: str | None = None


class CreateLogsRequest(BaseModel):
    """Request model for creating logs."""

    model_config = ConfigDict(extra='forbid')

    message: str
    level: str = 'info'
    context: dict[str, Any] | None = None
    file: str | None = Field(None, description='Base64-encoded file data')


class PluginRunRequest(BaseModel):
    """Request model for running a plugin."""

    model_config = ConfigDict(extra='forbid')

    agent: int | None = None
    action: str | None = None
    params: dict[str, Any] | None = None
    storage_id: int | None = None
    job_id: int | None = None
    debug: bool | None = None


class PluginReleaseCreateRequest(BaseModel):
    """Request model for creating a plugin release."""

    model_config = ConfigDict(extra='forbid')

    plugin: str
    version: str
    config: dict[str, Any] | None = None
    requirements: list[str] | None = None
    debug: bool = False


class ModelCreateRequest(BaseModel):
    """Request model for creating a model."""

    model_config = ConfigDict(extra='forbid')

    name: str
    plugin: int | None = None
    version: str | None = None
    chunked_upload: int | None = Field(None, description='ID of chunked upload')


class ServeApplicationCreateRequest(BaseModel):
    """Request model for creating a Ray Serve application."""

    model_config = ConfigDict(extra='forbid')

    name: str
    plugin_release: int
    action: str
    params: dict[str, Any] | None = None
    num_replicas: int = 1


class TaskCreateRequest(BaseModel):
    """Request model for creating annotation tasks."""

    model_config = ConfigDict(extra='forbid')

    project: int
    data: list[dict[str, Any]]


class SetTagsRequest(BaseModel):
    """Request model for setting tags on tasks/assignments."""

    model_config = ConfigDict(extra='forbid')

    ids: list[int]
    tags: list[int]
    action: str = 'add'  # 'add' or 'remove'


class DataUnitCreateRequest(BaseModel):
    """Request model for creating data units."""

    model_config = ConfigDict(extra='forbid')

    data_collection: int
    files: dict[str, dict[str, Any]]  # {name: {'checksum': ..., 'path': ...}}
    meta: dict[str, Any] | None = None


class Agent(BaseModel):
    """Agent configuration from backend API."""

    model_config = ConfigDict(extra='ignore')

    id: int
    name: str
    url: str | None = None
    status: str | None = None
    token: str | None = None
    node_install_script: str | None = None

    @property
    def is_connected(self) -> bool:
        """Check if agent is connected."""
        return self.status and self.status.lower() == 'connected'

    def extract_token(self) -> str | None:
        """Extract agent token from node_install_script if not set."""
        if self.token:
            return self.token
        if not self.node_install_script:
            return None
        import re

        pattern = r'agents/([a-f0-9]{40})/node_install_script'
        match = re.search(pattern, self.node_install_script)
        return match.group(1) if match else None


__all__ = [
    # Enums
    'StorageCategory',
    'StorageProvider',
    'JobStatus',
    # Response models
    'Agent',
    'Storage',
    'ChunkedUploadResponse',
    'ChunkedUploadFinalizeResponse',
    'DataFileResponse',
    # Request models
    'UpdateJobRequest',
    'CreateLogsRequest',
    'PluginRunRequest',
    'PluginReleaseCreateRequest',
    'ModelCreateRequest',
    'ServeApplicationCreateRequest',
    'TaskCreateRequest',
    'SetTagsRequest',
    'DataUnitCreateRequest',
]
