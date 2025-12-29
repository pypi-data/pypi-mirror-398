---
id: core-mixin
title: CoreClientMixin
sidebar_position: 7
---

# CoreClientMixin

Provides core file upload and fundamental operations for the Synapse backend.

## Overview

The `CoreClientMixin` handles core system operations, particularly file upload capabilities including chunked upload for large files. This mixin is automatically included in the `BackendClient` and provides essential functionality used by other mixins.

## File Upload Operations

### `create_chunked_upload(file_path)`

Upload large files using chunked upload for optimal performance and reliability.

```python
from pathlib import Path

# Upload a large file
file_path = Path('/path/to/large_dataset.zip')
result = client.create_chunked_upload(file_path)
print(f"Upload completed: {result}")
print(f"File ID: {result['id']}")
```

**Parameters:**

- `file_path` (str | Path): Path to the file to upload

**Returns:**

- `dict`: Upload result with file ID and metadata

**Features:**

- **50MB Chunks**: Uses optimal chunk size for performance
- **MD5 Integrity**: Automatic checksum verification
- **Resume Capability**: Can resume interrupted uploads
- **Progress Tracking**: Supports upload progress monitoring
- **Error Recovery**: Automatic retry for failed chunks

### Upload Process Details

The chunked upload process works as follows:

1. **File Analysis**: Calculate file size and MD5 hash
2. **Chunk Creation**: Split file into 50MB chunks
3. **Sequential Upload**: Upload chunks one by one
4. **Integrity Check**: Verify each chunk with MD5
5. **Assembly**: Server assembles chunks into final file
6. **Verification**: Final integrity check of complete file

```python
import hashlib
import os
from pathlib import Path

def upload_with_progress(file_path):
    """Upload file with detailed progress tracking."""

    file_path = Path(file_path)

    # Get file info
    file_size = os.path.getsize(file_path)
    print(f"Uploading file: {file_path.name}")
    print(f"File size: {file_size / (1024*1024):.2f} MB")

    # Calculate MD5 (this is done automatically by the client)
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    print(f"MD5 checksum: {hash_md5.hexdigest()}")

    # Upload with chunked upload
    try:
        result = client.create_chunked_upload(file_path)
        print("Upload successful!")
        return result
    except Exception as e:
        print(f"Upload failed: {e}")
        raise

# Usage
upload_result = upload_with_progress('/path/to/large_file.zip')
```

## Advanced Upload Scenarios

### Batch File Upload

```python
def batch_chunked_upload(file_paths, max_concurrent=3):
    """Upload multiple large files with concurrency control."""
    import concurrent.futures
    import threading

    upload_results = []
    failed_uploads = []

    def upload_single_file(file_path):
        try:
            print(f"Starting upload: {file_path}")
            result = client.create_chunked_upload(file_path)
            print(f"Completed upload: {file_path}")
            return {'file_path': file_path, 'result': result, 'status': 'success'}
        except Exception as e:
            print(f"Failed upload: {file_path} - {e}")
            return {'file_path': file_path, 'error': str(e), 'status': 'failed'}

    # Use ThreadPoolExecutor for concurrent uploads
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_file = {
            executor.submit(upload_single_file, file_path): file_path
            for file_path in file_paths
        }

        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()

            if result['status'] == 'success':
                upload_results.append(result)
            else:
                failed_uploads.append(result)

    return {
        'successful': upload_results,
        'failed': failed_uploads,
        'total': len(file_paths)
    }

# Upload multiple files
file_list = [
    Path('/data/file1.zip'),
    Path('/data/file2.zip'),
    Path('/data/file3.zip')
]

batch_results = batch_chunked_upload(file_list, max_concurrent=2)
print(f"Successful uploads: {len(batch_results['successful'])}")
print(f"Failed uploads: {len(batch_results['failed'])}")
```

### Upload with Retry Logic

```python
import time
from synapse_sdk.clients.exceptions import ClientError

def robust_chunked_upload(file_path, max_retries=3, retry_delay=5):
    """Upload with retry logic for improved reliability."""

    for attempt in range(max_retries):
        try:
            result = client.create_chunked_upload(file_path)
            print(f"Upload successful on attempt {attempt + 1}")
            return result

        except ClientError as e:
            if e.status_code == 413:  # File too large
                print(f"File {file_path} is too large for upload")
                raise
            elif e.status_code == 507:  # Insufficient storage
                print("Server storage full")
                raise
            elif e.status_code >= 500:  # Server error
                if attempt < max_retries - 1:
                    print(f"Server error on attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Upload failed after {max_retries} attempts")
                    raise
            else:
                print(f"Upload failed with error: {e}")
                raise

        except OSError as e:
            print(f"File system error: {e}")
            raise

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                time.sleep(retry_delay)
            else:
                print(f"Upload failed after {max_retries} attempts with error: {e}")
                raise

# Use robust upload
try:
    result = robust_chunked_upload('/path/to/file.zip')
    print(f"File uploaded successfully: {result['id']}")
except Exception as e:
    print(f"Final upload failure: {e}")
```

### Upload Progress Monitoring

```python
import os
from tqdm import tqdm

class ProgressTracker:
    """Simple progress tracker for file uploads."""

    def __init__(self, total_size):
        self.total_size = total_size
        self.uploaded_size = 0
        self.progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Uploading")

    def update(self, chunk_size):
        self.uploaded_size += chunk_size
        self.progress_bar.update(chunk_size)

        if self.uploaded_size >= self.total_size:
            self.progress_bar.close()

    def get_progress_percentage(self):
        return (self.uploaded_size / self.total_size) * 100 if self.total_size > 0 else 0

def upload_with_progress_bar(file_path):
    """Upload file with visual progress bar."""

    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)

    # Create progress tracker
    tracker = ProgressTracker(file_size)

    try:
        # Note: The actual chunked upload doesn't expose chunk-level progress
        # This is a conceptual example of how you might track progress
        print(f"Starting upload of {file_path.name} ({file_size / (1024*1024):.2f} MB)")

        result = client.create_chunked_upload(file_path)

        # Simulate progress completion
        tracker.update(file_size)
        print(f"Upload completed: {result['id']}")

        return result

    except Exception as e:
        tracker.progress_bar.close()
        print(f"Upload failed: {e}")
        raise

# Usage
upload_result = upload_with_progress_bar('/path/to/large_file.zip')
```

