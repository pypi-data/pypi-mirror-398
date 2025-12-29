---
id: upload-plugin-template
title: Upload Plugin Template Development
sidebar_position: 3
---

# Upload Plugin Template Development with BaseUploader

This guide is for plugin developers who want to create custom upload plugins using the BaseUploader template. The BaseUploader provides a workflow-based foundation for file processing and organization within upload plugins.

## Overview

The BaseUploader template (`synapse_sdk.plugins.categories.upload.templates.plugin`) provides a structured approach to building upload plugins. It handles the common upload workflow while allowing customization through method overrides.

### BaseUploader Workflow

The BaseUploader implements a 6-step workflow pipeline:

```
1. setup_directories()    # Create custom directory structures
2. organize_files()       # Organize and structure files
3. before_process()       # Pre-processing hooks
4. process_files()        # Main processing logic (REQUIRED)
5. after_process()        # Post-processing hooks
6. validate_files()       # Final validation
```

## Getting Started

### Template Structure

When you create an upload plugin, you get this structure:

```
synapse-{plugin-code}-plugin/
├── config.yaml              # Plugin metadata and configuration
├── plugin/                  # Source code directory
│   ├── __init__.py
│   └── upload.py           # Main upload implementation with BaseUploader
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Package configuration
└── README.md               # Plugin documentation
```

### Basic Plugin Implementation

```python
# plugin/__init__.py
from pathlib import Path
from typing import Any, Dict, List

class BaseUploader:
    """Base class with common upload functionality."""

    def __init__(self, run, path: Path, file_specification: List = None,
                 organized_files: List = None, extra_params: Dict = None):
        self.run = run
        self.path = path
        self.file_specification = file_specification or []
        self.organized_files = organized_files or []
        self.extra_params = extra_params or {}

    # Core workflow methods available for override
    def setup_directories(self) -> None:
        """Setup custom directories - override as needed."""
        pass

    def organize_files(self, files: List) -> List:
        """Organize files - override for custom logic."""
        return files

    def before_process(self, organized_files: List) -> List:
        """Pre-process hook - override as needed."""
        return organized_files

    def process_files(self, organized_files: List) -> List:
        """Main processing - MUST be overridden."""
        return organized_files

    def after_process(self, processed_files: List) -> List:
        """Post-process hook - override as needed."""
        return processed_files

    def validate_files(self, files: List) -> List:
        """Validation - override for custom validation."""
        return self._filter_valid_files(files)

    def handle_upload_files(self) -> List:
        """Main entry point - executes the workflow."""
        self.setup_directories()
        current_files = self.organized_files
        current_files = self.organize_files(current_files)
        current_files = self.before_process(current_files)
        current_files = self.process_files(current_files)
        current_files = self.after_process(current_files)
        current_files = self.validate_files(current_files)
        return current_files

# plugin/upload.py
from . import BaseUploader

class Uploader(BaseUploader):
    """Custom upload plugin implementation."""

    def process_files(self, organized_files: List) -> List:
        """Required: Implement your file processing logic."""
        # Your custom processing logic here
        return organized_files
```

## Core Methods Reference

### Required Method

#### `process_files(organized_files: List) -> List`

**Purpose**: Main processing method that must be implemented by all plugins.

**When to use**: Always - this is where your plugin's core logic goes.

**Example**:

```python
def process_files(self, organized_files: List) -> List:
    """Convert TIFF images to JPEG format."""
    processed_files = []

    for file_group in organized_files:
        files_dict = file_group.get('files', {})
        converted_files = {}

        for spec_name, file_path in files_dict.items():
            if file_path.suffix.lower() in ['.tif', '.tiff']:
                # Convert TIFF to JPEG
                jpeg_path = self.convert_tiff_to_jpeg(file_path)
                converted_files[spec_name] = jpeg_path
                self.run.log_message(f"Converted {file_path} to {jpeg_path}")
            else:
                converted_files[spec_name] = file_path

        file_group['files'] = converted_files
        processed_files.append(file_group)

    return processed_files
```

### Optional Hook Methods

#### `setup_directories() -> None`

