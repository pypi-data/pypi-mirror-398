---
id: to-task-template-development
title: ToTask Template Development with AnnotationToTask
sidebar_position: 4
---

# ToTask Template Development with AnnotationToTask

This guide is for plugin developers who want to create custom pre-annotation plugins using the `AnnotationToTask` template. The AnnotationToTask template provides a simple interface for converting data to task annotations in Synapse projects.

## Overview

The `AnnotationToTask` template (`synapse_sdk.plugins.categories.pre_annotation.templates.plugin.to_task`) provides a structured approach to building pre-annotation plugins. It handles the workflow integration while you focus on implementing custom data conversion logic.

### What is AnnotationToTask?

`AnnotationToTask` is a template class that defines two key conversion methods:
- **`convert_data_from_file()`**: Convert JSON data from files into task annotations
- **`convert_data_from_inference()`**: Convert model inference results into task annotations

The ToTaskAction framework automatically calls these methods during the annotation workflow, allowing you to customize how data is transformed into task objects.

### When to Use This Template

Use the AnnotationToTask template when you need to:
- Transform external annotation data into Synapse task format
- Convert model predictions to task annotations
- Implement custom data validation and transformation logic
- Create reusable annotation conversion plugins

## Getting Started

### Template Structure

When you create a pre-annotation plugin using the ToTask template, you get this structure:

```
synapse-{plugin-code}-plugin/
├── config.yaml              # Plugin metadata and configuration
├── plugin/                  # Source code directory
│   ├── __init__.py
│   └── to_task.py          # AnnotationToTask implementation
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Package configuration
└── README.md               # Plugin documentation
```

### Basic Plugin Implementation

```python
# plugin/to_task.py
class AnnotationToTask:
    """Template for custom annotation conversion logic."""

    def __init__(self, run, *args, **kwargs):
        """Initialize the plugin task pre annotation action class.

        Args:
            run: Plugin run object providing logging and context.
        """
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """Convert data from a file to a task object.

        Args:
            primary_file_url: URL of the primary file (e.g., image being annotated)
            primary_file_original_name: Original name of primary file
            data_file_url: URL of the annotation data file (JSON)
            data_file_original_name: Original name of annotation file

        Returns:
            dict: Task object with annotations in Synapse format
        """
        # Your custom implementation here
        converted_data = {}
        return converted_data

    def convert_data_from_inference(self, data: dict) -> dict:
        """Convert data from inference result to a task object.

        Args:
            data: Raw inference results from pre-processor

        Returns:
            dict: Task object with annotations in Synapse format
        """
        # Your custom implementation here
        return data
```

## AnnotationToTask Class Reference

### Constructor

```python
def __init__(self, run, *args, **kwargs):
```

**Parameters:**
- `run`: Plugin run object providing logging and context access
  - Use `self.run.log_message(msg)` for logging
  - Access configuration via `self.run.params`

**Usage:**
```python
def __init__(self, run, *args, **kwargs):
    self.run = run
    # Initialize any custom attributes
    self.confidence_threshold = 0.8
    self.custom_mapping = {}
```

### Method: convert_data_from_file()

Converts annotation data from a JSON file into Synapse task object format.

```python
def convert_data_from_file(
    self,
    primary_file_url: str,
    primary_file_original_name: str,
    data_file_url: str,
    data_file_original_name: str,
) -> dict:
```

**Parameters:**
- `primary_file_url` (str): HTTP/HTTPS URL of the primary file (e.g., the image being annotated)
- `primary_file_original_name` (str): Original filename of the primary file
- `data_file_url` (str): HTTP/HTTPS URL of the annotation JSON file
- `data_file_original_name` (str): Original filename of the annotation file

**Returns:**
- `dict`: Task object containing annotations in Synapse format

**Called By:**
- `FileAnnotationStrategy` during file-based annotation workflow

**Workflow:**
1. Download JSON data from `data_file_url`
2. Parse and validate the JSON structure
3. Transform data to match Synapse task object schema
4. Return formatted task object

**Example Implementation:**

