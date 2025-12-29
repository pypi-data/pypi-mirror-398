---
id: data-collection-mixin
title: DataCollectionClientMixin
sidebar_position: 3
---

# DataCollectionClientMixin

Provides data collection and file management operations for the Synapse backend.

## Overview

The `DataCollectionClientMixin` handles all operations related to data collections, file uploads, data units, and batch processing. This mixin is automatically included in the `BackendClient` and provides methods for managing large-scale data operations.

## Data Collection Operations

### `list_data_collection()`

Retrieve a list of all available data collections.

```python
collections = client.list_data_collection()
for collection in collections:
    print(f"Collection: {collection['name']} (ID: {collection['id']})")
```

**Returns:**

- `list`: List of data collection objects

### `get_data_collection(data_collection_id)`

Get detailed information about a specific data collection.

```python
collection = client.get_data_collection(123)
print(f"Collection: {collection['name']}")
print(f"Description: {collection['description']}")

# Access file specifications
file_specs = collection['file_specifications']
for spec in file_specs:
    print(f"File type: {spec['name']}, Required: {spec['is_required']}")
```

**Parameters:**

- `data_collection_id` (int): Data collection ID

**Returns:**

- `dict`: Detailed collection information including file specifications

**Collection structure:**

- `id`: Collection ID
- `name`: Collection name
- `description`: Collection description
- `file_specifications`: List of required file types and formats
- `project`: Associated project ID
- `created_at`: Creation timestamp

## File Operations

### `create_data_file(file_path, use_chunked_upload=False)`

Create and upload a data file to the backend.

```python
from pathlib import Path

# Regular upload for smaller files
data_file = client.create_data_file(Path('/path/to/image.jpg'))
print(f"Uploaded file ID: {data_file['id']}")

# Chunked upload for large files (>50MB recommended)
large_file = client.create_data_file(
    Path('/path/to/large_dataset.zip'),
    use_chunked_upload=True
)
print(f"Large file uploaded: {large_file['id']}")
```

**Parameters:**

- `file_path` (Path): Path object pointing to the file to upload
- `use_chunked_upload` (bool): Enable chunked upload for large files

**Returns:**

- `dict` or `str`: File upload response with file ID and metadata

**When to use chunked upload:**

- Files larger than 50MB
- Unreliable network connections
- When you need upload progress tracking
- For better error recovery

### `upload_data_file(organized_file, collection_id, use_chunked_upload=False)`

Upload organized file data to a specific collection.

```python
# Organize file data
organized_file = {
    'files': {
        'image': Path('/path/to/image.jpg'),
        'annotation': Path('/path/to/annotation.json'),
        'metadata': Path('/path/to/metadata.xml')
    },
    'meta': {
        'origin_file_stem': 'sample_001',
        'origin_file_extension': '.jpg',
        'created_at': '2023-10-01T12:00:00Z',
        'batch_id': 'batch_001'
    }
}

# Upload to collection
result = client.upload_data_file(
    organized_file=organized_file,
    collection_id=123,
    use_chunked_upload=False
)
```

**Parameters:**

- `organized_file` (dict): Structured file data with files and metadata
- `collection_id` (int): Target data collection ID
- `use_chunked_upload` (bool): Enable chunked upload

**Organized file structure:**

- `files` (dict): Dictionary mapping file types to file paths
- `meta` (dict): Metadata associated with the file group

**Returns:**

- `dict`: Upload result with file references and IDs

### `create_data_units(uploaded_files)`

Create data units from previously uploaded files.

```python
# Files that have been uploaded
uploaded_files = [
    {
        'id': 1,
        'file': {'image': 'file_id_123', 'annotation': 'file_id_124'},
        'meta': {'batch': 'batch_001'}
    },
    {
        'id': 2,
        'file': {'image': 'file_id_125', 'annotation': 'file_id_126'},
        'meta': {'batch': 'batch_001'}
    }
]

# Create data units
data_units = client.create_data_units(uploaded_files)
print(f"Created {len(data_units)} data units")
```

**Parameters:**

- `uploaded_files` (list): List of uploaded file structures

**Returns:**

- `list`: Created data units with IDs and metadata

## Batch Processing

The mixin supports efficient batch processing for large-scale operations:

```python
from multiprocessing import Pool
from pathlib import Path

# Example: Batch upload multiple files
file_paths = [
    Path('/data/batch1/file1.jpg'),
    Path('/data/batch1/file2.jpg'),
    Path('/data/batch1/file3.jpg'),
    # ... more files
]

# Process files in batches
batch_size = 10
for i in range(0, len(file_paths), batch_size):
    batch = file_paths[i:i+batch_size]

    # Upload batch
    uploaded_files = []
    for file_path in batch:
        result = client.create_data_file(file_path)
        uploaded_files.append({
            'id': len(uploaded_files) + 1,
            'file': {'image': result['id']},
            'meta': {'batch': f'batch_{i//batch_size}'}
        })

    # Create data units for batch
    data_units = client.create_data_units(uploaded_files)
    print(f"Processed batch {i//batch_size}: {len(data_units)} data units")
```