**Purpose**: Create custom directory structures before processing begins.

**When to use**: When your plugin needs specific directories for processing, temporary files, or output.

**Example**:

```python
def setup_directories(self):
    """Create processing directories."""
    (self.path / 'temp').mkdir(exist_ok=True)
    (self.path / 'processed').mkdir(exist_ok=True)
    (self.path / 'thumbnails').mkdir(exist_ok=True)
    self.run.log_message("Created processing directories")
```

#### `organize_files(files: List) -> List`

**Purpose**: Reorganize and structure files before main processing.

**When to use**: When you need to group files differently, filter by criteria, or restructure the data.

**Example**:

```python
def organize_files(self, files: List) -> List:
    """Group files by size for optimized processing."""
    large_files = []
    small_files = []

    for file_group in files:
        total_size = sum(f.stat().st_size for f in file_group.get('files', {}).values())
        if total_size > 100 * 1024 * 1024:  # 100MB
            large_files.append(file_group)
        else:
            small_files.append(file_group)

    # Process large files first
    return large_files + small_files
```

#### `before_process(organized_files: List) -> List`

**Purpose**: Pre-processing hook for setup tasks before main processing.

**When to use**: For validation, preparation, or initialization tasks.

**Example**:

```python
def before_process(self, organized_files: List) -> List:
    """Validate and prepare files for processing."""
    self.run.log_message(f"Starting processing of {len(organized_files)} file groups")

    # Check available disk space
    if not self.check_disk_space(organized_files):
        raise Exception("Insufficient disk space for processing")

    return organized_files
```

#### `after_process(processed_files: List) -> List`

**Purpose**: Post-processing hook for cleanup and finalization.

**When to use**: For cleanup, final transformations, or resource deallocation.

**Example**:

```python
def after_process(self, processed_files: List) -> List:
    """Clean up temporary files and generate summary."""
    # Remove temporary files
    temp_dir = self.path / 'temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # Generate processing summary
    summary = {
        'total_processed': len(processed_files),
        'processing_time': time.time() - self.start_time
    }

    self.run.log_message(f"Processing complete: {summary}")
    return processed_files
```

#### `validate_files(files: List) -> List`

**Purpose**: Custom validation logic beyond type checking.

**When to use**: When you need additional validation rules beyond built-in file type validation.

**Example**:

```python
def validate_files(self, files: List) -> List:
    """Custom validation with size and format checks."""
    # First apply built-in validation
    validated_files = super().validate_files(files)

    # Then apply custom validation
    final_files = []
    for file_group in validated_files:
        if self.validate_file_group(file_group):
            final_files.append(file_group)
        else:
            self.run.log_message(f"File group failed validation: {file_group}")

    return final_files
```

#### `filter_files(organized_file: Dict[str, Any]) -> bool`

**Purpose**: Filter individual files based on custom criteria.

**When to use**: When you need to exclude specific files from processing.

**Example**:

```python
def filter_files(self, organized_file: Dict[str, Any]) -> bool:
    """Filter out small files."""
    files_dict = organized_file.get('files', {})
    total_size = sum(f.stat().st_size for f in files_dict.values())

    if total_size < 1024:  # Skip files smaller than 1KB
        self.run.log_message(f"Skipping small file group: {total_size} bytes")
        return False

    return True
```

## File Extension Filtering

The BaseUploader includes a built-in extension filtering system that automatically filters files based on their file type. This feature is integrated into the workflow and runs automatically during the validation step.

### How It Works

1. **Automatic Integration**: Extension filtering is automatically applied during the `ValidateFilesStep` in the upload workflow
2. **Case-Insensitive**: Extensions are matched case-insensitively (`.mp4` matches `.MP4`, `.Mp4`, etc.)
3. **Type-Based**: Filtering is done per file type (video, image, audio, etc.)
4. **Automatic Logging**: Filtered files are logged with WARNING level showing which extensions were filtered

### Default Backend Configuration

