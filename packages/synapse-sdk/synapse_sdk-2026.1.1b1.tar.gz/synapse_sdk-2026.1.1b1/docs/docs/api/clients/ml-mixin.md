---
id: ml-mixin
title: MLClientMixin
sidebar_position: 5
---

# MLClientMixin

Provides machine learning model management and ground truth operations for the Synapse backend.

## Overview

The `MLClientMixin` handles all operations related to machine learning models, ground truth datasets, and model evaluation workflows. This mixin is automatically included in the `BackendClient` and provides methods for ML pipeline integration.

## Model Management

### `list_models(params=None)`

List available machine learning models with filtering options.

```python
# List all models
models = client.list_models()
for model in models[0]:
    print(f"Model: {model['name']} (ID: {model['id']})")

# List models for a specific project
project_models = client.list_models(params={'project': 123})

# List models by type
classification_models = client.list_models(params={'model_type': 'classification'})

# List active models only
active_models = client.list_models(params={'is_active': True})
```

**Parameters:**

- `params` (dict, optional): Filtering parameters

**Common filtering params:**

- `project`: Filter by project ID
- `model_type`: Filter by model type (`classification`, `detection`, `segmentation`)
- `is_active`: Filter by model status
- `created_after`: Filter by creation date
- `search`: Text search in model names and descriptions

**Returns:**

- `tuple`: (models_list, total_count)

### `get_model(pk, params=None, url_conversion=None)`

Get detailed information about a specific model.

```python
# Get basic model info
model = client.get_model(456)
print(f"Model: {model['name']}")
print(f"Type: {model['model_type']}")
print(f"Accuracy: {model['metrics']['accuracy']}")

# Get model with expanded metrics
model = client.get_model(456, params={'expand': 'metrics'})

# Get model with custom URL conversion for files
model = client.get_model(
    456,
    url_conversion={'file': lambda url: f"https://cdn.example.com{url}"}
)
```

**Parameters:**

- `pk` (int): Model ID
- `params` (dict, optional): Query parameters
- `url_conversion` (dict, optional): Custom URL conversion for file fields

**Common params:**

- `expand`: Include additional data (`metrics`, `evaluations`, `versions`)
- `include_file`: Whether to include model file information

**Returns:**

- `dict`: Complete model information including metadata and metrics

**Model structure:**

- `id`: Model ID
- `name`: Model name
- `description`: Model description
- `model_type`: Type of model
- `file`: Model file reference
- `metrics`: Performance metrics
- `project`: Associated project ID
- `is_active`: Whether model is currently active
- `created_at`: Creation timestamp

### `create_model(data)`

Create a new machine learning model with file upload.

```python
# Create model with file upload
model_data = {
    'name': 'Object Detection Model v2',
    'description': 'Improved object detection with better accuracy',
    'model_type': 'detection',
    'project': 123,
    'metrics': {
        'accuracy': 0.92,
        'precision': 0.89,
        'recall': 0.94,
        'f1_score': 0.91
    },
    'configuration': {
        'input_size': [640, 640],
        'num_classes': 10,
        'framework': 'pytorch'
    },
    'file': '/path/to/model.pkl'  # Will be uploaded via chunked upload
}

new_model = client.create_model(model_data)
print(f"Created model with ID: {new_model['id']}")
```

**Parameters:**

- `data` (dict): Model configuration and metadata

**Model data structure:**

- `name` (str, required): Model name
- `description` (str): Model description
- `model_type` (str, required): Model type
- `project` (int, required): Project ID
- `file` (str, required): Path to model file
- `metrics` (dict): Performance metrics
- `configuration` (dict): Model configuration
- `is_active` (bool): Whether model should be active

**Returns:**

- `dict`: Created model with generated ID

**Note:** The model file is automatically uploaded using chunked upload for optimal performance.

## Ground Truth Operations

### `list_ground_truth_events(params=None, url_conversion=None, list_all=False)`

List ground truth events with comprehensive filtering options.

