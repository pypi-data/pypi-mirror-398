from __future__ import annotations

from enum import StrEnum


class PluginCategory(StrEnum):
    """Categories for organizing plugins by functionality."""

    NEURAL_NET = 'neural_net'
    EXPORT = 'export'
    UPLOAD = 'upload'
    SMART_TOOL = 'smart_tool'
    POST_ANNOTATION = 'post_annotation'
    PRE_ANNOTATION = 'pre_annotation'
    DATA_VALIDATION = 'data_validation'
    CUSTOM = 'custom'


class RunMethod(StrEnum):
    """Execution methods for plugin actions."""

    JOB = 'job'
    TASK = 'task'
    SERVE = 'serve'


class PackageManager(StrEnum):
    """Package managers for plugin dependencies."""

    PIP = 'pip'
    UV = 'uv'


class DataType(StrEnum):
    """Data types handled by plugins."""

    IMAGE = 'image'
    TEXT = 'text'
    VIDEO = 'video'
    PCD = 'pcd'
    AUDIO = 'audio'


class AnnotationCategory(StrEnum):
    """Annotation categories for smart tools."""

    OBJECT_DETECTION = 'object_detection'
    CLASSIFICATION = 'classification'
    SEGMENTATION = 'segmentation'
    KEYPOINT = 'keypoint'
    TEXT = 'text'


class AnnotationType(StrEnum):
    """Annotation types for smart tools."""

    BBOX = 'bbox'
    POLYGON = 'polygon'
    POINT = 'point'
    LINE = 'line'
    MASK = 'mask'
    LABEL = 'label'


class SmartToolType(StrEnum):
    """Smart tool implementation types."""

    INTERACTIVE = 'interactive'
    AUTOMATIC = 'automatic'
    SEMI_AUTOMATIC = 'semi_automatic'


__all__ = [
    'PluginCategory',
    'RunMethod',
    'PackageManager',
    'DataType',
    'AnnotationCategory',
    'AnnotationType',
    'SmartToolType',
]