The system comes with sensible defaults that match backend file type restrictions:

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """Get allowed file extensions configuration.

    Override this method to restrict file extensions per file type.
    Extensions are case-insensitive and must include the dot prefix.
    """
    return {
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'],
        'image': ['.jpg', '.jpeg', '.png'],
        'pcd': ['.pcd'],
        'text': ['.txt', '.html'],
        'audio': ['.mp3', '.wav'],
        'data': ['.xml', '.bin', '.json', '.fbx'],
    }
```

### Customizing Extension Filtering

To restrict file extensions for your plugin, simply modify the `get_file_extensions_config()` method in the plugin template file (`plugin/__init__.py`):

#### Example 1: Restrict to MP4 Videos Only

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """Allow only MP4 videos."""
    return {
        'video': ['.mp4'],  # Only MP4 allowed
        'image': ['.jpg', '.jpeg', '.png'],
        'pcd': ['.pcd'],
        'text': ['.txt', '.html'],
        'audio': ['.mp3', '.wav'],
        'data': ['.xml', '.bin', '.json', '.fbx'],
    }
```

**Result**: When uploading, files with extensions `.avi`, `.mkv`, `.mov`, etc. will be automatically filtered out and logged:

```
WARNING: Filtered 3 video files with unavailable extensions: .avi, .mkv, .mov (allowed: .mp4)
```

#### Example 2: Add Support for Additional Formats

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """Add support for additional video and image formats."""
    return {
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'],
        'image': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],  # Added more formats
        'pcd': ['.pcd'],
        'text': ['.txt', '.html', '.md', '.csv'],  # Added .md and .csv
        'audio': ['.mp3', '.wav', '.flac', '.aac'],  # Added .flac and .aac
        'data': ['.xml', '.bin', '.json', '.fbx', '.yaml'],  # Added .yaml
    }
```

#### Example 3: Completely Custom Configuration

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """Custom configuration for specific project needs."""
    return {
        'video': ['.mp4'],  # Strict video format
        'image': ['.jpg'],  # Strict image format
        'cad': ['.dwg', '.dxf', '.step'],  # Custom CAD type
        'document': ['.pdf', '.docx'],  # Custom document type
    }
```

### Extension Filtering Workflow

```
OrganizeFilesStep
  ↓
ValidateFilesStep
  ├─ Uploader.handle_upload_files()
  │   └─ validate_files()
  │       └─ validate_file_types()  ← Extension filtering happens here
  │           ├─ Read get_file_extensions_config()
  │           ├─ Filter files by type
  │           └─ Log filtered extensions
  └─ Strategy validation
```

## Real-World Examples

### Example 1: Image Processing Plugin

```python
from pathlib import Path
from typing import List
from plugin import BaseUploader

class ImageProcessingUploader(BaseUploader):
    """Converts TIFF images to JPEG and generates thumbnails."""

    def setup_directories(self):
        """Create directories for processed images."""
        (self.path / 'processed').mkdir(exist_ok=True)
        (self.path / 'thumbnails').mkdir(exist_ok=True)

    def process_files(self, organized_files: List) -> List:
        """Convert images and generate thumbnails."""
        processed_files = []

        for file_group in organized_files:
            files_dict = file_group.get('files', {})
            converted_files = {}

            for spec_name, file_path in files_dict.items():
                if file_path.suffix.lower() in ['.tif', '.tiff']:
                    # Convert to JPEG
                    jpeg_path = self.convert_to_jpeg(file_path)
                    converted_files[spec_name] = jpeg_path

                    # Generate thumbnail
                    thumbnail_path = self.generate_thumbnail(jpeg_path)
                    converted_files[f"{spec_name}_thumbnail"] = thumbnail_path

                    self.run.log_message(f"Processed {file_path.name}")
                else:
                    converted_files[spec_name] = file_path

            file_group['files'] = converted_files
            processed_files.append(file_group)

        return processed_files

    def convert_to_jpeg(self, tiff_path: Path) -> Path:
        """Convert TIFF to JPEG using PIL."""
        from PIL import Image

        output_path = self.path / 'processed' / f"{tiff_path.stem}.jpg"

        with Image.open(tiff_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=95)

        return output_path

    def generate_thumbnail(self, image_path: Path) -> Path:
        """Generate thumbnail."""
        from PIL import Image

        thumbnail_path = self.path / 'thumbnails' / f"{image_path.stem}_thumb.jpg"

        with Image.open(image_path) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85)

        return thumbnail_path
```

