---
id: base
title: BaseClient
sidebar_position: 3
---

# BaseClient

Base class for all Synapse SDK clients providing core HTTP operations and pagination.

## Overview

The `BaseClient` provides common functionality for HTTP operations, error handling, request management, and pagination used by all other clients. It implements efficient pagination handling with automatic file URL conversion capabilities.

## Features

- HTTP request handling with retry logic
- Automatic timeout management
- Efficient pagination with generators
- File URL to local path conversion
- Pydantic model validation
- Connection pooling

## Core HTTP Methods

The BaseClient provides low-level HTTP methods that are used internally by all client mixins:

- `_get()` - GET requests with optional response model validation
- `_post()` - POST requests with request/response validation
- `_put()` - PUT requests with model validation
- `_patch()` - PATCH requests with model validation
- `_delete()` - DELETE requests with model validation

These methods are typically not called directly. Instead, use the higher-level methods provided by client mixins.

## Pagination Methods

### `_list(path, url_conversion=None, list_all=False, params=None, **kwargs)`

List resources from a paginated API endpoint with optional automatic pagination and file URL conversion.

**Parameters:**

- `path` (str): URL path to request
- `url_conversion` (dict, optional): Configuration for converting file URLs to local paths
 - Structure: `{'files_fields': ['field1', 'field2'], 'is_list': True}`
 - Automatically downloads files and replaces URLs with local paths
- `list_all` (bool): If True, returns all results across all pages using a generator
- `params` (dict, optional): Query parameters (filters, sorting, etc.)
- `**kwargs`: Additional request arguments

**Returns:**

- If `list_all=False`: Dict with `results`, `count`, `next`, `previous`
- If `list_all=True`: Tuple of `(generator, total_count)`

**Examples:**

```python
# Get first page only
response = client._list('api/tasks/')
tasks = response['results'] # First page of tasks
total = response['count'] # Total number of tasks

# Get all results using generator (memory efficient)
generator, total_count = client._list('api/tasks/', list_all=True)
all_tasks = list(generator) # Fetches all pages automatically

# With filters
params = {'status': 'pending', 'priority': 'high'}
response = client._list('api/tasks/', params=params)

# With url_conversion for file fields
url_conversion = {'files_fields': ['files'], 'is_list': True}
generator, count = client._list(
 'api/data_units/',
 url_conversion=url_conversion,
 list_all=True,
 params={'status': 'active'}
)
# File URLs in 'files' field are automatically downloaded and converted to local paths
for unit in generator:
 print(unit['files']) # Local file paths, not URLs
```

### `_list_all(path, url_conversion=None, params=None, **kwargs)`

Generator that yields all results from a paginated API endpoint.

This method is called internally by `_list()` when `list_all=True`. It handles pagination automatically by following `next` URLs and uses an iterative approach (while loop) instead of recursion to avoid stack overflow with deep pagination.

**Key Improvements (SYN-5757):**

1. **No duplicate page_size**: The `page_size` parameter is only added to the first request. Subsequent requests use the `next` URL directly, which already contains all necessary parameters.

2. **Proper params handling**: User-specified query parameters are correctly passed to the first request and preserved through pagination via the `next` URL.

3. **url_conversion on all pages**: URL conversion is applied to every page, not just the first one.

4. **Iterative instead of recursive**: Uses a while loop instead of recursion for better memory efficiency and to prevent stack overflow on large datasets.

**Parameters:**

- `path` (str): Initial URL path
- `url_conversion` (dict, optional): Applied to all pages
- `params` (dict, optional): Query parameters for first request only
- `**kwargs`: Additional request arguments

**Yields:**

Individual result items from all pages, fetched lazily.

**Examples:**

```python
# Basic: iterate through all tasks
for task in client._list_all('api/tasks/'):
 process_task(task)

# With filters
params = {'status': 'pending'}
for task in client._list_all('api/tasks/', params=params):
 print(task['id'])

# With url_conversion for nested file fields
url_conversion = {'files_fields': ['data.files', 'metadata.attachments'], 'is_list': True}
for item in client._list_all('api/items/', url_conversion=url_conversion):
 print(item['data']['files']) # Local paths

# Collect all results (memory intensive for large datasets)
all_results = list(client._list_all('api/tasks/'))
```

## URL Conversion for File Downloads

The `url_conversion` parameter enables automatic downloading of files referenced by URLs in API responses. This is particularly useful when working with data units, tasks, or any resources that include file references.

### URL Conversion Structure

```python
url_conversion = {
 'files_fields': ['files', 'images', 'data.attachments'], # Field paths
 'is_list': True # Whether processing a list of items
}
```

- `files_fields`: List of field paths (supports dot notation for nested fields)
- `is_list`: Set to `True` for paginated list responses

### How It Works

1. API returns responses with file URLs
2. `url_conversion` identifies fields containing URLs
3. Files are downloaded automatically to a temporary directory
4. URLs are replaced with local file paths
5. Your code receives responses with local paths instead of URLs

### Examples

```python
# Simple file field
url_conversion = {'files_fields': ['image_url'], 'is_list': True}
generator, count = client._list(
 'api/photos/',
 url_conversion=url_conversion,
 list_all=True
)
for photo in generator:
 # photo['image_url'] is now a local Path object, not a URL
 with open(photo['image_url'], 'rb') as f:
 process_image(f)

# Multiple file fields
url_conversion = {
 'files_fields': ['thumbnail', 'full_image', 'raw_data'],
 'is_list': True
}

# Nested fields using dot notation
url_conversion = {
 'files_fields': ['data.files', 'metadata.preview', 'annotations.image'],
 'is_list': True
}

# With async download for better performance
from synapse_sdk.utils.file import files_url_to_path_from_objs

results = client._list('api/data_units/')['results']
files_url_to_path_from_objs(
 results,
 files_fields=['files'],
 is_list=True,
 is_async=True # Download all files concurrently
)
```

## Performance Considerations

### Memory Efficiency

When working with large datasets, use generators instead of loading all results into memory:

```python
# Memory intensive - loads all results
all_tasks = list(client._list('api/tasks/', list_all=True)[0])

# Memory efficient - processes one at a time
generator, _ = client._list('api/tasks/', list_all=True)
for task in generator:
 process_task(task)
 # Task is processed and can be garbage collected
```

### Pagination Best Practices

1. **Use list_all=True** for datasets larger than one page
2. **Set appropriate page_size** in params if default (100) isn't optimal
3. **Use url_conversion** only when you need to process files
4. **Consider async downloads** for multiple files per item

```python
# Optimal pagination for large dataset
params = {'page_size': 50} # Smaller pages for faster first response
generator, total = client._list(
 'api/large_dataset/',
 list_all=True,
 params=params
)

# Process with progress tracking
from tqdm import tqdm
for item in tqdm(generator, total=total):
 process_item(item)
```

## Usage in Client Mixins

The BaseClient pagination methods are used internally by all client mixins:

```python
# DataCollectionClientMixin
def list_data_units(self, params=None, url_conversion=None, list_all=False):
 return self._list('data_units/', params=params,
 url_conversion=url_conversion, list_all=list_all)

# AnnotationClientMixin
def list_tasks(self, params=None, url_conversion=None, list_all=False):
 return self._list('sdk/tasks/', params=params,
 url_conversion=url_conversion, list_all=list_all)
```

## See Also

- [BackendClient](./backend.md) - Main client implementation
- [AgentClient](./agent.md) - Agent-specific operations
- [DataCollectionClientMixin](./data-collection-mixin.md) - Data and file operations
- [AnnotationClientMixin](./annotation-mixin.md) - Task and annotation management
