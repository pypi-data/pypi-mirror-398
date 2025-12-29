---
id: plugins
title: Plugin System
sidebar_position: 1
---

# Plugin System

The Synapse SDK provides a comprehensive plugin system for building and managing ML plugins across different categories and execution methods. The plugin system enables modular, reusable components that can be distributed and executed in various environments.

## Overview

The plugin system is built around the concept of **actions** - discrete operations that can be packaged, distributed, and executed in different contexts. Each plugin belongs to a specific category and can support multiple actions.

### Key Features

- **Modular Architecture**: Plugins are self-contained with their own dependencies and configuration
- **Multiple Execution Methods**: Support for Jobs, Tasks, and REST API endpoints
- **Distributed Execution**: Built for scalable, distributed computing
- **Template System**: Cookiecutter-based scaffolding for rapid plugin development
- **Progress Tracking**: Built-in logging, metrics, and progress monitoring
- **Dynamic Loading**: Runtime plugin discovery and registration

## Plugin Categories

The SDK organizes plugins into specific categories, each designed for different aspects of ML workflows:

### 1. Neural Networks (`neural_net`)

ML model training, inference, and deployment operations.

**Available Actions:**

- `deployment` - Deploy models to production environments
- `gradio` - Create interactive web interfaces for models
- `inference` - Run model predictions on data
- `test` - Validate model performance and accuracy
- `train` - Train ML models with custom datasets
- `tune` - Hyperparameter optimization and model tuning

**Use Cases:**

- Training computer vision models
- Deploying models as web services
- Running batch inference on datasets
- Creating interactive model demos

### 2. Export (`export`)

Data export and transformation operations for exporting annotated data, ground truth datasets, assignments, and tasks from the Synapse platform.

**Available Actions:**

- `export` - Export data from various sources (assignments, ground truth, tasks) with customizable processing

**Use Cases:**

- Exporting annotated datasets for training
- Converting ground truth data to custom formats
- Creating data packages for distribution
- Batch processing of assignment results
- Transforming annotation data for external tools

**Supported Export Targets:**

- `assignment` - Export assignment data with annotations
- `ground_truth` - Export ground truth dataset versions
- `task` - Export task data with associated annotations

For detailed information about export plugins, BaseExporter class architecture, implementation examples, and best practices, see the [Export Plugins](./export-plugins) documentation.

### 3. Upload (`upload`)

File and data upload functionality with support for various storage backends and flexible asset path configuration.

**Available Actions:**

- `upload` - Upload files to storage providers with multi-path mode support

**Use Cases:**

- Uploading datasets from multiple locations with individual path settings
- Organizing complex multi-asset datasets with per-asset recursive discovery
- Processing datasets with Excel metadata integration
- Handling large-scale uploads with batch processing and progress tracking

** Upload Plugin Documentation:**

- **[Upload Plugin Overview](./categories/upload-plugins/upload-plugin-overview.md)** - User guide with configuration examples and usage
- **[BaseUploader Template Guide](./categories/upload-plugins/upload-plugin-template.md)** - Plugin development guide using BaseUploader template
- **[Upload Action Development](./categories/upload-plugins/upload-plugin-action.md)** - SDK developer guide for action architecture and internals

### 4. Smart Tools (`smart_tool`)

Intelligent automation tools powered by AI.

**Available Actions:**

- `auto_label` - Automated data labeling and annotation

**Use Cases:**

- Pre-labeling datasets with AI models
- Quality assurance for manual annotations
- Accelerating annotation workflows

### 5. Pre-annotation (`pre_annotation`)

Data preparation and processing before annotation.

**Available Actions:**

- `pre_annotation` - Prepare data for annotation workflows
- `to_task` - Convert data to annotation tasks

**Use Cases:**

- Data preprocessing and filtering
- Creating annotation tasks from raw data
- Setting up annotation workflows

### 6. Post-annotation (`post_annotation`)

Data processing and validation after annotation.

**Available Actions:**

- `post_annotation` - Process completed annotations

**Use Cases:**

- Validating annotation quality
- Post-processing annotated data
- Generating training datasets from annotations

### 7. Data Validation (`data_validation`)

Data quality checks and validation operations.

**Available Actions:**

- `validation` - Perform data quality and integrity checks

**Use Cases:**

- Validating dataset integrity
- Checking annotation consistency
- Quality assurance workflows

## Execution Methods

Plugins support three different execution methods depending on the use case:

### Job Execution