```python
# List ground truth events for a dataset version
events = client.list_ground_truth_events(params={
    'ground_truth_dataset_versions': [123]
})

# List all events (handles pagination automatically)
all_events = client.list_ground_truth_events(list_all=True)

# List events with date filtering
from datetime import datetime, timedelta
recent_date = (datetime.now() - timedelta(days=30)).isoformat()
recent_events = client.list_ground_truth_events(params={
    'created_after': recent_date,
    'ground_truth_dataset_versions': [123]
})

# List events with custom URL conversion
events = client.list_ground_truth_events(
    params={'ground_truth_dataset_versions': [123]},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**Parameters:**

- `params` (dict, optional): Filtering parameters
- `url_conversion` (dict, optional): Custom URL conversion for file fields
- `list_all` (bool): If True, automatically handles pagination

**Common filtering params:**

- `ground_truth_dataset_versions`: List of dataset version IDs
- `project`: Filter by project ID
- `created_after`: Filter by creation date
- `data_type`: Filter by data type
- `search`: Text search in event data

**Returns:**

- `tuple`: (events_list, total_count) if `list_all=False`
- `list`: All events if `list_all=True`

**Ground truth event structure:**

- `id`: Event ID
- `data`: Annotation/ground truth data
- `data_unit`: Associated data unit information
- `ground_truth_dataset_version`: Dataset version ID
- `created_at`: Creation timestamp
- `metadata`: Additional event metadata

### `get_ground_truth_version(pk)`

Get detailed information about a ground truth dataset version.

```python
version = client.get_ground_truth_version(123)
print(f"Dataset version: {version['version']}")
print(f"Dataset: {version['ground_truth_dataset']['name']}")
print(f"Total events: {version['event_count']}")
print(f"Created: {version['created_at']}")
```

**Parameters:**

- `pk` (int): Ground truth dataset version ID

**Returns:**

- `dict`: Complete dataset version information

**Dataset version structure:**

- `id`: Version ID
- `version`: Version number/name
- `ground_truth_dataset`: Parent dataset information
- `event_count`: Number of events in this version
- `description`: Version description
- `is_active`: Whether version is currently active
- `created_at`: Creation timestamp
- `statistics`: Version statistics and metrics

## Model Evaluation Workflows

### Model Performance Analysis

```python
def analyze_model_performance(model_id, ground_truth_version_id):
    """Analyze model performance against ground truth data."""

    # Get model details
    model = client.get_model(model_id, params={'expand': 'metrics'})
    print(f"Analyzing model: {model['name']}")

    # Get ground truth data
    gt_events = client.list_ground_truth_events(
        params={'ground_truth_dataset_versions': [ground_truth_version_id]},
        list_all=True
    )

    print(f"Ground truth events: {len(gt_events)}")

    # Extract metrics
    model_metrics = model.get('metrics', {})
    print("Model Metrics:")
    for metric, value in model_metrics.items():
        print(f"  {metric}: {value}")

    # Analyze ground truth distribution
    data_types = {}
    for event in gt_events:
        data_type = event['data'].get('type', 'unknown')
        data_types[data_type] = data_types.get(data_type, 0) + 1

    print("Ground Truth Distribution:")
    for data_type, count in data_types.items():
        print(f"  {data_type}: {count}")

    return {
        'model': model,
        'ground_truth_stats': data_types,
        'total_gt_events': len(gt_events)
    }

# Usage
analysis = analyze_model_performance(456, 123)
```

### Model Comparison

```python
def compare_models(model_ids, metric='accuracy'):
    """Compare multiple models by a specific metric."""
    models = []

    for model_id in model_ids:
        model = client.get_model(model_id, params={'expand': 'metrics'})
        models.append(model)

    # Sort by metric
    sorted_models = sorted(
        models,
        key=lambda m: m.get('metrics', {}).get(metric, 0),
        reverse=True
    )

    print(f"Models ranked by {metric}:")
    for i, model in enumerate(sorted_models, 1):
        metric_value = model.get('metrics', {}).get(metric, 'N/A')
        print(f"{i}. {model['name']}: {metric_value}")

    return sorted_models

# Compare models by accuracy
model_ranking = compare_models([456, 457, 458], metric='accuracy')
```

### Ground Truth Data Export

```python
def export_ground_truth_data(dataset_version_id, output_format='coco'):
    """Export ground truth data in specified format."""

    # Get dataset version info
    version = client.get_ground_truth_version(dataset_version_id)
    print(f"Exporting dataset: {version['ground_truth_dataset']['name']}")

    # Get all events
    events = client.list_ground_truth_events(
        params={'ground_truth_dataset_versions': [dataset_version_id]},
        list_all=True
    )

    if output_format == 'coco':
        # Convert to COCO format
        coco_data = {
            'info': {
                'description': version['description'],
                'version': version['version'],
                'year': 2023,
                'contributor': 'Synapse SDK'
            },
            'images': [],
            'annotations': [],
            'categories': []
        }

        # Process events
        for event in events:
            # Extract image info from data_unit
            data_unit = event['data_unit']
            files = data_unit.get('files', {})

            # Add image
            if 'image' in files:
                image_info = {
                    'id': data_unit['id'],
                    'file_name': files['image'].get('name', ''),
                    'width': files['image'].get('width', 0),
                    'height': files['image'].get('height', 0)
                }
                coco_data['images'].append(image_info)

            # Add annotations
            annotations = event['data'].get('annotations', [])
            for ann in annotations:
                annotation = {
                    'id': len(coco_data['annotations']),
                    'image_id': data_unit['id'],
                    'category_id': ann.get('category_id', 1),
                    'bbox': ann.get('bbox', []),
                    'area': ann.get('area', 0),
                    'iscrowd': ann.get('iscrowd', 0)
                }
                coco_data['annotations'].append(annotation)

        return coco_data

    else:
        # Return raw format
        return events