```python
import requests
import json

def convert_data_from_file(
    self,
    primary_file_url: str,
    primary_file_original_name: str,
    data_file_url: str,
    data_file_original_name: str,
) -> dict:
    """Convert COCO format annotations to Synapse task format."""

    # Download annotation file
    response = requests.get(data_file_url, timeout=30)
    response.raise_for_status()
    coco_data = response.json()

    # Extract annotations
    annotations = coco_data.get('annotations', [])

    # Convert to Synapse format
    task_objects = []
    for idx, ann in enumerate(annotations):
        task_object = {
            'id': f'obj_{idx}',
            'class_id': ann['category_id'],
            'type': 'bbox',
            'coordinates': {
                'x': ann['bbox'][0],
                'y': ann['bbox'][1],
                'width': ann['bbox'][2],
                'height': ann['bbox'][3]
            },
            'properties': {
                'area': ann.get('area', 0),
                'iscrowd': ann.get('iscrowd', 0)
            }
        }
        task_objects.append(task_object)

    # Log conversion info
    self.run.log_message(
        f'Converted {len(task_objects)} COCO annotations from {data_file_original_name}'
    )

    return {'objects': task_objects}
```

### Method: convert_data_from_inference()

Converts model inference results into Synapse task object format.

```python
def convert_data_from_inference(self, data: dict) -> dict:
```

**Parameters:**
- `data` (dict): Raw inference results from the pre-processor plugin

**Returns:**
- `dict`: Task object containing annotations in Synapse format

**Called By:**
- `InferenceAnnotationStrategy` during inference-based annotation workflow

**Workflow:**
1. Receive inference results from pre-processor
2. Extract predictions, bounding boxes, classes, etc.
3. Transform to Synapse task object schema
4. Apply any filtering or post-processing
5. Return formatted task object

**Example Implementation:**

```python
def convert_data_from_inference(self, data: dict) -> dict:
    """Convert YOLOv8 detection results to Synapse task format."""

    # Extract detections from inference results
    detections = data.get('detections', [])

    # Filter by confidence threshold
    confidence_threshold = 0.5
    task_objects = []

    for idx, det in enumerate(detections):
        confidence = det.get('confidence', 0)

        # Skip low-confidence detections
        if confidence < confidence_threshold:
            continue

        # Convert to Synapse format
        task_object = {
            'id': f'det_{idx}',
            'class_id': det['class_id'],
            'type': 'bbox',
            'coordinates': {
                'x': det['bbox']['x'],
                'y': det['bbox']['y'],
                'width': det['bbox']['width'],
                'height': det['bbox']['height']
            },
            'properties': {
                'confidence': confidence,
                'class_name': det.get('class_name', 'unknown')
            }
        }
        task_objects.append(task_object)

    # Log conversion info
    self.run.log_message(
        f'Converted {len(task_objects)} detections '
        f'(filtered from {len(detections)} total)'
    )

    return {'objects': task_objects}
```

## Using SDK Data Converters

The Synapse SDK provides built-in data converters that handle common annotation formats (COCO, YOLO, Pascal VOC). Instead of writing custom parsing logic, you can leverage these converters in your templates for faster development and better reliability.

### Why Use SDK Converters?

- **Proven & Tested**: Converters are maintained and tested by the SDK team
- **Standard Formats**: Support for COCO, YOLO, Pascal VOC out of the box
- **Less Code**: Avoid reimplementing format parsers
- **Consistent**: Same conversion logic across all plugins
- **Error Handling**: Built-in validation and error messages

### Available Converters

| Converter | Format | Direction | Module Path | Use Case |
|-----------|--------|-----------|-------------|----------|
| `COCOToDMConverter` | COCO JSON | External → DM | `synapse_sdk.utils.converters.coco` | COCO format annotations |
| `YOLOToDMConverter` | YOLO .txt | External → DM | `synapse_sdk.utils.converters.yolo` | YOLO format labels |
| `PascalToDMConverter` | Pascal VOC XML | External → DM | `synapse_sdk.utils.converters.pascal` | Pascal VOC annotations |
| `DMV2ToV1Converter` | DM v2 | DM v2 → DM v1 | `synapse_sdk.utils.converters.dm` | Version conversion |
| `DMV1ToV2Converter` | DM v1 | DM v1 → DM v2 | `synapse_sdk.utils.converters.dm` | Version conversion |

