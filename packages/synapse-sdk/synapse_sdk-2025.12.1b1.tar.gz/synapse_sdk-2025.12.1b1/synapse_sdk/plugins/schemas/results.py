"""Common result types for plugin actions.

These provide standardized schemas for common action outputs.
Plugin developers can use these directly or extend them for
custom result types.

Example usage:
    >>> from synapse_sdk.plugins import BaseTrainAction
    >>> from synapse_sdk.plugins.schemas import TrainResult
    >>>
    >>> class MyTrainAction(BaseTrainAction[MyParams, TrainResult]):
    ...     def execute(self) -> TrainResult:
    ...         return TrainResult(
    ...             weights_path='/models/best.pt',
    ...             final_epoch=100,
    ...             train_metrics={'loss': 0.05},
    ...             val_metrics={'mAP50': 0.85},
    ...         )
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WeightsResult(BaseModel):
    """Result type for actions that produce model weights.

    Use this for actions that output trained model weights.

    Example:
        >>> class TrainAction(BaseAction[TrainParams, WeightsResult]):
        ...     def execute(self) -> WeightsResult:
        ...         return WeightsResult(
        ...             weights_path='/models/best.pt',
        ...             checkpoint_paths=['/models/epoch_10.pt'],
        ...         )
    """

    weights_path: str = Field(description='Path to the best/final model weights')
    checkpoint_paths: list[str] = Field(default_factory=list, description='Paths to intermediate checkpoints')
    format: str = Field(default='pt', description='Weights format (pt, onnx, safetensors, etc.)')


class MetricsResult(BaseModel):
    """Result type for actions that produce metrics only.

    Use this for evaluation/testing actions that output metrics.

    Example:
        >>> class EvalAction(BaseAction[EvalParams, MetricsResult]):
        ...     def execute(self) -> MetricsResult:
        ...         return MetricsResult(
        ...             metrics={'mAP50': 0.85, 'mAP50-95': 0.72},
        ...             category='validation',
        ...         )
    """

    metrics: dict[str, float] = Field(description='Metric name to value mapping')
    category: str = Field(default='default', description='Metrics category (train, validation, test)')


class TrainResult(BaseModel):
    """Combined result type for training actions.

    Includes both weights and training metrics. Use this for
    standard training workflows.

    Example:
        >>> class TrainAction(BaseTrainAction[TrainParams, TrainResult]):
        ...     def execute(self) -> TrainResult:
        ...         return TrainResult(
        ...             weights_path='/models/best.pt',
        ...             final_epoch=100,
        ...             best_epoch=85,
        ...             train_metrics={'loss': 0.05},
        ...             val_metrics={'mAP50': 0.85, 'mAP50-95': 0.72},
        ...         )
    """

    weights_path: str = Field(description='Path to trained model weights')
    final_epoch: int = Field(description='Last completed epoch')
    best_epoch: int | None = Field(default=None, description='Best epoch by validation metric')
    train_metrics: dict[str, float] = Field(default_factory=dict, description='Final training metrics')
    val_metrics: dict[str, float] = Field(default_factory=dict, description='Final validation metrics')


class InferenceResult(BaseModel):
    """Result type for inference actions.

    Generic container for inference outputs.

    Example:
        >>> class InferAction(BaseInferenceAction[InferParams, InferenceResult]):
        ...     def execute(self) -> InferenceResult:
        ...         return InferenceResult(
        ...             predictions=[{'class': 'dog', 'confidence': 0.95}],
        ...             processed_count=100,
        ...         )
    """

    predictions: list[dict[str, Any]] = Field(default_factory=list, description='List of prediction results')
    processed_count: int = Field(default=0, description='Number of items processed')
    output_path: str | None = Field(default=None, description='Path to output file if results were saved')


class ExportResult(BaseModel):
    """Result type for export actions.

    Example:
        >>> class ExportAction(BaseExportAction[ExportParams, ExportResult]):
        ...     def execute(self) -> ExportResult:
        ...         return ExportResult(
        ...             output_path='/exports/dataset.zip',
        ...             exported_count=1000,
        ...             format='coco',
        ...         )
    """

    output_path: str = Field(description='Path to exported file/directory')
    exported_count: int = Field(description='Number of items exported')
    format: str = Field(description='Export format (coco, yolo, voc, csv, etc.)')
    file_size_bytes: int | None = Field(default=None, description='Size of exported file in bytes')


class UploadResult(BaseModel):
    """Result type for upload actions.

    Example:
        >>> class UploadAction(BaseUploadAction[UploadParams, UploadResult]):
        ...     def execute(self) -> UploadResult:
        ...         return UploadResult(
        ...             uploaded_count=500,
        ...             remote_path='s3://bucket/dataset/',
        ...         )
    """

    uploaded_count: int = Field(description='Number of items uploaded')
    remote_path: str | None = Field(default=None, description='Remote path or URL where data was uploaded')
    status: str = Field(default='completed', description='Upload status')


__all__ = [
    'ExportResult',
    'InferenceResult',
    'MetricsResult',
    'TrainResult',
    'UploadResult',
    'WeightsResult',
]
