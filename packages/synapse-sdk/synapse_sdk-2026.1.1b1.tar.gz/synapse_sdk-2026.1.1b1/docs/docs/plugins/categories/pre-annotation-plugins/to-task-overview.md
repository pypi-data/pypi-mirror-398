---
id: to-task-overview
title: ToTask Action - User Guide
sidebar_position: 2
---

# ToTask Action - User Guide

The `to_task` action provides automated task annotation capabilities, supporting both file-based and AI inference-based annotation methods with comprehensive validation and progress tracking.

## Overview

The ToTask action annotates tasks in your Synapse project by:

- Retrieving annotation data from JSON files (file-based method)
- Running model inference through pre-processors (inference-based method)
- Applying annotations to task data automatically
- Tracking progress and metrics in real-time
- Handling errors gracefully with automatic rollback

## Prerequisites

### Common Requirements

- Valid Synapse project with tasks
- Data collection linked to the project
- Agent with appropriate permissions
- Tasks matching your filter criteria

### File-based Method Requirements

- Data units must have files matching the `target_specification_name`
- JSON files must be accessible via HTTP/HTTPS URLs
- JSON structure must match task object format

### Inference-based Method Requirements

- Deployed and active pre-processor plugin
- Pre-processor must support the data types in your tasks
- Tasks must have primary images or compatible input data

## Basic Usage

### File-based Annotation

Annotate tasks using JSON data from file URLs stored in data units.

```python
from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

# Configuration
params = {
    'name': 'File_Based_Annotation',
    'description': 'Annotate tasks from JSON files',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'file',
    'target_specification_name': 'annotation_data',
    'pre_processor_params': {}
}

# Execute
action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# Check result
if result['status'] == 'SUCCEEDED':
    print(f"Success: {result['message']}")
else:
    print(f"Failed: {result['message']}")
```

**How it works:**

1. System finds tasks matching the filters
2. For each task, retrieves the data unit
3. Finds files with specification name `annotation_data`
4. Downloads JSON data from the file URL
5. Applies the JSON data to the task
6. Tracks success/failure for each task

### Inference-based Annotation

Annotate tasks using AI model inference through a pre-processor.

```python
params = {
    'name': 'Inference_Based_Annotation',
    'description': 'Auto-annotate using AI model',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'assignee': None  # Unassigned tasks only
    },
    'method': 'inference',
    'pre_processor': 789,  # Pre-processor plugin release ID
    'pre_processor_params': {
        'confidence_threshold': 0.8,
        'model_config': {
            'batch_size': 16,
            'device': 'cuda'
        }
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

**How it works:**

1. System validates the pre-processor is active
2. Finds tasks matching the filters
3. For each task, extracts the primary image URL
4. Calls pre-processor API with image and parameters
5. Converts inference results to task object format
6. Updates task with generated annotations

## Parameter Reference

### Required Parameters

#### `name` (string)

- Action name identifier
- Must not contain whitespace
- Example: `"File_Annotation_Job"`

#### `project` (integer)

- Synapse project ID
- Must be a valid, accessible project
- Example: `123`

#### `agent` (integer)

- Agent ID for execution
- Agent must have permissions on the project
- Example: `1`

#### `task_filters` (object)

- Dictionary of filter criteria for task selection
- Supports all task query parameters
- Example: `{"status": "pending", "data_collection": 456}`

#### `method` (string)

- Annotation method type
- Values: `"file"` or `"inference"`
- Determines which annotation strategy to use

### Method-Specific Parameters

#### For File-based Method

**`target_specification_name`** (string, required for file method)

- Name of the file specification containing annotation JSON
- Must exist in the project's file specifications
- Example: `"annotation_data"`

#### For Inference-based Method

**`pre_processor`** (integer, required for inference method)

- Pre-processor plugin release ID
- Pre-processor must be deployed and active
- Example: `789`

**`pre_processor_params`** (object, optional)

- Configuration parameters passed to the pre-processor
- Structure depends on the pre-processor implementation
- Example:
  ```python
  {
      'confidence_threshold': 0.8,
      'model_config': {
          'batch_size': 16,
          'device': 'cuda',
          'use_fp16': True
      },
      'post_processing': {
          'nms_threshold': 0.5,
          'min_size': 10
      }
  }
  ```

### Optional Parameters

#### `description` (string)

- Human-readable description of the action
- Example: `"Annotate all pending tasks with model v2 predictions"`

## Task Filtering

The `task_filters` parameter supports rich filtering options:

### Common Filter Examples

```python
# Filter by status
task_filters = {'status': 'pending'}

# Filter by data collection
task_filters = {'data_collection': 456}

# Filter by assignee
task_filters = {'assignee': 12}  # Specific user
task_filters = {'assignee': None}  # Unassigned tasks

# Multiple filters (AND logic)
task_filters = {
    'status': 'pending',
    'data_collection': 456,
    'assignee': None
}