**Job-based execution** for long-running, distributed processing tasks.

- Best for: Training models, processing large datasets
- Features: Distributed execution, resource management, fault tolerance
- Monitoring: Full job lifecycle tracking and logging

### Task Execution

**Task-based execution** for simple, short-running operations.

- Best for: Quick data processing, validation checks
- Features: Lightweight execution, fast startup
- Monitoring: Basic progress tracking

### REST API Execution

**Serve-based execution** for web API endpoints.

- Best for: Real-time inference, interactive applications
- Features: HTTP endpoints, auto-scaling, load balancing
- Monitoring: Request/response logging, performance metrics

## Plugin Architecture

### Core Components

#### Plugin Models

**PluginRelease Class** (`synapse_sdk/plugins/models.py:14`)

- Manages plugin metadata and configuration
- Handles versioning and checksums
- Provides runtime environment setup

**Run Class** (`synapse_sdk/plugins/models.py:98`)

- Manages plugin execution instances
- Provides logging and progress tracking
- Handles backend communication

#### Action Base Class

**Action Class** (`synapse_sdk/plugins/categories/base.py:19`)

- Unified interface for all plugin actions
- Parameter validation with Pydantic models
- Built-in logging and error handling
- Runtime environment management

#### Template System

**Cookiecutter Templates** (`synapse_sdk/plugins/templates/`)

- Standardized plugin scaffolding
- Category-specific templates
- Automated project setup with proper structure

### Plugin Structure

Each plugin follows a standardized structure:

```
synapse-{plugin-code}-plugin/
├── config.yaml # Plugin metadata and configuration
├── plugin/ # Source code directory
│ ├── __init__.py
│ ├── {action1}.py # Action implementations
│ └── {action2}.py
├── requirements.txt # Python dependencies
├── pyproject.toml # Package configuration
└── README.md # Plugin documentation
```

### Configuration File (`config.yaml`)

```yaml
# Plugin metadata
code: "my-plugin"
name: "My Custom Plugin"
version: "1.0.0"
category: "neural_net"
description: "A custom ML plugin"

# Package management
package_manager: "pip" # or "uv"

# Package manager options (optional)
# For uv: defaults to ['--no-cache']
# For pip: defaults to ['--upgrade'] to ensure requirements.txt versions override pre-installed packages
package_manager_options: ["--no-cache", "--quiet"]

# Action definitions
actions:
 train:
 entrypoint: "plugin.train.TrainAction"
 method: "job"
 inference:
 entrypoint: "plugin.inference.InferenceAction"
 method: "restapi"
```

## Creating Plugins

### 1. Generate Plugin Template

Use the CLI to create a new plugin from templates:

```bash
synapse plugin create
```

This will prompt for:

- Plugin code (unique identifier)
- Plugin name and description
- Category selection
- Required actions

### 2. Implement Actions

Each action inherits from the base `Action` class:

```python
# plugin/train.py
from synapse_sdk.plugins.categories.neural_net import TrainAction as BaseTrainAction
from pydantic import BaseModel

class TrainParams(BaseModel):
 dataset_path: str
 epochs: int = 10
 learning_rate: float = 0.001

class TrainAction(BaseTrainAction):
 name = "train"
 params_model = TrainParams

 def start(self):
 # Access validated parameters
 dataset_path = self.params['dataset_path']
 epochs = self.params['epochs']

 # Log progress
 self.run.log_message("Starting training...")

 # Your training logic here
 for epoch in range(epochs):
 # Update progress
 self.run.set_progress(epoch + 1, epochs, "training")

 # Training step
 loss = train_epoch(dataset_path)

 # Log metrics
 self.run.set_metrics({"loss": loss}, "training")

 self.run.log_message("Training completed!")
 return {"status": "success", "final_loss": loss}
```

#### Creating Export Plugins

Export plugins now use the BaseExporter class-based approach for better organization and reusability. Here's how to create a custom export plugin:

**Step 1: Generate Export Plugin Template**

```bash
synapse plugin create
# Select 'export' as category
# Plugin will be created with export template
```

**Step 2: Customize Export Parameters**

The `ExportParams` model defines the required parameters:

```python
from synapse_sdk.plugins.categories.export.actions.export import ExportParams
from pydantic import BaseModel
from typing import Literal

class CustomExportParams(ExportParams):
 # Add custom parameters
 output_format: Literal['json', 'csv', 'xml'] = 'json'
 include_metadata: bool = True
 compression: bool = False
```

