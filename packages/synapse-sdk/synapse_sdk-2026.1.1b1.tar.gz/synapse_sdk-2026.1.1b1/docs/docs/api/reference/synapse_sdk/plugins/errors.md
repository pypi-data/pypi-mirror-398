---
sidebar_label: errors
title: synapse_sdk.plugins.errors
---

## PluginError Objects

```python
class PluginError(Exception)
```

Base exception for plugin-related errors.

## ValidationError Objects

```python
class ValidationError(PluginError)
```

Raised when plugin parameters fail validation.

## ActionNotFoundError Objects

```python
class ActionNotFoundError(PluginError)
```

Raised when the requested action doesn't exist in the plugin.

## ExecutionError Objects

```python
class ExecutionError(PluginError)
```

Raised when action execution fails.

## PluginUploadError Objects

```python
class PluginUploadError(PluginError)
```

Raised when plugin upload fails.

Covers storage upload failures, network errors during upload,
and other upload-related issues.

## ArchiveError Objects

```python
class ArchiveError(PluginError)
```

Raised when archive creation fails.

Covers ZIP creation failures, git ls-files failures,
and file permission errors during archiving.

## BuildError Objects

```python
class BuildError(PluginError)
```

Raised when wheel build fails.

Covers wheel build failures, missing pyproject.toml,
and package manager not found errors.

## ChecksumMismatchError Objects

```python
class ChecksumMismatchError(PluginError)
```

Raised when checksum verification fails.

Indicates file integrity issues - the actual checksum
does not match the expected value.