# Export as COCO format
coco_data = export_ground_truth_data(123, 'coco')
print(f"Exported {len(coco_data['images'])} images and {len(coco_data['annotations'])} annotations")
```

## Model Training Integration

### Training Data Preparation

```python
def prepare_training_data(project_id, split_ratio=0.8):
    """Prepare training and validation data from ground truth."""

    # Get all ground truth events for project
    events = client.list_ground_truth_events(
        params={'project': project_id},
        list_all=True
    )

    # Split data
    import random
    random.shuffle(events)
    split_point = int(len(events) * split_ratio)

    train_events = events[:split_point]
    val_events = events[split_point:]

    print(f"Training samples: {len(train_events)}")
    print(f"Validation samples: {len(val_events)}")

    return {
        'train': train_events,
        'validation': val_events,
        'total': len(events)
    }

# Prepare data
data_split = prepare_training_data(123, split_ratio=0.8)
```

### Model Deployment

```python
def deploy_model(model_path, model_config):
    """Deploy a trained model to the system."""

    # Create model entry
    model_data = {
        'name': model_config['name'],
        'description': model_config['description'],
        'model_type': model_config['type'],
        'project': model_config['project_id'],
        'file': model_path,
        'metrics': model_config.get('metrics', {}),
        'configuration': model_config.get('configuration', {}),
        'is_active': True
    }

    # Upload and create model
    model = client.create_model(model_data)
    print(f"Deployed model: {model['id']}")

    # Deactivate previous models if requested
    if model_config.get('replace_active', False):
        existing_models = client.list_models(params={
            'project': model_config['project_id'],
            'is_active': True
        })

        for existing_model in existing_models[0]:
            if existing_model['id'] != model['id']:
                # Note: You'd need an update_model method for this
                print(f"Would deactivate model: {existing_model['id']}")

    return model

# Deploy model
deployment_config = {
    'name': 'Production Object Detector v3',
    'description': 'Latest object detection model for production',
    'type': 'detection',
    'project_id': 123,
    'metrics': {'accuracy': 0.94, 'mAP': 0.87},
    'configuration': {'input_size': [640, 640], 'confidence_threshold': 0.5},
    'replace_active': True
}

deployed_model = deploy_model('/path/to/trained_model.pkl', deployment_config)
```

## Complete ML Workflow

```python
def complete_ml_workflow(project_id):
    """Complete machine learning workflow from data to deployed model."""

    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    print("=== ML Workflow Started ===")

    # 1. Analyze available ground truth data
    print("1. Analyzing ground truth data...")
    events = client.list_ground_truth_events(
        params={'project': project_id},
        list_all=True
    )
    print(f"Found {len(events)} ground truth events")

    # 2. Get existing models for comparison
    print("2. Checking existing models...")
    existing_models = client.list_models(params={'project': project_id})
    print(f"Found {len(existing_models[0])} existing models")

    # 3. Create and deploy new model (simulated)
    print("3. Deploying new model...")
    model_data = {
        'name': f'Auto-Generated Model for Project {project_id}',
        'description': 'Model created through automated workflow',
        'model_type': 'classification',
        'project': project_id,
        'file': '/path/to/new_model.pkl',  # In real scenario, this would be actual trained model
        'metrics': {
            'accuracy': 0.93,
            'precision': 0.91,
            'recall': 0.95,
            'f1_score': 0.93
        },
        'configuration': {
            'framework': 'pytorch',
            'input_size': [224, 224],
            'num_classes': 10
        }
    }

    new_model = client.create_model(model_data)
    print(f"Deployed model: {new_model['id']}")

    # 4. Compare with existing models
    print("4. Comparing model performance...")
    all_models = existing_models[0] + [new_model]
    best_model = max(all_models, key=lambda m: m.get('metrics', {}).get('accuracy', 0))
    print(f"Best model: {best_model['name']} (Accuracy: {best_model['metrics']['accuracy']})")

    print("=== ML Workflow Completed ===")
    return new_model

# Run workflow
if __name__ == "__main__":
    result = complete_ml_workflow(123)
```

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_model_operations():
    """Example of robust model operations with error handling."""

    try:
        # Try to get model
        model = client.get_model(999)
    except ClientError as e:
        if e.status_code == 404:
            print("Model not found")
            return None
        else:
            print(f"Error getting model: {e}")
            raise

    try:
        # Try to create model
        model_data = {
            'name': 'Test Model',
            'model_type': 'classification',
            'project': 123,
            'file': '/path/to/model.pkl'
        }
        new_model = client.create_model(model_data)
    except ClientError as e:
        if e.status_code == 400:
            print(f"Invalid model data: {e.response}")
        elif e.status_code == 413:
            print("Model file too large")
        else:
            print(f"Error creating model: {e}")
        return None

    return new_model
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [DataCollectionClientMixin](./data-collection-mixin.md) - Data management operations
- [IntegrationClientMixin](./integration-mixin.md) - Plugin and job management