### Example 2: Data Validation Plugin

```python
class DataValidationUploader(BaseUploader):
    """Validates data files and generates quality reports."""

    def __init__(self, run, path, file_specification=None,
                 organized_files=None, extra_params=None):
        super().__init__(run, path, file_specification, organized_files, extra_params)

        # Initialize from extra_params
        self.validation_config = extra_params.get('validation_config', {})
        self.strict_mode = extra_params.get('strict_validation', False)

    def before_process(self, organized_files: List) -> List:
        """Initialize validation engine."""
        self.validation_results = []
        self.run.log_message(f"Starting validation of {len(organized_files)} file groups")
        return organized_files

    def process_files(self, organized_files: List) -> List:
        """Validate files and generate quality reports."""
        processed_files = []

        for file_group in organized_files:
            validation_result = self.validate_file_group(file_group)

            # Add validation metadata
            file_group['validation'] = validation_result
            file_group['quality_score'] = validation_result['score']

            # Include file group based on validation results
            if self.should_include_file_group(validation_result):
                processed_files.append(file_group)
                self.run.log_message(f"File group passed: score {validation_result['score']}")
            else:
                self.run.log_message(f"File group failed: {validation_result['errors']}")

        return processed_files

    def validate_file_group(self, file_group: Dict) -> Dict:
        """Comprehensive validation of file group."""
        files_dict = file_group.get('files', {})
        errors = []
        score = 100

        for spec_name, file_path in files_dict.items():
            # File existence
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                score -= 50
                continue

            # File size validation
            file_size = file_path.stat().st_size
            if file_size == 0:
                errors.append(f"Empty file: {file_path}")
                score -= 40
            elif file_size > 1024 * 1024 * 1024:  # 1GB
                score -= 10

        return {
            'score': max(0, score),
            'errors': errors,
            'validated_at': datetime.now().isoformat()
        }

    def should_include_file_group(self, validation_result: Dict) -> bool:
        """Determine if file group should be included."""
        if validation_result['errors'] and self.strict_mode:
            return False

        min_score = self.validation_config.get('min_score', 50)
        return validation_result['score'] >= min_score
```

### Example 3: Batch Processing Plugin

```python
class BatchProcessingUploader(BaseUploader):
    """Processes files in configurable batches."""

    def __init__(self, run, path, file_specification=None,
                 organized_files=None, extra_params=None):
        super().__init__(run, path, file_specification, organized_files, extra_params)

        self.batch_size = extra_params.get('batch_size', 10)
        self.parallel_processing = extra_params.get('use_parallel', True)
        self.max_workers = extra_params.get('max_workers', 4)

    def organize_files(self, files: List) -> List:
        """Organize files into processing batches."""
        batches = []
        current_batch = []

        for file_group in files:
            current_batch.append(file_group)

            if len(current_batch) >= self.batch_size:
                batches.append({
                    'batch_id': len(batches) + 1,
                    'files': current_batch,
                    'batch_size': len(current_batch)
                })
                current_batch = []

        # Add remaining files
        if current_batch:
            batches.append({
                'batch_id': len(batches) + 1,
                'files': current_batch,
                'batch_size': len(current_batch)
            })

        self.run.log_message(f"Organized into {len(batches)} batches")
        return batches

    def process_files(self, organized_files: List) -> List:
        """Process files in batches."""
        all_processed_files = []

        if self.parallel_processing:
            all_processed_files = self.process_batches_parallel(organized_files)
        else:
            all_processed_files = self.process_batches_sequential(organized_files)

        return all_processed_files

    def process_batches_sequential(self, batches: List) -> List:
        """Process batches sequentially."""
        all_files = []

        for i, batch in enumerate(batches, 1):
            self.run.log_message(f"Processing batch {i}/{len(batches)}")
            processed_batch = self.process_single_batch(batch)
            all_files.extend(processed_batch)

        return all_files

    def process_batches_parallel(self, batches: List) -> List:
        """Process batches in parallel using ThreadPoolExecutor."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self.process_single_batch, batch): batch
                for batch in batches
            }

            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    processed_files = future.result()
                    all_files.extend(processed_files)
                    self.run.log_message(f"Batch {batch['batch_id']} complete")
                except Exception as e:
                    self.run.log_message(f"Batch {batch['batch_id']} failed: {e}")

        return all_files

    def process_single_batch(self, batch: Dict) -> List:
        """Process a single batch of files."""
        batch_files = batch['files']
        processed_files = []

        for file_group in batch_files:
            # Add batch metadata
            file_group['batch_processed'] = True
            file_group['batch_id'] = batch['batch_id']
            processed_files.append(file_group)

        return processed_files
```

