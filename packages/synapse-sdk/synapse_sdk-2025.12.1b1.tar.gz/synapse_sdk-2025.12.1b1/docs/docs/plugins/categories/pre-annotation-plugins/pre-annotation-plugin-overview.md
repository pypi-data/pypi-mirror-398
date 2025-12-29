---
id: pre-annotation-plugin-overview
title: Pre-annotation Plugin Overview
sidebar_position: 1
---

# Pre-annotation Plugin Overview

Pre-annotation plugins provide automated task annotation capabilities for the Synapse platform, enabling both file-based and AI-inference-based annotation workflows with comprehensive validation, progress tracking, and error handling.

## Quick Overview

**Category:** Pre-annotation
**Available Actions:** `to_task`
**Execution Method:** Job-based execution

## Key Features

- **File-based Annotation**: Automatically annotate tasks using JSON data from file URLs
- **Inference-based Annotation**: AI-powered annotation using pre-processor plugins and model inference
- **Strategy Pattern Architecture**: Pluggable validation, annotation, and metrics strategies
- **Workflow Orchestration**: 7-stage orchestrated workflow with automatic rollback on failure
- **Progress Tracking**: Real-time progress updates and comprehensive metrics
- **Flexible Task Filtering**: Advanced task filtering with multiple criteria

## Use Cases

- Bulk task annotation from pre-generated JSON files
- AI-powered auto-annotation using trained models
- Pre-labeling tasks before human review
- Dataset preparation with automated annotations
- Model-assisted annotation workflows
- Batch processing of pending tasks

## Supported Annotation Methods

### File-based Annotation (`method: 'file'`)

Retrieves annotation data from JSON files stored in data unit file specifications and applies them to tasks.

**When to use:**

- You have pre-generated annotation JSON files
- Annotations are stored as files in your data units
- You need deterministic, reproducible annotations
- External tools have generated annotation files

**Requirements:**

- `target_specification_name`: Name of the file specification containing annotation JSON
- Tasks must have data units with the specified file specification
- JSON files must be accessible via HTTP/HTTPS URLs

### Inference-based Annotation (`method: 'inference'`)

Uses pre-processor plugins to run model inference on task data and generate annotations automatically.

**When to use:**

- You have a trained model for automated annotation
- You want AI-assisted annotation
- You need to process images/data through a model
- You're implementing active learning workflows

**Requirements:**

- `pre_processor`: ID of a deployed pre-processor plugin
- Pre-processor must be active and running
- Tasks must have primary images or compatible data

## Configuration Overview

### Basic Parameters

```json
{
  "name": "Annotation Job",
  "description": "Annotate pending tasks",
  "project": 123,
  "agent": 1,
  "task_filters": {
    "status": "pending"
  },
  "method": "file"
}
```

### Key Parameters

| Parameter                   | Type    | Required    | Description                                        |
| --------------------------- | ------- | ----------- | -------------------------------------------------- |
| `name`                      | string  | Yes         | Action name (no whitespace)                        |
| `description`               | string  | No          | Action description                                 |
| `project`                   | integer | Yes         | Project ID                                         |
| `agent`                     | integer | Yes         | Agent ID                                           |
| `task_filters`              | object  | Yes         | Task filtering criteria                            |
| `method`                    | string  | Yes         | Annotation method: `'file'` or `'inference'`       |
| `target_specification_name` | string  | Conditional | File specification name (required for file method) |
| `pre_processor`             | integer | Conditional | Pre-processor ID (required for inference method)   |
| `pre_processor_params`      | object  | No          | Pre-processor configuration parameters             |

## Quick Start

### File-based Annotation Example

```python
from synapse_sdk.plugins.categories.pre_annotation.actions.to_task import ToTaskAction

params = {
    'name': 'File_Annotation_Job',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending',
        'data_collection': 456
    },
    'method': 'file',
    'target_specification_name': 'annotation_data'
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

### Inference-based Annotation Example

```python
params = {
    'name': 'AI_Annotation_Job',
    'project': 123,
    'agent': 1,
    'task_filters': {
        'status': 'pending'
    },
    'method': 'inference',
    'pre_processor': 789,
    'pre_processor_params': {
        'confidence_threshold': 0.8
    }
}

action = ToTaskAction(run=run_instance, params=params)
result = action.start()
```

## Workflow Stages

The to_task action executes through a 7-stage orchestrated workflow:

1. **Project Validation** - Verify project exists and has data collection
2. **Task Validation** - Find and validate tasks matching filters
3. **Method Determination** - Identify annotation method (file or inference)
4. **Method Validation** - Validate method-specific requirements
5. **Processing Initialization** - Set up metrics and progress tracking
6. **Task Processing** - Execute annotation strategy for each task
7. **Finalization** - Aggregate final metrics and results

Each stage is validated and can trigger automatic rollback on failure.

## Progress and Metrics

The action provides real-time updates on:

- **Progress Percentage**: Overall completion percentage
- **Success Count**: Number of successfully annotated tasks
- **Failed Count**: Number of tasks that failed annotation
- **Standby Count**: Number of tasks not yet processed

## Error Handling

### Task-Level Errors

Individual task failures are logged and tracked but do not stop the overall workflow. The action continues processing remaining tasks.

### Critical Errors

System-level errors (e.g., invalid project, network failures) trigger immediate workflow termination and rollback of completed steps.

### Automatic Rollback

On critical failures, the orchestrator automatically rolls back:

- Clears cached project data
- Resets task ID lists
- Cleans up temporary files
- Reverts metrics

## Next Steps

- **User Guide**: Read the [ToTask Overview](./to-task-overview.md) for detailed usage instructions
- **Developer Guide**: See the [ToTask Action Development](./to-task-action-development.md) for architecture details
- **API Reference**: Explore the complete API documentation

## Related Documentation

- [Upload Plugins](../upload-plugins/upload-plugin-overview.md) - File upload and data ingestion
- Plugin Development Guide - Creating custom plugins
- Pre-processor Plugins - Model deployment and inference
