"""Dataset format Pydantic models."""

from __future__ import annotations

from synapse_sdk.plugins.datasets.formats.dm import (
    # Shared
    DMAttribute,
    # Aliases (default to V2)
    DMBoundingBox,
    DMDataset,
    DMGroup,
    DMImageItem,
    DMKeypoint,
    DMPolygon,
    DMPolyline,
    DMRelation,
    # V1 Models
    DMv1AnnotationBase,
    DMv1AnnotationDataItem,
    DMv1AnnotationGroupItem,
    DMv1Classification,
    DMv1Dataset,
    DMv1GroupMemberItem,
    DMv1RelationItem,
    # V2 Models
    DMv2AnnotationBase,
    DMv2BoundingBox,
    DMv2Dataset,
    DMv2Group,
    DMv2ImageItem,
    DMv2Keypoint,
    DMv2Polygon,
    DMv2Polyline,
    DMv2Relation,
    # Version enum
    DMVersion,
)
from synapse_sdk.plugins.datasets.formats.yolo import (
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
    'DMv1AnnotationDataItem',
    'DMv1AnnotationGroupItem',
    'DMv1Classification',
    'DMv1Dataset',
    'DMv1GroupMemberItem',
    'DMv1RelationItem',
    # DM V2
    'DMv2AnnotationBase',
    'DMv2BoundingBox',
    'DMv2Dataset',
    'DMv2Group',
    'DMv2ImageItem',
    'DMv2Keypoint',
    'DMv2Polygon',
    'DMv2Polyline',
    'DMv2Relation',
    # DM Aliases (V2)
    'DMBoundingBox',
    'DMDataset',
    'DMGroup',
    'DMImageItem',
    'DMKeypoint',
    'DMPolygon',
    'DMPolyline',
    'DMRelation',
    # YOLO
    'YOLOAnnotation',
    'YOLODataset',
    'YOLODatasetConfig',
    'YOLOImage',
]