**Step 3: Implement Data Transformation**

Implement the required methods in your `Exporter` class in `plugin/export.py`:

```python
from datetime import datetime
from synapse_sdk.plugins.categories.export.templates.plugin import BaseExporter

class Exporter(BaseExporter):
 """Custom export plugin with COCO format conversion."""

 def convert_data(self, data):
 """Convert annotation data to your desired format."""
 # Example: Convert to COCO format
 if data.get('data_type') == 'image_detection':
 return self.convert_to_coco_format(data)
 elif data.get('data_type') == 'image_classification':
 return self.convert_to_classification_format(data)
 return data

 def before_convert(self, export_item):
 """Preprocess data before conversion."""
 # Add validation, filtering, or preprocessing
 if not export_item.get('data'):
 return None # Skip empty items

 # Add custom metadata
 export_item['processed_at'] = datetime.now().isoformat()
 return export_item

 def after_convert(self, converted_data):
 """Post-process converted data."""
 # Add final touches, validation, or formatting
 if 'annotations' in converted_data:
 converted_data['annotation_count'] = len(converted_data['annotations'])
 return converted_data

 def convert_to_coco_format(self, data):
 """Example: Convert to COCO detection format."""
 coco_data = {
 "images": [],
 "annotations": [],
 "categories": []
 }

 # Transform annotation data to COCO format
 for annotation in data.get('annotations', []):
 coco_annotation = {
 "id": annotation['id'],
 "image_id": annotation['image_id'],
 "category_id": annotation['category_id'],
 "bbox": annotation['bbox'],
 "area": annotation.get('area', 0),
 "iscrowd": 0
 }
 coco_data["annotations"].append(coco_annotation)

 return coco_data
```

**Step 4: Configure Export Targets**

The export action supports different data sources:

```python
# Filter examples for different targets
filters = {
 # For ground truth export
 "ground_truth": {
 "ground_truth_dataset_version": 123,
 "expand": ["data"]
 },

 # For assignment export
 "assignment": {
 "project": 456,
 "status": "completed",
 "expand": ["data"]
 },

 # For task export
 "task": {
 "project": 456,
 "assignment": 789,
 "expand": ["data_unit", "assignment"]
 }
}
```

**Step 5: Handle File Operations**

Customize file saving and organization by overriding BaseExporter methods:

```python
import json
from pathlib import Path
from synapse_sdk.plugins.categories.export.enums import ExportStatus

class Exporter(BaseExporter):
 """Custom export plugin with multiple format support."""

 def save_as_json(self, result, base_path, error_file_list):
 """Custom JSON saving with different formats."""
 file_name = Path(self.get_original_file_name(result['files'])).stem

 # Choose output format based on params
 if self.params.get('output_format') == 'csv':
 return self.save_as_csv(result, base_path, error_file_list)
 elif self.params.get('output_format') == 'xml':
 return self.save_as_xml(result, base_path, error_file_list)

 # Default JSON handling
 json_data = result['data']
 file_info = {'file_name': f'{file_name}.json'}

 try:
 with (base_path / f'{file_name}.json').open('w', encoding='utf-8') as f:
 json.dump(json_data, f, indent=4, ensure_ascii=False)
 status = ExportStatus.SUCCESS
 except Exception as e:
 error_file_list.append([f'{file_name}.json', str(e)])
 status = ExportStatus.FAILED

 self.run.export_log_json_file(result['id'], file_info, status)
 return status

 def setup_output_directories(self, unique_export_path, save_original_file_flag):
 """Custom directory structure."""
 # Create format-specific directories
 output_paths = super().setup_output_directories(unique_export_path, save_original_file_flag)

 # Add custom directories based on output format
 format_dir = unique_export_path / self.params.get('output_format', 'json')
 format_dir.mkdir(parents=True, exist_ok=True)
 output_paths['format_output_path'] = format_dir

 return output_paths
```

**Step 6: Usage Examples**

Running export plugins with different configurations:

```bash
# Basic export of ground truth data
synapse plugin run export '{
 "name": "my_export",
 "storage": 1,
 "target": "ground_truth",
 "filter": {"ground_truth_dataset_version": 123},
 "path": "exports/ground_truth",
 "save_original_file": true
}' --plugin my-export-plugin

# Export assignments with custom parameters
synapse plugin run export '{
 "name": "assignment_export",
 "storage": 1,
 "target": "assignment",
 "filter": {"project": 456, "status": "completed"},
 "path": "exports/assignments",
 "save_original_file": false,
 "extra_params": {
 "output_format": "coco",
 "include_metadata": true
 }
}' --plugin custom-coco-export
```

