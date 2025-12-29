"""Dataset formats and converters.

This module provides:
- Pydantic models for dataset formats (Datamaker v1/v2, YOLO)
- Bidirectional converters between formats

For dataset download and conversion workflows, use DatasetAction:
    from synapse_sdk.plugins.actions import DatasetAction, DatasetParams

For pipeline orchestration:
    from synapse_sdk.plugins.pipelines import ActionPipeline

Example:
    >>> from synapse_sdk.plugins.datasets import (
    ...     DatasetFormat,
    ...     FromDMToYOLOConverter,
    ...     DMVersion,
    ... )
    >>> from synapse_sdk.plugins.actions import DatasetAction
    >>> from synapse_sdk.plugins.pipelines import ActionPipeline
    >>>
    >>> # Pipeline: Download | Convert | Train
    >>> pipeline = ActionPipeline([DatasetAction, DatasetAction, TrainAction])
"""

from __future__ import annotations

from synapse_sdk.plugins.datasets.converters import (
    BaseConverter,
    DatasetFormat,
    FromDMConverter,
    FromDMToYOLOConverter,
    ToDMConverter,
    YOLOToDMConverter,
    get_converter,
)
from synapse_sdk.plugins.datasets.formats import (
    # DM Shared
    DMAttribute,
    # DM Aliases (V2)
    DMBoundingBox,
    DMDataset,
    DMGroup,
    DMImageItem,
    DMKeypoint,
    DMPolygon,
    DMPolyline,
    DMRelation,
    # DM V1
    DMv1AnnotationBase,
    DMv1Classification,
    DMv1Dataset,
    # DM V2
    DMv2BoundingBox,
    DMv2Dataset,
    DMv2Group,
    DMv2ImageItem,
    DMv2Keypoint,
    DMv2Polygon,
    DMv2Polyline,
    DMv2Relation,
    # DM Version
    DMVersion,
    # YOLO
    YOLOAnnotation,
    YOLODataset,
    YOLODatasetConfig,
    YOLOImage,
)

__all__ = [
    # DM Version
    'DMVersion',
    # DM Shared
    'DMAttribute',
    # DM V1
    'DMv1AnnotationBase',
    'DMv1Classification',
    'DMv1Dataset',
    # DM V2
    'DMv2BoundingBox',
    'DMv2Dataset',
    'DMv2ImageItem',
    'DMv2Keypoint',
    'DMv2Polygon',
    'DMv2Polyline',
    'DMv2Relation',
    'DMv2Group',
    # DM Aliases (V2 default)
    'DMBoundingBox',
    'DMDataset',
    'DMGroup',
    'DMImageItem',
    'DMKeypoint',
    'DMPolygon',
    'DMPolyline',
    'DMRelation',
    # YOLO Formats
    'YOLOAnnotation',
    'YOLODataset',
    'YOLODatasetConfig',
    'YOLOImage',
    # Converters - Base
    'BaseConverter',
    'DatasetFormat',
    'FromDMConverter',
    'ToDMConverter',
    # Converters - YOLO
    'FromDMToYOLOConverter',
    'YOLOToDMConverter',
    # Converter factory
    'get_converter',
]
