"""DatamakerV1 and DatamakerV2 format Pydantic models.

Supports both schema versions:
- DMv1: Event-based, per-assignment structure (annotations keyed by asset)
- DMv2: Collection-based, organized by media type (images array)

Version must be explicitly specified when using converters.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DMVersion(StrEnum):
    """DataMaker schema version."""

    V1 = 'v1'
    V2 = 'v2'


# =============================================================================
# Shared Types
# =============================================================================


class DMAttribute(BaseModel):
    """Attribute on an annotation (shared between v1/v2).

    Attributes:
        name: Attribute name.
        value: Attribute value (string, number, boolean, or list).
    """

    name: str
    value: str | int | float | bool | list[str]


# =============================================================================
# DataMaker V1 Models (Event-based, per-assignment)
# =============================================================================


class DMv1Classification(BaseModel):
    """V1 classification as flat key-value pairs.

    Structure defined by admin but stored flat.
    """

    model_config = {'extra': 'allow'}


class DMv1AnnotationBase(BaseModel):
    """V1 base annotation object.

    Attributes:
        id: Unique annotation ID.
        tool: Name of the tool used.
        isLocked: Whether annotation is locked.
        isVisible: Whether annotation is visible.
        classification: Flat key-value classification attributes.
    """

    id: str
    tool: str
    isLocked: bool = False
    isVisible: bool = True
    classification: DMv1Classification | None = None

    model_config = {'extra': 'allow'}


class DMv1RelationItem(BaseModel):
    """V1 relation (edge) between annotations.

    Attributes:
        id: Unique relation ID.
        tool: Always 'relation'.
        annotationId: Source annotation ID.
        targetAnnotationId: Target annotation ID.
        classification: Attributes assigned to the relation.
    """

    id: str
    tool: str = 'relation'
    isLocked: bool = False
    isVisible: bool = True
    annotationId: str
    targetAnnotationId: str
    classification: DMv1Classification | None = None


class DMv1GroupMemberItem(BaseModel):
    """V1 group member with optional hierarchy.

    Attributes:
        annotationId: ID of annotation in group.
        children: Sub-groups or hierarchical structure.
    """

    annotationId: str
    children: list[DMv1GroupMemberItem] = Field(default_factory=list)


class DMv1AnnotationGroupItem(BaseModel):
    """V1 annotation group.

    Attributes:
        id: Unique group ID.
        tool: Always 'annotationGroup'.
        classification: Group classification.
        annotationList: List of group members.
    """

    id: str
    tool: str = 'annotationGroup'
    isLocked: bool = False
    classification: DMv1Classification | None = None
    annotationList: list[DMv1GroupMemberItem] = Field(default_factory=list)


class DMv1AnnotationDataItem(BaseModel):
    """V1 supplementary annotation data (frames, model results).

    Attributes:
        frameIndex: Frame number for video/time-series.
        section: Start/end frame range.
        input: Prompt input.
        output: Model output.
    """

    frameIndex: int | None = None
    section: dict[str, int] | None = None  # {startFrame, endFrame}
    input: str | None = None
    output: str | None = None


class DMv1Dataset(BaseModel):
    """DataMaker V1 dataset schema (event-based).

    Per-assignment structure with annotations keyed by asset.

    Attributes:
        assignmentId: Optional job identifier.
        extra: Asset-level additional metadata.
        annotations: Annotations per asset (Record<string, AnnotationBase[]>).
        relations: Relationships between annotations.
        annotationGroups: Grouping information.
        annotationsData: Supplementary data (frames, model results).

    Example:
        >>> dataset = DMv1Dataset(
        ...     assignmentId='job-123',
        ...     annotations={'image_0': [annotation1, annotation2]},
        ... )
    """

    assignmentId: str | None = None
    extra: dict | None = None
    annotations: dict[str, list[DMv1AnnotationBase]] = Field(default_factory=dict)
    relations: dict[str, list[DMv1RelationItem]] = Field(default_factory=dict)
    annotationGroups: dict[str, list[DMv1AnnotationGroupItem]] = Field(default_factory=dict)
    annotationsData: dict[str, list[DMv1AnnotationDataItem]] = Field(default_factory=dict)


# =============================================================================
# DataMaker V2 Models (Collection-based, organized by media type)
# =============================================================================


class DMv2AnnotationBase(BaseModel):
    """V2 base annotation with id, classification, and attrs.

    Attributes:
        id: Unique annotation ID (alphanumeric, typically 10 chars).
        classification: Class label for this annotation.
        attrs: Optional list of attributes.
    """

    id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$')
    classification: str
    attrs: list[DMAttribute] = Field(default_factory=list)


class DMv2BoundingBox(DMv2AnnotationBase):
    """V2 bounding box annotation.

    Attributes:
        data: [x, y, width, height] in absolute pixel coordinates.
    """

    data: tuple[float, float, float, float]


class DMv2Polygon(DMv2AnnotationBase):
    """V2 polygon annotation.

    Attributes:
        data: List of [x, y] points forming the polygon.
    """

    data: list[tuple[float, float]]


class DMv2Polyline(DMv2AnnotationBase):
    """V2 polyline annotation (open path).

    Attributes:
        data: List of [x, y] points forming the polyline.
    """

    data: list[tuple[float, float]]


class DMv2Keypoint(DMv2AnnotationBase):
    """V2 single keypoint annotation.

    Attributes:
        data: [x, y] coordinate.
    """

    data: tuple[float, float]


class DMv2Relation(DMv2AnnotationBase):
    """V2 relation annotation linking two annotations.

    Attributes:
        data: [from_id, to_id] annotation IDs.
    """

    data: tuple[str, str]


class DMv2Group(DMv2AnnotationBase):
    """V2 group annotation containing multiple annotation IDs.

    Attributes:
        data: List of annotation IDs in the group.
    """

    data: list[str]


class DMv2ImageItem(BaseModel):
    """V2 container for 2D image annotations.

    Groups all annotation types for a single image.
    """

    bounding_box: list[DMv2BoundingBox] = Field(default_factory=list)
    polygon: list[DMv2Polygon] = Field(default_factory=list)
    polyline: list[DMv2Polyline] = Field(default_factory=list)
    keypoint: list[DMv2Keypoint] = Field(default_factory=list)
    relation: list[DMv2Relation] = Field(default_factory=list)
    group: list[DMv2Group] = Field(default_factory=list)


class DMv2Dataset(BaseModel):
    """DataMaker V2 dataset schema (collection-based).

    Organized by media type with typed annotation arrays.

    Attributes:
        classification: Mapping of tool types to available class labels.
        images: List of image annotation containers.

    Example:
        >>> dataset = DMv2Dataset(
        ...     classification={'bounding_box': ['car', 'person']},
        ...     images=[DMv2ImageItem(bounding_box=[...])],
        ... )
        >>> class_names = dataset.get_class_names('bounding_box')
    """

    classification: dict[str, list[str]] = Field(default_factory=dict)
    images: list[DMv2ImageItem] = Field(default_factory=list)

    def get_class_names(self, tool: str = 'bounding_box') -> list[str]:
        """Get class names for a specific annotation tool.

        Args:
            tool: Tool type (e.g., 'bounding_box', 'polygon').

        Returns:
            List of class names for the tool.
        """
        return self.classification.get(tool, [])

    def get_all_class_names(self) -> list[str]:
        """Get all unique class names across all tools.

        Returns:
            Sorted list of unique class names.
        """
        all_classes: set[str] = set()
        for classes in self.classification.values():
            all_classes.update(classes)
        return sorted(all_classes)


# =============================================================================
# Aliases for backward compatibility / convenience
# =============================================================================

# Default to V2 models for convenience
DMBoundingBox = DMv2BoundingBox
DMPolygon = DMv2Polygon
DMPolyline = DMv2Polyline
DMKeypoint = DMv2Keypoint
DMRelation = DMv2Relation
DMGroup = DMv2Group
DMImageItem = DMv2ImageItem
DMDataset = DMv2Dataset


__all__ = [
    # Version enum
    'DMVersion',
    # Shared
    'DMAttribute',
    # V1 Models
    'DMv1AnnotationBase',
    'DMv1AnnotationDataItem',
    'DMv1AnnotationGroupItem',
    'DMv1Classification',
    'DMv1Dataset',
    'DMv1GroupMemberItem',
    'DMv1RelationItem',
    # V2 Models
    'DMv2AnnotationBase',
    'DMv2BoundingBox',
    'DMv2Dataset',
    'DMv2Group',
    'DMv2ImageItem',
    'DMv2Keypoint',
    'DMv2Polygon',
    'DMv2Polyline',
    'DMv2Relation',
    # Aliases (default to V2)
    'DMBoundingBox',
    'DMDataset',
    'DMGroup',
    'DMImageItem',
    'DMKeypoint',
    'DMPolygon',
    'DMPolyline',
    'DMRelation',
]
