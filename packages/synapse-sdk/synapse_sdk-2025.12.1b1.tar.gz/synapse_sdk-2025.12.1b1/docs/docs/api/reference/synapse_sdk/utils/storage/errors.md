---
sidebar_label: errors
title: synapse_sdk.utils.storage.errors
---

Storage-specific exceptions.

## StorageError Objects

```python
class StorageError(Exception)
```

Base exception for storage-related errors.

## StorageConfigError Objects

```python
class StorageConfigError(StorageError)
```

Raised when storage configuration is invalid.

## StorageProviderNotFoundError Objects

```python
class StorageProviderNotFoundError(StorageError)
```

Raised when requested provider is not registered.

## StorageConnectionError Objects

```python
class StorageConnectionError(StorageError)
```

Raised when connection to storage fails.

## StorageUploadError Objects

```python
class StorageUploadError(StorageError)
```

Raised when file upload fails.

## StorageNotFoundError Objects

```python
class StorageNotFoundError(StorageError)
```

Raised when requested path does not exist.

## StoragePermissionError Objects

```python
class StoragePermissionError(StorageError)
```

Raised when access to storage is denied.

