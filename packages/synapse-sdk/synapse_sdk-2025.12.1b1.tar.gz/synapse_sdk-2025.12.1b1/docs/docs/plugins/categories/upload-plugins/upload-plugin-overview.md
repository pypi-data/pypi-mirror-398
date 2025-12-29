---
id: upload-plugin-overview
title: Upload Plugin Overview
sidebar_position: 1
---

# Upload Plugin Overview

Upload plugins provide comprehensive file upload and data ingestion operations for processing files into the Synapse platform with metadata support, security validation, and organized data unit generation.

## Quick Overview

**Category:** Upload
**Available Actions:** `upload`
**Execution Method:** Job-based execution

## Key Features

- **Multi-Path Mode Support**: Upload files from different locations with individual path settings for each asset
- **Excel Metadata Integration**: Automatic metadata annotation from Excel files
- **Flexible File Organization**: Single-path or multi-path modes for different use cases
- **Batch Processing**: Optimized batch processing for large-scale uploads
- **Progress Tracking**: Real-time progress updates across workflow stages
- **Security Validation**: Comprehensive file and Excel security checks

## Use Cases

- Bulk file uploads with metadata annotation
- Excel-based metadata mapping and validation
- Recursive directory processing
- Type-based file organization
- Batch data unit creation
- Multi-source dataset uploads (sensors, cameras, annotations from different locations)
- Secure file processing with size and content validation

## Supported Upload Sources

- Local file system paths (files and directories)
- Recursive directory scanning
- Excel metadata files for enhanced file annotation
- Mixed file types with automatic organization
- Distributed data sources with per-asset path configuration

## Configuration Modes

### Mode 1: Single Path Mode (Default - `use_single_path: true`)

All assets share one base directory. The system expects subdirectories for each file specification.

```json
{
  "name": "Standard Upload",
  "use_single_path": true,
  "path": "/data/experiment",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 5
}
```

**Expected Directory Structure:**

```
/data/experiment/
├── pcd_1/           # Point clouds
│   └── *.pcd
├── image_1/         # Images
│   └── *.jpg
└── json_meta_1/     # Metadata
    └── *.json
```

### Mode 2: Multi-Path Mode (`use_single_path: false`)

Each asset has its own path and recursive setting. Perfect for distributed data sources.

```json
{
  "name": "Multi-Source Upload",
  "use_single_path": false,
  "assets": {
    "pcd_1": {
      "path": "/sensors/lidar/scan_001",
      "is_recursive": false
    },
    "image_1": {
      "path": "/sensors/camera/front",
      "is_recursive": true
    },
    "json_meta_1": {
      "path": "/metadata/annotations",
      "is_recursive": false
    }
  },
  "storage": 1,
  "data_collection": 5
}
```

**Optional File Specs:**

In multi-path mode, file specifications can be marked as optional in the data collection's file specification template:

- **Required specs** (`is_required: true`): Must have an asset path in the `assets` parameter
- **Optional specs** (`is_required: false`): Can be omitted from `assets` - the system will skip them

Example with optional spec omitted:

```json
{
  "name": "Multi-Source Upload",
  "use_single_path": false,
  "assets": {
    "pcd_1": {"path": "/sensors/lidar", "is_recursive": false},
    "image_1": {"path": "/cameras/front", "is_recursive": true}
    // "json_meta_1" is optional and omitted
  },
  "storage": 1,
  "data_collection": 5
}
```

The system logs: `"Skipping optional spec json_meta_1: no asset path configured"`

## Basic Usage

### CLI Usage

```bash
# Single path mode (traditional)
synapse plugin run upload '{
  "name": "Dataset Upload",
  "use_single_path": true,
  "path": "/data/training",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 5
}'

# Multi-path mode (advanced)
synapse plugin run upload '{
  "name": "Multi-Sensor Upload",
  "use_single_path": false,
  "assets": {
    "lidar": {"path": "/sensors/lidar", "is_recursive": true},
    "camera": {"path": "/sensors/camera", "is_recursive": false}
  },
  "storage": 1,
  "data_collection": 5
}'
```

### Python API Usage

```python
from synapse_sdk.plugins.categories.upload.actions.upload.action import UploadAction

# Configure upload parameters
params = {
    "name": "Dataset Upload",
    "use_single_path": true,
    "path": "/data/training_images",
    "is_recursive": True,
    "storage": 1,
    "data_collection": 5,
    "max_file_size_mb": 100
}

action = UploadAction(params=params, plugin_config=plugin_config)
result = action.start()

print(f"Uploaded {result['uploaded_files_count']} files")
print(f"Generated {result['generated_data_units_count']} data units")
```

## Configuration Parameters

### Required Parameters

| Parameter         | Type  | Description        | Example       |
| ----------------- | ----- | ------------------ | ------------- |
| `name`            | `str` | Upload name        | `"My Upload"` |
| `storage`         | `int` | Storage ID         | `1`           |
| `data_collection` | `int` | Data collection ID | `5`           |