# Filter by creation date
task_filters = {
    'created_at__gte': '2025-01-01',
    'created_at__lte': '2025-01-31'
}
```

### Advanced Filtering

```python
# Combine multiple criteria
task_filters = {
    'status__in': ['pending', 'in_progress'],
    'data_collection': 456,
    'created_at__gte': '2025-01-01'
}
```

## Progress and Metrics

### Real-time Progress Updates

The action provides continuous progress updates:

```python
# Progress is logged automatically during execution
# Example log output:
# [annotate_task_data] Progress: 25.0% (25/100)
# [annotate_task_data] Progress: 50.0% (50/100)
# [annotate_task_data] Progress: 100.0% (100/100)
```

### Metrics Categories

**Success Metrics:**

- Total tasks processed
- Successfully annotated count
- Failed annotation count
- Standby (not yet processed) count

**Status Messages:**

```python
# Example metrics output
{
    'total': 100,
    'success': 95,
    'failed': 5,
    'stand_by': 0
}
```

### Accessing Metrics

Metrics are automatically logged to the run logger and can be accessed through the Synapse platform UI or API.

## File-based Annotation Details

### Expected JSON Structure

The JSON files must follow the task data object format:

```json
{
  "objects": [
    {
      "id": "obj_001",
      "class_id": 1,
      "type": "bbox",
      "coordinates": {
        "x": 100,
        "y": 150,
        "width": 200,
        "height": 180
      },
      "properties": {
        "confidence": 0.95,
        "label": "person"
      }
    }
  ]
}
```

### File Specification Setup

1. **Define file specification** in your project with the target name (e.g., `annotation_data`)
2. **Upload annotation JSON files** to data units under this specification
3. **Ensure files are accessible** via HTTP/HTTPS URLs
4. **Run the ToTask action** with `target_specification_name` matching your specification

### Example Workflow

```python
# Step 1: Prepare your data
# - Upload images to data collection
# - Upload annotation JSON files with specification "annotations"