**Common Export Patterns:**

```python
# Pattern 1: Format-specific conversion
class Exporter(BaseExporter):
 def convert_data(self, data):
 """Convert to YOLO format."""
 if data.get('task_type') == 'object_detection':
 return self.convert_to_yolo_format(data)
 return data

# Pattern 2: Conditional file organization
class Exporter(BaseExporter):
 def setup_output_directories(self, unique_export_path, save_original_file_flag):
 # Call parent method
 output_paths = super().setup_output_directories(unique_export_path, save_original_file_flag)

 # Create separate folders by category
 for category in ['train', 'val', 'test']:
 category_path = unique_export_path / category
 category_path.mkdir(parents=True, exist_ok=True)
 output_paths[f'{category}_path'] = category_path

 return output_paths

# Pattern 3: Batch processing with validation
class Exporter(BaseExporter):
 def before_convert(self, export_item):
 # Validate required fields
 required_fields = ['data', 'files', 'id']
 for field in required_fields:
 if field not in export_item:
 raise ValueError(f"Missing required field: {field}")
 return export_item
```

### 3. Configure Actions

Define actions in `config.yaml`:

```yaml
actions:
 train:
 entrypoint: "plugin.train.TrainAction"
 method: "job"
 description: "Train a neural network model"

 # Export plugin configuration
 export:
 entrypoint: "plugin.export.Exporter"
 method: "job"
 description: "Export and transform annotation data"
```

### 4. Package and Publish

```bash
# Test locally
synapse plugin run train --debug

# Package for distribution
synapse plugin publish
```

## Running Plugins

### Command Line Interface

```bash
# Run a plugin action
synapse plugin run {action} {params}

# With specific plugin
synapse plugin run train '{"dataset_path": "/data/images", "epochs": 20}' --plugin my-plugin@1.0.0

# Debug mode (use local code)
synapse plugin run train '{"dataset_path": "/data/images"}' --debug

# Background job
synapse plugin run train '{"dataset_path": "/data/images"}' --job-id my-training-job
```

### Programmatic Usage

```python
from synapse_sdk.plugins.utils import get_action_class

# Get action class by category and name
ActionClass = get_action_class("neural_net", "train")

# Create and run action
action = ActionClass(
 params={"dataset_path": "/data/images", "epochs": 10},
 plugin_config=plugin_config,
 envs=env_vars
)

result = action.run_action()
```

## Development Workflow

### 1. Local Development

```bash
# Create plugin
synapse plugin create

# Develop and test locally
cd synapse-my-plugin-plugin
synapse plugin run action-name --debug

# Use development server for REST APIs
synapse plugin run serve --debug
```

### 2. Testing

```bash
# Run plugin tests
pytest plugin/test_*.py

# Integration testing with distributed computing
synapse plugin run action-name --debug --job-id test-job
```

### 3. Deployment

```bash
# Package plugin
synapse plugin publish

# Deploy to cluster
synapse plugin run action-name --job-id production-job
```

## Advanced Features

### Custom Progress Categories

```python
class MyAction(Action):
 progress_categories = {
 "preprocessing": "Data preprocessing",
 "training": "Model training",
 "validation": "Model validation"
 }

 def start(self):
 # Update different progress categories
 self.run.set_progress(50, 100, "preprocessing")
 self.run.set_progress(10, 50, "training")
```

### Custom Metrics

```python
def start(self):
 # Log custom metrics
 self.run.set_metrics({
 "accuracy": 0.95,
 "loss": 0.1,
 "f1_score": 0.92
 }, "validation")
```

### Runtime Environment Customization

```python
def get_runtime_env(self):
 env = super().get_runtime_env()

 # Add custom environment variables
 env['env_vars']['CUSTOM_VAR'] = 'value'

 # Add additional packages
 env['pip']['packages'].append('custom-package==1.0.0')

 return env
```

### Parameter Validation

```python
from pydantic import BaseModel, validator
from typing import Literal

class TrainParams(BaseModel):
 model_type: Literal["cnn", "transformer", "resnet"]
 dataset_path: str
 batch_size: int = 32

 @validator('batch_size')
 def validate_batch_size(cls, v):
 if v <= 0 or v > 512:
 raise ValueError('Batch size must be between 1 and 512')
 return v
```