### Mode-Specific Required Parameters

**Single Path Mode** (`use_single_path: true`):

- `path` (str): Base directory path

**Multi-Path Mode** (`use_single_path: false`):

- `assets` (dict): Asset-specific configurations with `path` and `is_recursive` per asset

### Optional Parameters

| Parameter                       | Type          | Default | Description                       |
| ------------------------------- | ------------- | ------- | --------------------------------- |
| `description`                   | `str \| None` | `None`  | Upload description                |
| `project`                       | `int \| None` | `None`  | Project ID                        |
| `use_single_path`               | `bool`        | `true`  | Mode toggle                       |
| `is_recursive`                  | `bool`        | `true`  | Recursive scan (single path mode) |
| `excel_metadata_path`           | `str \| None` | `None`  | Excel metadata file path |
| `max_file_size_mb`              | `int`         | `50`    | Maximum file size in MB           |
| `creating_data_unit_batch_size` | `int`         | `100`   | Batch size for data units         |

## Excel Metadata Support

The upload plugin provides advanced Excel metadata processing with flexible header support and comprehensive filename matching capabilities.

### Specifying Excel Metadata Files

You can provide Excel metadata files using the `excel_metadata_path` parameter. The system supports multiple path resolution strategies:

1. **Absolute Path**: Full filesystem path to the Excel file
2. **Storage-Relative Path**: Path relative to the storage's default directory
3. **Working Directory-Relative Path**: Path relative to the upload working directory (single-path mode only)

**Examples:**

```json
{
  "excel_metadata_path": "/data/metadata.xlsx"  // Absolute path
}
```

```json
{
  "excel_metadata_path": "metadata.xlsx"  // Relative to storage default path
}
```

```json
{
  "excel_metadata_path": "metadata/dataset_info.xlsx"  // Subdirectory in storage
}
```

### Path Resolution Order

The system resolves Excel metadata paths in the following order:

1. **Absolute path**: If the path starts with `/`, it's treated as an absolute filesystem path
2. **Storage-relative path**: The path is resolved relative to the storage's default path
3. **Working directory-relative path** (single-path mode): The path is resolved relative to the current working directory

This flexible resolution allows you to store metadata files alongside your data in the configured storage location.

### Default Metadata Files

If no `excel_metadata_path` is specified, the system automatically searches for default metadata files in the working directory (single-path mode only):

- `meta.xlsx` (checked first)
- `meta.xls` (fallback)

**Python Example:**

```python
# Explicit path to Excel metadata
upload_params = {
    "name": "Upload with Metadata",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5,
    "excel_metadata_path": "metadata/dataset_info.xlsx"  // Relative to storage
}

# Using default metadata file (meta.xlsx in working directory)
upload_params = {
    "name": "Upload with Default Metadata",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5
    // No excel_metadata_path specified - will use meta.xlsx if present
}
```

### Excel Format

Both header formats are supported (case-insensitive):

**Option 1: "filename" header**
| filename | category | description | custom_field |
|----------|----------|-------------|--------------|
| image1.jpg | nature | Mountain landscape | high_res |
| image2.png | urban | City skyline | processed |

**Option 2: "filename" header**
| file_name | category | description | custom_field |
|-----------|----------|-------------|--------------|
| image1.jpg | nature | Mountain landscape | high_res |
| image2.png | urban | City skyline | processed |

### Filename Matching

The system uses a 5-tier priority matching algorithm:

1. **Exact stem match** (highest priority): `image1` matches `image1.jpg`
2. **Exact filename match**: `image1.jpg` matches `image1.jpg`
3. **Metadata key stem match**: `path/image1.ext` stem matches `image1`
4. **Partial path matching**: `/uploads/image1.jpg` contains `image1`
5. **Full path matching**: Complete path matching for complex structures

### Security Validation

Excel files undergo security validation:

```python
# Default security limits
max_file_size_mb: 10      # File size limit
max_rows: 100000          # Row count limit
max_columns: 50           # Column count limit
```

### Configuration

Configure Excel security in `config.yaml`:

```yaml
actions:
  upload:
    excel_config:
      max_file_size_mb: 10
      max_rows: 100000
      max_columns: 50
```

## Progress Tracking

The upload action tracks progress across three main phases:

| Category              | Proportion | Description                         |
| --------------------- | ---------- | ----------------------------------- |
| `analyze_collection`  | 2%         | Parameter validation and setup      |
| `upload_data_files`   | 38%        | File upload processing              |
| `generate_data_units` | 60%        | Data unit creation and finalization |

## Common Use Cases

### 1. Simple Dataset Upload

```json
{
  "name": "Training Dataset",
  "use_single_path": true,
  "path": "/datasets/training",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 2
}
```

### 2. Multi-Source Sensor Data

