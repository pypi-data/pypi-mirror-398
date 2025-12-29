"""Common schema types for plugin actions."""

from synapse_sdk.plugins.schemas.results import (
    ExportResult,
    InferenceResult,
    MetricsResult,
    TrainResult,
    UploadResult,
    WeightsResult,
)

__all__ = [
    'ExportResult',
    'InferenceResult',
    'MetricsResult',
    'TrainResult',
    'UploadResult',
    'WeightsResult',
]