**DM Format**: Synapse's internal Data Manager format (what task objects use)

### Using Converters in Templates

All To-DM converters provide a `convert_single_file()` method specifically designed for template usage.

#### In convert_data_from_file()

```python
import requests
from synapse_sdk.utils.converters.coco import COCOToDMConverter

class AnnotationToTask:
    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """Convert COCO annotations using SDK converter."""

        # Download annotation file
        response = requests.get(data_file_url, timeout=30)
        response.raise_for_status()
        coco_data = response.json()

        # Create converter in single-file mode
        converter = COCOToDMConverter(is_single_conversion=True)

        # Create a mock file object with the image path
        class FileObj:
            def __init__(self, name):
                self.name = name

        # Convert using SDK converter
        result = converter.convert_single_file(
            data=coco_data,
            original_file=FileObj(primary_file_url),
            original_image_name=primary_file_original_name
        )

        # Return the DM format data
        return result['dm_json']
```

#### In convert_data_from_inference()

```python
from synapse_sdk.utils.converters.dm import DMV2ToV1Converter

class AnnotationToTask:
    def convert_data_from_inference(self, data: dict) -> dict:
        """Convert inference results with optional DM version conversion."""

        # Your inference result processing
        dm_v2_data = self._process_inference_results(data)

        # Optionally convert DM v2 to v1 if needed
        if self._needs_v1_format():
            converter = DMV2ToV1Converter(new_dm_data=dm_v2_data)
            dm_v1_data = converter.convert()
            return dm_v1_data

        return dm_v2_data
```

### Converter Examples

#### Example 1: COCO Converter

Complete implementation using `COCOToDMConverter`:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.coco import COCOToDMConverter