## Best Practices

### 1. Code Organization

- Keep `process_files()` focused on core logic
- Use hook methods for setup, cleanup, and validation
- Separate concerns using helper methods

### 2. Error Handling

- Implement comprehensive error handling
- Log errors with context information
- Fail gracefully when possible

### 3. Performance

- Profile your processing logic
- Use appropriate data structures
- Consider memory usage for large files
- Implement async processing for I/O-heavy operations

### 4. Testing

- Write unit tests for all methods
- Include integration tests with real files
- Test error conditions and edge cases

### 5. Logging

- Log important operations and milestones
- Include timing information
- Use structured logging for analysis

### 6. Configuration

- Use `extra_params` for plugin configuration
- Provide sensible defaults
- Validate configuration parameters

## Integration with Upload Action

Your BaseUploader plugin integrates with the upload action workflow:

1. **File Discovery**: Upload action discovers and organizes files
2. **Plugin Invocation**: Your `handle_upload_files()` is called with organized files
3. **Workflow Execution**: BaseUploader runs its 6-step workflow
4. **Return Results**: Processed files are returned to upload action
5. **Upload & Data Unit Creation**: Upload action completes the upload

### Data Flow

```
Upload Action (OrganizeFilesStep)
    ↓ organized_files
BaseUploader.handle_upload_files()
    ↓ setup_directories()
    ↓ organize_files()
    ↓ before_process()
    ↓ process_files()      ← Your custom logic
    ↓ after_process()
    ↓ validate_files()
    ↓ processed_files
Upload Action (UploadFilesStep, GenerateDataUnitsStep)
```

## Configuration

### Plugin Configuration (config.yaml)

```yaml
code: "my-upload-plugin"
name: "My Upload Plugin"
version: "1.0.0"
category: "upload"

package_manager: "pip"

actions:
  upload:
    entrypoint: "plugin.upload.Uploader"
    method: "job"
```

### Dependencies (requirements.txt)

```txt
synapse-sdk>=1.0.0
pillow>=10.0.0  # For image processing
pandas>=2.0.0   # For data processing
```

## Testing Your Plugin

### Unit Testing

```python
import pytest
from unittest.mock import Mock
from pathlib import Path
from plugin.upload import Uploader

class TestUploader:

    def setup_method(self):
        self.mock_run = Mock()
        self.test_path = Path('/tmp/test')
        self.file_spec = [{'name': 'image_1', 'file_type': 'image'}]

    def test_process_files(self):
        """Test file processing."""
        uploader = Uploader(
            run=self.mock_run,
            path=self.test_path,
            file_specification=self.file_spec,
            organized_files=[{'files': {}}]
        )

        result = uploader.process_files([{'files': {}}])
        assert isinstance(result, list)
```

### Integration Testing

```bash
# Test with sample data
synapse plugin run upload '{
  "name": "Test Upload",
  "use_single_path": true,
  "path": "/test/data",
  "storage": 1,
  "data_collection": 5
}' --plugin my-upload-plugin --debug
```

## See Also

- [Upload Plugin Overview](./upload-plugin-overview.md) - User guide and configuration reference
- [Upload Action Development](./upload-plugin-action.md) - SDK developer guide for action architecture and internals
