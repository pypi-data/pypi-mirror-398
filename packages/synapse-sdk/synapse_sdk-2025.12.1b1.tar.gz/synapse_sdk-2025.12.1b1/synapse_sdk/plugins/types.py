"""Data types for action input/output declarations.

Provides type classes for declaring what data an action expects and produces.
Used by ActionPipeline to validate compatibility between actions.

Example:
    >>> from synapse_sdk.plugins.types import YOLODataset, ModelWeights
    >>>
    >>> class TrainAction(BaseTrainAction[TrainParams]):
    ...     input_type = YOLODataset
    ...     output_type = ModelWeights
"""

from __future__ import annotations

from typing import ClassVar


class DataType:
    """Base class for action input/output type declarations.

    Subclass to define semantic data types that actions can consume or produce.
    Types are compatible if they are the same class or one is a subclass of the other.

    Class Attributes:
        name: Human-readable type name.
        format: Data format identifier (e.g., 'yolo', 'coco', 'dm_v2').
        description: Optional description of the data type.

    Example:
        >>> class MyCustomDataset(DataType):
        ...     name = 'my_dataset'
        ...     format = 'custom'
        ...     description = 'My custom dataset format'
    """

    name: ClassVar[str] = 'data'
    format: ClassVar[str | None] = None
    description: ClassVar[str] = ''

    @classmethod
    def is_compatible_with(cls, other: type[DataType]) -> bool:
        """Check if this type is compatible with another type.

        Types are compatible if:
        - They are the same class
        - One is a subclass of the other

        Args:
            other: The other DataType class to check compatibility with.

        Returns:
            True if types are compatible.
        """
        return issubclass(cls, other) or issubclass(other, cls)

    @classmethod
    def __repr__(cls) -> str:
        return f'<DataType: {cls.name}>'


# -----------------------------------------------------------------------------
# Dataset Types
# -----------------------------------------------------------------------------


class Dataset(DataType):
    """Base type for all dataset formats."""

    name: ClassVar[str] = 'dataset'
    description: ClassVar[str] = 'Generic dataset'


class DMDataset(Dataset):
    """Datamaker format dataset (v1 or v2)."""

    name: ClassVar[str] = 'dm_dataset'
    format: ClassVar[str] = 'dm'
    description: ClassVar[str] = 'Datamaker format dataset'


class DMv1Dataset(DMDataset):
    """Datamaker v1 format dataset."""

    name: ClassVar[str] = 'dm_v1_dataset'
    format: ClassVar[str] = 'dm_v1'
    description: ClassVar[str] = 'Datamaker v1 format dataset'


class DMv2Dataset(DMDataset):
    """Datamaker v2 format dataset."""

    name: ClassVar[str] = 'dm_v2_dataset'
    format: ClassVar[str] = 'dm_v2'
    description: ClassVar[str] = 'Datamaker v2 format dataset'


class YOLODataset(Dataset):
    """YOLO format dataset with dataset.yaml config."""

    name: ClassVar[str] = 'yolo_dataset'
    format: ClassVar[str] = 'yolo'
    description: ClassVar[str] = 'YOLO format dataset with dataset.yaml'


class COCODataset(Dataset):
    """COCO format dataset."""

    name: ClassVar[str] = 'coco_dataset'
    format: ClassVar[str] = 'coco'
    description: ClassVar[str] = 'COCO format dataset'


class PascalVOCDataset(Dataset):
    """Pascal VOC format dataset."""

    name: ClassVar[str] = 'pascal_voc_dataset'
    format: ClassVar[str] = 'pascal'
    description: ClassVar[str] = 'Pascal VOC format dataset'


# -----------------------------------------------------------------------------
# Model Types
# -----------------------------------------------------------------------------


class Model(DataType):
    """Base type for all model formats."""

    name: ClassVar[str] = 'model'
    description: ClassVar[str] = 'Generic model'


class ModelWeights(Model):
    """Trained model weights."""

    name: ClassVar[str] = 'model_weights'
    format: ClassVar[str] = 'weights'
    description: ClassVar[str] = 'Trained model weights'


class ONNXModel(Model):
    """ONNX format model."""

    name: ClassVar[str] = 'onnx_model'
    format: ClassVar[str] = 'onnx'
    description: ClassVar[str] = 'ONNX format model'


class TensorRTModel(Model):
    """TensorRT format model."""

    name: ClassVar[str] = 'tensorrt_model'
    format: ClassVar[str] = 'tensorrt'
    description: ClassVar[str] = 'TensorRT format model'


# -----------------------------------------------------------------------------
# Result Types
# -----------------------------------------------------------------------------


class Result(DataType):
    """Base type for action results."""

    name: ClassVar[str] = 'result'
    description: ClassVar[str] = 'Generic result'


class TestResults(Result):
    """Test/evaluation results with metrics."""

    name: ClassVar[str] = 'test_results'
    format: ClassVar[str] = 'metrics'
    description: ClassVar[str] = 'Test results with metrics'


class InferenceResults(Result):
    """Inference/prediction results."""

    name: ClassVar[str] = 'inference_results'
    format: ClassVar[str] = 'predictions'
    description: ClassVar[str] = 'Inference predictions'


__all__ = [
    # Base
    'DataType',
    # Datasets
    'Dataset',
    'DMDataset',
    'DMv1Dataset',
    'DMv2Dataset',
    'YOLODataset',
    'COCODataset',
    'PascalVOCDataset',
    # Models
    'Model',
    'ModelWeights',
    'ONNXModel',
    'TensorRTModel',
    # Results
    'Result',
    'TestResults',
    'InferenceResults',
]