# Step 2: Configure and run
params = {
    'name': 'Apply_Pregenerated_Annotations',
    'project': 123,
    'agent': 1,
    'task_filters': {'status': 'pending'},
    'method': 'file',
    'target_specification_name': 'annotations'
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

## Inference-based Annotation Details

### Pre-processor Requirements

Your pre-processor must:

- Be deployed and in `RUNNING` status
- Accept image URLs as input
- Return results in task-compatible format
- Support the data types in your tasks

### Pre-processor Parameters

Configure inference behavior through `pre_processor_params`:

```python
pre_processor_params = {
    # Model configuration
    'model_config': {
        'batch_size': 16,
        'device': 'cuda',
        'use_fp16': True
    },

    # Inference thresholds
    'confidence_threshold': 0.8,
    'nms_threshold': 0.5,

    # Post-processing
    'min_object_size': 10,
    'max_objects': 100,

    # Output formatting
    'include_masks': True,
    'output_format': 'coco'
}
```

### Inference Workflow

```python
# Step 1: Deploy your pre-processor
# (See Pre-processor Plugin documentation)

# Step 2: Configure inference annotation
params = {
    'name': 'AI_Auto_Annotation',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.85,
        'model_config': {
            'device': 'cuda'
        }
    }
}

# Step 3: Execute
action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# Step 4: Review results
# Check success/failed counts in metrics
# Review annotated tasks in Synapse UI
```

### Pre-processor Management

The system automatically:

- Checks if pre-processor is running
- Starts the pre-processor if needed
- Waits for pre-processor to be ready
- Handles pre-processor errors gracefully

## Error Handling

### Task-level Errors

Individual task failures don't stop the workflow:

```python
# Example: 100 tasks to process
# - 95 succeed
# - 5 fail (e.g., invalid JSON, network errors)
# Result: Job completes with success=95, failed=5
```

Failed tasks are logged with error details:

```
[Task 123] Failed: Invalid JSON format in annotation file
[Task 456] Failed: Pre-processor inference timeout
```

### Critical Errors

System-level errors trigger immediate rollback:

```python
# Critical error examples:
# - Project not found
# - No data collection linked
# - Target specification doesn't exist
# - Pre-processor not deployed

# On critical error:
# 1. Workflow stops immediately
# 2. Completed steps are rolled back
# 3. Temporary files are cleaned up
# 4. Error is raised with detailed message
```

### Common Errors and Solutions

#### "Project has no data collection"

**Solution:** Link a data collection to your project before running.

#### "Target specification not found"

**Solution:** Verify the `target_specification_name` exists in project file specifications.

#### "Pre-processor not active"

**Solution:** Deploy and start your pre-processor before running inference annotation.

#### "No tasks found matching filters"

**Solution:** Check your `task_filters` criteria and verify tasks exist.

#### "Failed to download JSON from URL"

**Solution:** Ensure annotation files are accessible and URLs are valid.

## Best Practices

### Performance Optimization

1. **Batch size for inference**

   ```python
   pre_processor_params = {
       'model_config': {
           'batch_size': 32  # Adjust based on GPU memory
       }
   }
   ```

2. **Filter tasks effectively**

   ```python
   # Good: Specific filters
   task_filters = {
       'status': 'pending',
       'data_collection': 456,
       'created_at__gte': '2025-01-01'
   }

   # Avoid: Too broad
   task_filters = {'status': 'pending'}  # May match thousands
   ```

3. **Use appropriate confidence thresholds**

   ```python
   # Higher threshold = fewer false positives
   pre_processor_params = {
       'confidence_threshold': 0.9  # Strict
   }

   # Lower threshold = more detections
   pre_processor_params = {
       'confidence_threshold': 0.5  # Permissive
   }
   ```

### Reliability

1. **Validate data before processing**

   - Check that tasks have required data (images, files)
   - Verify file specifications exist
   - Ensure pre-processors are tested and stable

2. **Monitor progress**

   - Review progress logs during execution
   - Check metrics after completion
   - Investigate failed tasks

3. **Handle partial failures**
   ```python
   # After execution, check metrics
   if result['status'] == 'SUCCEEDED':
       # Check if all tasks succeeded
       # Review failed count
       # Re-run for failed tasks if needed
   ```

### Security

1. **File access validation**

   - Ensure JSON files are from trusted sources
   - Validate file content before upload
   - Use secure HTTPS URLs

2. **Input validation**
   - Validate pre-processor parameters
   - Check confidence thresholds are reasonable
   - Verify task filters don't expose sensitive data

## Complete Examples

### Example 1: Bulk File-based Annotation

```python
"""
Scenario: You have 1000 images with pre-generated annotation JSON files.
Goal: Apply all annotations to pending tasks.
"""

from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

params = {
    'name': 'Bulk_File_Annotation_Jan2025',
    'description': 'Apply pre-generated annotations from external tool',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456,
        'created_at__gte': '2025-01-01'
    },
    'method': 'file',
    'target_specification_name': 'external_annotations',
    'pre_processor_params': {}
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
```

### Example 2: AI-powered Auto-annotation

```python
"""
Scenario: You have a trained object detection model deployed as a pre-processor.
Goal: Auto-annotate all unassigned tasks with high-confidence predictions.
"""

params = {
    'name': 'AI_Object_Detection_v2',
    'description': 'Auto-detect objects using YOLOv8 model',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'assignee': None,  # Only unassigned
        'data_collection': 789
    },
    'method': 'inference',
    'pre_processor': 456,
    'pre_processor_params': {
        'confidence_threshold': 0.85,
        'nms_threshold': 0.5,
        'model_config': {
            'batch_size': 16,
            'device': 'cuda',
            'use_fp16': True
        },
        'class_filter': [1, 2, 3],  # Only detect specific classes
        'min_object_size': 20
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()

# Check results
if result['status'] == 'SUCCEEDED':
    print("Auto-annotation completed successfully")
    # Review tasks in Synapse UI for quality check
else:
    print(f"Failed: {result['message']}")
```

### Example 3: Active Learning Workflow

```python
"""
Scenario: Iterative model improvement with active learning.
Goal: Auto-annotate with model, review uncertain cases manually.
"""

# Step 1: Auto-annotate with medium confidence
params_high_confidence = {
    'name': 'Active_Learning_Round1_High',
    'project': 123,
    'agent': 1,
    'task_filters': {'status': 'pending'},
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.9  # High confidence only
    }
}

action = ToTaskAction(run=run_instance, params=params_high_confidence)
result = action.start()

# Step 2: Low confidence cases go to manual review
# (These remain pending for human annotators)

# Step 3: After manual review, retrain model and repeat
```

## Troubleshooting

### Debugging Failed Tasks

1. **Check logs for specific errors**

   ```
   Look for messages like:
   [Task 123] Failed: <error_message>
   ```

2. **Verify task data structure**

   - Ensure tasks have required fields
   - Check data units exist
   - Validate file URLs are accessible

3. **Test with small batch first**
   ```python
   # Test with 10 tasks first
   task_filters = {
       'status': 'pending',
       'limit': 10
   }
   ```

### Performance Issues

1. **Reduce batch size** if experiencing timeouts
2. **Filter tasks more narrowly** to process smaller groups
3. **Check pre-processor resource usage** for inference method

### Validation Errors

1. **"No tasks found"** - Verify filters and task existence
2. **"Invalid project"** - Check project ID and permissions
3. **"Target specification not found"** - Verify file specification name
4. **"Pre-processor not found"** - Check pre-processor ID and status

## Next Steps

- **Architecture Details**: Read [ToTask Action Development](./to-task-action-development.md) for technical architecture
- **Custom Strategies**: Learn how to extend the ToTask action with custom validation and annotation strategies
- **Pre-processor Guide**: See Pre-processor Plugin documentation for model deployment

## Related Documentation

- [Pre-annotation Plugin Overview](./pre-annotation-plugin-overview.md)
- [Upload Plugins](../upload-plugins/upload-plugin-overview.md)
- Plugin Development Guide
- API Reference