## File Validation

### Pre-Upload Validation

```python
def validate_file_for_upload(file_path, max_size_gb=10):
    """Validate file before attempting upload."""

    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check if it's a file (not directory)
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Check file size
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_gb * 1024 * 1024 * 1024

    if file_size > max_size_bytes:
        raise ValueError(f"File too large: {file_size / (1024**3):.2f} GB (max: {max_size_gb} GB)")

    # Check file permissions
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")

    # Basic file integrity check
    try:
        with open(file_path, 'rb') as f:
            f.read(1024)  # Try to read first 1KB
    except Exception as e:
        raise ValueError(f"File appears to be corrupted: {e}")

    return {
        'valid': True,
        'file_size': file_size,
        'file_path': str(file_path)
    }

def safe_chunked_upload(file_path):
    """Upload with pre-validation."""

    try:
        # Validate file first
        validation = validate_file_for_upload(file_path)
        print(f"File validation passed: {validation['file_size'] / (1024*1024):.2f} MB")

        # Proceed with upload
        result = client.create_chunked_upload(file_path)
        print(f"Upload successful: {result['id']}")

        return result

    except (FileNotFoundError, ValueError, PermissionError) as e:
        print(f"Validation failed: {e}")
        return None
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

# Usage
upload_result = safe_chunked_upload('/path/to/file.zip')
```

## Performance Optimization

### Optimized Upload Strategy

```python
def optimized_upload_strategy(file_path):
    """Choose optimal upload strategy based on file characteristics."""

    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)

    # Thresholds (in bytes)
    SMALL_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
    LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

    if file_size < SMALL_FILE_THRESHOLD:
        print(f"Small file ({file_size / (1024*1024):.2f} MB) - using regular upload")
        # For small files, you might use a different upload method
        # This is conceptual as the CoreClientMixin only provides chunked upload
        return client.create_chunked_upload(file_path)

    elif file_size < LARGE_FILE_THRESHOLD:
        print(f"Medium file ({file_size / (1024*1024):.2f} MB) - using chunked upload")
        return client.create_chunked_upload(file_path)

    else:
        print(f"Large file ({file_size / (1024*1024):.2f} MB) - using optimized chunked upload")
        # For very large files, you might want additional optimizations
        return robust_chunked_upload(file_path, max_retries=5)

# Usage
result = optimized_upload_strategy('/path/to/any_size_file.zip')
```

## Integration with Other Operations

### Upload and Process Workflow

```python
def upload_and_process_workflow(file_path, collection_id):
    """Complete workflow: upload file and create data unit."""

    try:
        # Step 1: Upload file using chunked upload
        print("Step 1: Uploading file...")
        upload_result = client.create_chunked_upload(file_path)
        file_id = upload_result['id']
        print(f"File uploaded successfully: {file_id}")

        # Step 2: Create data file entry
        print("Step 2: Creating data file entry...")
        data_file = client.create_data_file(Path(file_path))
        print(f"Data file created: {data_file}")

        # Step 3: Organize for collection
        print("Step 3: Organizing for collection...")
        organized_file = {
            'files': {'primary': Path(file_path)},
            'meta': {
                'origin_file_stem': Path(file_path).stem,
                'origin_file_extension': Path(file_path).suffix,
                'uploaded_file_id': file_id
            }
        }

        # Step 4: Upload to collection
        collection_result = client.upload_data_file(
            organized_file,
            collection_id
        )
        print(f"Added to collection: {collection_result}")

        # Step 5: Create data unit
        data_units = client.create_data_units([collection_result])
        print(f"Data unit created: {data_units[0]['id']}")

        return {
            'file_id': file_id,
            'data_file': data_file,
            'collection_result': collection_result,
            'data_unit': data_units[0]
        }

    except Exception as e:
        print(f"Workflow failed: {e}")
        raise

# Complete workflow
workflow_result = upload_and_process_workflow(
    '/path/to/data.zip',
    collection_id=123
)
```

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

def handle_upload_errors():
    """Comprehensive error handling for uploads."""

    try:
        result = client.create_chunked_upload('/path/to/file.zip')
        return result

    except FileNotFoundError:
        print("Error: File not found")
        return None

    except PermissionError:
        print("Error: Permission denied - check file permissions")
        return None

    except ClientError as e:
        if e.status_code == 413:
            print("Error: File too large for upload")
        elif e.status_code == 507:
            print("Error: Server storage full")
        elif e.status_code == 429:
            print("Error: Rate limited - too many requests")
        elif e.status_code >= 500:
            print(f"Error: Server error ({e.status_code})")
        else:
            print(f"Error: Client error ({e.status_code}): {e}")
        return None

    except OSError as e:
        print(f"Error: Operating system error: {e}")
        return None

    except MemoryError:
        print("Error: Insufficient memory for upload")
        return None

    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        return None

# Use error handling
upload_result = handle_upload_errors()
if upload_result:
    print(f"Upload successful: {upload_result['id']}")
else:
    print("Upload failed")
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [DataCollectionClientMixin](./data-collection-mixin.md) - Data collection operations that use chunked upload
- [MLClientMixin](./ml-mixin.md) - ML model uploads that use chunked upload