```json
{
  "name": "Multi-Camera Dataset",
  "use_single_path": false,
  "assets": {
    "front_camera": { "path": "/cameras/front", "is_recursive": true },
    "rear_camera": { "path": "/cameras/rear", "is_recursive": true },
    "lidar": { "path": "/sensors/lidar", "is_recursive": false }
  },
  "storage": 1,
  "data_collection": 2
}
```

### 3. Dataset with Metadata (Absolute Path)

```json
{
  "name": "Annotated Dataset",
  "use_single_path": true,
  "path": "/data/annotated",
  "is_recursive": true,
  "excel_metadata_path": "/data/metadata.xlsx",
  "storage": 1,
  "data_collection": 5
}
```

### 4. Dataset with Metadata (Storage-Relative Path)

```json
{
  "name": "Upload with Storage-Relative Metadata",
  "use_single_path": true,
  "path": "/data/uploads",
  "is_recursive": true,
  "excel_metadata_path": "metadata/dataset_info.xlsx",
  "storage": 1,
  "data_collection": 5
}
```

**Python Example - Using Different Path Types:**

```python
# Example 1: Absolute path
params = {
    "name": "Upload with Absolute Path Metadata",
    "path": "/data/uploads",
    "excel_metadata_path": "/data/metadata.xlsx",
    "storage": 1,
    "data_collection": 5
}

# Example 2: Storage-relative path
params = {
    "name": "Upload with Storage-Relative Metadata",
    "path": "/data/uploads",
    "excel_metadata_path": "metadata/info.xlsx",  # Relative to storage default path
    "storage": 1,
    "data_collection": 5
}

# Example 3: Using default metadata file
params = {
    "name": "Upload with Default Metadata",
    "path": "/data/uploads",
    # No excel_metadata_path - will look for meta.xlsx in working directory
    "storage": 1,
    "data_collection": 5
}
```

## Benefits

### For Users

- **Flexibility**: Upload files from multiple different locations in a single operation
- **Granular Control**: Set recursive search per asset, not globally
- **Organization**: Map complex file structures to data collection specifications
- **Use Case Support**: Multi-sensor data collection, distributed datasets, heterogeneous sources

### For Developers

- **Backward Compatible**: Existing code continues to work without changes
- **Type Safe**: Full Pydantic validation with clear error messages
- **Maintainable**: Clean separation between single-path and multi-path logic
- **Extensible**: Easy to add more per-asset configuration options in the future

## Next Steps

- **For Plugin Developers**: See [BaseUploader Template Guide](./upload-plugin-template.md) for creating custom upload plugins with file processing logic
- **For SDK/Action Developers**: See [Upload Action Development](./upload-plugin-action.md) for architecture details, strategy patterns, and action internals

## Migration Guide

### From Legacy to Current Version

The upload action maintains 100% backward compatibility. The default behavior (`use_single_path=true`) works identically to the previous version.

#### No Migration Required

Existing configurations continue to work without changes:

```python
# This legacy usage still works
params = {
    "name": "My Upload",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5
}
```

#### Adopting Multi-Path Mode

To use the new multi-path functionality:

1. Set `use_single_path: false`
2. Remove the `path` field (it will be ignored)
3. Add `assets` dictionary with per-asset configurations

```python
# New multi-path mode
params = {
    "name": "Multi-Source Upload",
    "use_single_path": false,
    "assets": {
        "pcd_1": {"path": "/sensors/lidar", "is_recursive": false},
        "image_1": {"path": "/cameras/front", "is_recursive": true}
    },
    "storage": 1,
    "data_collection": 5
}
```

## Troubleshooting

### Common Issues

#### "No Files Found" Error

```bash
# Check path exists and is readable
ls -la /path/to/data
test -r /path/to/data && echo "Readable" || echo "Not readable"

# Verify files exist
find /path/to/data -name "*.jpg" | head -10
```

#### Excel Processing Errors

```bash
# Check file format and size
file /path/to/metadata.xlsx
ls -lh /path/to/metadata.xlsx
```

#### Mode Validation Errors

- **Single path mode**: Ensure `path` is provided
- **Multi-path mode**: Ensure `assets` is provided with at least one asset configuration

## Best Practices

### Directory Organization

- Use clear, descriptive directory names
- Keep reasonable directory sizes (< 10,000 files per directory)
- Use absolute paths for reliability

### Performance Optimization

- Enable recursive only when needed
- Keep Excel files under 5MB for best performance
- Organize files in balanced directory structures

### Security Considerations

- Validate all paths before processing
- Use read-only permissions for source data
- Set appropriate Excel size limits

## Support and Resources

- **Action Development Guide**: [Upload Plugin Action Development](./upload-plugin-action.md)
- **Template Development Guide**: [Upload Plugin Template Development](./upload-plugin-template.md)
- **API Reference**: See action development documentation for detailed API reference