## Best Practices

### 1. Plugin Design

- **Single Responsibility**: Each action should have a clear, focused purpose
- **Parameterization**: Make actions configurable through parameters
- **Error Handling**: Implement robust error handling and validation
- **Documentation**: Provide clear documentation and examples

### 2. Performance

- **Resource Management**: Use appropriate resource allocation for jobs
- **Progress Tracking**: Provide meaningful progress updates for long operations
- **Logging**: Log important events and errors for debugging
- **Memory Management**: Handle large datasets efficiently

### 3. Testing

- **Unit Tests**: Test individual action logic
- **Integration Tests**: Test with distributed execution environment
- **Parameter Validation**: Test edge cases and error conditions
- **Performance Tests**: Validate execution time and resource usage

### 4. Export Plugin Best Practices

#### Data Processing

- **Memory Efficiency**: Use generators for processing large datasets
- **Error Recovery**: Implement graceful error handling for individual items
- **Progress Reporting**: Update progress regularly for long-running exports
- **Data Validation**: Validate data structure before conversion

```python
class Exporter(BaseExporter):
 def export(self, export_items=None, results=None, **kwargs):
 """Override the main export method for custom processing."""
 # Use tee to count items without consuming generator
 items_to_process = export_items if export_items is not None else self.export_items
 export_items_count, export_items_process = tee(items_to_process)
 total = sum(1 for _ in export_items_count)

 # Custom processing with error handling
 for no, export_item in enumerate(export_items_process, start=1):
 try:
 # Use the built-in data conversion pipeline
 processed_item = self.process_data_conversion(export_item)
 self.run.set_progress(no, total, category='dataset_conversion')
 except Exception as e:
 self.run.log_message(f"Error processing item {no}: {str(e)}", "ERROR")
 continue

 # Call parent's export method for standard processing
 # or implement your own complete workflow
 return super().export(export_items, results, **kwargs)
```

#### File Management

- **Unique Paths**: Prevent file collisions with timestamp or counter suffixes
- **Directory Structure**: Organize output files logically
- **Error Logging**: Track failed files for debugging
- **Cleanup**: Remove temporary files on completion

```python
class Exporter(BaseExporter):
 def setup_output_directories(self, unique_export_path, save_original_file_flag):
 """Create unique export directory structure."""
 # BaseExporter already handles unique path creation via _create_unique_export_path
 # This method sets up the internal directory structure
 output_paths = super().setup_output_directories(unique_export_path, save_original_file_flag)

 # Add custom subdirectories as needed
 custom_dir = unique_export_path / 'custom_output'
 custom_dir.mkdir(parents=True, exist_ok=True)
 output_paths['custom_output_path'] = custom_dir

 return output_paths
```

#### Format Conversion

- **Flexible Templates**: Design templates that work with multiple data types
- **Schema Validation**: Validate output against expected schemas
- **Metadata Preservation**: Maintain important metadata during conversion
- **Version Compatibility**: Handle different data schema versions

### 5. Security

- **Input Validation**: Validate all parameters and inputs
- **File Access**: Restrict file system access appropriately
- **Dependencies**: Keep dependencies updated and secure
- **Secrets**: Never log sensitive information

## Monitoring and Debugging

### Plugin Execution Logs

```python
# In your action
self.run.log_message("Processing started", "INFO")
self.run.log_message("Warning: low memory", "WARNING")
self.run.log_message("Error occurred", "ERROR")

# With structured data
self.run.log("model_checkpoint", {
 "epoch": 10,
 "accuracy": 0.95,
 "checkpoint_path": "/models/checkpoint_10.pth"
})
```

### Progress Monitoring

```python
# Simple progress
self.run.set_progress(current=50, total=100)

# Categorized progress
self.run.set_progress(current=30, total=100, category="training")
self.run.set_progress(current=20, total=50, category="validation")
```

### Metrics Collection

```python
# Training metrics
self.run.set_metrics({
 "epoch": 10,
 "train_loss": 0.1,
 "train_accuracy": 0.95,
 "learning_rate": 0.001
}, "training")

# Performance metrics
self.run.set_metrics({
 "inference_time": 0.05,
 "throughput": 200,
 "memory_usage": 1024
}, "performance")
```

The plugin system provides a powerful foundation for building scalable, distributed ML workflows. By following the established patterns and best practices, you can create robust plugins that integrate seamlessly with the Synapse ecosystem.
