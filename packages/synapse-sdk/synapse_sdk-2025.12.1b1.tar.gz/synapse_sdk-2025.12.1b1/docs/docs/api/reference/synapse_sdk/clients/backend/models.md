---
sidebar_label: models
title: synapse_sdk.clients.backend.models
---

Backend client models and enums.

This module defines Pydantic v2 models for backend API entities.
All models use modern Python type syntax (PEP 585, PEP 604).

## StorageCategory Objects

```python
class StorageCategory(StrEnum)
```

Storage category classification.

## StorageProvider Objects

```python
class StorageProvider(StrEnum)
```

Supported storage providers.

## JobStatus Objects

```python
class JobStatus(StrEnum)
```

Job execution status.

## Storage Objects

```python
class Storage(BaseModel)
```

Storage configuration from backend API.

## UpdateJobRequest Objects

```python
class UpdateJobRequest(BaseModel)
```

Request model for updating job status and data.

All fields are optional - only include fields to update.

## ChunkedUploadResponse Objects

```python
class ChunkedUploadResponse(BaseModel)
```

Response from chunked upload endpoint.

## ChunkedUploadFinalizeResponse Objects

```python
class ChunkedUploadFinalizeResponse(BaseModel)
```

Response after finalizing a chunked upload.

## DataFileResponse Objects

```python
class DataFileResponse(BaseModel)
```

Response from data file creation.

## CreateLogsRequest Objects

```python
class CreateLogsRequest(BaseModel)
```

Request model for creating logs.

## PluginRunRequest Objects

```python
class PluginRunRequest(BaseModel)
```

Request model for running a plugin.

## PluginReleaseCreateRequest Objects

```python
class PluginReleaseCreateRequest(BaseModel)
```

Request model for creating a plugin release.

## ModelCreateRequest Objects

```python
class ModelCreateRequest(BaseModel)
```

Request model for creating a model.

## ServeApplicationCreateRequest Objects

```python
class ServeApplicationCreateRequest(BaseModel)
```

Request model for creating a Ray Serve application.

## TaskCreateRequest Objects

```python
class TaskCreateRequest(BaseModel)
```

Request model for creating annotation tasks.

## SetTagsRequest Objects

```python
class SetTagsRequest(BaseModel)
```

Request model for setting tags on tasks/assignments.

#### action

'add' or 'remove'

## DataUnitCreateRequest Objects

```python
class DataUnitCreateRequest(BaseModel)
```

Request model for creating data units.

#### files

\{name: \{'checksum': ..., 'path': ...\}\}