class AnnotationToTask:
    """Use SDK COCO converter for annotation conversion."""

    def __init__(self, run, *args, **kwargs):
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """Convert COCO JSON to Synapse task format using SDK converter."""

        try:
            # Download COCO annotation file
            self.run.log_message(f'Downloading COCO annotations: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            coco_data = response.json()

            # Validate COCO structure
            if 'annotations' not in coco_data or 'images' not in coco_data:
                raise ValueError('Invalid COCO format: missing required fields')

            # Create converter for single file conversion
            converter = COCOToDMConverter(is_single_conversion=True)

            # Create file object
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # Convert using SDK converter
            result = converter.convert_single_file(
                data=coco_data,
                original_file=MockFile(primary_file_url),
                original_image_name=primary_file_original_name
            )

            self.run.log_message(
                f'Successfully converted COCO data using SDK converter'
            )

            # Return DM format
            return result['dm_json']

        except requests.RequestException as e:
            self.run.log_message(f'Failed to download annotations: {str(e)}')
            raise
        except ValueError as e:
            self.run.log_message(f'Invalid COCO data: {str(e)}')
            raise
        except Exception as e:
            self.run.log_message(f'Conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """Not used for this plugin."""
        return data
```

**Supported COCO Features:**
- Bounding boxes
- Keypoints
- Groups (bbox + keypoints)
- Category mapping
- Attributes

#### Example 2: YOLO Converter

Complete implementation using `YOLOToDMConverter`:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.yolo import YOLOToDMConverter

class AnnotationToTask:
    """Use SDK YOLO converter for label conversion."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # YOLO class names (must match your model)
        self.class_names = ['person', 'car', 'truck', 'bicycle']

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """Convert YOLO labels to Synapse task format using SDK converter."""

        try:
            # Download YOLO label file
            self.run.log_message(f'Downloading YOLO labels: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            label_text = response.text

            # Parse label lines
            label_lines = [line.strip() for line in label_text.splitlines() if line.strip()]

            # Create converter with class names
            converter = YOLOToDMConverter(
                is_single_conversion=True,
                class_names=self.class_names
            )

            # Create file object
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # Convert using SDK converter
            result = converter.convert_single_file(
                data=label_lines,  # List of label strings
                original_file=MockFile(primary_file_url)
            )

            self.run.log_message(
                f'Successfully converted {len(label_lines)} YOLO labels'
            )

            return result['dm_json']

        except Exception as e:
            self.run.log_message(f'YOLO conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """Not used for this plugin."""
        return data
```

**Supported YOLO Features:**
- Bounding boxes (standard YOLO format)
- Polygons (segmentation format)
- Keypoints (pose estimation format)
- Automatic coordinate denormalization
- Class name mapping

#### Example 3: Pascal VOC Converter

Complete implementation using `PascalToDMConverter`:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.pascal import PascalToDMConverter

class AnnotationToTask:
    """Use SDK Pascal VOC converter for XML annotation conversion."""

    def __init__(self, run, *args, **kwargs):
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """Convert Pascal VOC XML to Synapse task format using SDK converter."""

        try:
            # Download Pascal VOC XML file
            self.run.log_message(f'Downloading Pascal VOC XML: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            xml_content = response.text

            # Create converter
            converter = PascalToDMConverter(is_single_conversion=True)

            # Create file object
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # Convert using SDK converter
            result = converter.convert_single_file(
                data=xml_content,  # XML string
                original_file=MockFile(primary_file_url)
            )

            self.run.log_message('Successfully converted Pascal VOC annotations')

            return result['dm_json']

        except Exception as e:
            self.run.log_message(f'Pascal VOC conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """Not used for this plugin."""
        return data
```

**Supported Pascal VOC Features:**
- Bounding boxes (xmin, ymin, xmax, ymax)
- Object names/classes
- Automatic width/height calculation
- XML parsing and validation

### Best Practices with Converters

#### 1. When to Use Converters

**Use SDK Converters When:**
- Working with standard formats (COCO, YOLO, Pascal VOC)
- Need reliable, tested conversion logic
- Want to minimize maintenance burden
- Working with complex formats (COCO with keypoints, YOLO segmentation)

**Write Custom Code When:**
- Format is non-standard or proprietary
- Need special preprocessing before conversion
- Converter doesn't support your specific variant
- Performance optimization is critical

#### 2. Error Handling with Converters

Always wrap converter calls in try-except blocks:

```python
def convert_data_from_file(self, *args) -> dict:
    try:
        converter = COCOToDMConverter(is_single_conversion=True)
        result = converter.convert_single_file(...)
        return result['dm_json']

    except ValueError as e:
        # Validation errors from converter
        self.run.log_message(f'Invalid data format: {str(e)}')
        raise

    except KeyError as e:
        # Missing required fields
        self.run.log_message(f'Missing field in result: {str(e)}')
        raise

    except Exception as e:
        # Unexpected errors
        self.run.log_message(f'Converter error: {str(e)}')
        raise
```

#### 3. Combining Converters with Custom Logic

You can post-process converter output:

```python
def convert_data_from_file(self, *args) -> dict:
    # Use converter for basic conversion
    converter = YOLOToDMConverter(
        is_single_conversion=True,
        class_names=self.class_names
    )
    result = converter.convert_single_file(...)
    dm_data = result['dm_json']

    # Add custom post-processing
    for img in dm_data.get('images', []):
        for bbox in img.get('bounding_box', []):
            # Add custom attributes
            bbox['attrs'].append({
                'name': 'source',
                'value': 'yolo_model_v2'
            })

            # Filter by size
            if bbox['data'][2] < 10 or bbox['data'][3] < 10:
                # Mark small boxes
                bbox['attrs'].append({
                    'name': 'too_small',
                    'value': True
                })

    return dm_data
```

#### 4. Performance Considerations

**Converters are optimized but:**
- Download files efficiently (use timeouts, streaming if large)
- Cache converter instances if processing multiple files
- Log conversion progress for monitoring

```python
def __init__(self, run, *args, **kwargs):
    self.run = run
    # Cache converter instance
    self.coco_converter = COCOToDMConverter(is_single_conversion=True)

def convert_data_from_file(self, *args) -> dict:
    # Reuse cached converter
    result = self.coco_converter.convert_single_file(...)
    return result['dm_json']
```

#### 5. Testing with Converters

Test both converter integration and edge cases:

```python
# test_to_task.py
import pytest
from plugin.to_task import AnnotationToTask

class MockRun:
    def log_message(self, msg):
        print(msg)

def test_coco_converter_integration():
    """Test COCO converter integration."""
    converter = AnnotationToTask(MockRun())

    # Test with valid COCO data
    coco_data = {
        'images': [{'id': 1, 'file_name': 'test.jpg'}],
        'annotations': [{
            'id': 1,
            'image_id': 1,
            'category_id': 1,
            'bbox': [10, 20, 100, 200]
        }],
        'categories': [{'id': 1, 'name': 'person'}]
    }

    result = converter._convert_with_coco_converter(coco_data, 'test.jpg')

    # Verify DM structure
    assert 'images' in result
    assert len(result['images']) == 1
    assert 'bounding_box' in result['images'][0]

def test_invalid_format_handling():
    """Test error handling for invalid data."""
    converter = AnnotationToTask(MockRun())

    # Test with invalid COCO data
    invalid_data = {'invalid': 'data'}

    with pytest.raises(ValueError):
        converter._convert_with_coco_converter(invalid_data, 'test.jpg')
```

### Converter API Reference

#### COCOToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: Dict[str, Any],
    original_file: IO,
    original_image_name: str
) -> Dict[str, Any]:
```

**Parameters:**
- `data`: COCO format dictionary (JSON content)
- `original_file`: File object with `.name` attribute
- `original_image_name`: Name of the image file

**Returns:**
```python
{
    'dm_json': {...},        # DM format data
    'image_path': str,       # Path from file object
    'image_name': str        # Basename of image
}
```

#### YOLOToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: List[str],
    original_file: IO
) -> Dict[str, Any]:
```

**Parameters:**
- `data`: List of YOLO label lines (strings from .txt file)
- `original_file`: File object with `.name` attribute

**Returns:**
```python
{
    'dm_json': {...},        # DM format data
    'image_path': str,       # Path from file object
    'image_name': str        # Basename of image
}
```

#### PascalToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: str,
    original_file: IO
) -> Dict[str, Any]:
```

**Parameters:**
- `data`: Pascal VOC XML content as string
- `original_file`: File object with `.name` attribute

**Returns:**
```python
{
    'dm_json': {...},        # DM format data
    'image_path': str,       # Path from file object
    'image_name': str        # Basename of image
}
```

## Complete Examples

### Example 1: COCO Format Annotation Plugin

A complete plugin for converting COCO format annotations to Synapse tasks.

```python
# plugin/to_task.py
import requests
import json
from typing import Dict, List

class AnnotationToTask:
    """Convert COCO format annotations to Synapse task objects."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # COCO category ID to Synapse class ID mapping
        self.category_mapping = {
            1: 1,   # person
            2: 2,   # bicycle
            3: 3,   # car
            # Add more mappings as needed
        }

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """Convert COCO JSON file to Synapse task format."""

        try:
            # Download COCO annotation file
            self.run.log_message(f'Downloading: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            coco_data = response.json()

            # Validate COCO structure
            if 'annotations' not in coco_data:
                raise ValueError('Invalid COCO format: missing annotations')

            # Convert annotations
            task_objects = self._convert_coco_annotations(
                coco_data['annotations']
            )

            self.run.log_message(
                f'Successfully converted {len(task_objects)} annotations'
            )

            return {
                'objects': task_objects,
                'metadata': {
                    'source': 'coco',
                    'file': data_file_original_name
                }
            }

        except requests.RequestException as e:
            self.run.log_message(f'Failed to download file: {str(e)}')
            raise
        except json.JSONDecodeError as e:
            self.run.log_message(f'Invalid JSON format: {str(e)}')
            raise
        except Exception as e:
            self.run.log_message(f'Conversion failed: {str(e)}')
            raise

    def _convert_coco_annotations(self, annotations: List[Dict]) -> List[Dict]:
        """Convert COCO annotations to Synapse task objects."""
        task_objects = []

        for idx, ann in enumerate(annotations):
            # Map COCO category to Synapse class
            coco_category = ann.get('category_id')
            synapse_class = self.category_mapping.get(coco_category)

            if not synapse_class:
                self.run.log_message(
                    f'Warning: Unmapped category {coco_category}, skipping'
                )
                continue

            # Convert bbox format: [x, y, width, height]
            bbox = ann.get('bbox', [])
            if len(bbox) != 4:
                continue

            task_object = {
                'id': f'coco_{ann.get("id", idx)}',
                'class_id': synapse_class,
                'type': 'bbox',
                'coordinates': {
                    'x': float(bbox[0]),
                    'y': float(bbox[1]),
                    'width': float(bbox[2]),
                    'height': float(bbox[3])
                },
                'properties': {
                    'area': ann.get('area', 0),
                    'iscrowd': ann.get('iscrowd', 0),
                    'original_category': coco_category
                }
            }
            task_objects.append(task_object)

        return task_objects

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """Not used for this plugin - file-based only."""
        return data
```

### Example 2: Object Detection Inference Plugin

A complete plugin for converting object detection model outputs.

```python
# plugin/to_task.py
from typing import Dict, List

class AnnotationToTask:
    """Convert object detection inference results to Synapse tasks."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # Configuration
        self.confidence_threshold = 0.7
        self.nms_threshold = 0.5
        self.max_detections = 100

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """Not used for this plugin - inference-based only."""
        return {}

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """Convert YOLOv8 detection results to Synapse format."""

        try:
            # Extract predictions
            predictions = data.get('predictions', [])

            if not predictions:
                self.run.log_message('No predictions found in inference results')
                return {'objects': []}

            # Filter and convert detections
            task_objects = self._process_detections(predictions)

            # Apply NMS if needed
            if len(task_objects) > self.max_detections:
                task_objects = self._apply_nms(task_objects)

            self.run.log_message(
                f'Converted {len(task_objects)} detections '
                f'(threshold: {self.confidence_threshold})'
            )

            return {
                'objects': task_objects,
                'metadata': {
                    'model': data.get('model_name', 'unknown'),
                    'inference_time': data.get('inference_time_ms', 0),
                    'confidence_threshold': self.confidence_threshold
                }
            }

        except Exception as e:
            self.run.log_message(f'Inference conversion failed: {str(e)}')
            raise

    def _process_detections(self, predictions: List[Dict]) -> List[Dict]:
        """Process and filter detections."""
        task_objects = []

        for idx, pred in enumerate(predictions):
            confidence = pred.get('confidence', 0.0)

            # Filter by confidence
            if confidence < self.confidence_threshold:
                continue

            # Extract bbox coordinates
            bbox = pred.get('bbox', {})

            task_object = {
                'id': f'det_{idx}',
                'class_id': pred.get('class_id', 0),
                'type': 'bbox',
                'coordinates': {
                    'x': float(bbox.get('x', 0)),
                    'y': float(bbox.get('y', 0)),
                    'width': float(bbox.get('width', 0)),
                    'height': float(bbox.get('height', 0))
                },
                'properties': {
                    'confidence': float(confidence),
                    'class_name': pred.get('class_name', 'unknown'),
                    'model_version': pred.get('model_version', '1.0')
                }
            }
            task_objects.append(task_object)

        return task_objects

    def _apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """Apply Non-Maximum Suppression to reduce overlapping boxes."""
        # Sort by confidence
        sorted_dets = sorted(
            detections,
            key=lambda x: x['properties']['confidence'],
            reverse=True
        )

        # Return top N detections
        return sorted_dets[:self.max_detections]
```

### Example 3: Hybrid Plugin (File + Inference)

A plugin supporting both annotation methods.

```python
# plugin/to_task.py
import requests
import json
from typing import Dict

class AnnotationToTask:
    """Hybrid plugin supporting both file and inference annotation."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        self.default_confidence = 0.8

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """Handle custom JSON annotation format."""

        # Download annotation file
        response = requests.get(data_file_url, timeout=30)
        response.raise_for_status()
        annotation_data = response.json()

        # Convert from custom format
        task_objects = []
        for obj in annotation_data.get('objects', []):
            task_object = {
                'id': obj['id'],
                'class_id': obj['class'],
                'type': obj.get('type', 'bbox'),
                'coordinates': obj['coords'],
                'properties': obj.get('props', {})
            }
            task_objects.append(task_object)

        return {'objects': task_objects}

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """Handle inference results with validation."""

        # Extract and validate predictions
        predictions = data.get('predictions', [])

        task_objects = []
        for idx, pred in enumerate(predictions):
            # Validate required fields
            if not self._validate_prediction(pred):
                continue

            task_object = {
                'id': f'pred_{idx}',
                'class_id': pred['class_id'],
                'type': 'bbox',
                'coordinates': pred['bbox'],
                'properties': {
                    'confidence': pred.get('confidence', self.default_confidence),
                    'source': 'inference'
                }
            }
            task_objects.append(task_object)

        return {'objects': task_objects}

    def _validate_prediction(self, pred: Dict) -> bool:
        """Validate prediction has required fields."""
        required_fields = ['class_id', 'bbox']
        return all(field in pred for field in required_fields)
```

## Best Practices

### 1. Data Validation

Always validate input data before conversion:

```python
def convert_data_from_file(self, *args) -> dict:
    # Validate JSON structure
    if 'required_field' not in data:
        raise ValueError('Missing required field in annotation data')

    # Validate data types
    if not isinstance(data['objects'], list):
        raise TypeError('Objects must be a list')

    # Validate values
    for obj in data['objects']:
        if obj.get('confidence', 0) < 0 or obj.get('confidence', 1) > 1:
            raise ValueError('Confidence must be between 0 and 1')
```

### 2. Error Handling

Implement comprehensive error handling:

```python
def convert_data_from_file(self, *args) -> dict:
    try:
        # Conversion logic
        return converted_data

    except requests.RequestException as e:
        self.run.log_message(f'Network error: {str(e)}')
        raise

    except json.JSONDecodeError as e:
        self.run.log_message(f'Invalid JSON: {str(e)}')
        raise

    except KeyError as e:
        self.run.log_message(f'Missing field: {str(e)}')
        raise

    except Exception as e:
        self.run.log_message(f'Unexpected error: {str(e)}')
        raise
```

### 3. Logging

Use logging to track conversion progress:

```python
def convert_data_from_inference(self, data: dict) -> dict:
    # Log start
    self.run.log_message('Starting inference data conversion')

    predictions = data.get('predictions', [])
    self.run.log_message(f'Processing {len(predictions)} predictions')

    # Process data
    filtered = [p for p in predictions if p['confidence'] > 0.5]
    self.run.log_message(f'Filtered to {len(filtered)} high-confidence predictions')

    # Log completion
    self.run.log_message('Conversion completed successfully')

    return converted_data
```

### 4. Configuration

Make your plugin configurable:

```python
class AnnotationToTask:
    def __init__(self, run, *args, **kwargs):
        self.run = run

        # Get configuration from plugin params
        params = getattr(run, 'params', {})
        pre_processor_params = params.get('pre_processor_params', {})

        # Set configuration
        self.confidence_threshold = pre_processor_params.get('confidence_threshold', 0.7)
        self.nms_threshold = pre_processor_params.get('nms_threshold', 0.5)
        self.max_detections = pre_processor_params.get('max_detections', 100)
```

### 5. Testing

Test your conversions thoroughly:

```python
# test_to_task.py
import pytest
from plugin.to_task import AnnotationToTask

class MockRun:
    def log_message(self, msg):
        print(msg)

def test_convert_coco_format():
    """Test COCO format conversion."""
    converter = AnnotationToTask(MockRun())

    # Mock COCO data
    coco_data = {
        'annotations': [
            {
                'id': 1,
                'category_id': 1,
                'bbox': [10, 20, 100, 200],
                'area': 20000
            }
        ]
    }

    result = converter._convert_coco_annotations(coco_data['annotations'])

    assert len(result) == 1
    assert result[0]['class_id'] == 1
    assert result[0]['coordinates']['x'] == 10

def test_confidence_filtering():
    """Test confidence threshold filtering."""
    converter = AnnotationToTask(MockRun())
    converter.confidence_threshold = 0.7

    predictions = [
        {'confidence': 0.9, 'class_id': 1, 'bbox': {}},
        {'confidence': 0.5, 'class_id': 2, 'bbox': {}},  # Below threshold
        {'confidence': 0.8, 'class_id': 3, 'bbox': {}},
    ]

    result = converter._process_detections(predictions)

    # Only 2 should pass threshold
    assert len(result) == 2
```

## Integration with ToTaskAction

### How Template Methods Are Called

Your template methods are called by the ToTaskAction framework during workflow execution:

**File-based Annotation Flow:**
```
1. ToTaskAction.start()
   ↓
2. ToTaskOrchestrator.execute_workflow()
   ↓
3. FileAnnotationStrategy.process_task()
   ↓
4. annotation_to_task = context.entrypoint(logger)
   ↓
5. converted_data = annotation_to_task.convert_data_from_file(...)
   ↓
6. client.annotate_task_data(task_id, data=converted_data)
```

**Inference-based Annotation Flow:**
```
1. ToTaskAction.start()
   ↓
2. ToTaskOrchestrator.execute_workflow()
   ↓
3. InferenceAnnotationStrategy.process_task()
   ↓
4. inference_result = preprocessor_api.predict(...)
   ↓
5. annotation_to_task = context.entrypoint(logger)
   ↓
6. converted_data = annotation_to_task.convert_data_from_inference(inference_result)
   ↓
7. client.annotate_task_data(task_id, data=converted_data)
```

### Debugging Templates

When debugging your template:

1. **Check Logs**: Review plugin run logs for your log messages
2. **Validate Returns**: Ensure return format matches Synapse task object schema
3. **Test Locally**: Test conversion methods independently before deploying
4. **Inspect Inputs**: Log input parameters to verify data being received
5. **Handle Errors**: Catch and log exceptions with descriptive messages

```python
def convert_data_from_file(self, *args) -> dict:
    # Debug logging
    self.run.log_message(f'Received URLs: primary={args[0]}, data={args[2]}')

    try:
        # Your logic
        result = process_data()

        # Validate result
        self.run.log_message(f'Converted {len(result["objects"])} objects')

        return result

    except Exception as e:
        # Detailed error logging
        self.run.log_message(f'Conversion failed: {type(e).__name__}: {str(e)}')
        import traceback
        self.run.log_message(traceback.format_exc())
        raise
```

## Common Pitfalls

### 1. Incorrect Return Format

**Wrong:**
```python
def convert_data_from_file(self, *args) -> dict:
    return [obj1, obj2, obj3]  # Returns list, not dict
```

**Correct:**
```python
def convert_data_from_file(self, *args) -> dict:
    return {'objects': [obj1, obj2, obj3]}  # Returns dict with 'objects' key
```

### 2. Missing Error Handling

**Wrong:**
```python
def convert_data_from_file(self, *args) -> dict:
    response = requests.get(url)  # No timeout, no error handling
    data = response.json()
    return data
```

**Correct:**
```python
def convert_data_from_file(self, *args) -> dict:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return self._transform_data(data)
    except Exception as e:
        self.run.log_message(f'Error: {str(e)}')
        raise
```

### 3. Not Using Logging

**Wrong:**
```python
def convert_data_from_inference(self, data: dict) -> dict:
    # Silent conversion - no visibility
    return process(data)
```

**Correct:**
```python
def convert_data_from_inference(self, data: dict) -> dict:
    self.run.log_message(f'Converting {len(data["predictions"])} predictions')
    result = process(data)
    self.run.log_message(f'Conversion complete: {len(result["objects"])} objects')
    return result
```

## Related Documentation

- [ToTask Overview](./to-task-overview.md) - User guide for ToTask action
- [ToTask Action Development](./to-task-action-development.md) - SDK developer guide
- [Pre-annotation Plugin Overview](./pre-annotation-plugin-overview.md) - Category overview
- Plugin Development Guide - General plugin development

## Template Source Code

- Template: `synapse_sdk/plugins/categories/pre_annotation/templates/plugin/to_task.py`
- Called by: `synapse_sdk/plugins/categories/pre_annotation/actions/to_task/strategies/annotation.py`