## Progress Tracking

For large uploads, you can track progress:

```python
import os
from tqdm import tqdm

def upload_with_progress(file_paths, collection_id):
    """Upload files with progress tracking."""
    uploaded_files = []

    with tqdm(total=len(file_paths), desc="Uploading files") as pbar:
        for file_path in file_paths:
            try:
                # Check file size to decide upload method
                file_size = os.path.getsize(file_path)
                use_chunked = file_size > 50 * 1024 * 1024  # 50MB

                # Upload file
                result = client.create_data_file(
                    file_path,
                    use_chunked_upload=use_chunked
                )

                # Organize for collection
                organized_file = {
                    'files': {'primary': file_path},
                    'meta': {
                        'origin_file_stem': file_path.stem,
                        'origin_file_extension': file_path.suffix,
                        'file_size': file_size
                    }
                }

                upload_result = client.upload_data_file(
                    organized_file,
                    collection_id,
                    use_chunked_upload=use_chunked
                )

                uploaded_files.append(upload_result)
                pbar.update(1)

            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
                pbar.update(1)
                continue

    return uploaded_files

# Usage
file_paths = [Path(f'/data/file_{i}.jpg') for i in range(100)]
results = upload_with_progress(file_paths, collection_id=123)
```

## Data Validation

### File Specification Validation

```python
def validate_files_against_collection(file_paths, collection_id):
    """Validate files against collection specifications."""
    collection = client.get_data_collection(collection_id)
    file_specs = collection['file_specifications']

    # Create specification lookup
    required_types = {spec['name'] for spec in file_specs if spec['is_required']}
    optional_types = {spec['name'] for spec in file_specs if not spec['is_required']}

    # Validate file organization
    organized_files = []
    for file_path in file_paths:
        # Extract file type from path or metadata
        file_type = extract_file_type(file_path)  # Custom function

        if file_type in required_types or file_type in optional_types:
            organized_files.append({
                'path': file_path,
                'type': file_type,
                'valid': True
            })
        else:
            print(f"Warning: Unknown file type '{file_type}' for {file_path}")
            organized_files.append({
                'path': file_path,
                'type': file_type,
                'valid': False
            })

    return organized_files

def extract_file_type(file_path):
    """Extract file type from path - implement based on your naming convention."""
    # Example implementation
    if 'image' in str(file_path):
        return 'image'
    elif 'annotation' in str(file_path):
        return 'annotation'
    elif 'metadata' in str(file_path):
        return 'metadata'
    else:
        return 'unknown'
```

## Error Handling and Retry Logic

```python
import time
from synapse_sdk.clients.exceptions import ClientError

def robust_upload(file_path, max_retries=3):
    """Upload with retry logic for reliability."""
    for attempt in range(max_retries):
        try:
            result = client.create_data_file(file_path, use_chunked_upload=True)
            return result
        except ClientError as e:
            if e.status_code == 413:  # File too large
                print(f"File {file_path} too large, trying chunked upload")
                try:
                    return client.create_data_file(file_path, use_chunked_upload=True)
                except Exception as retry_e:
                    print(f"Chunked upload failed: {retry_e}")
                    if attempt == max_retries - 1:
                        raise
            elif e.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Upload failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
        except Exception as e:
            print(f"Unexpected error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Brief pause before retry
```

## Complete Workflow Example

```python
from pathlib import Path
from synapse_sdk.clients.backend import BackendClient

def complete_data_ingestion_workflow():
    """Complete workflow for data ingestion."""
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. Choose or create data collection
    collections = client.list_data_collection()
    collection_id = collections[0]['id']  # Use first available

    # 2. Get collection specifications
    collection = client.get_data_collection(collection_id)
    print(f"Using collection: {collection['name']}")

    # 3. Prepare file paths
    data_dir = Path('/path/to/your/data')
    image_files = list(data_dir.glob('*.jpg'))

    # 4. Upload files and create data units
    uploaded_files = []
    for i, image_path in enumerate(image_files):
        # Upload individual file
        data_file = client.create_data_file(image_path)

        # Organize for collection
        organized_file = {
            'files': {'image': image_path},
            'meta': {
                'origin_file_stem': image_path.stem,
                'origin_file_extension': image_path.suffix,
                'sequence': i,
                'batch': 'batch_001'
            }
        }

        # Upload to collection
        upload_result = client.upload_data_file(
            organized_file,
            collection_id
        )
        uploaded_files.append(upload_result)

    # 5. Create data units in batches
    batch_size = 10
    all_data_units = []
    for i in range(0, len(uploaded_files), batch_size):
        batch = uploaded_files[i:i+batch_size]
        data_units = client.create_data_units(batch)
        all_data_units.extend(data_units)
        print(f"Created batch {i//batch_size}: {len(data_units)} data units")

    print(f"Total data units created: {len(all_data_units)}")
    return all_data_units

# Run the workflow
if __name__ == "__main__":
    data_units = complete_data_ingestion_workflow()
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [CoreClientMixin](./core-mixin.md) - Core file operations
- [AnnotationClientMixin](./annotation-mixin.md) - Task and annotation management
